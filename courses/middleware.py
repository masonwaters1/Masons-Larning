from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class PinGateMiddleware:
    """Require a session PIN to view any page. The PIN entry page and static
    files are always accessible; everything else redirects to the PIN page
    until the correct PIN has been entered."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.get("pin_ok"):
            return self.get_response(request)

        try:
            pin_path = reverse("pin")
        except NoReverseMatch:
            pin_path = "/pin/"

        static_url = settings.STATIC_URL or "/static/"
        if not static_url.startswith("/"):
            static_url = "/" + static_url

        path = request.path
        if path == pin_path or path.startswith(static_url):
            return self.get_response(request)

        return redirect(f"{pin_path}?next={path}")
