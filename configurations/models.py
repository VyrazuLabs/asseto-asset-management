from django.db import models

from dashboard.models import Organization

class BrandingImages(models.Model):

    logo_path="/logo/"
    favicon_path="/favicon/"
    login_page_logo_path="/login_page_logo/"

    id=models.AutoField(primary_key=True)
    logo=models.TextField(max_length=255, null=True)
    favicon=models.TextField(max_length=255, null=True)
    login_page_logo=models.TextField(max_length=255, null=True,)
    organization=models.ForeignKey(Organization, null=True, on_delete=models.CASCADE, related_name='organization_logo')