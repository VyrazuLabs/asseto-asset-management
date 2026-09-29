"""View and form tests for serialized consumables (add/edit rules, checkout, unit actions)."""

import pytest
from django.core.management import call_command
from django.urls import reverse

from common.factories import OrganizationFactory, UserFactory, make_user_with_permissions
from consumables.forms import ConsumableForm
from consumables.models import ConsumableUnit
from consumables.tests.factories import ConsumableFactory
from consumables.utils import checkout_serialized_units
from products.models import Product

EDIT_PERMS = ("consumables.view_consumable", "consumables.edit_consumable", "consumables.add_consumable")


@pytest.fixture
def permissions(db):
    """Create the Permission rows that make_user_with_permissions looks up."""
    call_command("sync_permissions", verbosity=0)


@pytest.fixture
def editor(client, permissions):
    user = make_user_with_permissions(*EDIT_PERMS)
    client.force_login(user)
    return user


def _serialized(org, quantity=3):
    consumable = ConsumableFactory(organization=org, is_serialized=True, quantity=quantity)
    consumable.apply_serialized_quantity()
    return consumable


@pytest.mark.django_db
def test_form_with_serialized_quantity_lowered_is_invalid():
    # Arrange
    consumable = _serialized(OrganizationFactory(), quantity=3)
    data = {"consumable_name": "x", "product": _product(consumable).pk, "quantity": 2, "is_serialized": "on"}

    # Act
    form = ConsumableForm(data, instance=consumable, organization=consumable.organization)

    # Assert
    assert not form.is_valid()
    assert "quantity" in form.errors


@pytest.mark.django_db
def test_form_serialized_flag_is_disabled_once_consumable_has_checkouts():
    # Arrange
    consumable = _serialized(OrganizationFactory(), quantity=2)
    user = UserFactory(organization=consumable.organization)
    checkout_serialized_units(consumable, [str(consumable.units.first().pk)], user, "", "t")

    # Act
    form = ConsumableForm(instance=consumable, organization=consumable.organization)

    # Assert
    assert form.fields["is_serialized"].disabled is True


def _product(consumable):
    return Product.objects.create(name="P", organization=consumable.organization)


@pytest.mark.django_db
def test_checkout_view_with_picked_units_checks_out_only_those_units(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=4)
    picked = consumable.units.all()[1:3]

    # Act
    response = client.post(
        reverse("consumables:checkout", args=[consumable.pk]),
        {"user": editor.pk, "units": [str(u.pk) for u in picked], "notes": "n"},
    )

    # Assert
    consumable.refresh_from_db()
    assert response.status_code == 302
    assert consumable.remaining_quantity == 2
    assert set(consumable.units.filter(status="checked_out").values_list("sequence", flat=True)) == {2, 3}


@pytest.mark.django_db
def test_checkout_view_without_units_on_serialized_consumable_changes_nothing(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=2)

    # Act
    client.post(reverse("consumables:checkout", args=[consumable.pk]), {"user": editor.pk, "quantity": 1})

    # Assert
    consumable.refresh_from_db()
    assert consumable.remaining_quantity == 2


@pytest.mark.django_db
def test_checkout_view_for_non_serialized_consumable_still_uses_quantity(client, editor):
    # Arrange
    consumable = ConsumableFactory(organization=editor.organization, quantity=5)

    # Act
    client.post(reverse("consumables:checkout", args=[consumable.pk]), {"user": editor.pk, "quantity": 2})

    # Assert
    consumable.refresh_from_db()
    assert consumable.remaining_quantity == 3


@pytest.mark.django_db
def test_checkout_view_for_other_organizations_consumable_changes_nothing(client, editor):
    # Arrange
    foreign = _serialized(OrganizationFactory())

    # Act
    client.post(
        reverse("consumables:checkout", args=[foreign.pk]),
        {"user": editor.pk, "units": [str(foreign.units.first().pk)]},
    )

    # Assert
    foreign.refresh_from_db()
    assert foreign.remaining_quantity == 3


@pytest.mark.django_db
def test_available_units_returns_only_in_stock_units(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=3)
    consumable.units.filter(sequence=1).update(status=ConsumableUnit.STATUS_LOST)

    # Act
    response = client.get(reverse("consumables:available_units", args=[consumable.pk]))

    # Assert
    assert [u["sub_id"] for u in response.json()["units"]] == ["#100000-02", "#100000-03"]


@pytest.mark.django_db
def test_available_units_for_user_without_edit_permission_is_denied(client, permissions):
    # Arrange
    user = make_user_with_permissions("consumables.view_consumable")
    client.force_login(user)
    consumable = _serialized(user.organization)

    # Act
    response = client.get(reverse("consumables:available_units", args=[consumable.pk]))

    # Assert
    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_update_unit_saves_serial(client, editor):
    # Arrange
    unit = _serialized(editor.organization, quantity=1).units.first()

    # Act
    client.post(reverse("consumables:update_unit", args=[unit.pk]), {"serial_no": "SN-9"})

    # Assert
    unit.refresh_from_db()
    assert unit.serial_no == "SN-9"


