"""Tests for serialized consumables: unit numbering, quantity sync, and unit services."""

import pytest
from django.core.exceptions import ValidationError

from common.factories import UserFactory
from consumables.models import CONSUMABLE_ID_START, ConsumableUnit
from consumables.tests.factories import ConsumableFactory
from consumables.utils import (
    bulk_assign_serials,
    checkout_serialized_units,
    retire_unit,
    set_unit_serial,
)


def _serialized(quantity=5, **kwargs):
    consumable = ConsumableFactory(is_serialized=True, quantity=quantity, **kwargs)
    consumable.apply_serialized_quantity()
    return consumable


@pytest.mark.django_db
def test_consumable_id_first_in_organization_starts_at_100000():
    # Arrange / Act
    consumable = ConsumableFactory()

    # Assert
    assert consumable.consumable_id == CONSUMABLE_ID_START


@pytest.mark.django_db
def test_consumable_id_increments_per_organization_independently():
    # Arrange
    first = ConsumableFactory()
    second = ConsumableFactory(organization=first.organization)
    other_org = ConsumableFactory()

    # Assert
    assert second.consumable_id == first.consumable_id + 1
    assert other_org.consumable_id == CONSUMABLE_ID_START


@pytest.mark.django_db
def test_apply_serialized_quantity_creates_units_with_sequential_sub_ids():
    # Arrange / Act
    consumable = _serialized(quantity=3)

    # Assert
    assert [u.sub_id for u in consumable.units.select_related("consumable")] == [
        "#100000-01",
        "#100000-02",
        "#100000-03",
    ]
    assert consumable.remaining_quantity == 3


@pytest.mark.django_db
def test_apply_serialized_quantity_on_non_serialized_creates_no_units():
    # Arrange
    consumable = ConsumableFactory(quantity=4)

    # Act
    consumable.apply_serialized_quantity()

    # Assert
    assert consumable.units.count() == 0


@pytest.mark.django_db
def test_apply_serialized_quantity_when_raised_adds_only_new_units():
    # Arrange
    consumable = _serialized(quantity=3)
    consumable.quantity = 5

    # Act
    consumable.apply_serialized_quantity()

    # Assert
    assert list(consumable.units.values_list("sequence", flat=True)) == [1, 2, 3, 4, 5]
    assert consumable.quantity == 5


@pytest.mark.django_db
def test_apply_serialized_quantity_when_lowered_resyncs_without_deleting_units():
    # Arrange
    consumable = _serialized(quantity=3)
    consumable.quantity = 1

    # Act
    consumable.apply_serialized_quantity()

    # Assert
    assert consumable.units.count() == 3
    assert consumable.quantity == 3


@pytest.mark.django_db
def test_add_units_with_zero_count_is_noop():
    # Arrange
    consumable = _serialized(quantity=2)

    # Act
    consumable.add_units(0)

    # Assert
    assert consumable.units.count() == 2


@pytest.mark.django_db
def test_sync_quantities_on_non_serialized_leaves_quantity_untouched():
    # Arrange
    consumable = ConsumableFactory(quantity=7)

    # Act
    consumable.sync_quantities()

    # Assert
    assert consumable.quantity == 7


@pytest.mark.django_db
def test_checkout_serialized_units_marks_units_and_updates_remaining():
    # Arrange
    consumable = _serialized(quantity=5)
    user = UserFactory(organization=consumable.organization)
    picked = list(consumable.units.all()[2:4])

    # Act
    checkout = checkout_serialized_units(
        consumable, [str(u.pk) for u in picked], user, "note", "tester"
    )

    # Assert
    consumable.refresh_from_db()
    assert checkout.quantity == 2
    assert consumable.remaining_quantity == 3
    assert consumable.total_checked_out == 2
    assert set(checkout.units.values_list("pk", flat=True)) == {u.pk for u in picked}


@pytest.mark.django_db
def test_checkout_serialized_units_with_already_checked_out_unit_raises():
    # Arrange
    consumable = _serialized(quantity=2)
    user = UserFactory(organization=consumable.organization)
    unit = consumable.units.first()
    checkout_serialized_units(consumable, [str(unit.pk)], user, "", "tester")

    # Act / Assert
    with pytest.raises(ValidationError):
        checkout_serialized_units(consumable, [str(unit.pk)], user, "", "tester")


