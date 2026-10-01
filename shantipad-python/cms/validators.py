import warnings
from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from PIL import Image, UnidentifiedImageError


phone_number = RegexValidator(
    regex=r"^\+[1-9][0-9]{7,14}$",
    message="Use an international number starting with + and country code, without spaces; for example +919405644319.",
)


def safe_asset_url(value):
    if not value:
        return
    decoded = unquote(value)
    if any(ord(char) < 32 for char in decoded) or "\\" in decoded:
        raise ValidationError("Use an HTTPS URL or a /static/ or /media/ file path.")
    parsed = urlsplit(value)
    if not parsed.scheme and not parsed.netloc:
        if decoded.startswith(("/static/", "/media/")) and ".." not in decoded.split("/"):
            return
        raise ValidationError("Local files must start with /static/ or /media/.")
    URLValidator(schemes=["https"])(value)


def safe_external_url(value):
    if value:
        URLValidator(schemes=["https"])(value)


def image_upload(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Images must be 5 MB or smaller.")
    if Path(value.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError("The image filename must end in .jpg, .jpeg, .png, or .webp.")
    position = value.tell()
    try:
        value.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(value) as picture:
                if picture.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Upload a JPEG, PNG, or WebP image.")
                picture.verify()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise ValidationError("Upload a valid JPEG, PNG, or WebP image.") from error
    finally:
        value.seek(position)


def pdf_upload(value):
    if value.size > 10 * 1024 * 1024:
        raise ValidationError("Certificates must be 10 MB or smaller.")
    position = value.tell()
    try:
        value.seek(0)
        start = value.read(8)
        value.seek(max(0, value.size - 1024))
        end = value.read(1024)
        if not value.name.lower().endswith(".pdf") or not start.startswith(b"%PDF-") or b"%%EOF" not in end:
            raise ValidationError("Upload a PDF certificate.")
    finally:
        value.seek(position)
