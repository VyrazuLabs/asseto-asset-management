from email.policy import default
from django.db import models
from roles.models import Role
from dashboard.models import TimeStampModel
import uuid
from authentication.models import User


class Notification(TimeStampModel):
    NotificationTypeChoices = [
        (0, 'browser'),
        (1, 'email'),
        (2, 'slack'),
        (3, 'slack')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance_id = models.UUIDField(default=uuid.uuid4, editable=False)
    notification_title = models.CharField(max_length = 255, blank = True, null = True)
    notification_text = models.CharField(max_length = 255, blank = True, null = True)
    icon = models.CharField(max_length = 225, blank = True, null = True)
    link = models.CharField(max_length = 225, blank = True, null = True)
    is_superuser = models.BooleanField(default=False)
    entity_type = models.IntegerField(choices=NotificationTypeChoices, default=0)


class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank = True, null = True)
    notification = models.ForeignKey(Notification, models.DO_NOTHING, blank = True, null = True)
    is_seen = models.BooleanField(default=False)
