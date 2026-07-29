import os
from urllib.parse import urlparse

from django.db import connections, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError, ConnectionDoesNotExist
from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property

from configurations.models import Extensions


class DBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        skip_paths = [
            reverse("authentication:introduce"),
            # Allow public access to gate pass checkout via QR
            "/gate-pass/checkout/",
        ]

        if request.path in skip_paths or request.path.startswith(
            "/gate-pass/checkout/"
        ):
            return self.get_response(request)

        if "api/" in request.get_full_path("/"):
            api_extension = Extensions.objects.filter(entity_name="API").first()
            if (not api_extension) or (api_extension.status == 0):
                return JsonResponse(
                    data={"message": "API access not allowed", "status": 403}
                )

        try:
            conn = connections[DEFAULT_DB_ALIAS]
            conn.ensure_connection()
        except OperationalError:
            return redirect("authentication:introduce")
        except ConnectionDoesNotExist:
            return redirect("authentication:introduce")
        except Exception:
            return redirect("authentication:introduce")

        return self.get_response(request)


class DynamicCsrfMiddleware(CsrfViewMiddleware):
    def __call__(self, request):
        self.provided_request = request
        return super().__call__(request)

    def __add_custom_origin_to_trusted_origins(self, trusted: list):
        origin = self.provided_request.META.get("HTTP_ORIGIN")
        origin_host = os.environ.get("ORIGIN_HOST")
        if origin:
            parsed = urlparse(origin)
            trusted.add(f"{parsed.scheme}://{parsed.netloc}")
        if origin_host:
            if not origin_host.startswith(("http://", "https://")):
                origin_host = f"https://{origin_host}"
            trusted.add(origin_host)
        return trusted

    @cached_property
    def csrf_trusted_origins_hosts(self):
        return self.__add_custom_origin_to_trusted_origins(
            super().crsf_trusted_origins_hosts
        )

    @cached_property
    def allowed_origins_exact(self):
        return self.__add_custom_origin_to_trusted_origins(
            super().allowed_origins_exact
        )

    @cached_property
    def allowed_origin_subdomains(self):
        return self.__add_custom_origin_to_trusted_origins(
            super().allowed_origin_subdomains
        )