@pytest.mark.django_db
def test_checkout_serialized_units_with_unit_of_another_consumable_raises():
    # Arrange
    consumable = _serialized(quantity=1)
    foreign_unit = _serialized(quantity=1).units.first()
    user = UserFactory(organization=consumable.organization)

    # Act / Assert
    with pytest.raises(ValidationError):
        checkout_serialized_units(consumable, [str(foreign_unit.pk)], user, "", "tester")


@pytest.mark.django_db
@pytest.mark.parametrize("unit_ids", [[], ["not-a-uuid"]])
def test_checkout_serialized_units_with_empty_or_malformed_selection_raises(unit_ids):
    # Arrange
    consumable = _serialized(quantity=1)
    user = UserFactory(organization=consumable.organization)

    # Act / Assert
    with pytest.raises(ValidationError):
        checkout_serialized_units(consumable, unit_ids, user, "", "tester")


@pytest.mark.django_db
def test_retire_unit_reduces_quantity_and_remaining():
    # Arrange
    consumable = _serialized(quantity=3)
    unit = consumable.units.first()

    # Act
    retire_unit(unit, ConsumableUnit.STATUS_LOST)

    # Assert
    consumable.refresh_from_db()
    assert consumable.quantity == 2
    assert consumable.remaining_quantity == 2


@pytest.mark.django_db
def test_retire_unit_with_invalid_status_raises():
    # Arrange
    unit = _serialized(quantity=1).units.first()

    # Act / Assert
    with pytest.raises(ValidationError):
        retire_unit(unit, ConsumableUnit.STATUS_IN_STOCK)


@pytest.mark.django_db
def test_retire_unit_when_checked_out_raises():
    # Arrange
    consumable = _serialized(quantity=1)
    user = UserFactory(organization=consumable.organization)
    unit = consumable.units.first()
    checkout_serialized_units(consumable, [str(unit.pk)], user, "", "tester")
    unit.refresh_from_db()

    # Act / Assert
    with pytest.raises(ValidationError):
        retire_unit(unit, ConsumableUnit.STATUS_LOST)


@pytest.mark.django_db
def test_set_unit_serial_with_duplicate_in_same_consumable_raises():
    # Arrange
    consumable = _serialized(quantity=2)
    first, second = consumable.units.all()
    set_unit_serial(first, "SN-1")

    # Act / Assert
    with pytest.raises(ValidationError):
        set_unit_serial(second, "SN-1")


@pytest.mark.django_db
def test_set_unit_serial_with_blank_value_clears_serial():
    # Arrange
    unit = _serialized(quantity=1).units.first()
    set_unit_serial(unit, "SN-1")

    # Act
    set_unit_serial(unit, "  ")

    # Assert
    unit.refresh_from_db()
    assert unit.serial_no is None


@pytest.mark.django_db
def test_bulk_assign_serials_tags_untagged_units_in_sequence_order():
    # Arrange
    consumable = _serialized(quantity=3)
    set_unit_serial(consumable.units.first(), "SN-A")

    # Act
    tagged = bulk_assign_serials(consumable, "SN-B\n\nSN-C\n")

    # Assert
    assert tagged == 2
    assert list(consumable.units.values_list("serial_no", flat=True)) == ["SN-A", "SN-B", "SN-C"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "raw_text",
    ["", "SN-1\nSN-1", "SN-1\nSN-2\nSN-3", "SN-X"],
    ids=["empty", "duplicate-in-paste", "more-than-untagged", "already-in-use"],
)
def test_bulk_assign_serials_with_invalid_input_raises_and_writes_nothing(raw_text):
    # Arrange
    consumable = _serialized(quantity=2)
    set_unit_serial(consumable.units.first(), "SN-X")

    # Act
    with pytest.raises(ValidationError):
        bulk_assign_serials(consumable, raw_text)

    # Assert
    assert list(consumable.units.values_list("serial_no", flat=True)) == ["SN-X", None]
