# Task 3 Report: common/services.py and common/factories.py

## Summary

Implemented the Phase 0 shared service base, the asset-conditions helper, and base
factories for `Organization`/`User`, plus a focused pytest test. All verification
steps pass.

## Model verification (before writing code)

- `Organization` (`dashboard/models.py:85`): `TimeStampModel` subclass only (NOT a
  `SoftDeleteModel` — no `undeleted_objects` manager on `Organization` itself). Fields:
  `id` (UUID pk), `name` (CharField, `blank=True, null=True`), `website`, `email`,
  `phone`, `currency`, `date_format`, `logo`. The brief's `name = factory.Sequence(...)`
  assumption was correct.
- `User` (`authentication/models.py:67`): `AbstractBaseUser, PermissionsMixin,
  TimeStampModel, SoftDeleteModel`. UUID pk. Has `organization` FK
  (`models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)`) —
  confirmed it exists as the brief assumed. `USERNAME_FIELD = 'email'`,
  `REQUIRED_FIELDS = ['full_name', 'phone', 'username']`.
- `UserManager.create_user(self, email, full_name, username, phone, password,
  **extra_fields)` (`authentication/models.py:25`): builds the user via `self.model(...)`,
  calls `user.set_password(password)`, then **unconditionally sets
  `is_staff = True` and `is_superuser = True`** before saving. This looks like a
  pre-existing bug/design quirk (every user created via `create_user` becomes
  staff+superuser), but it is out of scope for this task — not touched, just noted.
  `is_active` defaults to `False` on the model and `create_user` does not set it, so
  the factory explicitly defaults `is_active=True` via `kwargs.setdefault` so factory-built
  users are usable in later phases' tests without every test having to set it manually.
- `SoftDeleteManager`/`undeleted_objects` confirmed at `dashboard/models.py:35-44`
  (`SoftDeleteModel.objects = models.Manager()`, `undeleted_objects = SoftDeleteManager()`,
  filtering `is_deleted=False`). `BaseMultiTenantService.base_queryset` relies on this
  convention for whatever `model` is passed in (e.g. `Asset`, `Audit` in later phases) —
  not on `Organization`, which doesn't have this manager.

## Files created

### `common/services.py`

```python
"""Shared service-layer base classes and helpers for the project.

This module provides the multi-tenant org-scoping base that every later
per-app ``Service`` class builds on (``BaseMultiTenantService``), plus a
shared helper that consolidates duplicated asset-condition aggregation logic
found across several apps' ``utils.py`` modules (``build_asset_conditions_map``).
"""

from collections import defaultdict


class BaseMultiTenantService:
    """Base class for per-app service classes that operate on org-scoped models.

    Subclasses should call ``base_queryset`` to obtain a queryset that is
    always filtered to the current user's organization, preventing
    cross-tenant data leakage.
    """

    @staticmethod
    def base_queryset(model, user):
        """Return an org-scoped, non-deleted queryset for ``model``.

        Args:
            model: A Django model class that exposes an ``undeleted_objects``
                manager (the project's ``SoftDeleteManager`` convention, see
                ``dashboard/models.py``) and an ``organization`` foreign key.
            user: The current ``User`` instance whose ``organization`` is used
                to scope the queryset.

        Returns:
            QuerySet: ``model.undeleted_objects`` filtered to
            ``organization=user.organization``. Never returns rows belonging
            to a different organization.
        """
        return model.undeleted_objects.filter(organization=user.organization)


def build_asset_conditions_map(audits_queryset):
    """Build a mapping of asset id to the list of conditions from its audits.

    Consolidates duplicated logic independently found in ``clients/utils.py``,
    ``vendors/utils.py``, ``audit/utils.py``, and ``assets/utils.py``, all of
    which iterate an ``Audit`` queryset and append ``audit.condition`` to a
    list keyed by ``audit.asset_id``.

    Args:
        audits_queryset: An iterable/queryset of ``Audit`` instances, each
            exposing ``asset_id`` and ``condition`` attributes.

    Returns:
        dict[Any, list]: A ``defaultdict(list)`` mapping each ``asset_id`` to
        the ordered list of ``condition`` values from its audits, in the
        order the queryset was iterated.
    """
    asset_conditions_map = defaultdict(list)
    for audit in audits_queryset:
        asset_conditions_map[audit.asset_id].append(audit.condition)
    return asset_conditions_map
```

### `common/factories.py`

```python
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
```

### `common/tests/__init__.py` (empty, makes `common/tests` a package)

### `common/tests/test_factories.py`

```python
"""Tests for the shared base factories in ``common.factories``.

Verifies that ``UserFactory`` produces a persisted, valid ``User`` with an
``organization`` assigned and a usable hashed password, exercising the
custom ``UserManager.create_user`` path used by the factory.
"""

import pytest

from common.factories import OrganizationFactory, UserFactory


@pytest.mark.django_db
def test_user_factory_creates_valid_user():
    """UserFactory() should create a persisted user with a valid organization.

    Asserts the user has a primary key (was saved), is linked to an
    ``Organization`` instance, and has a usable hashed password set via
    ``UserManager.create_user``.
    """
    user = UserFactory()

    assert user.pk is not None
    assert user.organization is not None
    assert user.organization.pk is not None
    assert user.check_password("TestPass123!")


@pytest.mark.django_db
def test_organization_factory_creates_valid_organization():
    """OrganizationFactory() should create a persisted organization with a name."""
    organization = OrganizationFactory()

    assert organization.pk is not None
    assert organization.name
```

## Testing performed

