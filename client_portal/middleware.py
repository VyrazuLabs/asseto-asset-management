from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from clients.models import ClientContact
from .utils import clear_portal_session, portal_access_denied_reason


class ClientPortalMiddleware:
    """
    Protects /client-portal/* routes.
    Allows login, verify-otp, and logout without session.
    All other portal pages require a valid 'client_contact_id' in session —
    re-checked against the DB on every request so that disabling the client,
    removing portal access (or deleting the client/contact) revokes the
    session immediately and shows the user why.
    """

    PUBLIC_PATHS = frozenset(
        {
            "/client-portal/login",
            "/client-portal/verify-otp",
            "/client-portal/logout",
            "/client-portal/resend-otp",
        }
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/")

        # Only apply to client portal routes
        if path != "/client-portal" and not path.startswith("/client-portal/"):
            return self.get_response(request)

        # Allow public paths
        if path in self.PUBLIC_PATHS:
            return self.get_response(request)

        # Check authenticated session
        contact_id = request.session.get("client_contact_id")
        if not contact_id:
            return redirect("client_portal:login")

        # Re-validate access against the DB on every request
        contact = self._get_contact(contact_id)
        reason = portal_access_denied_reason(contact)
        if reason:
            self._clear_portal_session(request)
            messages.error(request, reason)
            return redirect("client_portal:login")

        # Cache validated contact on the request so views avoid a duplicate DB query
        request.portal_contact = contact
        return self.get_response(request)

    @staticmethod
    def _get_contact(contact_id):
        try:
            return (
                ClientContact.objects.select_related("client")
                .filter(id=contact_id)
                .first()
            )
        except (ValidationError, ValueError):
            # Corrupted/stale session value — treat as "no such contact"
            return None

    @staticmethod
    def _clear_portal_session(request):
        clear_portal_session(request)
