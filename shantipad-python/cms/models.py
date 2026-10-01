from django.core.exceptions import ValidationError
from django.db import models

from .storage import private_certificate_storage
from .validators import image_upload, pdf_upload, phone_number, safe_asset_url, safe_external_url


class LocalizedName(models.Model):
    name_en = models.CharField("Name (English)", max_length=250)
    name_hi = models.CharField("Name (Hindi)", max_length=250, blank=True)
    name_mr = models.CharField("Name (Marathi)", max_length=250, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name_en


class PublishedItem(models.Model):
    published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["order", "pk"]


class Hospital(LocalizedName):
    address_en = models.TextField("Address (English)")
    address_hi = models.TextField("Address (Hindi)", blank=True)
    address_mr = models.TextField("Address (Marathi)", blank=True)
    about_en = models.TextField("Introduction (English)")
    about_hi = models.TextField("Introduction (Hindi)", blank=True)
    about_mr = models.TextField("Introduction (Marathi)", blank=True)
    phone = models.CharField(max_length=40, validators=[phone_number], help_text="Country code with no spaces, for example +919405644319.")
    email = models.EmailField(blank=True)
    maps_url = models.CharField(max_length=1000, blank=True, validators=[safe_external_url])
    emergency_24h = models.BooleanField(default=False)
    logo = models.ImageField(upload_to="hospital/", blank=True, validators=[image_upload])
    logo_url = models.CharField(max_length=1000, blank=True, validators=[safe_asset_url], help_text="Fallback image; use HTTPS or /static/ or /media/.")
    hero_image = models.ImageField(upload_to="hospital/", blank=True, validators=[image_upload])
    hero_image_url = models.CharField(max_length=1000, blank=True, validators=[safe_asset_url])
    certification_title_en = models.CharField("Certification title (English)", max_length=250, blank=True)
    certification_title_hi = models.CharField("Certification title (Hindi)", max_length=250, blank=True)
    certification_title_mr = models.CharField("Certification title (Marathi)", max_length=250, blank=True)
    certification_body_en = models.TextField("Certification details (English)", blank=True)
    certification_body_hi = models.TextField("Certification details (Hindi)", blank=True)
    certification_body_mr = models.TextField("Certification details (Marathi)", blank=True)
    certification_number = models.CharField(max_length=100, blank=True)
    certification_valid_from = models.DateField(null=True, blank=True)
    certification_valid_to = models.DateField(null=True, blank=True)
    certification_image = models.ImageField(upload_to="certification/", storage=private_certificate_storage, blank=True, validators=[image_upload], help_text="Private file, accessible only to authorized website administrators.")
    certification_image_url = models.CharField(max_length=1000, blank=True, editable=False, validators=[safe_asset_url])
    certificate = models.FileField(upload_to="certification/", storage=private_certificate_storage, blank=True, validators=[pdf_upload], help_text="Private PDF, accessible only to authorized website administrators.")
    certificate_url = models.CharField(max_length=1000, blank=True, editable=False, validators=[safe_asset_url])

    class Meta:
        verbose_name = "Hospital settings"
        verbose_name_plural = "Hospital settings"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="hospital_singleton")]

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.certification_valid_from and self.certification_valid_to and self.certification_valid_to < self.certification_valid_from:
            raise ValidationError({"certification_valid_to": "The expiry date must follow the start date."})


class Doctor(LocalizedName, PublishedItem):
    specialty = models.CharField(max_length=10, choices=[("child", "Child specialist"), ("dental", "Dentist")])
    qualifications = models.CharField(max_length=500)
    experience_en = models.TextField("Experience (English)", blank=True)
    experience_hi = models.TextField("Experience (Hindi)", blank=True)
    experience_mr = models.TextField("Experience (Marathi)", blank=True)
    bio_en = models.TextField("Biography (English)", blank=True)
    bio_hi = models.TextField("Biography (Hindi)", blank=True)
    bio_mr = models.TextField("Biography (Marathi)", blank=True)
    consultation_en = models.TextField("Consultation (English)", blank=True)
    consultation_hi = models.TextField("Consultation (Hindi)", blank=True)
    consultation_mr = models.TextField("Consultation (Marathi)", blank=True)
    registration = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(upload_to="doctors/", blank=True, validators=[image_upload])
    photo_url = models.CharField(max_length=1000, blank=True, validators=[safe_asset_url])

    class Meta(PublishedItem.Meta):
        abstract = False


class DescribedItem(LocalizedName, PublishedItem):
    description_en = models.TextField("Description (English)", blank=True)
    description_hi = models.TextField("Description (Hindi)", blank=True)
    description_mr = models.TextField("Description (Marathi)", blank=True)

    class Meta(PublishedItem.Meta):
        abstract = True


class Service(DescribedItem):
    department = models.CharField(max_length=10, choices=[("child", "Child care"), ("dental", "Dental care")])


class Facility(DescribedItem):
    class Meta(PublishedItem.Meta):
        verbose_name_plural = "Facilities"


class Partner(PublishedItem):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class AppointmentPhone(PublishedItem):
    number = models.CharField(max_length=40, validators=[phone_number], help_text="Country code with no spaces, for example +919326543972.")

    class Meta(PublishedItem.Meta):
        verbose_name = "Appointment phone"

    def __str__(self):
        return self.number


class OpeningHour(PublishedItem):
    label_en = models.CharField("Label (English)", max_length=150)
    label_hi = models.CharField("Label (Hindi)", max_length=150, blank=True)
    label_mr = models.CharField("Label (Marathi)", max_length=150, blank=True)
    times_en = models.CharField("Times (English)", max_length=250)
    times_hi = models.CharField("Times (Hindi)", max_length=250, blank=True)
    times_mr = models.CharField("Times (Marathi)", max_length=250, blank=True)
    note_en = models.CharField("Note (English)", max_length=500, blank=True)
    note_hi = models.CharField("Note (Hindi)", max_length=500, blank=True)
    note_mr = models.CharField("Note (Marathi)", max_length=500, blank=True)

    def __str__(self):
        return self.label_en


class FAQ(PublishedItem):
    question_en = models.CharField("Question (English)", max_length=500)
    question_hi = models.CharField("Question (Hindi)", max_length=500, blank=True)
    question_mr = models.CharField("Question (Marathi)", max_length=500, blank=True)
    answer_en = models.TextField("Answer (English)")
    answer_hi = models.TextField("Answer (Hindi)", blank=True)
    answer_mr = models.TextField("Answer (Marathi)", blank=True)

    class Meta(PublishedItem.Meta):
        verbose_name = "Frequently asked question"

    def __str__(self):
        return self.question_en


class ContentText(models.Model):
    key = models.SlugField(max_length=150, unique=True, help_text="Existing website copy key. Keep this key unchanged when editing text.")
    en = models.TextField("English")
    hi = models.TextField("Hindi", blank=True)
    mr = models.TextField("Marathi", blank=True)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Page text"
        verbose_name_plural = "Page text"

    def __str__(self):
        return self.key


class SeedRun(models.Model):
    key = models.CharField(max_length=100, unique=True)
    applied_at = models.DateTimeField(auto_now_add=True)
