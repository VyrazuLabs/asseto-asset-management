# AI Coding Assistant Instructions for Asset Management Project

## Project Overview

This is a Django-based asset management system with multi-tenant architecture. The project manages organizational assets, users, vendors, products, and includes features like asset assignment, tracking, reporting, and audit trails.

## Architecture & Key Components

### Core Apps Structure

- **assets**: Core asset management (Asset, AssetStatus, AssignAsset models)
- **authentication**: Custom user management with roles and permissions
- **dashboard**: Common models (Organization, Location, Department) and dashboard views
- **products/vendors**: Product and vendor catalogs
- **audit**: Audit logging and tracking
- **configurations**: System settings and localization
- **notifications**: User notifications system
- **roles/users**: Role-based access control
- **recycle_bin**: Soft delete recovery system

### Model Inheritance Patterns

All models inherit from:

- `TimeStampModel`: Adds `created_at`, `updated_at`, `created_by`, `updated_by` fields
- `SoftDeleteModel`: Adds `is_deleted` field with custom managers for soft deletes
- `HistoricalRecords`: From django-simple-history for audit trails

Example:

```python
class Asset(TimeStampModel, SoftDeleteModel):
    # fields...
    history = HistoricalRecords()
```

### API Response Pattern

Use `common.API_custom_response.api_response()` for all API responses:

```python
from common.API_custom_response import api_response

return api_response(
    success=True,
    status=200,
    data=serialized_data,
    message="Asset created successfully"
)
```

### Pagination

Use `common.pagination.add_pagination()` for API pagination:

```python
from common.pagination import add_pagination

paginated_response = add_pagination(queryset, page=request.GET.get('page', 1))
return api_response(data=paginated_response)
```

## Development Workflow

### Environment Setup

1. Copy `.env.example` to `.env` and configure database/settings
2. Create virtual environment: `python -m venv env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Create superuser: `python manage.py createsuperuser`

### Testing

- Run all tests: `python manage.py test`
- Run specific app tests: `python manage.py test assets`
- Use `--keepdb` to avoid recreating test database

### Key Commands

- Development server: `python manage.py runserver`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Seed data: Check `assets/seeders.py` for seeding functions

## Coding Conventions

### Model Design

- Use UUID primary keys: `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
- Foreign keys use `models.DO_NOTHING` or `models.PROTECT` (avoid CASCADE deletes)
- Always include organization foreign key for multi-tenancy
- Add `history = HistoricalRecords()` for auditable models

### API Views

- Inherit from `APIView` with `permission_classes=[IsAuthenticated]`
- Use DRF Spectacular for OpenAPI documentation: `@extend_schema(...)`
- Handle exceptions with try/catch and return appropriate api_response

### URL Patterns

- Template URLs: `/assets/list`, `/assets/add`
- API URLs: `/api/asset/list/`, `/api/asset/add/`
- Include app-specific URL patterns in main `AssetManagement/urls.py`

### File Upload

- Use `ResizedImageField` from django-resized for profile/organization logos
- Custom upload paths with `path_and_rename` function
- Store in `upload/` directory with UUID naming

### Authentication & Permissions

- Custom User model with role-based access
- JWT authentication via djangorestframework-simplejwt
- Organization-based data isolation in all queries

## Common Patterns

### Querying with Organization Filter

```python
assets = Asset.objects.filter(organization=request.user.organization, is_deleted=False)
```

### Soft Delete Handling

```python
# Soft delete
asset.is_deleted = True
asset.save()

# Query non-deleted
Asset.undeleted_objects.filter(...)

# Query deleted (for recycle bin)
Asset.deleted_objects.filter(...)
```

### Asset Status Management

Assets have both `status` (integer choices) and `asset_status` (foreign key to AssetStatus model). The status field uses hardcoded choices while asset_status allows dynamic status creation.

### Barcode Generation

Assets support barcode generation using `python-barcode` library. See `assets/barcode.py` for implementation.

## External Integrations

### HTMX Integration

- Use `django-htmx` for dynamic frontend updates
- Middleware: `"django_htmx.middleware.HtmxMiddleware"`
- Check requests with `request.htmx` in views

### Notifications

- Slack integration for notifications
- In-app notifications via `notifications` app
- Email notifications configured via SMTP settings

### Reporting & Analytics

- PDF generation using `xhtml2pdf` and `reportlab`
- Excel/CSV export functionality in various apps
- Charts and analytics in dashboard

## Deployment Considerations

### Environment Variables

- `DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Django secret key
- Database settings: `DB_ENGINE`, `DB_DATABASE`, etc.
- Email settings: `EMAIL_HOST`, `EMAIL_HOST_USER`, etc.
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` for production

### Static/Media Files

- Static files served via Whitenoise in production
- Media files (uploads) served directly by Django in debug mode

### Database Support

- MySQL (primary) and PostgreSQL support
- Uses `pymysql` for MySQL connections
- Migrations handle both database types

## Testing Strategy

### Unit Tests

- Located in `app/tests.py` files
- Test models, views, and API endpoints
- Use Django's `TestCase` and DRF's `APITestCase`

### Coverage

- Use `coverage` package for test coverage reporting
- Run with `coverage run manage.py test`

## Security Notes

- All sensitive operations require authentication
- CSRF protection enabled
- Password hashing via Django's auth system
- Organization-based data isolation prevents cross-tenant access
- Audit trails via django-simple-history track all changes
