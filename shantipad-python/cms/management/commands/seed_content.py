import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cms.models import AppointmentPhone, ContentText, Doctor, Facility, FAQ, Hospital, OpeningHour, Partner, SeedRun, Service
from cms.storage import private_certificate_storage


def localized_fields(data, names):
    fields = {}
    for name in names:
        values = data.get(name, {}) or {}
        if isinstance(values, str):
            values = {"en": values}
        for language in ("en", "hi", "mr"):
            fields[f"{name}_{language}"] = values.get(language, "")
    return fields


def create(model, fields):
    item = model(**fields)
    item.full_clean()
    item.save()
    return item


class Command(BaseCommand):
    help = "Import the supplied seed.json once. Existing content and later admin edits are preserved."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=settings.BASE_DIR / "seed.json")

    @transaction.atomic
    def handle(self, *args, **options):
        if SeedRun.objects.filter(key="initial-content").exists():
            self.stdout.write("Initial content already imported; existing edits preserved.")
            return
        content_models = (Hospital, Doctor, Service, Facility, Partner, AppointmentPhone, OpeningHour, FAQ, ContentText)
        if any(model.objects.exists() for model in content_models):
            raise CommandError("Website content already exists. Import skipped to preserve existing edits.")
        try:
            data = json.loads(options["file"].read_text(encoding="utf-8"))
            hospital = data["hospital"]
            values = localized_fields(hospital, ["name", "address", "about"])
            for field in ("phone", "email", "maps_url", "logo_url", "hero_image_url"):
                values[field] = hospital.get(field, "")
            values["emergency_24h"] = hospital.get("emergency_24h", False)
            certification = hospital.get("certification", {}) or {}
            for field in ("title", "body"):
                for key, value in localized_fields(certification, [field]).items():
                    values[f"certification_{key}"] = value
            for field in ("number",):
                values[f"certification_{field}"] = certification.get(field, "")
            for field in ("valid_from", "valid_to"):
                values[f"certification_{field}"] = certification.get(field) or None
            for source, field in (("image_file", "certification_image"), ("certificate_file", "certificate")):
                filename = certification.get(source, "")
                if filename:
                    path = Path(filename)
                    if path.is_absolute() or ".." in path.parts or not filename.startswith("certification/") or not private_certificate_storage.exists(filename):
                        raise ValueError("Private certificate seed files must exist under private/certification/.")
                    values[field] = filename
            values["id"] = 1
            create(Hospital, values)

            specs = [
                ("doctors", Doctor, ["name", "experience", "bio", "consultation"], ["qualifications", "specialty", "registration", "photo_url"]),
                ("services", Service, ["name", "description"], ["department"]),
                ("facilities", Facility, ["name", "description"], []),
                ("hours", OpeningHour, ["label", "times", "note"], []),
                ("faqs", FAQ, ["question", "answer"], []),
            ]
            for section, model, local_fields, plain_fields in specs:
                for order, row in enumerate(data.get(section, [])):
                    values = localized_fields(row, local_fields)
                    values.update({field: row.get(field, "") for field in plain_fields})
                    values.update(order=order, published=True)
                    create(model, values)
            for section, model, field in [("partners", Partner, "name"), ("appointments", AppointmentPhone, "number")]:
                for order, value in enumerate(data.get(section, [])):
                    create(model, {field: value, "order": order, "published": True})
            copy = data.get("copy", {})
            for key, english in copy.get("en", {}).items():
                if not english:
                    continue
                create(ContentText, {"key": key, "en": english, "hi": copy.get("hi", {}).get(key, ""), "mr": copy.get("mr", {}).get(key, "")})
            SeedRun.objects.create(key="initial-content")
        except (OSError, KeyError, TypeError, AttributeError, json.JSONDecodeError, ValidationError, ValueError) as error:
            raise CommandError(f"Content import failed; no changes saved: {error}") from error
        self.stdout.write(self.style.SUCCESS("Initial hospital content imported. No administrator account was created."))
