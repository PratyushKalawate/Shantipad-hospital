from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from cms.views import content, frontend_page


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/content/", content, name="content"),
    path("", frontend_page, {"page": "index.html"}, name="home"),
    path("about/", frontend_page, {"page": "about/index.html"}, name="about"),
    path("child-care/", frontend_page, {"page": "child-care/index.html"}, name="child-care"),
    path("dental-care/", frontend_page, {"page": "dental-care/index.html"}, name="dental-care"),
    path("doctors/", frontend_page, {"page": "doctors/index.html"}, name="doctors"),
    path("contact/", frontend_page, {"page": "contact/index.html"}, name="contact"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
