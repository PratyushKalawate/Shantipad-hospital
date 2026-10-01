from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import AppointmentPhone, ContentText, Doctor, Facility, FAQ, Hospital, OpeningHour, Partner, Service


LANGUAGES = ("en", "hi", "mr")


def localized(item, field):
    english = getattr(item, f"{field}_en", "")
    return {language: getattr(item, f"{field}_{language}", "") or english for language in LANGUAGES}


def asset(item, upload_field, fallback_field):
    upload = getattr(item, upload_field)
    return upload.url if upload else getattr(item, fallback_field)


def hospital_content(hospital):
    if hospital is None:
        return None
    return {
        "name": localized(hospital, "name"),
        "address": localized(hospital, "address"),
        "about": localized(hospital, "about"),
        "phone": hospital.phone,
        "email": hospital.email,
        "maps_url": hospital.maps_url,
        "emergency_24h": hospital.emergency_24h,
        "logo_url": asset(hospital, "logo", "logo_url"),
        "hero_image_url": asset(hospital, "hero_image", "hero_image_url"),
    }


@require_GET
@never_cache
def content(request):
    copy = {language: {} for language in LANGUAGES}
    for item in ContentText.objects.filter(published=True):
        if item.key in {"certTitle", "certBody", "certNumber", "certValidity", "viewCertificate"}:
            continue
        for language in LANGUAGES:
            copy[language][item.key] = getattr(item, language) or item.en
    response = {
        "hospital": hospital_content(Hospital.objects.first()),
        "doctors": [{
            "name": localized(item, "name"),
            "qualifications": item.qualifications,
            "experience": localized(item, "experience"),
            "bio": localized(item, "bio"),
            "consultation": localized(item, "consultation"),
            "specialty": item.specialty,
            "registration": item.registration,
            "photo_url": asset(item, "photo", "photo_url"),
        } for item in Doctor.objects.filter(published=True)],
        "services": [{
            "department": item.department,
            "name": localized(item, "name"),
            "description": localized(item, "description"),
        } for item in Service.objects.filter(published=True)],
        "facilities": [{
            "name": localized(item, "name"),
            "description": localized(item, "description"),
        } for item in Facility.objects.filter(published=True)],
        "partners": list(Partner.objects.filter(published=True).values_list("name", flat=True)),
        "appointments": list(AppointmentPhone.objects.filter(published=True).values_list("number", flat=True)),
        "hours": [{
            "label": localized(item, "label"),
            "times": localized(item, "times"),
            "note": localized(item, "note"),
        } for item in OpeningHour.objects.filter(published=True)],
        "faqs": [{
            "question": localized(item, "question"),
            "answer": localized(item, "answer"),
        } for item in FAQ.objects.filter(published=True)],
        "copy": copy,
    }
    return JsonResponse(response, json_dumps_params={"ensure_ascii": False})


@require_GET
def frontend_page(request, page):
    path = Path(settings.BASE_DIR) / "frontend" / page
    if not path.is_file():
        raise Http404("Page not found")
    return FileResponse(path.open("rb"), content_type="text/html; charset=utf-8")
