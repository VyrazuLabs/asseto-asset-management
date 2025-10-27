import os
from django.db import connection, connections
from django.shortcuts import redirect
from django.urls import reverse

from AssetManagement.settings import BASE_DIR
    
class DBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print('middlewere running!')
        skip_paths = [
            reverse('authentication:introduce'),
            reverse('authentication:db_configure'),
        ]
        if request.path in skip_paths:
            return self.get_response(request)
        

        if not os.environ.get('DB_NAME'):
            return redirect('authentication:introduce')
        
        return self.get_response(request)
            