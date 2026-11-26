from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from common.factories import OrganizationFactory, UserFactory
from configurations.models import Extensions, SMSConfiguration, SMSLog
from configurations.sms_providers.msg91 import MSG91Provider
from configurations.sms_providers.twilio import TwilioProvider
from configurations.sms_service import SMSService
from configurations.sms_tasks import RetryableSMSError, send_sms_task


class MSG91ProviderTests(TestCase):
    def test_sanitize_phone_prepends_91_for_all_10_digit_numbers(self):
        provider = MSG91Provider({"auth_key": "key", "template_id": "tmpl"})
        self.assertEqual(provider.sanitize_phone("9876543210"), "919876543210")
        self.assertEqual(provider.sanitize_phone("9123456789"), "919123456789")
        self.assertEqual(provider.sanitize_phone("+91 98765-43210"), "919876543210")

    def test_missing_required_credentials_raises(self):
        with self.assertRaises(ValueError):
            MSG91Provider({"auth_key": "key"})

    @patch("configurations.sms_providers.msg91.requests.post")
    def test_send_4xx_is_non_retryable_and_5xx_is_retryable(self, mock_post):
        provider = MSG91Provider({"auth_key": "key", "template_id": "tmpl"})

        bad_resp = MagicMock(status_code=400)
        bad_resp.json.return_value = {"type": "error", "message": "Invalid template"}
        mock_post.return_value = bad_resp
        res = provider.send(to="919876543210", message="hello")
        self.assertFalse(res.success)
        self.assertFalse(res.retryable)

        err_resp = MagicMock(status_code=503)
        err_resp.json.return_value = {"type": "error", "message": "Service unavailable"}
        mock_post.return_value = err_resp
        res = provider.send(to="919876543210", message="hello")
        self.assertFalse(res.success)
        self.assertTrue(res.retryable)


class TwilioProviderTests(TestCase):
    def test_rejects_invalid_account_sid_characters(self):
        with self.assertRaises(ValueError):
            TwilioProvider(
                {
                    "account_sid": "AC123/../../evil",
                    "auth_token": "tok",
                    "from_number": "+15550001111",
                }
            )

    def test_sanitize_phone_e164(self):
        provider = TwilioProvider(
            {"account_sid": "AC123456", "auth_token": "tok", "from_number": "+15550001111"}
        )
        self.assertEqual(provider.sanitize_phone("919876543210"), "+919876543210")
        self.assertEqual(provider.sanitize_phone("+1 555-0100"), "+15550100")


class SMSServiceAndTaskTests(TestCase):
    def setUp(self):
        self.org = OrganizationFactory()
        self.ext = Extensions.objects.create(
            organization=self.org, entity_name="SMS", status=1
        )
        self.config = SMSConfiguration.objects.create(
            organization=self.org,
            provider="twilio",
            credentials={
                "account_sid": "AC123456",
                "auth_token": "secret",
                "from_number": "+15550001111",
            },
            is_active=True,
        )

    @patch("configurations.sms_providers.twilio.requests.post")
    def test_permanent_failure_does_not_retry_and_logs_once(self, mock_post):
        bad_resp = MagicMock(status_code=400)
        bad_resp.json.return_value = {"error_code": 21211, "message": "Invalid To"}
        mock_post.return_value = bad_resp

        result = send_sms_task.apply(
            kwargs={
                "config_id": str(self.config.id),
                "to": "+15550009999",
                "message": "Test",
            }
        ).get()

        self.assertFalse(result["success"])
        self.assertEqual(SMSLog.objects.filter(organization=self.org).count(), 1)
        self.assertEqual(SMSLog.objects.first().status, "failed")

    @patch("configurations.sms_providers.twilio.requests.post")
    def test_transient_failure_raises_retryable_error(self, mock_post):
        err_resp = MagicMock(status_code=503)
        err_resp.json.return_value = {"message": "Upstream error"}
        mock_post.return_value = err_resp

        with self.assertRaises(RetryableSMSError):
            send_sms_task.run(
                config_id=str(self.config.id),
                to="+15550009999",
                message="Test",
            )


class SMSViewsSecurityTests(TestCase):
    def setUp(self):
        self.org_a = OrganizationFactory()
        self.org_b = OrganizationFactory()
        self.user_a = UserFactory(organization=self.org_a)
        perms = Permission.objects.filter(
            codename__in=["view_extensions", "edit_configuration"]
        )
        self.user_a.user_permissions.add(*perms)
        self.client.force_login(self.user_a)

        self.ext_b = Extensions.objects.create(
            organization=self.org_b, entity_name="SMS", status=0
        )

    def test_extension_status_blocks_cross_org_idor(self):
        url = reverse("configurations:extension_status", kwargs={"id": self.ext_b.id})
        resp = self.client.post(
            url,
            {"status": "on"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 404)
        self.ext_b.refresh_from_db()
        self.assertEqual(self.ext_b.status, 0)

    def test_save_sms_configuration_retains_masked_secret_and_masks_fixed_length(self):
        SMSConfiguration.objects.create(
            organization=self.org_a,
            provider="twilio",
            credentials={
                "account_sid": "AC123456",
                "auth_token": "super-secret-token",
                "from_number": "+15550001111",
            },
            is_active=False,
        )
        get_resp = self.client.get(reverse("configurations:sms_integration") + "?provider=twilio")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.context["display_credentials"]["auth_token"], "••••••••")

        post_resp = self.client.post(
            reverse("configurations:save_sms_configuration"),
            {
                "provider": "twilio",
                "account_sid": "AC123456",
                "auth_token": "••••••••",
                "from_number": "+15550001111",
                "is_active": "on",
            },
        )
        self.assertEqual(post_resp.status_code, 302)
        cfg = SMSConfiguration.objects.get(organization=self.org_a, provider="twilio")
        self.assertEqual(cfg.credentials["auth_token"], "super-secret-token")
        self.assertTrue(cfg.is_active)

    @patch("configurations.sms_providers.twilio.requests.post")
    def test_test_sms_forwards_custom_message(self, mock_post):
        ok_resp = MagicMock(status_code=201)
        ok_resp.json.return_value = {"sid": "SM123"}
        mock_post.return_value = ok_resp

        resp = self.client.post(
            reverse("configurations:test_sms"),
            {
                "provider": "twilio",
                "phone": "+15550009999",
                "message": "Custom hello",
                "account_sid": "AC123456",
                "auth_token": "tok",
                "from_number": "+15550001111",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_post.call_args.kwargs["data"]["Body"], "Custom hello")
