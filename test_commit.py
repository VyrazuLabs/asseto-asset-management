import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AssetManagement.settings')
django.setup()

from dashboard.models import Organization
from assets.models import Product, Vendor, AssetStatus, Asset
from upload.bulk_upload_utils import commit_bulk_session
from django.test import RequestFactory
import uuid

org = Organization.objects.first()
ven = Vendor.objects.first()
if not ven:
    ven = Vendor.objects.create(organization=org, name="Test Vendor")

print(f"Vendor: {ven.name}, ID: {ven.id}")

staged = [{
    'name': 'Test Asset',
    'vendor_target_id': str(ven.id),
}]

class DummySession:
    def __init__(self, org, staged):
        self.id = uuid.uuid4()
        self.organization = org
        self.staged_data = staged
    def delete(self): pass

session = DummySession(org, staged)
request = RequestFactory().post('/fake')

print("Before creation: Asset count =", Asset.objects.count())
vendors_by_id = {str(v.id): v for v in Vendor.objects.filter(organization=org)}
print(f"vendors_by_id keys: {list(vendors_by_id.keys())[:5]}")
print(f"vend_id passed: {str(ven.id)}")
print(f"Is vend_id in vendors_by_id? {str(ven.id) in vendors_by_id}")

created, errors = commit_bulk_session(session, request)
print("Created:", created, "Errors:", errors)

new_asset = Asset.objects.last()
if new_asset:
    print("New Asset Vendor:", new_asset.vendor)
    new_asset.delete()

