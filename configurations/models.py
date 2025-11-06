import uuid
import base64
import binascii

from django.db import models
from dashboard.models import Organization
from authentication.models import User

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

class Extensions(models.Model):
    STATUS_CHOICES = [
        (0, 'Inactive'),
        (1, 'Active'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description=models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='integrations'
    )
    entity_name = models.CharField(
        max_length=150,
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    payment_date = models.DateTimeField(auto_now_add=True)
    validity= models.IntegerField( default=0)

class SlackConfiguration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="slack_configuration")
    slack_user_id = models.CharField(max_length=100, null=True, blank=True)
    access_token = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    team_id=models.CharField(max_length=100, null=True, blank=True)
    channel_id=models.CharField(max_length=100, null=True, blank=True)
    client_id=models.CharField(max_length=100, null=True, blank=True)
    client_secret=models.CharField(max_length=100, null=True, blank=True)

    # @staticmethod
    # def is_valid_base64(string):
    #     try:
    #         return string == base64.b64encode(base64.b64decode(string.encode())).decode()
    #     except Exception:
    #         return False

    # def save(self, *args, client_id=None, client_secret=None, **kwargs):
    #     import pdb; pdb.set_trace();
    #     try:
    #         client_id = client_id or self.client_id
    #         if client_id is not None and not self.is_valid_base64(client_id):
    #             self.client_id = base64.b64encode(client_id.encode()).decode()
    #     except (TypeError, ValueError, AttributeError, binascii.Error):
    #         pass

    #     try:
    #         client_secret = client_secret or self.client_secret
    #         if client_secret is not None and not self.is_valid_base64(client_secret): 
    #             self.client_secret = base64.b64encode(client_secret.encode()).decode()
    #     except (TypeError, ValueError, AttributeError, binascii.Error):
    #         pass

    #     super().save(*args, **kwargs)