@pytest.mark.django_db
def test_update_unit_retire_marks_unit_lost(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=2)
    unit = consumable.units.first()

    # Act
    client.post(reverse("consumables:update_unit", args=[unit.pk]), {"retire": "lost"})

    # Assert
    unit.refresh_from_db()
    consumable.refresh_from_db()
    assert unit.status == ConsumableUnit.STATUS_LOST
    assert consumable.quantity == 1


@pytest.mark.django_db
def test_update_unit_of_other_organization_changes_nothing(client, editor):
    # Arrange
    unit = _serialized(OrganizationFactory(), quantity=1).units.first()

    # Act
    client.post(reverse("consumables:update_unit", args=[unit.pk]), {"serial_no": "X"})

    # Assert
    unit.refresh_from_db()
    assert unit.serial_no is None


@pytest.mark.django_db
def test_bulk_serials_view_tags_units(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=2)

    # Act
    client.post(reverse("consumables:bulk_serials", args=[consumable.pk]), {"serials": "A1\nA2"})

    # Assert
    assert list(consumable.units.values_list("serial_no", flat=True)) == ["A1", "A2"]


@pytest.mark.django_db
def test_bulk_serials_view_for_non_serialized_consumable_renders_not_found_page(client, editor):
    # Arrange
    consumable = ConsumableFactory(organization=editor.organization)

    # Act
    response = client.post(reverse("consumables:bulk_serials", args=[consumable.pk]), {"serials": "A1"})

    # Assert
    assert "error-404" in [t.name.rsplit("/", 1)[-1].removesuffix(".html") for t in response.templates if t.name]


@pytest.mark.django_db
def test_detail_view_for_serialized_consumable_lists_sub_ids(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=2)

    # Act
    response = client.get(reverse("consumables:detail", args=[consumable.pk]))

    # Assert
    assert response.status_code == 200
    assert b"#100000-01" in response.content
    assert b"#100000-02" in response.content


@pytest.mark.django_db
def test_add_view_with_serialized_flag_creates_units_for_quantity(client, editor):
    # Arrange
    product = Product.objects.create(name="P", organization=editor.organization)

    # Act
    client.post(
        reverse("consumables:add"),
        {"consumable_name": "Toner", "product": product.pk, "quantity": 3, "is_serialized": "on"},
    )

    # Assert
    from consumables.models import Consumable

    consumable = Consumable.objects.get(consumable_name="Toner")
    assert consumable.units.count() == 3
    assert consumable.remaining_quantity == 3


@pytest.mark.django_db
def test_edit_view_when_serialized_quantity_raised_adds_units(client, editor):
    # Arrange
    consumable = _serialized(editor.organization, quantity=2)
    product = _product(consumable)

    # Act
    client.post(
        reverse("consumables:edit", args=[consumable.pk]),
        {"consumable_name": "x", "product": product.pk, "quantity": 4, "is_serialized": "on"},
    )

    # Assert
    consumable.refresh_from_db()
    assert consumable.units.count() == 4
    assert consumable.remaining_quantity == 4


@pytest.mark.django_db
def test_checkout_view_with_return_to_detail_redirects_to_detail_page(client, editor):
    # Arrange
    consumable = ConsumableFactory(organization=editor.organization, quantity=5)

    # Act
    response = client.post(
        reverse("consumables:checkout", args=[consumable.pk]),
        {"user": editor.pk, "quantity": 1, "return_to": "detail"},
    )

    # Assert
    assert response.url == reverse("consumables:detail", args=[consumable.pk])


@pytest.mark.django_db
def test_checkout_view_without_return_to_redirects_to_list(client, editor):
    # Arrange
    consumable = ConsumableFactory(organization=editor.organization, quantity=5)

    # Act
    response = client.post(
        reverse("consumables:checkout", args=[consumable.pk]), {"user": editor.pk, "quantity": 1}
    )

    # Assert
    assert response.url == reverse("consumables:list")


@pytest.mark.django_db
def test_detail_view_with_edit_permission_renders_checkout_button_and_modal(client, editor):
    # Arrange
    consumable = ConsumableFactory(organization=editor.organization, quantity=5)

    # Act
    response = client.get(reverse("consumables:detail", args=[consumable.pk]))

    # Assert
    assert b'id="checkoutModal"' in response.content
    assert b"openCheckoutModal(" in response.content


@pytest.mark.django_db
def test_detail_view_without_edit_permission_hides_checkout_button(client, permissions):
    # Arrange
    user = make_user_with_permissions("consumables.view_consumable")
    client.force_login(user)
    consumable = ConsumableFactory(organization=user.organization, quantity=5)

    # Act
    response = client.get(reverse("consumables:detail", args=[consumable.pk]))

    # Assert
    assert b'id="checkoutModal"' not in response.content
