import os
from urllib.parse import urlparse

from django.middleware.csrf import CsrfViewMiddleware
from django.utils.functional import cached_property


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
