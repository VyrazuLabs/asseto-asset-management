import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import ClientPortalOTP


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


OTP_EXPIRY_MINUTES = 2


def send_otp_email(contact, otp):
    """Send OTP to the client contact's email address."""
    subject = "Asseto Client Portal — Your Login Code"
    message = (
        f"Hello {contact.name},\n\n"
        f"Your one-time login code is: {otp}\n\n"
        f"This code expires in {OTP_EXPIRY_MINUTES} minute(s). Do not share it with anyone.\n\n"
        f"— Asseto Team"
    )
    # Using fail_silently=False during development to catch email issues
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [contact.email],
        fail_silently=False,
    )


def create_otp_for_contact(contact):
    """Generate a new OTP, send it via email, then invalidate older OTPs."""
    otp_code = generate_otp()
    otp_record = ClientPortalOTP.objects.create(
        contact=contact,
        otp=otp_code,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )

    try:
        send_otp_email(contact, otp_code)
    except Exception:
        # Email never left the server — drop the new code so the previous
        # OTP (the one the user may actually have) stays valid.
        otp_record.delete()
        raise

    # Only now is the new code confirmed sent — retire older codes.
    ClientPortalOTP.objects.filter(contact=contact, is_used=False).exclude(
        pk=otp_record.pk
    ).update(is_used=True)
    return otp_code


def otp_remaining_seconds(contact):
    """Seconds left before the latest active OTP expires (0 if none/expired)."""
    otp_record = (
        ClientPortalOTP.objects.filter(contact=contact, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp_record:
        return 0
    remaining = (otp_record.expires_at - timezone.now()).total_seconds()
    return max(0, int(remaining))


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

    # Check expiry FIRST
    if timezone.now() > otp_record.expires_at:
        otp_record.is_used = True
        otp_record.save()
        return False, "The verification code has expired. Please request a new one."

    # Check attempt limit
    if otp_record.attempts >= ClientPortalOTP.MAX_ATTEMPTS:
        otp_record.is_used = True
        otp_record.save()
        return False, "Too many failed attempts. Please request a new code."

    # Increment attempt counter BEFORE comparing
    otp_record.attempts += 1
    otp_record.save(update_fields=["attempts"])

    if otp_record.otp != entered_otp:
        remaining = ClientPortalOTP.MAX_ATTEMPTS - otp_record.attempts
        if remaining <= 0:
            # Last allowed attempt used up — lock this code now
            otp_record.is_used = True
            otp_record.save()
            return False, "Too many failed attempts. Please request a new code."
        return False, f"Invalid verification code. {remaining} attempt(s) remaining."

    # Mark as used
    otp_record.is_used = True
    otp_record.save()
    return True, "Success"
