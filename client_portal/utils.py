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
DEFAULT_BRAND_NAME = "Asseto"

PORTAL_SESSION_KEYS = (
    "client_contact_id",
    "client_id",
    "pending_contact_id",
    "pending_contact_email",
    "show_welcome_banner",
)

# Client.status value for a disabled client (clients.models.STATUS_CHOICES "0").
DISABLED_CLIENT_STATUS = "0"

CLIENT_ACCESS_DISABLED_MSG = (
    "Your client account has been disabled. Please contact administration."
)
PORTAL_ACCESS_REVOKED_MSG = (
    "Your portal access has been disabled or removed. Please contact administration."
)


def portal_access_denied_reason(contact):
    """
    Why ``contact`` may not use the portal right now, or ``None`` if allowed.

    Used by the middleware (every portal request) and by the login/OTP views so
    that a client whose status is disabled, or whose portal access was removed,
    is kicked out of the portal with an explanatory error on their next request.
    """
    if contact is None or contact.is_deleted:
        return PORTAL_ACCESS_REVOKED_MSG
    if not contact.is_portal_active:
        return PORTAL_ACCESS_REVOKED_MSG
    client = contact.client
    if client is None or client.is_deleted or client.status == DISABLED_CLIENT_STATUS:
        return CLIENT_ACCESS_DISABLED_MSG
    return None


def clear_portal_session(request):
    """
    Remove only the client portal's own keys from the session.

    The portal shares the browser's single Django session cookie with the
    main site (where a staff user may be logged in via django.contrib.auth),
    so request.session.flush() here would also delete _auth_user_id and log
    that user out of the main site.
    """
    removed = False
    for key in PORTAL_SESSION_KEYS:
        if key in request.session:
            del request.session[key]
            removed = True
    if removed:
        request.session.cycle_key()


def get_organization_name(contact):
    """Organization name from configurations/add-organization/ for the
    contact's client, falling back to the default brand name."""
    organization = getattr(getattr(contact, "client", None), "organization", None)
    return (getattr(organization, "name", None) or "").strip() or DEFAULT_BRAND_NAME


def send_otp_email(contact, otp):
    """Send OTP to the client contact's email address."""
    org_name = get_organization_name(contact)

    subject = f"Your {org_name} Client Portal login code"
    message = (
        f"Hello {contact.name},\n\n"
        f"Use this one-time code to sign in to the {org_name} Client Portal:\n\n"
        f"    {otp}\n\n"
        f"The code is valid for {OTP_EXPIRY_MINUTES} minutes and can only be used once.\n"
        f"If you did not request this code, you can safely ignore this email — no one can access your account without it.\n\n"
        f"— The {org_name} Team"
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
