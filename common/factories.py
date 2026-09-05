"""Base factory_boy factories shared across the test suite.

These are the foundational factories that later per-app factories will
subclass or depend on, since every org-scoped model factory needs an
org+user dependency chain. Defined here (in ``common``) so Phase 1+ work can
import them without duplicating org/user setup in each app.
"""

import factory
import factory.django

from authentication.models import User
from common.permissions import get_content_type_for_module
from dashboard.models import Organization
from roles.models import Role


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


class RoleFactory(factory.django.DjangoModelFactory):
    """Factory for ``roles.models.Role``.

    ``Role`` is a Django ``Group`` (multi-table inheritance) plus an
    ``organization`` FK — ``name`` must stay unique per Group semantics, so
    a random one is generated the same way ``roles/views.py`` does it.
    """

    class Meta:
        model = Role

    related_name = factory.Sequence(lambda n: f"Role {n}")
    organization = factory.SubFactory(OrganizationFactory)

    @factory.lazy_attribute
    def name(self):
        """Generate a unique Group.name, mirroring roles/views.py's uuid4().hex."""
        import uuid

        return uuid.uuid4().hex


def make_user_with_permissions(*codenames: str, organization=None) -> User:
    """Build a non-superuser ``User`` whose role grants exactly ``codenames``.

    ``UserFactory``/``UserManager.create_user`` force-sets
    ``is_superuser=True`` on every created user, so this explicitly flips
    it back off after creation — otherwise every "permission denied" test
    written against this helper would silently pass regardless of the
    role's actual permissions.

    Args:
        *codenames: Fully-qualified permission strings the built user's
            role should hold, e.g. ``"clients.view_client"``.
        organization: Organization to scope the user/role to; a fresh one
            is created if omitted.

    Returns:
        User: A saved, non-superuser user with a role granting exactly the
        requested permissions.
    """
    from django.contrib.auth.models import Permission

    org = organization or OrganizationFactory()
    user = UserFactory(organization=org)
    user.is_superuser = False
    user.is_staff = True
    user.save()

    role = RoleFactory(organization=org)
    for codename in codenames:
        app_label, _, bare_codename = codename.partition(".")
        module = next((m for m in _permission_modules() if m.app_label == app_label and bare_codename in m.codenames()), None)
        if module is None:
            raise ValueError(f"No PermissionModule owns codename {codename!r}")
        content_type = get_content_type_for_module(module)
        permission = Permission.objects.get(codename=bare_codename, content_type=content_type)
        role.permissions.add(permission)

    user.groups.add(role)
    return user


def _permission_modules():
    """Lazy import to avoid a hard import-time dependency on the registry."""
    from common.permissions import PERMISSION_MODULES

    return PERMISSION_MODULES
