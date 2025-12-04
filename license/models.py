from django.db import models
from dashboard.models import LicenseType, TimeStampModel,SoftDeleteModel
from vendors.models import Vendor
from simple_history.models import HistoricalRecords
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
    history = HistoricalRecords()

    def __str__(self):
        return self.name