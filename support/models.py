import uuid
import random
from django.db import models
from uuid import uuid4
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from dashboard.models import TimeStampModel, SoftDeleteModel

PRIORITY_CHOICES = [
    ('emergency', 'Emergency'),
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('in_testing', 'In Testing'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed'),
]

TICKET_TYPE_CHOICES = [
    ('hardware_repair', 'Hardware Repair'),
    ('software_issue', 'Software Issue'),
    ('network', 'Network'),
    ('preventive_maintenance', 'Preventive Maintenance'),
    ('inspection', 'Inspection'),
    ('critical_failure', 'Critical Failure'),
    ('other', 'Other'),
]

IMPACT_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

ACTIVITY_TYPE_CHOICES = [
    ('created', 'Ticket Created'),
    ('status_changed', 'Status Changed'),
    ('assigned', 'Technician Assigned'),
    ('reassigned', 'Technician Reassigned'),
    ('comment', 'Public Comment'),
    ('internal_note', 'Internal Note'),
    ('attachment_added', 'Attachment Added'),
    ('updated', 'Ticket Updated'),
]

def generate_ticket_id():
    return f"TK-{random.randint(10000, 99999)}"


class SupportTicket(TimeStampModel, SoftDeleteModel):
    id            = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    ticket_id     = models.CharField(max_length=20, unique=True, blank=True)
    
    # Core fields
    subject       = models.CharField(max_length=500)
    description   = models.TextField(blank=True, null=True)
    
    # Linked asset (FK to assets.Asset)
    asset         = models.ForeignKey('assets.Asset', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    # Priority
    priority      = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Status
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Work Details
    ticket_type   = models.CharField(max_length=100, choices=TICKET_TYPE_CHOICES, default='hardware_repair')
    estimated_eta = models.DateTimeField(blank=True, null=True)
    hours_worked  = models.DecimalField(max_digits=8, decimal_places=1, default=0.0)
    impact_level  = models.CharField(max_length=20, choices=IMPACT_CHOICES, default='medium')
    service_level = models.CharField(max_length=100, blank=True, null=True)
    
    # Assignment
    assigned_to   = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    department    = models.ForeignKey('dashboard.Department', on_delete=models.SET_NULL, null=True, blank=True)
    location      = models.ForeignKey('dashboard.Location', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Client link
    # client        = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    
    # Organization
    organization  = models.ForeignKey('dashboard.Organization', on_delete=models.DO_NOTHING, null=True, blank=True)
    
    # History tracking
    history       = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = generate_ticket_id()
            while SupportTicket.objects.filter(ticket_id=self.ticket_id).exists():
                self.ticket_id = generate_ticket_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"

class TicketAttachment(TimeStampModel):
    id         = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    ticket     = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='attachments')
    file       = models.FileField(upload_to='support/attachments/')
    file_name  = models.CharField(max_length=255)
    file_size  = models.PositiveIntegerField(default=0)  # bytes
    uploaded_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.file_name

class TicketActivity(TimeStampModel):
    id           = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    ticket       = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    description  = models.TextField()
    is_internal  = models.BooleanField(default=False)
    performed_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.activity_type} on {self.ticket.ticket_id}"
