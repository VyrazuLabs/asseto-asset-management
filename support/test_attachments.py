"""Tests for support-ticket attachment upload/delete endpoints and the
``TicketAttachment.extension`` / ``is_image`` helpers.

Covers auth failures, cross-tenant 404s, validation rejections (including the
removed ``.svg`` allowlist entry), the POST-only delete contract and the
open-redirect guard on the post-delete redirect.
"""

import uuid

import factory
import factory.django
import pytest
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from common.factories import OrganizationFactory, UserFactory, make_user_with_permissions
from support.models import SupportTicket, TicketActivity, TicketAttachment


class _SupportTicketFactory(factory.django.DjangoModelFactory):
    """Local factory for ``SupportTicket``; promote to ``support/factories.py``
    when another suite needs it."""

    class Meta:
        model = SupportTicket

    subject = factory.Sequence(lambda n: f"Ticket {n}")
    organization = factory.SubFactory(OrganizationFactory)


class _TicketAttachmentFactory(factory.django.DjangoModelFactory):
    """Local factory for ``TicketAttachment`` backed by a tiny in-memory PDF."""

    class Meta:
        model = TicketAttachment

    ticket = factory.SubFactory(_SupportTicketFactory)
    file = factory.django.FileField(filename="doc.pdf", data=b"%PDF-1.4")
    file_name = "doc.pdf"
    file_size = 8


@pytest.fixture(autouse=True)
def _synced_permissions(db):
    """Permission rows are written by ``sync_permissions``, not post_migrate."""
    call_command("sync_permissions", verbosity=0)


@pytest.fixture(autouse=True)
def _isolated_media_root(settings, tmp_path):
    """Keep uploaded test files out of the real MEDIA_ROOT."""
    settings.MEDIA_ROOT = str(tmp_path)


def _rendered_templates(response):
    """Base names of rendered templates; the app's 403/404 handlers return HTTP 200."""
    return [
        t.name.rsplit("/", 1)[-1].removesuffix(".html")
        for t in response.templates
        if t.name
    ]


def _upload_url(ticket):
    return reverse("support:ticket_upload_attachment", kwargs={"id": ticket.id})


def _delete_url(attachment):
    return reverse("support:ticket_attachment_delete", kwargs={"id": attachment.id})


def _file(name, content=b"data", content_type="application/octet-stream"):
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.mark.django_db
def test_upload_attachment_with_valid_pdf_returns_card_html_and_logs_activity(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)

    # Act
    response = client.post(
        _upload_url(ticket), {"attachments": _file("report.pdf", b"%PDF-1.4")}
    )

    # Assert
    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["count"] == 1
    assert "report.pdf" in payload["html"]
    assert ticket.attachments.count() == 1
    assert TicketActivity.objects.filter(
        ticket=ticket, activity_type="attachment_added"
    ).exists()


@pytest.mark.django_db
def test_upload_attachment_without_file_returns_400(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)

    # Act
    response = client.post(_upload_url(ticket), {})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"success": False, "error": "No file selected."}
    assert ticket.attachments.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("filename", ["script.sh", "payload.exe", "logo.svg", "noext"])
def test_upload_attachment_with_disallowed_extension_returns_400(client, filename):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)

    # Act
    response = client.post(_upload_url(ticket), {"attachments": _file(filename)})

    # Assert
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert "not allowed" in response.json()["error"]
    assert ticket.attachments.count() == 0


@pytest.mark.django_db
def test_upload_attachment_with_double_extension_uses_final_extension(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)

    # Act
    response = client.post(_upload_url(ticket), {"attachments": _file("a.pdf.exe")})

    # Assert
    assert response.status_code == 400
    assert ticket.attachments.count() == 0


@pytest.mark.django_db
def test_upload_attachment_over_size_limit_returns_400(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)
    too_big = _file("big.png", b"x" * (11 * 1024 * 1024), "image/png")

    # Act
    response = client.post(_upload_url(ticket), {"attachments": too_big})

    # Assert
    assert response.status_code == 400
    assert "exceeds the 10MB" in response.json()["error"]


@pytest.mark.django_db
def test_upload_attachment_to_other_orgs_ticket_returns_404(client):
    # Arrange
    user = make_user_with_permissions("support.edit_ticket")
    foreign_ticket = _SupportTicketFactory()
    client.force_login(user)

    # Act
    response = client.post(
        _upload_url(foreign_ticket), {"attachments": _file("a.pdf", b"%PDF")}
    )

    # Assert
    assert "error-404" in _rendered_templates(response)
    assert foreign_ticket.attachments.count() == 0


@pytest.mark.django_db
def test_upload_attachment_with_get_returns_405(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)

    # Act
    response = client.get(_upload_url(ticket))

    # Assert
    assert response.status_code == 405


