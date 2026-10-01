import os
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create a local administrator with a generated password stored in a private file."

    def add_arguments(self, parser):
        parser.add_argument("--credentials-file", type=Path, required=True)
        parser.add_argument("--username", default="shantipad-admin")

    def handle(self, *args, **options):
        path = options["credentials_file"].expanduser().resolve()
        for public_path in (settings.BASE_DIR / "frontend", settings.STATIC_ROOT, settings.MEDIA_ROOT):
            if path.is_relative_to(Path(public_path).resolve()):
                raise CommandError("The credentials file must be outside public static and media directories.")
        if not path.parent.is_dir():
            raise CommandError("Create the private destination directory first.")
        username = options["username"]
        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            self.stdout.write("That administrator already exists; account and password were not changed.")
            return
        password = secrets.token_urlsafe(24)
        created_file = False
        try:
            with transaction.atomic():
                user_model.objects.create_superuser(username=username, password=password, email="")
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                created_file = True
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(f"Shantipad local administrator\nUsername: {username}\nPassword: {password}\n\nKeep this file private. Do not include it in a shared project archive.\n")
        except OSError as error:
            if created_file:
                path.unlink(missing_ok=True)
            raise CommandError(f"Could not create private credentials file; account creation rolled back: {error}") from error
        self.stdout.write(self.style.SUCCESS(f"Administrator created. Private credentials saved to {path}."))
