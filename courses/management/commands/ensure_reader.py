import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ("Create or update the reader login account from the "
            "READER_USERNAME and READER_PASSWORD environment variables. "
            "Safe to run on every deploy; does nothing if the vars are unset.")

    def handle(self, *args, **opts):
        username = os.environ.get("READER_USERNAME")
        password = os.environ.get("READER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                "READER_USERNAME / READER_PASSWORD not set — skipping reader "
                "account setup.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} reader account '{username}'."))
