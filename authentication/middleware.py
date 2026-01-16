from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.db import connections, DEFAULT_DB_ALIAS
from django.conf import settings
from django.db.utils import OperationalError, ConnectionDoesNotExist
from configurations.models import Extensions
import os


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
    
