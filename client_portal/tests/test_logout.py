import uuid

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from client_portal.models import ClientPortalOTP
from client_portal.utils import (
    CLIENT_ACCESS_DISABLED_MSG,
    PORTAL_ACCESS_REVOKED_MSG,
)
from clients.models import Client, ClientContact
from dashboard.models import Organization

User = get_user_model()

PORTAL_KEYS = (
    "client_contact_id",
    "client_id",
    "pending_contact_id",
    "pending_contact_email",
    "show_welcome_banner",
)


class ClientPortalLogoutTests(TestCase):
    """Portal logout must not touch the main site's django.contrib.auth login."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@example.com",
            full_name="Admin",
            username="admin",
            phone="+919876543210",
            password="pass1234",
        )
        self.client.force_login(self.user)

    def _set_portal_keys(self, **extra):
        session = self.client.session
        session["client_contact_id"] = str(uuid.uuid4())
        session["client_id"] = str(uuid.uuid4())
        session["pending_contact_id"] = str(uuid.uuid4())
        session["pending_contact_email"] = "client@example.com"
        session["show_welcome_banner"] = True
        session.update(extra)
        session.save()

    def test_logout_view_keeps_main_site_session(self):
        self._set_portal_keys(org_lang_id=3)

        self.client.get(reverse("client_portal:logout"))

        session = self.client.session
        for key in PORTAL_KEYS:
            self.assertNotIn(key, session)
        self.assertIn(SESSION_KEY, session)
        self.assertEqual(str(session[SESSION_KEY]), str(self.user.pk))


class ClientPortalAccessRevocationTests(TestCase):
    """Disabling a client or removing contact portal access logs out on refresh."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.client_obj = Client.objects.create(
            name="Acme Corp",
            status="1",
            organization=self.org,
        )
        self.contact = ClientContact.objects.create(
            client=self.client_obj,
            name="Jane Doe",
            email="jane@acme.example",
            is_portal_active=True,
        )

    def _login_portal(self):
        session = self.client.session
        session["client_contact_id"] = str(self.contact.id)
        session["client_id"] = str(self.client_obj.id)
        session.save()

    def test_active_client_and_contact_can_access_dashboard(self):
        self._login_portal()
        response = self.client.get(reverse("client_portal:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_disabling_client_logs_out_on_refresh_with_message(self):
        self._login_portal()
        self.client_obj.status = "0"
        self.client_obj.save()

        response = self.client.get(reverse("client_portal:dashboard"))

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertNotIn("client_contact_id", self.client.session)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(CLIENT_ACCESS_DISABLED_MSG, msgs)

    def test_removing_portal_access_logs_out_on_refresh_with_message(self):
        self._login_portal()
        self.contact.is_portal_active = False
        self.contact.save()

        response = self.client.get(reverse("client_portal:dashboard"))

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertNotIn("client_contact_id", self.client.session)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(PORTAL_ACCESS_REVOKED_MSG, msgs)

    def test_disabled_client_cannot_request_login_otp(self):
        self.client_obj.status = "0"
        self.client_obj.save()

        response = self.client.post(
            reverse("client_portal:login"),
            {"email": self.contact.email},
        )

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertFalse(ClientPortalOTP.objects.filter(contact=self.contact).exists())
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(CLIENT_ACCESS_DISABLED_MSG, msgs)

    def test_disabled_client_blocked_at_verify_otp(self):
        session = self.client.session
        session["pending_contact_id"] = str(self.contact.id)
        session["pending_contact_email"] = self.contact.email
        session.save()

        self.client_obj.status = "0"
        self.client_obj.save()

        response = self.client.post(
            reverse("client_portal:verify_otp"),
            {"otp": "123456"},
        )

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertNotIn("pending_contact_id", self.client.session)
        self.assertNotIn("client_contact_id", self.client.session)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(CLIENT_ACCESS_DISABLED_MSG, msgs)
        self.assertEqual(session.get("org_lang_id"), 3)

    def test_middleware_access_revocation_keeps_main_site_session(self):
        # A contact id that no longer exists in the DB triggers the
        # middleware's "access revoked" cleanup path.
        self._set_portal_keys()

        response = self.client.get(reverse("client_portal:dashboard"))

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        session = self.client.session
        for key in PORTAL_KEYS:
            self.assertNotIn(key, session)
        self.assertIn(SESSION_KEY, session)
        self.assertEqual(str(session[SESSION_KEY]), str(self.user.pk))


class ClientPortalAccessRevocationTests(TestCase):
    """Disabling a client or removing contact portal access logs out on refresh."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.client_obj = Client.objects.create(
            name="Acme Corp",
            status="1",
            organization=self.org,
        )
        self.contact = ClientContact.objects.create(
            client=self.client_obj,
            name="Jane Doe",
            email="jane@acme.example",
            is_portal_active=True,
        )

    def _login_portal(self):
        session = self.client.session
        session["client_contact_id"] = str(self.contact.id)
        session["client_id"] = str(self.client_obj.id)
        session.save()

    def test_active_client_and_contact_can_access_dashboard(self):
        self._login_portal()
        response = self.client.get(reverse("client_portal:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_disabling_client_logs_out_on_refresh_with_message(self):
        self._login_portal()
        self.client_obj.status = "0"
        self.client_obj.save()

        response = self.client.get(reverse("client_portal:dashboard"))

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertNotIn("client_contact_id", self.client.session)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(CLIENT_ACCESS_DISABLED_MSG, msgs)

    def test_removing_portal_access_logs_out_on_refresh_with_message(self):
        self._login_portal()
        self.contact.is_portal_active = False
        self.contact.save()

        response = self.client.get(reverse("client_portal:dashboard"))

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertNotIn("client_contact_id", self.client.session)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(PORTAL_ACCESS_REVOKED_MSG, msgs)

    def test_disabled_client_cannot_request_login_otp(self):
        self.client_obj.status = "0"
        self.client_obj.save()

        response = self.client.post(
            reverse("client_portal:login"),
            {"email": self.contact.email},
        )

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertFalse(ClientPortalOTP.objects.filter(contact=self.contact).exists())
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(CLIENT_ACCESS_DISABLED_MSG, msgs)

    def test_disabled_client_blocked_at_verify_otp(self):
        session = self.client.session
        session["pending_contact_id"] = str(self.contact.id)
        session["pending_contact_email"] = self.contact.email
        session.save()

        self.client_obj.status = "0"
        self.client_obj.save()

        response = self.client.post(
            reverse("client_portal:verify_otp"),
            {"otp": "123456"},
        )

        self.assertRedirects(
            response, reverse("client_portal:login"), fetch_redirect_response=False
        )
        self.assertNotIn("pending_contact_id", self.client.session)
        self.assertNotIn("client_contact_id", self.client.session)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(CLIENT_ACCESS_DISABLED_MSG, msgs)
