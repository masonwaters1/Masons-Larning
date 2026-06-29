from django.conf import settings
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from .models import Course, Lesson, Progress, Highlight

_NUMBER_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
                 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}


def _count_word(n):
    return _NUMBER_WORDS.get(n, str(n))



def _next_unread():
    """Next unread lesson in interleaved order, preferring lessons that are
    actually written so 'Continue' lands on real content rather than a
    coming-soon page. Falls back to the first unread lesson when every written
    lesson has already been read."""
    first_unread = None
    for lesson in Lesson.global_queryset():
        if not lesson.is_read:
            if first_unread is None:
                first_unread = lesson
            if lesson.is_written:
                return lesson
    return first_unread


def dashboard(request):
    courses = Course.objects.all()
    total = Lesson.objects.count()
    read = Progress.objects.filter(is_read=True).count()
    seq = list(Lesson.global_queryset())
    nxt = _next_unread()

    # Group the interleaved sequence into "rounds" (one lesson number across courses)
    grouped = {}
    for lesson in seq:
        grouped.setdefault(lesson.course_lesson_number, []).append(lesson)
    rounds = sorted(grouped.items())

    # Show a window of ~6 rounds starting just before the next unread lesson.
    start = 0
    if nxt:
        target = nxt.course_lesson_number
        idx = next((i for i, (n, _) in enumerate(rounds) if n == target), 0)
        start = max(0, idx - 1)
    preview = rounds[start:start + 6]

    context = {
        "courses": courses,
        "course_count_word": _count_word(Course.objects.count()),
        "total": total,
        "read": read,
        "percent": round(100 * read / total) if total else 0,
        "next_lesson": nxt,
        "rounds": preview,
        "round_total": len(rounds),
        "active": "dashboard",
    }
    return render(request, "courses/dashboard.html", context)


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    units = course.units.prefetch_related("lessons").all()
    context = {
        "course": course,
        "units": units,
        "next_lesson": _next_unread(),
        "active": "course",
    }
    return render(request, "courses/course_detail.html", context)


@ensure_csrf_cookie
def lesson_detail(request, course_slug, slug):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, course=course, slug=slug)
    # ensure a progress row exists
    Progress.objects.get_or_create(lesson=lesson)
    highlights = [
        {
            "id": h.id,
            "start": h.start_offset,
            "end": h.end_offset,
            "quote": h.quote,
            "note": h.note,
            "color": h.color,
        }
        for h in lesson.highlights.all()
    ]
    context = {
        "course": course,
        "lesson": lesson,
        "prev": lesson.get_previous(),
        "next": lesson.get_next(),
        "active": "lesson",
        "courses": Course.objects.all(),
        "course_count_word": _count_word(Course.objects.count()),
        "highlights_json": highlights,
    }
    return render(request, "courses/lesson_detail.html", context)


@require_POST
def toggle_read(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    prog, _ = Progress.objects.get_or_create(lesson=lesson)
    prog.is_read = not prog.is_read
    prog.read_at = timezone.now() if prog.is_read else None
    prog.save()
    nxt = lesson.get_next()
    return JsonResponse({
        "is_read": prog.is_read,
        "next_url": nxt.get_absolute_url() if (prog.is_read and nxt) else None,
    })


@require_POST
def highlight_create(request, lesson_id):
    """Create a highlight (and optional note) on a lesson."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    try:
        data = json.loads(request.body or "{}")
        start = int(data["start"])
        end = int(data["end"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "bad request"}, status=400)
    if end <= start:
        return JsonResponse({"error": "empty range"}, status=400)
    color = (data.get("color") or "yellow")[:10]
    h = Highlight.objects.create(
        lesson=lesson,
        start_offset=start,
        end_offset=end,
        quote=(data.get("quote") or "")[:5000],
        note=(data.get("note") or "")[:10000],
        color=color,
    )
    return JsonResponse({
        "id": h.id, "start": h.start_offset, "end": h.end_offset,
        "quote": h.quote, "note": h.note, "color": h.color,
    })


@require_POST
def highlight_update(request, highlight_id):
    """Update a highlight's note and/or color."""
    h = get_object_or_404(Highlight, id=highlight_id)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "bad request"}, status=400)
    if "note" in data:
        h.note = (data.get("note") or "")[:10000]
    if "color" in data:
        h.color = (data.get("color") or "yellow")[:10]
    h.save()
    return JsonResponse({"id": h.id, "note": h.note, "color": h.color})


@require_POST
def highlight_delete(request, highlight_id):
    """Delete a highlight."""
    h = get_object_or_404(Highlight, id=highlight_id)
    h.delete()
    return JsonResponse({"ok": True})


def pin_view(request):
    """Show a PIN entry page; on the correct PIN, unlock the session."""
    if request.session.get("pin_ok"):
        return redirect("courses:dashboard")
    error = False
    if request.method == "POST":
        entered = (request.POST.get("pin") or "").strip()
        if entered == str(settings.ACCESS_PIN):
            request.session["pin_ok"] = True
            nxt = request.GET.get("next") or request.POST.get("next") or ""
            if nxt.startswith("/"):
                return redirect(nxt)
            return redirect("courses:dashboard")
        error = True
    return render(request, "courses/pin.html",
                  {"error": error, "next": request.GET.get("next", "")})


def lock_view(request):
    """Clear the session, re-locking the site behind the PIN."""
    request.session.flush()
    return redirect("pin")
