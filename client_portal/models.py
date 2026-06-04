import uuid
from django.db import models


class ClientPortalOTP(models.Model):
    """Stores OTPs for client portal email-based login."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(
        'clients.ClientContact',
        on_delete=models.CASCADE,
        related_name='portal_otps'
    )
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client Portal OTP'
        verbose_name_plural = 'Client Portal OTPs'

    def __str__(self):
        return f"OTP for {self.contact.email} — {'Used' if self.is_used else 'Active'}"
