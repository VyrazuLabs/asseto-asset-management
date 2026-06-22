# Task 3: common/services.py and common/factories.py

Part of Phase 0 (infrastructure) of the "Full Code Refactor" plan. Every later phase's per-app Service class will reuse the shared org-scoping base created here, so it must land now, before Phase 1+.

## Requirements (verbatim from the plan)

### `common/services.py` (new file)

```python
class BaseMultiTenantService:
    @staticmethod
    def base_queryset(model, user):
        return model.undeleted_objects.filter(organization=user.organization)
```
Requires `model` to expose an `undeleted_objects` manager (the project's `SoftDeleteManager` convention, defined in `dashboard/models.py:35` and used via `SoftDeleteModel` at `dashboard/models.py:41-46`) and an `organization` FK. Add a docstring per the project's docstring convention (purpose, args, return type — see CLAUDE.md global rule "Docstrings on public functions").

Also add:
```python
def build_asset_conditions_map(audits_queryset):
    """Build {asset_id: [condition, condition, ...]} from an Audit queryset."""
```
This consolidates duplicated `defaultdict(list)`-based logic independently found in `clients/utils.py`, `vendors/utils.py`, `audit/utils.py`, and `assets/utils.py` (all build the same shape: iterate an Audit queryset, append `audit.condition` to a list keyed by `audit.asset_id`). Do NOT modify those 4 files in this task — just create the shared helper function here. Wiring up the 4 call sites to use it happens in later phases (Phase 5 for `audit`, per-app phases for the others), not this task.

### `common/factories.py` (new file)

Base factory_boy factories that later per-app factories will subclass/depend on, since every org-scoped model factory needs an org+user dependency chain:

```python
class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization
    name = factory.Sequence(lambda n: f"Org {n}")

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    organization = factory.SubFactory(OrganizationFactory)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    full_name = factory.Faker("name")
    phone = factory.Sequence(lambda n: f"+1555000{n:04d}")
```

Find the actual model locations and field requirements before writing this:
- `Organization` is defined at `dashboard/models.py:85` (a `TimeStampModel` subclass — check what fields it actually requires; the plan's `name` field guess must be verified against the real model).
- `User` is `AUTH_USER_MODEL = 'authentication.User'` (settings.py), defined at `authentication/models.py:67` as `class User(AbstractBaseUser, PermissionsMixin, TimeStampModel, SoftDeleteModel)`. It has a UUID primary key (`models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`), and fields `email`, `username`, `full_name`, `phone`, plus whatever `organization` FK exists (verify it exists on this model — read the full class body, not just the excerpt above, since the brief's snippet may be incomplete). The factory must use `factory.django.DjangoModelFactory` with `set_password` handled correctly if a password field exists (check `UserManager.create_user` at `authentication/models.py:25` for the right way to construct a valid user — you may need a custom `_create` classmethod on the factory that calls `User.objects.create_user(...)` instead of plain `Meta.model(...)` construction, since this model has a custom manager with `create_user`).

## Constraints

- Do not modify any existing app's `utils.py`/`models.py`/`views.py` in this task — `common/services.py` and `common/factories.py` are new files only.
- factory_boy is already installed (Task 1 added it to requirements.txt and it's in the venv at `env/`).
- Match the project's docstring convention (see any existing utils.py for style, e.g. `clients/utils.py`).
- Do not run `git commit` — leave changes uncommitted in the working tree.

## Verification

- Both files import cleanly: `python -c "import django; django.setup(); from common.services import BaseMultiTenantService, build_asset_conditions_map"` (set `DJANGO_SETTINGS_MODULE=AssetManagement.settings` first) and similarly for `common.factories`.
- Write a focused test (new file `common/tests/test_factories.py` or similar — check if `common` app even has a `tests` setup; if `common` isn't a registered Django app with migrations, note that org/user factories still need a real DB to create rows, so this test needs Django's test DB, i.e. it must run via `pytest` with DB access, not a plain `python -c`) that creates one `UserFactory()` instance and asserts it has an `organization` and a usable account (e.g. `user.organization is not None`, `user.check_password(...)` if a password was set, or simply that `user.pk` is set after creation).
- Run `pytest common/ -v` (or wherever the test lands) and report pass/fail.

## Report

Write your full report to `.superpowers/sdd/task-3-report.md`. Return to the controller only: status, files changed, one-line test summary, concerns.
