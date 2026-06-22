import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import ClientPortalOTP


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return str(random.randint(100000, 999999))


def send_otp_email(contact, otp):
    """Send OTP to the client contact's email address."""
    subject = "Asseto Client Portal — Your Login Code"
    message = (
        f"Hello {contact.name},\n\n"
        f"Your one-time login code is: {otp}\n\n"
        f"This code expires in 5 minutes. Do not share it with anyone.\n\n"
        f"— Asseto Team"
    )
    # Using fail_silently=False during development to catch email issues
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [contact.email],
        fail_silently=False,
    )


def create_otp_for_contact(contact):
    """Invalidate old OTPs, generate a new one, save to DB, send it via email."""
    # Invalidate any existing unused OTPs
    ClientPortalOTP.objects.filter(contact=contact, is_used=False).update(is_used=True)

    otp_code = generate_otp()
    ClientPortalOTP.objects.create(
        contact=contact,
        otp=otp_code,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    send_otp_email(contact, otp_code)
    return otp_code


def verify_otp_for_contact(contact, entered_otp):
    """
    Check if 'entered_otp' matches the latest unused OTP for 'contact'.
    Returns True and marks OTP as used if valid, False otherwise.
    """
    otp_record = (
        ClientPortalOTP.objects.filter(
            contact=contact,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )

    if not otp_record:
        return False, "No active verification code found."

    if otp_record.otp != entered_otp:
        return False, "Invalid verification code."

    if timezone.now() > otp_record.expires_at:
        return False, "The verification code has expired."

    # Mark as used
    otp_record.is_used = True
    otp_record.save()
    return True, "Success"
