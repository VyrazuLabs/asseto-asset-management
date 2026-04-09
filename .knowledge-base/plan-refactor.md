# Refactoring Plan

This plan captures the high-level refactor steps for the Asset Management project. 

> **Important References:** Always adhere to the guidelines outlined in [`.github/django-best-practices.md`](../.github/django-best-practices.md) and [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) while implementing these changes.

> **Commenting & documentation standard:** all new or modified code should include concise docstrings for modules, classes, and public methods, with inline comments explaining non-obvious business logic. Follow the existing pattern in models like `Asset` and utilities like `common/API_custom_response.py`.

1. **Extract & simplify view logic**
   - Identify heavy logic in `assets/views.py` (e.g. `details` view runs multiple queries: `Audit.objects.filter`, `AssetImage.objects.filter`, barcode generation, custom field handling) and `assets/api_views.py` where asset lookups and status updates are inline.
   - Move business rules into services or model methods (_see_ `assets/api_utils.py` for existing helpers) or create new modules such as `assets/services.py`. For example, a method `Asset.get_with_history(id)` could encapsulate the queries used in `details`.
   - Keep view functions and API views focused on request/response handling; they should orchestrate service calls rather than perform complex data transformations.

2. **Add `select_related` / `prefetch_related`**
   - Audit querysets across `api_views.py`, `views.py` in assets, authentication, and other apps. For instance, `assigned_list` currently does:
     ```python
     AssignAsset.objects.filter(
         asset__is_assigned=True, asset__organization=request.user.organization
     )
     ```
     which will hit the database for each `asset` access; using `.select_related('asset', 'asset__vendor')` avoids the N+1 problem.
   - Similarly, in `AssetList` API the serializer might fetch related `product`/`vendor` fields separately; prefetch them upfront.
   - Update queries (e.g. `Asset.objects.filter(...).select_related('organization', 'vendor')`) to reduce database hits as noted above.

3. **Remove stray debug prints**
   - Search the workspace for `print(` occurrences; examples include `print("exception", e)` in `assets/api_utils.py`, `print(f"No vendor found for email")` in `upload/utils.py`, and active console prints in `common/API_custom_response.py`. Replace these with structured logging via `structlog` or Django’s `logging.getLogger()`.
   - Ensure tests don’t rely on printed output; use assertions on return values or captured logs instead.

4. **Modularize repeated code**
   - Factor common response/pagination patterns from `api_views` and views into decorators or helper functions. For example, `assigned_list` and `unassigned_list` both create a `Paginator` and page object; a helper `paginate(queryset, request)` could standardize this.
   - Share serializers and utility functions rather than duplicating logic; the `common.API_custom_response` is used widely but some views manually build JSON responses.

5. **Integrate CI checks**
   - Add a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs `python manage.py test`, linting (black/flake8), and coverage measurement. Include a step that greps for `print(` to prevent debug statements from landing in `main`.
   - Consider pre-commit hooks to catch prints, missing `select_related` calls, and to auto-format with `black`.

6. **Review & document changes**
   - Update README or `.github/copilot-instructions.md` with notes on refactoring and conventions. Mention project-specific patterns like using `TimeStampModel`, `SoftDeleteModel`, and custom API responses.
   - Provide links to key files (`assets/api_utils.py`, `common/API_custom_response.py`, `assets/views.py`) as examples of before/after refactors.

7. **Testing**
   - Write unit tests for every extracted service and for updated views. Use `django.test.TestCase` or `rest_framework.test.APITestCase` as appropriate. Tests should assert behavior, not just output.
   - Add tests for edge cases uncovered during the refactor (e.g. asset not found, permission checks). Ensure existing tests run with `--keepdb` to speed iterations.
