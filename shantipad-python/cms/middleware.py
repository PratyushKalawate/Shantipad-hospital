from urllib.parse import unquote

from django.http import HttpResponseNotFound


PRIVATE_ASSET_PATHS = {
    "/static/assets/nabh-certificate.pdf",
    "/static/assets/nabh-entry-level.jpeg",
}


class PrivateCertificateMiddleware:
    """Block legacy public certificate links before static-file middleware runs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = unquote(request.path).lower()
        legacy_static = path.startswith("/static/assets/") and path.rsplit("/", 1)[-1].startswith(("nabh-certificate", "nabh-entry-level"))
        if path in PRIVATE_ASSET_PATHS or legacy_static or path.startswith(("/media/certification/", "/static/certification/")):
            response = HttpResponseNotFound()
            response["Cache-Control"] = "private, no-store"
            return response
        return self.get_response(request)