@pytest.mark.django_db
def test_upload_attachment_without_edit_permission_returns_403(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.view_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    client.force_login(user)

    # Act
    response = client.post(
        _upload_url(ticket), {"attachments": _file("a.pdf", b"%PDF")}
    )

    # Assert
    assert "error-403" in _rendered_templates(response)
    assert ticket.attachments.count() == 0


@pytest.mark.django_db
def test_upload_attachment_when_anonymous_redirects_to_login(client):
    # Arrange
    ticket = _SupportTicketFactory()

    # Act
    response = client.post(
        _upload_url(ticket), {"attachments": _file("a.pdf", b"%PDF")}
    )

    # Assert
    assert response.status_code == 302
    assert ticket.attachments.count() == 0


@pytest.mark.django_db
def test_delete_attachment_with_get_returns_405_and_keeps_attachment(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.delete_ticket", organization=org)
    attachment = _TicketAttachmentFactory(ticket=_SupportTicketFactory(organization=org))
    client.force_login(user)

    # Act
    response = client.get(_delete_url(attachment))

    # Assert
    assert response.status_code == 405
    assert TicketAttachment.objects.filter(pk=attachment.pk).exists()


@pytest.mark.django_db
def test_delete_attachment_with_post_removes_it_and_falls_back_to_ticket_detail(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.delete_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    attachment = _TicketAttachmentFactory(ticket=ticket)
    client.force_login(user)

    # Act
    response = client.post(_delete_url(attachment))

    # Assert
    assert response.status_code == 302
    assert response.url == reverse("support:ticket_detail", kwargs={"id": ticket.id})
    assert not TicketAttachment.objects.filter(pk=attachment.pk).exists()


@pytest.mark.django_db
def test_delete_attachment_with_same_host_referer_redirects_back_to_referer(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.delete_ticket", organization=org)
    attachment = _TicketAttachmentFactory(ticket=_SupportTicketFactory(organization=org))
    client.force_login(user)
    referer = "http://testserver/support/tickets/update/some-ticket"

    # Act
    response = client.post(_delete_url(attachment), HTTP_REFERER=referer)

    # Assert
    assert response.status_code == 302
    assert response.url == referer


@pytest.mark.django_db
def test_delete_attachment_with_foreign_referer_falls_back_to_ticket_detail(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.delete_ticket", organization=org)
    ticket = _SupportTicketFactory(organization=org)
    attachment = _TicketAttachmentFactory(ticket=ticket)
    client.force_login(user)

    # Act
    response = client.post(
        _delete_url(attachment), HTTP_REFERER="https://evil.example.com/phish"
    )

    # Assert
    assert response.status_code == 302
    assert response.url == reverse("support:ticket_detail", kwargs={"id": ticket.id})


@pytest.mark.django_db
def test_delete_attachment_of_other_orgs_ticket_returns_404(client):
    # Arrange
    user = make_user_with_permissions("support.delete_ticket")
    foreign_attachment = _TicketAttachmentFactory()
    client.force_login(user)

    # Act
    response = client.post(_delete_url(foreign_attachment))

    # Assert
    assert "error-404" in _rendered_templates(response)
    assert TicketAttachment.objects.filter(pk=foreign_attachment.pk).exists()


@pytest.mark.django_db
def test_delete_attachment_without_delete_permission_returns_403(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("support.edit_ticket", organization=org)
    attachment = _TicketAttachmentFactory(ticket=_SupportTicketFactory(organization=org))
    client.force_login(user)

    # Act
    response = client.post(_delete_url(attachment))

    # Assert
    assert "error-403" in _rendered_templates(response)
    assert TicketAttachment.objects.filter(pk=attachment.pk).exists()


@pytest.mark.django_db
def test_delete_attachment_when_anonymous_redirects_to_login(client):
    # Arrange
    attachment = _TicketAttachmentFactory()

    # Act
    response = client.post(_delete_url(attachment))

    # Assert
    assert response.status_code == 302
    assert "login" in response.url.lower() or "next=" in response.url
    assert TicketAttachment.objects.filter(pk=attachment.pk).exists()


@pytest.mark.parametrize(
    "name, expected_extension, expected_is_image",
    [
        ("a.pdf.exe", "exe", False),
        ("photo.PNG", "png", True),
        ("scan.jpeg", "jpeg", True),
        ("archive.tar.gz", "gz", False),
        ("diagram.svg", "svg", False),
        ("noextension", "", False),
        ("report.pdf", "pdf", False),
    ],
)
def test_ticket_attachment_extension_uses_final_suffix(
    name, expected_extension, expected_is_image
):
    # Arrange
    attachment = TicketAttachment(file=f"support/attachments/{name}", file_name=name)

    # Act
    extension = attachment.extension
    is_image = attachment.is_image

    # Assert
    assert extension == expected_extension
    assert is_image is expected_is_image


def test_ticket_attachment_extension_falls_back_to_file_name_when_file_empty():
    # Arrange
    attachment = TicketAttachment(file="", file_name="fallback.webp")

    # Act
    extension = attachment.extension

    # Assert
    assert extension == "webp"
    assert attachment.is_image is True


@pytest.mark.django_db
def test_ticket_edit_page_renders_post_form_for_attachment_delete(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "support.view_ticket",
        "support.edit_ticket",
        "support.delete_ticket",
        organization=org,
    )
    attachment = _TicketAttachmentFactory(ticket=_SupportTicketFactory(organization=org))
    client.force_login(user)

    # Act
    response = client.get(
        reverse("support:ticket_update", kwargs={"id": attachment.ticket.id})
    )

    # Assert
    html = response.content.decode()
    assert response.status_code == 200
    assert f'id="delete-attachment-{attachment.id}"' in html
    assert f'form="delete-attachment-{attachment.id}"' in html
    assert f'action="{_delete_url(attachment)}"' in html


@pytest.mark.django_db
def test_ticket_edit_page_hides_attachment_delete_without_delete_permission(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "support.view_ticket", "support.edit_ticket", organization=org
    )
    attachment = _TicketAttachmentFactory(ticket=_SupportTicketFactory(organization=org))
    client.force_login(user)

    # Act
    response = client.get(
        reverse("support:ticket_update", kwargs={"id": attachment.ticket.id})
    )

    # Assert
    assert response.status_code == 200
    assert f"delete-attachment-{attachment.id}" not in response.content.decode()
