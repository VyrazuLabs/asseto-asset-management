from django.db import models
import uuid
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
 
class TagConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    prefix = models.CharField(max_length=50, blank=True, null=True)
    number_suffix = models.CharField(max_length=50,blank=True, null=True)
    use_default_settings = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.organization.name} - {self.prefix}"
    
class LocalizationConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    date_format = models.IntegerField( blank=True, null=True)
    time_format = models.IntegerField( blank=True, null=True)
    timezone = models.IntegerField( blank=True, null=True)
    currency = models.IntegerField( blank=True, null=True)
    name_display_format = models.IntegerField( blank=True, null=True)
    country_format = models.IntegerField( blank=True, null=True)
    default_language=models.IntegerField( blank=True, null=True)

    def __str__(self):
        return f"{self.organization.name} - Localization Settings"
    
class Integration(models.Model):
    STATUS_CHOICES = [
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    entity_model = models.CharField(
        max_length=150,
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default='inactive')

    # flags for paid access
    payment_flag = models.BooleanField(default=False, help_text="Indicates if this integration requires payment.")

    # Audit fields
    created_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, related_name='created_integrations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
