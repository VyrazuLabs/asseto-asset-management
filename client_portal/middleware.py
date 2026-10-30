from django.shortcuts import redirect

from clients.models import ClientContact


class ClientPortalMiddleware:
    """
    Protects /client-portal/* routes.
    Allows login, verify-otp, and logout without session.
    All other portal pages require a valid 'client_contact_id' in session —
    re-checked against the DB on every request so that removing portal
    access (or deleting the client/contact) revokes the session immediately.
    """

    PUBLIC_PATH_PREFIXES = [
        "/client-portal/login",
        "/client-portal/verify-otp",
        "/client-portal/logout",
        "/client-portal/resend-otp",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/")

        # Only apply to client portal routes
        if not path.startswith("/client-portal"):
            return self.get_response(request)

        # Allow public paths
        if any(path == pub.rstrip("/") for pub in self.PUBLIC_PATH_PREFIXES):
            return self.get_response(request)

        # Check authenticated session
        contact_id = request.session.get("client_contact_id")
        if not contact_id:
            return redirect("client_portal:login")

        # Re-validate access against the DB on every request
        has_access = ClientContact.objects.filter(
            id=contact_id,
            is_portal_active=True,
            is_deleted=False,
            client__is_deleted=False,
        ).exists()

        if not has_access:
            self._clear_portal_session(request)
            return redirect("client_portal:login")

        return self.get_response(request)

    @staticmethod
    def _clear_portal_session(request):
        for key in ("client_contact_id", "client_id"):
            request.session.pop(key, None)
