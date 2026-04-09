# Module-Specific Refactoring Tasks

Based on the overall refactoring plan, here is a detailed breakdown of the tasks for each module. This can be used as a checklist while executing the refactor.

## 1. `assets` Module
- [ ] **`assets/views.py`**: 
  - Extract the heavy business logic from the `details` view (which involves `Audit.objects.filter`, `AssetImage.objects.filter`, barcode generation, and custom field handling) and move it to `assets/services.py` or model methods.
  - Refactor `assigned_list` and `unassigned_list` to utilize a shared pagination helper.
- [ ] **`assets/api_views.py`**: 
  - Extract inline asset lookups and status updates into dedicated service functions.
  - Implement `select_related` and `prefetch_related` in API queries (e.g., `AssetList` fetching related `product` and `vendor` fields).
- [ ] **`assets/api_utils.py`**:
  - Replace the stray debug print `print("exception", e)` with structured logging (e.g., using `structlog` or `logging.getLogger()`).
- [ ] **General**:
  - Create `assets/services.py` to house new orchestrator functions (e.g., `Asset.get_with_history(id)`).
  - Add `select_related('organization', 'vendor')` to `AssignAsset` and `Asset` querysets to fix N+1 problems.
  - Write comprehensive unit tests for all newly extracted services and updated views using `django.test.TestCase` or `rest_framework.test.APITestCase`.

## 2. `common` Module
- [ ] **`common/API_custom_response.py`**:
  - Replace active `print` statements in the `log_error_to_terminal` function with a robust logging solution.
- [ ] **Pagination/Helpers**:
  - Create or update standard pagination helpers (e.g., standardizing the creation of `Paginator` and page objects) that can be reused across all `api_views.py` and `views.py` in the project.

## 3. `upload` Module
- [ ] **`upload/utils.py`**:
  - Locate `print(f"No vendor found for email")` and replace it with appropriate warning/error logging.

## 4. `authentication` Module
- [ ] **Views & API Views**:
  - Audit all querysets to ensure `select_related` or `prefetch_related` are being used to eliminate N+1 queries.
  - Ensure API responses use the standardized `common/API_custom_response.py` structure rather than building JSON responses manually.

## 5. Other Apps (`audit`, `dashboard`, `users`, `products`, etc.)
- [ ] **Query Optimization**:
  - Sweep through views and APIs to find inefficient querysets (looping over related models) and apply `select_related`/`prefetch_related`.
- [ ] **Code Cleanup**:
  - Search for and remove any remaining `print()` statements across all Python files, replacing them with standard logging.
  - Refactor repeated response building to use the `API_custom_response` utility.

## 6. Project & CI Level
- [ ] **`.github/workflows/ci.yml`**:
  - Create a GitHub Actions workflow to run `python manage.py test`.
  - Add steps for linting (`black`, `flake8`) and a check to prevent `print(` statements from being merged into `main`.
- [ ] **Pre-commit Hooks**:
  - Setup `.pre-commit-config.yaml` to run `black` formatting and check for stray prints/missing optimizations locally before commits.
- [ ] **Documentation**:
  - Update `README.md` to establish the new conventions.
  - Ensure that docstrings and comments are aligned with the principles outlined in `.github/django-best-practices.md` and `.github/copilot-instructions.md`.
