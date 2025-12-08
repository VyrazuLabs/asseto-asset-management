from django.shortcuts import redirect
from django.urls import reverse
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError, ConnectionDoesNotExist
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
        ]


        if request.path in skip_paths:
            return self.get_response(request)
        
        if not os.environ.get('EMAIL_HOST'):
            return redirect('authentication:introduce')

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
