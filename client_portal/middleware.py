from django.shortcuts import redirect


class ClientPortalMiddleware:
    """
    Protects /client-portal/* routes.
    Allows login, verify-otp, and logout without session.
    All other portal pages require 'client_contact_id' in session.
    """

    PUBLIC_PATHS = [
        "/client-portal/login",
        "/client-portal/verify-otp",
        "/client-portal/logout/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Only apply to client portal routes
        if not path.startswith("/client-portal/"):
            return self.get_response(request)

        # Allow public paths
        if path in self.PUBLIC_PATHS:
            return self.get_response(request)

        # Check authenticated session
        if not request.session.get("client_contact_id"):
            return redirect("client_portal:login")

        return self.get_response(request)
