from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("course/<slug:slug>/", views.course_detail, name="course_detail"),
    path("course/<slug:course_slug>/lesson/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path("lesson/<int:lesson_id>/toggle/", views.toggle_read, name="toggle_read"),
    path("lesson/<int:lesson_id>/highlight/", views.highlight_create, name="highlight_create"),
    path("highlight/<int:highlight_id>/update/", views.highlight_update, name="highlight_update"),
    path("highlight/<int:highlight_id>/delete/", views.highlight_delete, name="highlight_delete"),
]
