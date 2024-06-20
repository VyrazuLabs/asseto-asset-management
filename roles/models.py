from django.db import models
from dashboard.models import TimeStampModel, Organization
from django.contrib.auth.models import Group


# Create your models here.
class Role(Group, TimeStampModel):
    related_name = models.CharField(max_length=255, blank=True, null=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.related_name
