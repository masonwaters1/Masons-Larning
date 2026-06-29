from django.contrib import admin
from .models import Course, Unit, Lesson, Progress


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "total_lessons", "read_count")
    inlines = [UnitInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("course_lesson_number", "course", "title", "is_written", "is_read")
    list_filter = ("course", "unit")
    search_fields = ("title", "summary")


admin.site.register(Unit)
admin.site.register(Progress)
