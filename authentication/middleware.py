from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings
from django.db.utils import OperationalError, ConnectionDoesNotExist
from configurations.models import Extensions
from django.middleware.csrf import CsrfViewMiddleware
from urllib.parse import urlparse
import os
from django.utils.functional import cached_property


class DBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        skip_paths = [
            reverse('authentication:introduce'),
            reverse('authentication:db_configure'),
            reverse('authentication:email_configure'),
            reverse('authentication:register'),
            '/api/authentication/token/refresh/'
        ]


        if request.path in skip_paths:
            print(request.path)
            return self.get_response(request)
        
        if not os.environ.get('EMAIL_HOST'):
            return redirect('authentication:introduce')
        
        if "api/" in request.get_full_path("/"):
            api_extension=Extensions.objects.filter(entity_name="API").first()
            if (not api_extension) or (api_extension.status == 0):
                return JsonResponse(data={'messgae':'API access not allowed','status':401})

        try:
            conn = connections[DEFAULT_DB_ALIAS]
            conn.ensure_connection()
        except OperationalError as e:
            return redirect('authentication:introduce')
        except ConnectionDoesNotExist as e:
            return redirect('authentication:introduce')
        except Exception as e:
            return redirect('authentication:introduce')

        return self.get_response(request)
    
class DynamicCsrfMiddleware(CsrfViewMiddleware):
    # def process_view(self, request, view_func, view_args, view_kwargs):
    #     if view_func.__name__ != "introduce":
    #         return None
        
    #     super().process_view(request, view_func, view_args, view_kwargs)

    # def _get_trusted_origins(self, request):
    #     trusted = set(super()._get_trusted_origins(request))
    #     origin = request.META.get("HTTP_ORIGIN")
    #     origin_host= os.environ.get("ORIGIN_HOST")
    #     print("DynamicCsrfMiddleware origin_host", origin_host)
    #     if origin :
    #         parsed = urlparse(origin)
    #         trusted.add(f"{parsed.scheme}://{parsed.netloc}")
    #     if origin_host:
    #         if not origin_host.startswith(("http://", "https://")):
    #             origin_host = f"https://{origin_host}"
    #         trusted.add(origin_host)
    #     return trusted

    def __call__(self, request):
        print("DynamicCsrfMiddleware __call__ called")
        self.provided_request = request
        return super().__call__(request)

    def __add_custom_origin_to_trusted_origins(self, trusted: list):
        origin = self.provided_request.META.get("HTTP_ORIGIN")
        origin_host= os.environ.get("ORIGIN_HOST")
        print("DynamicCsrfMiddleware origin_host", origin_host)
        if origin :
            parsed = urlparse(origin)
            trusted.add(f"{parsed.scheme}://{parsed.netloc}")
        if origin_host:
            if not origin_host.startswith(("http://", "https://")):
                origin_host = f"https://{origin_host}"
            trusted.add(origin_host)
        return trusted       

    @cached_property
    def csrf_trusted_origins_hosts(self):
        print("DynamicCsrfMiddleware csrf_trusted_origins_hosts called")
        return self.__add_custom_origin_to_trusted_origins(super().crsf_trusted_origins_hosts)

    @cached_property
    def allowed_origins_exact(self):
        print("DynamicCsrfMiddleware allowed_origins_exact called")
        return self.__add_custom_origin_to_trusted_origins(super().allowed_origins_exact)
    
    @cached_property
    def allowed_origin_subdomains(self):
        print("DynamicCsrfMiddleware allowed_origin_subdomains called")
        return self.__add_custom_origin_to_trusted_origins(super().allowed_origin_subdomains)
