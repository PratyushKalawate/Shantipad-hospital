import io
import json
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command, CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import AppointmentPhone, ContentText, Doctor, Hospital, Partner, Service
from .validators import image_upload, pdf_upload, safe_asset_url


class ContentTests(TestCase):
    def setUp(self):
        Hospital.objects.create(name_en="Shantipad", address_en="Shegaon", about_en="Hospital", phone="+919405644319")

    def test_api_is_public_read_only_and_private_admin_requires_login(self):
        self.assertEqual(self.client.get("/api/content/").status_code, 200)
        for method in ("post", "put", "patch", "delete"):
            self.assertEqual(getattr(self.client, method)("/api/content/").status_code, 405)
        self.assertRedirects(self.client.get("/admin/"), "/admin/login/?next=/admin/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/api/content/").json()["hospital"]["name"]["en"], "Shantipad")

    def test_hidden_items_are_excluded_and_translations_fall_back_to_english(self):
        Doctor.objects.create(name_en="Visible doctor", specialty="child", qualifications="MBBS", order=1)
        Doctor.objects.create(name_en="Hidden doctor", specialty="dental", qualifications="BDS", published=False)
        Service.objects.create(name_en="Vaccination", department="child", name_hi="Hindi name")
        Service.objects.create(name_en="Hidden service", department="child", published=False)
        Partner.objects.create(name="Visible partner", order=2)
        Partner.objects.create(name="First partner", order=0)
        Partner.objects.create(name="Hidden partner", published=False)
        ContentText.objects.create(key="greeting", en="Welcome", hi="", mr="Marathi welcome")
        ContentText.objects.create(key="secret", en="Unpublished", published=False)
        data = self.client.get("/api/content/").json()
        self.assertEqual(len(data["doctors"]), 1)
        self.assertEqual(data["doctors"][0]["name"]["mr"], "Visible doctor")
        self.assertEqual(data["services"][0]["name"], {"en": "Vaccination", "hi": "Hindi name", "mr": "Vaccination"})
        self.assertEqual(data["partners"], ["First partner", "Visible partner"])
        self.assertEqual(data["copy"]["hi"]["greeting"], "Welcome")
        self.assertNotIn("secret", data["copy"]["en"])

    def test_authenticated_admin_edit_is_persisted_in_api(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.test", "testing-only-strong-password-123")
        partner = Partner.objects.create(name="Old partner")
        self.client.force_login(user)
        response = self.client.post(reverse("admin:cms_partner_change", args=[partner.pk]), {
            "name": "Updated partner", "order": "0", "published": "on", "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Client().get("/api/content/").json()["partners"], ["Updated partner"])

    def test_admin_requires_csrf_for_writes(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.test", "testing-only-strong-password-123")
        partner = Partner.objects.create(name="Original")
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        response = client.post(reverse("admin:cms_partner_change", args=[partner.pk]), {"name": "Changed", "order": "0"})
        self.assertEqual(response.status_code, 403)
        partner.refresh_from_db()
        self.assertEqual(partner.name, "Original")

    def test_frontend_routes_are_explicit_and_available(self):
        for route in ("/", "/about/", "/child-care/", "/dental-care/", "/doctors/", "/contact/"):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"<!doctype html", b"".join(response.streaming_content).lower())
        self.assertEqual(self.client.get("/seed.json").status_code, 404)
        self.assertEqual(self.client.get("/db.sqlite3").status_code, 404)


class SeedTests(TestCase):
    def test_packaged_seed_loads_private_certificates_without_public_links(self):
        call_command("seed_content", stdout=io.StringIO())
        hospital = Hospital.objects.get()
        self.assertTrue(hospital.certificate.storage.exists(hospital.certificate.name))
        self.assertTrue(hospital.certification_image.storage.exists(hospital.certification_image.name))
        self.assertTrue(hospital.certificate.url.startswith("/admin/"))
        self.assertEqual(hospital.certificate_url, "")
        self.assertNotIn("certification", self.client.get("/api/content/").json()["hospital"])

    def test_seed_rerun_preserves_admin_changes(self):
        data = {
            "hospital": {"name": {"en": "Hospital"}, "address": {"en": "Shegaon"}, "about": {"en": "Introduction"}, "phone": "+919405644319"},
            "doctors": [{"name": {"en": "Doctor"}, "specialty": "child", "qualifications": "MBBS"}],
            "copy": {"en": {"welcome": "Welcome", "unused": ""}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seed.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            call_command("seed_content", file=path, stdout=io.StringIO())
            Doctor.objects.update(name_en="Edited name")
            call_command("seed_content", file=path, stdout=io.StringIO())
        self.assertEqual(Doctor.objects.get().name_en, "Edited name")
        self.assertEqual(Hospital.objects.count(), 1)
        self.assertFalse(get_user_model().objects.exists())

    def test_bootstrap_admin_uses_private_file_and_does_not_reset_password(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.txt"
            call_command("bootstrap_admin", credentials_file=path, stdout=io.StringIO())
            content = path.read_text()
            password = content.split("Password: ", 1)[1].splitlines()[0]
            user = get_user_model().objects.get(username="shantipad-admin")
            self.assertTrue(user.check_password(password))
            self.assertTrue(user.is_superuser)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            call_command("bootstrap_admin", credentials_file=path, stdout=io.StringIO())
            self.assertEqual(path.read_text(), content)
            self.assertEqual(get_user_model().objects.count(), 1)

    def test_bootstrap_admin_does_not_overwrite_existing_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.txt"
            path.write_text("Existing file")
            with self.assertRaises(CommandError):
                call_command("bootstrap_admin", credentials_file=path, stdout=io.StringIO())
            self.assertEqual(path.read_text(), "Existing file")
            self.assertFalse(get_user_model().objects.exists())


class UploadTests(TestCase):
    def test_phone_fields_require_working_international_numbers(self):
        AppointmentPhone(number="+919326543972").full_clean()
        for number in ("93265 43972", "Call reception", "+91", "javascript:alert(1)"):
            with self.subTest(number=number), self.assertRaises(ValidationError):
                AppointmentPhone(number=number).full_clean()

    def test_asset_urls_reject_scripts_and_unsafe_relative_paths(self):
        for url in ("javascript:alert(1)", "http://example.test/a.png", "//example.test/a.png", "/static/../secret", "/static/%2e%2e/secret"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                safe_asset_url(url)
        for url in ("/static/assets/logo.jpeg", "/media/doctors/photo.webp", "https://example.test/photo.png"):
            safe_asset_url(url)

    def test_images_are_verified_and_oversized_or_invalid_files_rejected(self):
        image = io.BytesIO()
        Image.new("RGB", (10, 10), "white").save(image, format="PNG")
        image_upload(SimpleUploadedFile("photo.png", image.getvalue(), content_type="image/png"))
        for file in (
            SimpleUploadedFile("fake.png", b"<script>alert(1)</script>", content_type="image/png"),
            SimpleUploadedFile("big.jpg", b"x" * (5 * 1024 * 1024 + 1)),
            SimpleUploadedFile("image.html", image.getvalue(), content_type="image/png"),
        ):
            with self.assertRaises(ValidationError):
                image_upload(file)

    def test_pdf_check_rejects_renamed_non_pdf(self):
        with self.assertRaises(ValidationError):
            pdf_upload(SimpleUploadedFile("certificate.pdf", b"not a pdf"))


class PrivateCertificateTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(PRIVATE_MEDIA_ROOT=Path(self.directory.name) / "private", MEDIA_ROOT=Path(self.directory.name) / "public")
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.hospital = Hospital.objects.create(
            name_en="Hospital", address_en="Shegaon", about_en="Care", phone="+919405644319",
            certification_number="PRIVATE-CERTIFICATE-NUMBER", certification_title_en="Private certification",
            logo_url="/static/assets/hospital-logo.jpeg",
        )
        self.hospital.certificate.save("प्रमाणपत्र.pdf", SimpleUploadedFile("प्रमाणपत्र.pdf", b"%PDF-1.4\nprivate certificate\n%%EOF"))
        image = io.BytesIO()
        Image.new("RGB", (10, 10), "white").save(image, format="PNG")
        self.hospital.certification_image.save("private-mark.png", SimpleUploadedFile("private-mark.png", image.getvalue()))

    def test_public_api_omits_certificate_details_and_preserves_public_logo(self):
        ContentText.objects.create(key="certTitle", en="Private certification")
        ContentText.objects.create(key="viewCertificate", en="Private certificate link")
        response = self.client.get("/api/content/")
        data = response.json()
        self.assertNotIn("certification", data["hospital"])
        self.assertNotContains(response, "PRIVATE-CERTIFICATE-NUMBER")
        self.assertNotContains(response, "private-mark.png")
        self.assertNotIn("certTitle", data["copy"]["en"])
        self.assertEqual(data["hospital"]["logo_url"], "/static/assets/hospital-logo.jpeg")
        self.assertIsNotNone(finders.find("assets/hospital-logo.jpeg"))

    def test_private_downloads_require_hospital_permission(self):
        for file in (self.hospital.certificate, self.hospital.certification_image):
            self.assertTrue(Path(file.path).resolve().is_relative_to((Path(self.directory.name) / "private").resolve()))
            response = self.client.get(file.url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/admin/login/"))
        user = get_user_model().objects.create_user("staff", password="testing-only-strong-password-123", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.hospital.certificate.url).status_code, 403)
        user.user_permissions.add(Permission.objects.get(codename="view_hospital", content_type__app_label="cms"))
        for file in (self.hospital.certificate, self.hospital.certification_image):
            response = self.client.get(file.url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("attachment", response["Content-Disposition"])
            self.assertIn("no-store", response["Cache-Control"])
            self.assertTrue(b"".join(response.streaming_content))
        self.assertEqual(self.client.get(reverse("admin:cms_hospital_private_file", kwargs={"name": "certification/unrelated.pdf"})).status_code, 404)

    def test_old_public_urls_and_private_directory_urls_are_unavailable(self):
        for url in (
            "/static/assets/nabh-certificate.pdf", "/static/assets/nabh-entry-level.jpeg",
            "/static/assets/nabh-certificate.a12b34.pdf.gz",
            "/media/certification/certificate.pdf", "/media/certification/private-mark.png",
            "/private/certification/nabh-certificate.pdf",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
        self.assertIsNone(finders.find("assets/nabh-certificate.pdf"))
        self.assertIsNone(finders.find("assets/nabh-entry-level.jpeg"))

    def test_admin_form_uses_private_links_and_hides_old_fallback_fields(self):
        user = get_user_model().objects.create_superuser("owner", "", "testing-only-strong-password-123")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:cms_hospital_change", args=[self.hospital.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hospital.certificate.url)
        self.assertNotContains(response, 'name="certificate_url"')
        self.assertNotContains(response, 'name="certification_image_url"')