1. **Import check** (per brief's verification step):
   ```
   source env/bin/activate && DJANGO_SETTINGS_MODULE=AssetManagement.settings python -c "
   import django
   django.setup()
   from common.services import BaseMultiTenantService, build_asset_conditions_map
   from common.factories import OrganizationFactory, UserFactory
   print('imports OK')
   "
   ```
   Result: `imports OK` (plus pre-existing unrelated dotenv parse warnings and an
   `asset_signals_loaded` info log — both pre-existing, not caused by this change).

2. **Pytest run**:
   ```
   source env/bin/activate && pytest common/ -v --no-cov
   ```
   Result:
   ```
   common/tests/test_factories.py::test_user_factory_creates_valid_user PASSED
   common/tests/test_factories.py::test_organization_factory_creates_valid_organization PASSED
   2 passed, 4 warnings in 11.44s
   ```
   One teardown warning appeared (`OperationalError('database "test_asseto" is being
   accessed by other users...')`) — this is a test-DB-teardown artifact unrelated to
   the new code (likely a leftover connection from a concurrent process/shell), not a
   test failure; both tests reported PASSED.

3. **First attempt caught a real bug in my own code**: initially declared `password`
   inside a factory_boy `class Params:` block, which does NOT get passed as a kwarg to
   a custom `_create` override by default. This raised `KeyError: 'password'` on first
   run. Fixed by making `password` a plain factory attribute (`password = "TestPass123!"`)
   so it flows into `**kwargs` like the other fields. Re-ran and both tests passed.

4. **ruff check**: attempted `ruff check common/services.py common/factories.py
   common/tests/test_factories.py` — failed with a pre-existing `pyproject.toml` parse
   error (`unknown field 'known-django'` under `[tool.ruff]`), unrelated to this task's
   files; this is a Task 1 config issue, not something introduced here, and out of scope
   to fix under "one concern per change."

5. **mypy check**: ran `mypy common/services.py common/factories.py`. All 22 reported
   errors are in other pre-existing files pulled in transitively (`dashboard/models.py`,
   `authentication/models.py`, `AssetManagement/settings.py`, etc. — missing stubs for
   `django_resized`/`simple_history`/`pymysql`/`decouple`, and pre-existing type
   mismatches in unrelated model fields). Zero errors originate from
   `common/services.py` or `common/factories.py` themselves.

## Files changed

- `common/services.py` (new)
- `common/factories.py` (new)
- `common/tests/__init__.py` (new)
- `common/tests/test_factories.py` (new)

No existing files were modified. `common/utils.py` and other existing `common/*.py`
files (`API_custom_response.py`, `body_validations.py`, `convert_base64_image.py`,
`pagination.py`, `template_pagination.py`) were left untouched. The 4 files with
duplicated `asset_conditions_map` logic (`clients/utils.py`, `vendors/utils.py`,
`audit/utils.py`, `assets/utils.py`) were read for reference only, not modified, per
the brief's explicit instruction.

## Self-review findings

- `BaseMultiTenantService.base_queryset` is a `@staticmethod` exactly matching the
  brief's required shape, with a full docstring (purpose/args/return) per project
  convention (matched style against `clients/utils.py`'s existing docstrings).
- `base_queryset` always filters by `organization=user.organization` — never returns
  unfiltered/cross-tenant data, satisfying the org-isolation constraint.
- `build_asset_conditions_map` is a pure function with no side effects on the 4 source
  files; verified its logic is identical in shape to all 4 existing duplicated
  implementations (iterate audits, append `condition` keyed by `asset_id` into a
  `defaultdict(list)`).
- `UserFactory._create` explicitly pops the fields `create_user` requires positionally/
  by name (`email`, `full_name`, `username`, `phone`, `password`) and forwards any
  remaining kwargs (e.g. `organization`) as `**extra_fields`, matching the real
  `create_user(self, email, full_name, username, phone, password, **extra_fields)`
  signature exactly — verified against `authentication/models.py:25-34`.
- Noted (but did not fix, out of scope) that `UserManager.create_user` unconditionally
  sets `is_staff=True, is_superuser=True` for every user, and does not set `is_active`
  itself (model default `False`). The factory works around the latter by defaulting
  `is_active=True` so factory-created test users are usable; this does not change
  `create_user`'s behavior for any other caller.
- No wildcard imports; explicit named imports throughout both new files.
- No `print()` calls; no inline CSS/HTML; no `ai-`/`ai_` prefixes anywhere.
- Docstrings present on every public class/function in both new files, following the
  purpose/args/return convention matched from `clients/utils.py`.
- `common` was not previously a registered Django app (no `apps.py`, not in
  `INSTALLED_APPS`), but this wasn't a blocker: pytest's `python_files` config in
  `pyproject.toml` already discovers any `test_*.py` regardless of app registration,
  and `common/tests/test_factories.py` only needs DB access via `@pytest.mark.django_db`
  plus imports from already-registered apps (`authentication`, `dashboard`). No changes
  to `INSTALLED_APPS` or app registration were needed or made.
- No git write operations were run; `git status --porcelain | grep common` confirms
  only the 4 new files above are untracked/uncommitted.

## Concerns

- None blocking. The only items worth flagging to the controller:
  1. Pre-existing `ruff` config bug in `pyproject.toml` (`[tool.ruff]` `known-django`
     field) prevents running `ruff check` project- or file-wide until Task 1's ruff
     config is fixed — not something this task should fix (out of scope, one concern
     per change), but later phases relying on a clean `ruff check` in CI will hit this.
  2. `UserManager.create_user`'s unconditional `is_staff=True, is_superuser=True` looks
     like a latent bug (every test/factory user becomes superuser), inherited as-is
     since modifying `authentication/models.py` is out of scope for this task.
