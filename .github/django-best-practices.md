# Django Python Coding Standards

> A comprehensive set of rules and conventions for writing clean, consistent, and maintainable Django applications.

---

## 1. General Python Style

- Follow **PEP 8** for all Python code.
- Use **4 spaces** for indentation. Never use tabs.
- Maximum line length is **88 characters** (compatible with Black formatter).
- Use **Black** for auto-formatting and **isort** for import sorting.
- Use **flake8** or **ruff** for linting.
- All files must end with a single newline character.
- Avoid trailing whitespace.

---

## 2. Naming Conventions

| Element              | Convention                      | Example                |
| -------------------- | ------------------------------- | ---------------------- |
| Variables            | `snake_case`                    | `user_profile`         |
| Functions            | `snake_case`                    | `get_user_by_email()`  |
| Classes              | `PascalCase`                    | `UserProfile`          |
| Constants            | `UPPER_SNAKE_CASE`              | `MAX_RETRY_COUNT`      |
| Django Models        | `PascalCase` (singular)         | `Order`, `UserProfile` |
| Django Apps          | `snake_case` (short, lowercase) | `accounts`, `orders`   |
| URL names            | `kebab-case`                    | `user-profile-detail`  |
| Template files       | `snake_case.html`               | `user_profile.html`    |
| Template directories | match app name                  | `accounts/login.html`  |

---

## 3. Project Structure

```
project_root/
├── config/                  # Project configuration (settings, urls, wsgi, asgi)
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                    # All Django applications live here
│   ├── accounts/
│   ├── orders/
│   └── ...
├── static/
├── templates/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
└── .env
```

- Each Django app must be **self-contained**: models, views, urls, utils, serializers, tests, and admin in that app's directory.
- Never put business logic in `views.py`. All logic belongs in `utils.py`.
- Keep `urls.py` files thin — only route definitions, no logic.

---

## 4. Models

- Always define `__str__()` on every model.
- Always define `class Meta` with at least `verbose_name` and `verbose_name_plural`.
- Use `ordering` in `Meta` only when a default order is always appropriate.
- Prefer explicit `related_name` on all `ForeignKey`, `OneToOneField`, and `ManyToManyField`.
- Always use `on_delete` on `ForeignKey` fields — never omit it.
- Use `blank=True, null=True` sparingly and consistently. For string-based fields, prefer `blank=True` only (no `null=True`).
- Never use `null=True` on `CharField` or `TextField`.
- Add `db_index=True` on fields that are frequently filtered or joined.
- Use `UUIDField` for public-facing primary keys instead of auto-increment integers.
- Model field order convention:
  1. Primary key / UUID
  2. Relationship fields (`ForeignKey`, etc.)
  3. Data fields
  4. Boolean flags
  5. Timestamps (`created_at`, `updated_at`)

```python
# ✅ Good
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(max_length=50, choices=OrderStatus.choices)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} — {self.user}"
```

- Use `TextChoices` or `IntegerChoices` for field choices. Never use raw tuples.

```python
# ✅ Good
class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"

# ❌ Bad
STATUS_CHOICES = [("pending", "Pending"), ("confirmed", "Confirmed")]
```

---

## 5. Views

- Prefer **class-based views (CBVs)** for CRUD operations; use **function-based views (FBVs)** for simple or one-off logic.
- **Never put any logic inside views.** All business logic, data processing, and validations must live in `utils.py`.
- Always use Django's `get_object_or_404()` when fetching single objects from the DB in views.
- Do **not** use `LoginRequiredMixin` or `@login_required` in views. Authentication and permission checks must be handled inside `utils.py`.
- Keep views strictly to: receiving a request, calling a util function, and returning a response. Nothing else.

```python
# ✅ Good — view contains zero logic, delegates entirely to utils
from apps.orders.utils import create_order

class OrderCreateView(View):
    def post(self, request):
        result = create_order(request)
        if not result["success"]:
            return render(request, "orders/create.html", {"errors": result["errors"]})
        return redirect("order-detail", pk=result["order_id"])

# ❌ Bad — logic, auth checks, and validation inside the view
class OrderCreateView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_active:
            return HttpResponseForbidden()
        form = OrderForm(request.POST)
        if form.is_valid():
            Order.objects.create(user=request.user, **form.cleaned_data)
        return redirect("order-list")
```

---

## 6. URLs

