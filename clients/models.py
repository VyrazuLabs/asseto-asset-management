import uuid
import random
from django.db import models
from dashboard.models import TimeStampModel, Organization, SoftDeleteModel
from simple_history.models import HistoricalRecords


STATUS_CHOICES = [
    ('1', 'Active'),
    ('2', 'Review'),
    ('3', 'Dormant'),
    ('0', 'Inactive'),
]

RENTAL_TYPE_CHOICES = [
    ('Tech Equipment', 'Tech Equipment'),
    ('Heavy Machinery', 'Heavy Machinery'),
    ('Office Infrastructure', 'Office Infrastructure'),
    ('Energy Systems', 'Energy Systems'),
    ('Transport Vehicles', 'Transport Vehicles'),
    ('Medical Equipment', 'Medical Equipment'),
    ('Other', 'Other'),
]


INDUSTRY_CHOICES = [
    ('1', 'Technology'),
    ('2', 'Healthcare'),
    ('3', 'Finance'),
    ('4', 'Manufacturing'),
    ('5', 'Retail'),
    ('6', 'Education'),
    ('7', 'Real Estate'),
    ('8', 'Transportation'),
    ('9', 'Energy'),
    ('10', 'Construction'),
    ('11', 'Hospitality'),
    ('12', 'Media & Entertainment'),
    ('13', 'Telecommunications'),
    ('14', 'Agriculture'),
    ('15', 'Other'),
]

INDUSTRY_MAP = dict(INDUSTRY_CHOICES)


def generate_client_id():
    """Generate a unique client ID like CL-XXXXX"""
    return f"CL-{random.randint(10000, 99999)}"


class Client(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=255)
    rental_type = models.CharField(
        max_length=100, choices=RENTAL_TYPE_CHOICES,
        default='Tech Equipment', blank=True, null=True
    )
    active_rentals = models.PositiveIntegerField(default=0)
    open_tickets = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='1'
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.DO_NOTHING, blank=True, null=True
    )
    industry = models.CharField(max_length=255, blank=True, null=True)
    corporate_website = models.URLField(max_length=500, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name or ''

    def save(self, *args, **kwargs):
        if not self.client_id:
            cid = generate_client_id()
            while Client.objects.filter(client_id=cid).exists():
                cid = generate_client_id()
            self.client_id = cid
        super().save(*args, **kwargs)

    @property
    def initials(self):
        parts = self.name.split() if self.name else []
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        elif parts:
            return parts[0][:2].upper()
        return 'CL'

    @property
    def industry_name(self):
        return INDUSTRY_MAP.get(self.industry, self.industry or 'Not Specified')

class ClientContact(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=45, blank=True, null=True)
    role = models.ForeignKey(
        'roles.Role', on_delete=models.SET_NULL, blank=True, null=True, related_name='contact_roles'
    )
    notes = models.TextField(blank=True, null=True)
    is_portal_active = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.name

    @property
    def initials(self):
        parts = self.name.split() if self.name else []
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        elif parts:
            return parts[0][:2].upper()
        return 'CT'
