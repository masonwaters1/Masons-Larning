from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        login_not_required(
            auth_views.LoginView.as_view(template_name="courses/login.html")
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("courses.urls")),
]