- Always use `app_name` in `urls.py` for namespacing.
- Always name every URL pattern.
- Use `path()` over `re_path()` unless regex is strictly necessary.
- Group related URL patterns together and include app-level `urls.py` into the root router.

```python
# apps/orders/urls.py
app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("<uuid:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("create/", views.OrderCreateView.as_view(), name="order-create"),
]
```

---

## 7. Utils & Business Logic

- **All logic lives in `utils.py`** inside the relevant app — no exceptions.
- This includes: authentication checks, permission validation, input validation, DB operations, and any processing that would otherwise be in a view or model method.
- Util functions receive the `request` object (or explicit parameters) and return a structured result dict — never an HTTP response object.
- Use `transaction.atomic()` in util functions where multiple DB writes occur.
- Raise domain exceptions (`ValueError`, custom exceptions) from utils — never return raw HTTP status codes from a util function.
- Auth and permission checks must be the **first thing** performed inside a util function before any other logic runs.

```python
# apps/orders/utils.py
from django.db import transaction
from .models import Order

def create_order(request) -> dict:
    """Handle all logic for creating an order, including auth and validation."""
    # Auth check lives here, not in the view
    if not request.user.is_authenticated:
        return {"success": False, "errors": {"auth": "Authentication required."}}

    if not request.user.is_active:
        return {"success": False, "errors": {"auth": "Inactive users cannot place orders."}}

    form = OrderForm(request.POST)
    if not form.is_valid():
        return {"success": False, "errors": form.errors}

    order = _persist_order(user=request.user, data=form.cleaned_data)
    return {"success": True, "order_id": str(order.id)}


@transaction.atomic
def _persist_order(user, data: dict) -> Order:
    """Private helper — DB write is wrapped in a transaction."""
    order = Order.objects.create(user=user, **data)
    notify_user_of_order(order)
    return order
```

---

## 8. QuerySets & Database

- Never use raw SQL unless absolutely necessary. Use the ORM.
- Always use `select_related()` for `ForeignKey` / `OneToOneField` and `prefetch_related()` for `ManyToManyField` / reverse relations to avoid N+1 queries.
- Never filter querysets inside templates or serializers. Filter only in views, services, or custom managers.
- Use custom `Manager` and `QuerySet` classes for reusable query logic.
- Avoid `QuerySet.all()` followed by Python-level filtering. Use DB-level filters.
- Use `.exists()` instead of `.count() > 0` or `if queryset:` for existence checks.
- Use `.only()` or `.values()` when you only need a subset of fields.

```python
# ✅ Good
orders = Order.objects.select_related("user").prefetch_related("items").filter(
    is_paid=True
)

# ❌ Bad — N+1 query
for order in Order.objects.all():
    print(order.user.email)  # hits DB on every iteration
```

---

## 9. Settings

- Never commit secrets or credentials to version control.
- Use environment variables for all sensitive settings. Use `django-environ` or `python-decouple`.
- Split settings into `base.py`, `development.py`, and `production.py`.
- Set `DEBUG = False` in production. Never set `ALLOWED_HOSTS = ["*"]` in production.
- Always set `SECRET_KEY` from an environment variable.
- Define `AUTH_USER_MODEL` early and always use a custom user model.

```python
# config/settings/base.py
import environ

env = environ.Env()
environ.Env.read_env()

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
DATABASES = {"default": env.db("DATABASE_URL")}
AUTH_USER_MODEL = "accounts.User"
```

---

## 10. Forms & Validation

- Use Django forms or DRF serializers for all input validation. Never validate raw `request.POST` manually.
- Define `clean_<fieldname>()` methods for field-level validation.
- Define `clean()` for cross-field validation.
- Use `ModelForm` when form maps directly to a model; use plain `Form` otherwise.

---

## 11. Templates

- Templates must use Django's template language. No inline Python logic.
- Never put business logic in templates. Use template tags or context processors for complex data.
- Use template inheritance (`{% extends %}`) with a base template.
- Name template blocks clearly: `{% block content %}`, `{% block title %}`, `{% block scripts %}`.
- Always escape user-generated content. Never use `{% autoescape off %}` without strong justification.

---

## 12. Admin

- Register every model with `@admin.register(ModelName)`.
- Always define `list_display`, `search_fields`, and `list_filter` on `ModelAdmin`.
- Use `readonly_fields` for auto-generated fields like `created_at` and `updated_at`.
- Never expose sensitive fields (passwords, tokens) in admin views.

