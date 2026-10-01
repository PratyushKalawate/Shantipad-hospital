from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse


class PrivateCertificateStorage(FileSystemStorage):
    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return str(Path(self.base_location).resolve())

    def url(self, name):
        return reverse("admin:cms_hospital_private_file", kwargs={"name": name})


private_certificate_storage = PrivateCertificateStorage()
