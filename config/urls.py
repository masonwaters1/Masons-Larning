from django.contrib import admin
from django.urls import path, include
from courses import views as course_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("pin/", course_views.pin_view, name="pin"),
    path("lock/", course_views.lock_view, name="lock"),
    path("", include("courses.urls")),
]
