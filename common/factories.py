"""Base factory_boy factories shared across the test suite.

These are the foundational factories that later per-app factories will
subclass or depend on, since every org-scoped model factory needs an
org+user dependency chain. Defined here (in ``common``) so Phase 1+ work can
import them without duplicating org/user setup in each app.
"""

import factory
import factory.django

from authentication.models import User
from dashboard.models import Organization


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for ``dashboard.models.Organization``.

    Produces a minimal, valid ``Organization`` instance with a unique name.
    """

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Org {n}")


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for ``authentication.models.User``.

    Builds a ``User`` via the custom ``UserManager.create_user`` (rather than
    plain ``Meta.model()`` construction) because ``User`` uses a custom
    manager that hashes the password and sets manager-controlled flags
    (``is_staff``/``is_superuser``) as part of user creation. Each generated
    user belongs to its own ``OrganizationFactory``-created organization
    unless an ``organization`` is passed explicitly.

    ``UserManager.create_user`` unconditionally force-sets
    ``is_staff=True, is_superuser=True`` after construction, so every user
    from this factory is a superuser and passing ``is_staff=False`` /
    ``is_superuser=False`` here has no effect. Tests needing a non-privileged
    user must flip those flags and ``save()`` after the factory call.
    """

    class Meta:
        model = User

    organization = factory.SubFactory(OrganizationFactory)
    password = "TestPass123!"
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    full_name = factory.Faker("name")
    phone = factory.Sequence(lambda n: f"+1555000{n:04d}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create a ``User`` via ``UserManager.create_user``.

        Args:
            model_class: The ``User`` model class (``cls._meta.model``).
            *args: Unused positional args from factory_boy's call signature.
            **kwargs: Field values collected by factory_boy, including
                ``email``, ``full_name``, ``username``, ``phone``,
                ``organization``, and ``password``.

        Returns:
            User: A saved, persisted ``User`` instance with a usable
            hashed password and an assigned ``organization``.
        """
        password = kwargs.pop("password")
        email = kwargs.pop("email")
        full_name = kwargs.pop("full_name")
        username = kwargs.pop("username")
        phone = kwargs.pop("phone")
        kwargs.setdefault("is_active", True)
        manager = model_class.objects
        return manager.create_user(
            email=email,
            full_name=full_name,
            username=username,
            phone=phone,
            password=password,
            **kwargs,
        )
