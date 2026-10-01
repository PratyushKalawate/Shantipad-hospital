import hashlib
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.db import migrations


def move_certificates(apps, schema_editor):
    private_root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    frontend = (Path(settings.BASE_DIR) / "frontend").resolve()
    media = Path(settings.MEDIA_ROOT).resolve()
    collected = Path(settings.STATIC_ROOT).resolve()

    def move_file(source, relative):
        source = source.resolve()
        target = (private_root / relative).resolve()
        if not target.is_relative_to(private_root):
            raise ValueError("Private certificate path is invalid.")
        if not source.exists():
            return target.relative_to(private_root).as_posix() if target.is_file() else ""
        if not any(source.is_relative_to(root) for root in (frontend, media, collected)):
            raise ValueError("Certificate source is outside the expected asset directories.")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest():
                source.unlink()
                return target.relative_to(private_root).as_posix()
            target = target.with_name(f"{target.stem}-{uuid.uuid4().hex[:8]}{target.suffix}")
        shutil.move(str(source), str(target))
        return target.relative_to(private_root).as_posix()

    known = {
        "nabh-certificate.pdf": "certification/nabh-certificate.pdf",
        "nabh-entry-level.jpeg": "certification/nabh-entry-level.jpeg",
    }
    for filename, relative in known.items():
        move_file(frontend / "assets" / filename, relative)
        for source in (collected / "assets").glob(f"{Path(filename).stem}*"):
            if source.is_file():
                move_file(source, f"legacy-static/{source.name}")

    Hospital = apps.get_model("cms", "Hospital")
    for hospital in Hospital.objects.all():
        for field, fallback in (("certificate", "certificate_url"), ("certification_image", "certification_image_url")):
            filename = str(getattr(hospital, field) or "")
            if filename:
                moved = move_file(media / filename, filename)
            else:
                url_path = urlsplit(getattr(hospital, fallback)).path
                if url_path.startswith("/static/"):
                    source = frontend / url_path.removeprefix("/static/")
                    moved = move_file(source, f"certification/{source.name}")
                elif url_path.startswith("/media/"):
                    relative = url_path.removeprefix("/media/")
                    moved = move_file(media / relative, relative)
                else:
                    moved = ""
            if moved:
                setattr(hospital, field, moved)
            setattr(hospital, fallback, "")
        hospital.save(update_fields=["certificate", "certificate_url", "certification_image", "certification_image_url"])

    # Old unreferenced uploads must not remain reachable under the public media URL.
    old_directory = media / "certification"
    if old_directory.is_dir():
        for source in sorted(old_directory.rglob("*")):
            if source.is_file():
                move_file(source, source.relative_to(media))


class Migration(migrations.Migration):
    dependencies = [("cms", "0003_alter_hospital_certificate_and_more")]

    operations = [migrations.RunPython(move_certificates, migrations.RunPython.noop)]
