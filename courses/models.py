from django.db import models
from django.urls import reverse


class Course(models.Model):
    """A top-level course. `order` controls position in the interleaved sequence
    (Course 1 lesson read before Course 2 lesson at the same lesson number)."""
    order = models.PositiveIntegerField(unique=True)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=400, blank=True)
    description = models.TextField(blank=True)
    accent = models.CharField(max_length=7, default="#3a3a3a")
    accent_soft = models.CharField(max_length=7, default="#ece8e1")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.title}"

    def get_absolute_url(self):
        return reverse("courses:course_detail", args=[self.slug])

    @property
    def lessons(self):
        return Lesson.objects.filter(course=self).order_by("course_lesson_number")

    @property
    def total_lessons(self):
        return self.lessons.count()

    @property
    def read_count(self):
        return self.lessons.filter(progress__is_read=True).count()

    @property
    def percent_complete(self):
        total = self.total_lessons
        return round(100 * self.read_count / total) if total else 0


class Unit(models.Model):
    course = models.ForeignKey(Course, related_name="units", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=400, blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["course__order", "order"]
        unique_together = [("course", "number")]

    def __str__(self):
        return f"{self.course.title} — Unit {self.number}: {self.title}"


class Lesson(models.Model):
    unit = models.ForeignKey(Unit, related_name="lessons", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name="all_lessons", on_delete=models.CASCADE)
    course_lesson_number = models.PositiveIntegerField()
    order_in_unit = models.PositiveIntegerField()
    title = models.CharField(max_length=400)
    summary = models.CharField(max_length=600, blank=True)
    content = models.TextField(blank=True, help_text="Markdown. Footnotes supported.")
    slug = models.SlugField(max_length=300)

    class Meta:
        ordering = ["course_lesson_number", "course__order"]
        unique_together = [("course", "slug"), ("course", "course_lesson_number")]

    def __str__(self):
        return f"C{self.course.order}.L{self.course_lesson_number}: {self.title}"

    def get_absolute_url(self):
        return reverse("courses:lesson_detail", args=[self.course.slug, self.slug])

    @property
    def is_written(self):
        return bool(self.content.strip())

    @property
    def is_read(self):
        return hasattr(self, "progress") and self.progress.is_read

    @staticmethod
    def global_queryset():
        return Lesson.objects.select_related("course", "unit").order_by(
            "course_lesson_number", "course__order"
        )

    @property
    def global_position(self):
        ids = list(Lesson.global_queryset().values_list("id", flat=True))
        return ids.index(self.id) + 1

    def get_next(self):
        seq = list(Lesson.global_queryset())
        i = next((n for n, l in enumerate(seq) if l.id == self.id), None)
        if i is not None and i + 1 < len(seq):
            return seq[i + 1]
        return None

    def get_previous(self):
        seq = list(Lesson.global_queryset())
        i = next((n for n, l in enumerate(seq) if l.id == self.id), None)
        if i is not None and i - 1 >= 0:
            return seq[i - 1]
        return None


class Progress(models.Model):
    """Read-state for a lesson (single local user)."""
    lesson = models.OneToOneField(Lesson, related_name="progress", on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{'read' if self.is_read else 'unread'}: {self.lesson}"


class Highlight(models.Model):
    """A Kindle-style highlight on a lesson, with an optional attached note.
    Anchored by character offsets into the rendered lesson text."""
    lesson = models.ForeignKey(
        Lesson, related_name="highlights", on_delete=models.CASCADE)
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()
    quote = models.TextField()
    note = models.TextField(blank=True, default="")
    color = models.CharField(max_length=10, default="yellow")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_offset", "id"]

    def __str__(self):
        return f"Highlight on {self.lesson.title}: {self.quote[:40]}"
