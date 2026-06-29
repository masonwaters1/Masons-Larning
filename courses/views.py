from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from .models import Course, Lesson, Progress


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
    context = {
        "course": course,
        "lesson": lesson,
        "prev": lesson.get_previous(),
        "next": lesson.get_next(),
        "active": "lesson",
        "courses": Course.objects.all(),
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
