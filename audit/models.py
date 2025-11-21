from django.db import models
from assets.models import Asset
from authentication.models import Organization, User
from assets.models import AssetImage
import os
from uuid import uuid4

def path_and_rename(instance, filename):
    upload_to =  'audit/'
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

class Audit(models.Model):
    CONDITION_CHOICES = [
        (0, 'Excellent'),
        (1, 'Good'),
        (2, 'Fair'),
        (3, 'Bad'),
        (4, 'Retired')
    ]
    assigned_to = models.CharField(max_length=150,blank=True, null=True)
    asset = models.ForeignKey(Asset, null=True, blank=True, related_name='audits', on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, null=True, on_delete=models.CASCADE)
    condition = models.IntegerField(choices=CONDITION_CHOICES, default=0)
    notes = models.TextField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    audited_by=models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def condition_label(self):
        return dict(self.CONDITION_CHOICES).get(self.condition)
    
class AuditImage(models.Model):
    audit = models.ForeignKey('Audit', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=path_and_rename, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)