import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AssetManagement.settings")
django.setup()

from django.test import Client
from authentication.models import User

user = User.objects.first()
c = Client()
c.force_login(user)

response = c.get("/assets/search/1", {"search_text": "DOESNOTEXIST99999"})
print("Status Code:", response.status_code)
print(response.content.decode()[:500])
