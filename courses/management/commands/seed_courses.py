import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from courses.models import Course, Unit, Lesson, Progress

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
LESSON_DIR = DATA_DIR / "lessons"
DASH = "\u2014"  # em dash used as title/summary separator


def split_dash(line):
    """Split 'Title — Summary' on the first em dash. Returns (title, summary)."""
    if DASH in line:
        title, summary = line.split(DASH, 1)
        return title.strip(), summary.strip()
    return line.strip(), ""


class Command(BaseCommand):
    help = "Seed the four courses, their units and lessons from data/*.txt, " \
           "and load any full lesson markdown found in data/lessons/."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Delete existing courses before seeding.")

    def handle(self, *args, **opts):
        if opts["reset"]:
            Course.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing courses cleared."))

        files = sorted(DATA_DIR.glob("c*.txt"))
        for order, path in enumerate(files, start=1):
            self._seed_file(path, order)

        self._load_lessons()
        self.stdout.write(self.style.SUCCESS(
            f"Done. {Course.objects.count()} courses, "
            f"{Unit.objects.count()} units, {Lesson.objects.count()} lessons."))

    def _seed_file(self, path, order):
        lines = path.read_text(encoding="utf-8").splitlines()
        meta = {}
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith("@UNIT"):
                body_start = i
                break
            if "|" in line:
                k, v = line.split("|", 1)
                meta[k.strip()] = v.strip()

        course, _ = Course.objects.update_or_create(
            order=order,
            defaults={
                "slug": slugify(meta["TITLE"])[:50],
                "title": meta["TITLE"],
                "subtitle": meta.get("SUBTITLE", ""),
                "description": meta.get("DESC", ""),
                "accent": meta.get("ACCENT", "#3a3a3a"),
                "accent_soft": meta.get("ACCENTSOFT", "#ece8e1"),
            },
        )
        # Idempotent rebuild: update structure in place rather than deleting it,
        # so that reading Progress (a OneToOne on Lesson) survives every re-run.
        # This lets the deploy re-run seed_courses on each push to load new
        # lessons WITHOUT wiping which lessons have been marked as read.
        unit = None
        lesson_counter = 0
        order_in_unit = 0
        used_slugs = set()
        seen_unit_numbers = []
        seen_lesson_numbers = []
        for line in lines[body_start:]:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("@UNIT"):
                _, num, title, subtitle = (line.split("|") + ["", "", ""])[:4]
                unit, _ = Unit.objects.update_or_create(
                    course=course, number=int(num),
                    defaults={
                        "title": title.strip(),
                        "subtitle": subtitle.strip(),
                        "order": int(num),
                    },
                )
                seen_unit_numbers.append(int(num))
                order_in_unit = 0
                continue
            # lesson line
            lesson_counter += 1
            order_in_unit += 1
            title, summary = split_dash(line)
            base = slugify(title)[:60] or f"lesson-{lesson_counter}"
            slug = base
            n = 2
            while slug in used_slugs:
                slug = f"{base}-{n}"
                n += 1
            used_slugs.add(slug)
            lesson, _ = Lesson.objects.update_or_create(
                course=course, course_lesson_number=lesson_counter,
                defaults={
                    "unit": unit,
                    "order_in_unit": order_in_unit,
                    "title": title,
                    "summary": summary,
                    "slug": slug,
                },
            )
            seen_lesson_numbers.append(lesson_counter)
            Progress.objects.get_or_create(lesson=lesson)

        # Remove any structure no longer present in the seed file (rare). Lessons
        # that still exist keep their row — and therefore their Progress.
        course.all_lessons.exclude(
            course_lesson_number__in=seen_lesson_numbers).delete()
        course.units.exclude(number__in=seen_unit_numbers).delete()

        self.stdout.write(f"  Course {order}: {course.title} "
                          f"({course.units.count()} units, {lesson_counter} lessons)")

    def _load_lessons(self):
        """Load full lesson content from data/lessons/cN_LL.md if present.
        Filename convention: c{course_order}_l{course_lesson_number}.md"""
        if not LESSON_DIR.exists():
            return
        loaded = 0
        for f in sorted(LESSON_DIR.glob("c*_l*.md")):
            m = re.match(r"c(\d+)_l(\d+)", f.stem)
            if not m:
                continue
            c_order, l_num = int(m.group(1)), int(m.group(2))
            try:
                lesson = Lesson.objects.get(
                    course__order=c_order, course_lesson_number=l_num)
            except Lesson.DoesNotExist:
                continue
            lesson.content = f.read_text(encoding="utf-8")
            lesson.save(update_fields=["content"])
            loaded += 1
        if loaded:
            self.stdout.write(self.style.SUCCESS(f"  Loaded {loaded} full lesson(s)."))
