import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asseto.settings')
django.setup()

from assets.models import Asset, Product
from clients.models import Client
from upload.models import BulkUploadSession

print("Products:")
for p in Product.objects.all():
    print(repr(str(p.id)), p.name)

print("BulkUploadSessions:")
for s in BulkUploadSession.objects.all():
    print(s.id, s.staged_data[0] if s.staged_data else "Empty")
