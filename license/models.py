from django.db import models
from dashboard.models import LicenseType, TimeStampModel,SoftDeleteModel
from vendors.models import Vendor
from simple_history.models import HistoricalRecords
from authentication.models import User
class License(TimeStampModel,SoftDeleteModel):
    id=models.AutoField(primary_key=True, null=False)
    name=models.CharField(max_length=255)
    license_type=models.ForeignKey(LicenseType,on_delete=models.CASCADE)
    vendor=models.ForeignKey(Vendor,on_delete=models.CASCADE,blank=True,null=True)
    seats=models.IntegerField(blank=True,null=True)
    start_date=models.DateField(blank=True,null=True)
    expiry_date=models.DateField(blank=True,null=True)
    key=models.CharField(max_length=255,blank=True,null=True)
    notes=models.CharField(max_length=500,blank=True,null=True)
    is_assigned=models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
class AssignLicense(models.Model):
    id=models.AutoField(primary_key=True, null=False)
    license=models.OneToOneField(License, on_delete=models.CASCADE, null=True, blank=True)
    user=models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    notes=models.TextField(blank=True)
    assigned_date=models.DateTimeField(auto_now_add=True)
