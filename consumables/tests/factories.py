"""factory_boy factories for the consumables app."""

import factory
import factory.django

from common.factories import OrganizationFactory
from consumables.models import Consumable


class ConsumableFactory(factory.django.DjangoModelFactory):
    """Factory for ``Consumable``; pass ``is_serialized=True`` then call ``add_units`` via ``quantity``."""

    class Meta:
        model = Consumable

    consumable_name = factory.Sequence(lambda n: f"Consumable {n}")
    organization = factory.SubFactory(OrganizationFactory)
    quantity = 5
    min_qty = 1