```python
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "status", "is_paid", "created_at"]
    list_filter = ["status", "is_paid"]
    search_fields = ["user__email", "id"]
    readonly_fields = ["id", "created_at", "updated_at"]
```

---

## 13. APIs (Django REST Framework)

- Use `ModelSerializer` for standard CRUD; use plain `Serializer` for custom data shapes.
- Never expose internal model IDs publicly — use UUIDs or slugs.
- Use `APIView` or `ViewSet` — keep serializer logic out of views.
- Always version your API: `/api/v1/`, `/api/v2/`.
- Use `permission_classes` and `authentication_classes` explicitly on every view.
- Return consistent error response formats across all endpoints.
- Use `throttle_classes` on public-facing endpoints.

---

## 14. Testing

- Every app must have a `tests/` directory (not a single `tests.py` file).
- Structure: `tests/test_models.py`, `tests/test_views.py`, `tests/test_utils.py`.
- Use `pytest` with `pytest-django` as the test runner.
- Use `factory_boy` for test data factories instead of fixtures.
- Aim for **90%+ coverage** on utils and models; 80%+ overall.
- Use `@pytest.mark.django_db` to mark DB tests explicitly.
- Never use production data in tests. Never make real network calls — mock external services.
- Test one thing per test function. Use descriptive names: `test_create_order_returns_error_for_inactive_user`.

```python
# ✅ Good
@pytest.mark.django_db
def test_create_order_returns_error_for_inactive_user(rf, user_factory):
    user = user_factory(is_active=False)
    request = rf.post("/orders/create/", {})
    request.user = user
    result = create_order(request)
    assert result["success"] is False
    assert "auth" in result["errors"]
```

---

## 15. Migrations

- Never edit a migration file after it has been applied in any shared environment.
- Always run `makemigrations` after model changes and commit migrations alongside model changes in the same PR.
- Give migrations descriptive names: `python manage.py makemigrations --name add_status_to_order`.
- Do not put data migrations inside schema migrations. Use separate `RunPython` migration files.
- Squash migrations periodically on long-lived projects.

---

## 16. Security

- Never store plaintext passwords or secrets in code or the database.
- Always use Django's built-in `User.set_password()` for password changes.
- Use `CSRF` protection on all state-changing views (enabled by default).
- Set secure cookie and session settings in production:
  ```python
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_HSTS_SECONDS = 31536000
  ```
- Validate and sanitize all file uploads. Restrict `ALLOWED_EXTENSIONS` and file size.
- Use `django-axes` or similar for brute-force login protection.

---

## 17. Imports

- Import order (enforced by isort):
  1. Standard library
  2. Third-party packages
  3. Django
  4. Local app imports
- Use absolute imports. Avoid relative imports except within the same app.
- Never use wildcard imports (`from module import *`).

```python
# ✅ Good
import uuid
from datetime import datetime

from django.db import models
from django.contrib.auth import get_user_model

from apps.orders.models import Order
```

---

## 18. Documentation & Comments

- Write docstrings for all public functions, classes, and methods using the Google style.
- Comments should explain **why**, not **what**. The code explains what.
- Keep comments up to date — stale comments are worse than no comments.
- Use `# TODO:`, `# FIXME:`, `# HACK:` tags consistently and link to a ticket where possible.

```python
def create_order(user, data: dict) -> Order:
    """
    Create a new order for the given user.

    Args:
        user: The authenticated User instance placing the order.
        data: Validated order data dict (from form or serializer).

    Returns:
        The newly created Order instance.

    Raises:
        ValueError: If the user account is inactive.
    """
```

---

## 19. Environment & Dependencies

- Pin all dependencies with exact versions in `requirements/*.txt`.
- Use a virtual environment (`.venv`) for local development. Never install packages globally.
- Use `pre-commit` hooks to enforce linting, formatting, and type checking before commits.
- Required pre-commit hooks: `black`, `isort`, `flake8` (or `ruff`), `mypy`.

---

## 20. Git & Code Review

- One feature / fix per branch and PR.
- Branch naming: `feature/<ticket-id>-short-description`, `fix/<ticket-id>-short-description`.
- PR must include: description of change, how to test, and any migration notes.
- No PR is merged without at least one approving review.
- Do not push directly to `main` or `develop`.
- Commit messages use the **Conventional Commits** format:
  - `feat: add order cancellation endpoint`
  - `fix: prevent duplicate order creation on retry`
  - `refactor: extract order logic into service layer`
  - `test: add coverage for inactive user order creation`
