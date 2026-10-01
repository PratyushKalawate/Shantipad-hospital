from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.urls import path
from django.views.decorators.http import require_GET

from .models import AppointmentPhone, ContentText, Doctor, Facility, FAQ, Hospital, OpeningHour, Partner, Service


admin.site.site_header = "Shantipad Hospital Administration"
admin.site.site_title = "Shantipad Admin"
admin.site.index_title = "Website content"
admin.site.site_url = "/"


def translations(prefix):
    return (f"{prefix}_en", f"{prefix}_hi", f"{prefix}_mr")


class PublishedAdmin(admin.ModelAdmin):
    list_filter = ("published",)
    list_editable = ("order", "published")
    ordering = ("order", "pk")
    save_on_top = True


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Hospital", {"fields": (translations("name"), translations("address"), translations("about"))}),
        ("Contact", {"fields": ("phone", "email", "maps_url", "emergency_24h")}),
        ("Brand images", {"fields": ("logo", "logo_url", "hero_image", "hero_image_url"), "description": "Uploads replace the fallback image URL. JPEG, PNG or WebP, up to 5 MB."}),
        ("Private certification records", {"fields": (
            translations("certification_title"), translations("certification_body"),
            "certification_number", ("certification_valid_from", "certification_valid_to"),
            "certification_image", "certificate",
        ), "description": "These records and downloads are available only to authorized administrators. They are not shown on the public website."}),
    )
    save_on_top = True

    def get_urls(self):
        private_url = path("private-file/<path:name>", self.admin_site.admin_view(require_GET(self.private_file)), name="cms_hospital_private_file")
        return [private_url] + super().get_urls()

    def private_file(self, request, name):
        hospital = Hospital.objects.first()
        if not self.has_view_or_change_permission(request, hospital):
            raise PermissionDenied
        if hospital is None:
            raise Http404
        file = next((item for item in (hospital.certificate, hospital.certification_image) if item and item.name == name), None)
        if file is None or not file.storage.exists(file.name):
            raise Http404
        response = FileResponse(file.open("rb"), as_attachment=True, filename=file.name.rsplit("/", 1)[-1])
        response["Cache-Control"] = "private, no-store"
        return response

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not Hospital.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Doctor)
class DoctorAdmin(PublishedAdmin):
    list_display = ("name_en", "specialty", "qualifications", "order", "published")
    list_filter = ("specialty", "published")
    search_fields = ("name_en", "name_hi", "name_mr", "qualifications")
    fieldsets = (
        ("Doctor", {"fields": (translations("name"), "specialty", "qualifications", "registration", "photo", "photo_url")}),
        ("Profile", {"fields": (translations("experience"), translations("bio"), translations("consultation"))}),
        ("Visibility", {"fields": ("published", "order")}),
    )


@admin.register(Service)
class ServiceAdmin(PublishedAdmin):
    list_display = ("name_en", "department", "order", "published")
    list_filter = ("department", "published")
    search_fields = ("name_en", "name_hi", "name_mr")
    fields = ("department", translations("name"), translations("description"), "order", "published")


@admin.register(Facility)
class FacilityAdmin(PublishedAdmin):
    list_display = ("name_en", "order", "published")
    search_fields = ("name_en", "name_hi", "name_mr")
    fields = (translations("name"), translations("description"), "order", "published")


@admin.register(Partner)
class PartnerAdmin(PublishedAdmin):
    list_display = ("name", "order", "published")
    search_fields = ("name",)


@admin.register(AppointmentPhone)
class AppointmentPhoneAdmin(PublishedAdmin):
    list_display = ("number", "order", "published")


@admin.register(OpeningHour)
class OpeningHourAdmin(PublishedAdmin):
    list_display = ("label_en", "times_en", "order", "published")
    fields = (translations("label"), translations("times"), translations("note"), "order", "published")


@admin.register(FAQ)
class FAQAdmin(PublishedAdmin):
    list_display = ("question_en", "order", "published")
    search_fields = ("question_en", "answer_en")
    fields = (translations("question"), translations("answer"), "order", "published")


@admin.register(ContentText)
class ContentTextAdmin(admin.ModelAdmin):
    list_display = ("key", "english_preview", "published")
    list_filter = ("published",)
    search_fields = ("key", "en", "hi", "mr")
    list_editable = ("published",)
    fields = ("key", "en", "hi", "mr", "published")

    @admin.display(description="English")
    def english_preview(self, obj):
        return obj.en[:100]
