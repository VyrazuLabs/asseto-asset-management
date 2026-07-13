from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict

from common.factories import OrganizationFactory, UserFactory
from clients.models import Client, ClientContact
from support.models import SupportTicket, TicketComment, TicketActivity
from support.utils import SupportTicketService


class MockRequest:
    def __init__(self, user, post_data=None, files_data=None):
        self.user = user
        self.POST = post_data or {}
        self.FILES = MultiValueDict(files_data or {})


class SupportTicketCommentsTests(TestCase):
    def setUp(self):
        self.organization = OrganizationFactory()
        self.staff_user = UserFactory(organization=self.organization)
        self.client = Client.objects.create(
            name="Test Client",
            organization=self.organization,
        )
        self.contact = ClientContact.objects.create(
            name="Client Contact",
            email="contact@example.com",
            client=self.client,
        )
        self.ticket = SupportTicket.objects.create(
            subject="Test Difficulties",
            description="Testing details...",
            organization=self.organization,
            created_by=str(self.staff_user.id),
        )

    def test_add_comment_staff(self):
        """Verify that a staff user can post comments, logging activity and marking it as a staff comment."""
        post_data = {"comment_content": "This is a comment from staff."}
        request = MockRequest(user=self.staff_user, post_data=post_data)

        comment, created = SupportTicketService.add_comment(request, self.ticket)

        self.assertTrue(created)
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, "This is a comment from staff.")
        self.assertEqual(comment.author, self.staff_user)
        self.assertTrue(comment.is_staff_comment)
        self.assertEqual(comment.display_name, self.staff_user.get_full_name())

        # Verify activity was logged
        activity = TicketActivity.objects.filter(ticket=self.ticket, activity_type="comment").first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.description, "This is a comment from staff.")
        self.assertEqual(activity.performed_by, self.staff_user)

    def test_add_client_comment(self):
        """Verify that a client contact comment sets correct relations and is_staff_comment is False."""
        post_data = {"comment_content": "This is a client comment."}
        request = MockRequest(user=None, post_data=post_data)

        comment, created = SupportTicketService.add_client_comment(request, self.ticket, self.contact)

        self.assertTrue(created)
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, "This is a client comment.")
        self.assertIsNone(comment.author)
        self.assertEqual(comment.contact, self.contact)
        self.assertEqual(comment.client, self.client)
        self.assertFalse(comment.is_staff_comment)
        self.assertEqual(comment.display_name, self.contact.name)

        # Verify activity was logged
        activity = TicketActivity.objects.filter(ticket=self.ticket, activity_type="comment").first()
        self.assertIsNotNone(activity)
        self.assertEqual(activity.contact, self.contact)
        self.assertIsNone(activity.performed_by)

    def test_upload_validation_allowed_file(self):
        """Verify uploading an allowed file type (e.g., pdf) succeeds."""
        pdf_file = SimpleUploadedFile("document.pdf", b"file_content", content_type="application/pdf")
        post_data = {"comment_content": "Attached a PDF."}
        files_data = {"comment_attachments": [pdf_file]}
        request = MockRequest(user=self.staff_user, post_data=post_data, files_data=files_data)

        comment, created = SupportTicketService.add_comment(request, self.ticket)

        self.assertTrue(created)
        self.assertEqual(comment.attachments.count(), 1)
        attachment = comment.attachments.first()
        self.assertEqual(attachment.file_name, "document.pdf")

    def test_upload_validation_invalid_extension(self):
        """Verify uploading an unsafe file type (e.g., sh script) is rejected with ValidationError."""
        sh_file = SimpleUploadedFile("script.sh", b"echo 'bad script'", content_type="text/x-shellscript")
        post_data = {"comment_content": "Unsafe upload."}
        files_data = {"comment_attachments": [sh_file]}
        request = MockRequest(user=self.staff_user, post_data=post_data, files_data=files_data)

        with self.assertRaises(ValidationError) as context:
            SupportTicketService.add_comment(request, self.ticket)

        self.assertIn("not allowed", str(context.exception))
        # Ensure no comment was created
        self.assertEqual(TicketComment.objects.count(), 0)

    def test_upload_validation_size_exceeded(self):
        """Verify uploading a file exceeding 10MB is rejected with ValidationError."""
        # Create a mock file with size 11MB
        large_file = SimpleUploadedFile("large_image.png", b"x" * (11 * 1024 * 1024), content_type="image/png")
        post_data = {"comment_content": "Large file."}
        files_data = {"comment_attachments": [large_file]}
        request = MockRequest(user=self.staff_user, post_data=post_data, files_data=files_data)

        with self.assertRaises(ValidationError) as context:
            SupportTicketService.add_comment(request, self.ticket)

        self.assertIn("exceeds the 10MB", str(context.exception))
        # Ensure no comment was created
        self.assertEqual(TicketComment.objects.count(), 0)

    def test_display_name_deleted_staff(self):
        """Verify display_name fallback for deleted staff user comments."""
        comment = TicketComment.objects.create(
            ticket=self.ticket,
            content="Past staff comment.",
            author=None,
            is_staff_comment=True,
        )

        self.assertEqual(comment.display_name, "Deleted Staff")


class SupportTicketHappyCodeTests(TestCase):
    def setUp(self):
        self.organization = OrganizationFactory()
        self.staff_user = UserFactory(organization=self.organization)
        self.ticket = SupportTicket.objects.create(
            subject="Test Difficulties",
            description="Testing details...",
            organization=self.organization,
            created_by=str(self.staff_user.id),
            status="0", # Open
        )
        self.happy_code = self.ticket.happy_code
        self.assertTrue(self.happy_code)

    def test_close_ticket_with_exact_happy_code(self):
        """Verify that a ticket can be closed if the exact happy code is provided."""
        post_data = {"status": "4", "happy_code": self.happy_code}
        request = MockRequest(user=self.staff_user, post_data=post_data)

        class MockForm:
            def __init__(self, ticket):
                self.ticket = ticket
            def save(self, commit=False):
                self.ticket.status = "4"
                return self.ticket

        form = MockForm(self.ticket)
        # Should not raise ValidationError
        SupportTicketService.update(request, self.ticket.id, form)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "4")

    def test_close_ticket_with_prefixed_happy_code(self):
        """Verify that a ticket can be closed if the happy code is prefixed with HC-."""
        post_data = {"status": "4", "happy_code": f"HC-{self.happy_code}"}
        request = MockRequest(user=self.staff_user, post_data=post_data)

        class MockForm:
            def __init__(self, ticket):
                self.ticket = ticket
            def save(self, commit=False):
                self.ticket.status = "4"
                return self.ticket

        form = MockForm(self.ticket)
        # Should not raise ValidationError
        SupportTicketService.update(request, self.ticket.id, form)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "4")

    def test_close_ticket_with_invalid_happy_code(self):
        """Verify that closing is rejected if the happy code is incorrect."""
        post_data = {"status": "4", "happy_code": "WRONG1"}
        request = MockRequest(user=self.staff_user, post_data=post_data)

        class MockForm:
            def __init__(self, ticket):
                self.ticket = ticket
            def save(self, commit=False):
                self.ticket.status = "4"
                return self.ticket

        form = MockForm(self.ticket)
        with self.assertRaises(ValidationError) as context:
            SupportTicketService.update(request, self.ticket.id, form)

        self.assertIn("Invalid happy code", str(context.exception))

