# Changelog

All notable changes to Asseto Asset Management are documented here.

This project follows [Semantic Versioning](https://semver.org/) and the format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

> Changes staged on `develop` that have not yet been released.

---

## [1.6.7] — 2026-08-24

### Added
- **Global Dynamic Custom Fields** — Implemented global custom field system (`custom_fields` app) for Assets, Clients, Vendors, and Users with field definitions, value models, soft delete (`is_deleted`), and customizable UI forms and modals.
- **Bulk Asset Import Custom Fields Support** — Added dynamic custom field data parsing and validation in CSV bulk asset upload workflows.
- **Localization for Custom Fields** — Added multilingual translation keys (English, Hindi, Bengali, French) and enhanced error handling UI for custom field configurations.
- **Authentication & Permission Decorators** — Enabled authentication and strict permission check decorators for listed assets view.

### Changed
- **Entity Details Views** — Redesigned details pages for Assets, Clients, Products, and Vendors to seamlessly display custom fields and their values.
- **Audit Image Upload & Tag Config** — Refactored audit image upload and tag configuration forms for better UX and reliability.

### Fixed
- **Asset Details API** — Resolved serialization and response format bugs in the asset details API endpoint.

### Security
- **cryptography, pypdf & h2** — Updated project dependencies in `requirements.txt` to patch known security vulnerabilities.

---

## [1.6.6] — 2026-08-03

### Added
- **Docker & Shell Script Deployment Setup** — Introduced single-command installation (`setup.sh`), `Dockerfile`, `nginx.conf`, and `SETUP.md` for containerized application setup, Nginx reverse proxy, domain binding, and database connectivity.
- **Admin Registration CLI Command** — Implemented custom Django management command `user_register` for secure initial administrator creation using environment variable credentials.

### Changed
- **Tag Configuration** — Refactored Tag Configuration forms and templates to make prefix and suffix fields optional.
- **Support Ticket Layout** — Added ticket status dropdown and updated support ticket details view layout.

### Fixed
- **User Bulk Upload** — Resolved data processing, error handling, and session bugs during bulk user upload.
- **Asset Import & User Default Handling** — Fixed step indicator UI layout in asset bulk import workflow and default active user filtering.

### Security
- **Pillow** — Bumped `12.2.0 → 12.3.0` to patch 13 HIGH/MODERATE CVEs including JPEG2000 DoS, heap out-of-bounds reads/writes, decompression bomb bypasses, and OS command injection.
- **pypdf** — Bumped `6.10.2 → 6.14.2` to patch 10 HIGH/MODERATE CVEs including infinite loops for unterminated inline images, excessive memory usage, and long runtime attacks.
- **cryptography** — Bumped `46.0.7 → 49.0.0` to resolve HIGH CVE for vulnerable OpenSSL included in wheels.
- **pyasn1** — Bumped `0.6.3 → 0.6.4` to patch 2 HIGH CVEs: uncontrolled resource consumption and quadratic complexity DoS in OID processing.
- **msgpack** — Bumped `1.1.2 → 1.2.1` to patch HIGH CVE for out-of-bounds read/crash on Unpacker reuse after a caught error.
- **Django** — Bumped `5.2.14 → 5.2.16` to patch LOW CVE for STARTTLS partially-initialized connection reuse.
- **setuptools** — Relaxed constraint from `<82.0.0` to `>=83.0.0` to patch CVE for Unicode normalization bypass in `MANIFEST.in` exclusions.

---

## [1.6.5] — 2026-07-25

### Added
- **Asset Bulk Import Feature** — Implemented comprehensive asset bulk import workflows with Excel and ZIP upload support, transaction integrity, and progress indicators.

### Changed
- **Support Ticket Kanban View** — Redesigned ticket Kanban view, updated closed ticket handling logic, and enhanced overall ticket management workflows.
- **Documentation & UI Branding** — Updated README documentation, refreshed maintainer details, and tuned sidebar logo dimensions.

### Fixed
- **Product Categories & Subcategories** — Fixed update errors in product category and subcategory selection within the products module.
- **Asset Details & Notifications** — Resolved asset details view display issues and removed blocking notifications during bulk asset insertion for smoother processing.

---

## [1.6.4] — 2026-07-13

### Added
- **Technician role for users** — Implemented the technician role for users, showing only active and enabled users in technician lists, and added a Maintenance and repairs log section in asset details.
- **Client location feature** — Integrated client location details into the client portal module.
- **Two-way support comments** — Implemented two-way support ticket comment workflows in both the client portal and admin, including file upload validation, staff comment flags, and UI text localization.
- **Support ticket happy codes** — Implemented Happy Code validation, migration, and UI submission flows for support tickets on both admin and client portals.

### Changed
- **Asset details view** — Restored and redesigned the Maintenance and repairs section as well as the Maintenance log in the asset details view.
- **Client portal notifications** — Replaced success alert views with Toastify notifications for ticket actions.
- **Cleaned localization setup** — Moved translation code from `__init__.py` to utility and constant modules.
- **General UI improvements** — Removed the recycle bin statistics card from listing pages, improved the ticket Kanban view UI, and deduplicated views in the client portal.

### Fixed
- **2FA login API bug** — Fixed 2FA verification issues inside the login API.
- **Phone number validations** — Added phone number validation in user and client models.
- **Filtering & searching** — Fixed filtering and searching bugs in the vendor list and client list.
- **Gate pass & authorization** — Fixed issues related to saving gate passes and authorization settings.
- **Environment config** — Sanitized Firebase credential path and corrected environment example comments.
- **OTP verification page** — Fixed OTP verification HTML code layout and alignment issues.
- **Session cache invalidation** — Invalidated session cache correctly after updating user language settings.

---

## [1.6.3] — 2026-06-23

### Added
- **`is_logged_in` field on `UserTotp`** — Restored the `is_logged_in` boolean field to the `UserTotp` model (migration `0033`) to track active 2FA sessions correctly after the earlier rename migration.
- **Client Portal ticket creation and detail views** — Added `client_portal_add_ticket` and `client_portal_ticket_detail` views with corresponding URL patterns so portal users can open and view support tickets.
- **Global search API** — Extracted `GlobalSearch` API view into a dedicated `dashboard/api_views/` package with a clean module boundary.

### Changed
- **Code refactor — large-scale codebase cleanup** (`feature/code-refactor-1`) — PEP 8 formatting, DRY improvements, extracted shared logic to managers/mixins/utils, consolidated duplicate imports across 700+ files.
- **Dashboard URL structure** — `api_view` module re-mapped from `dashboard/views/` to `dashboard/api_views/` for clearer separation of HTML and API concerns.
- **Test organisation** — Moved app-level test files from flat `tests.py` to structured `tests/` packages (`test_assets.py`, `test_audit.py`, `test_products.py`, `test_vendors.py`, `test_dashboard.py`, `test_license.py`).
- **Pre-commit configuration** — Added `.pre-commit-config.yaml` to enforce linting and formatting on every commit.
- **`pyproject.toml`** — Added project-level tooling configuration.

### Fixed
- **`NameError: user_passes_test`** — Added missing import for `user_passes_test`, `logout`, `render`, `redirect`, and `get_object_or_404` in `authentication/views.py`.
- **Merge conflict syntax errors** — Resolved leftover git conflict markers in `products/api_utils.py` and `client_portal/views.py` that prevented the server from starting.
- **`ImportError: cannot import name 'api_view'`** — Fixed incorrect import path for the global search API view in `dashboard/urls.py`.
- **Relative import paths** — Fixed `from .serializers` and `from .api_utils` imports inside `dashboard/api_views/global_search_api_views.py` to use correct parent-package references.

---

## [1.6.2] — 2026-06-06

### Changed
- **Tailwind Play CDN Integration** — Disabled Tailwind Preflight (global CSS reset) on gate pass pages to prevent layout margin and font distortion.
- **Form Switch Toggle Fix** — Removed Tailwind Forms plugin from the gate pass templates to prevent overriding Bootstrap's switch toggle styling for the dark/light mode button.

### Fixed
- **Cleaned Codebase** — Removed legacy commented-out HTML sections, duplicate scripts, and old Python API routing code from the gate pass module.

---

## [1.6.1] — 2026-06-04

### Security
- **urllib3** upgraded `2.6.3` → `2.7.0` — fixes decompression-bomb bypass in streaming API (PYSEC-2026-142) and sensitive headers forwarded across origins in proxied redirects (PYSEC-2026-141)
- **Django** upgraded `5.2.13` → `5.2.14` — fixes improper length parameter handling (Moderate), persistent cookies containing sensitive information (Low), and cache containing sensitive information (Low)
- **idna** upgraded `3.10` → `3.15` — fixes bypass of CVE-2024-3651 fix via specially crafted inputs to `idna.encode()` (CVE-2026-45409)
- **PyJWT** upgraded `2.12.1` → `2.13.0` — fixes multiple JWT security advisories (PYSEC-2026-175/176/177/178/179)

---

## [1.6.0] — 2026-06-04

### Added
- **Client Portal** — Client login, dashboard, asset view, and support ticket portal with OTP verification
- **Client Portal Middleware** — Session-based client authentication middleware
- **Support Tickets** — Client association on support tickets; full ticket lifecycle management
- **Gate Pass QR** — Dynamic QR code generation on gate pass print document
- **Gate Pass** — Gate pass features including status workflow, search fix, authorization approval, and card count on listing page
- **Client Management** — Contact management, PDF/CSV export, client portal activation flag
- **Role Management** — Gate pass and client portal permissions integrated into RBAC

### Changed
- Gate Pass UI — footer fix on add page, discard button fix, design improvements throughout
- Support ticket CSS — improved styling and layout
- Client listing and details pages — redesigned for clarity
- `.gitignore` — `.knowledge-base` ignored recursively

### Fixed
- User dropdown and notification rendering issue
- Gate Pass ID structure corrected
- Dark mode design issue on details pages

---

## [1.2.0] — 2026-05-25

### Added
- Gate pass module with QR code checkout support
- Support ticket system with priority labels and status workflow
- Role management redesign for client portal
- Client portal feature branch

### Changed
- Asset list and filter pages refactored for performance
- Code refactor across multiple modules for maintainability

### Fixed
- Various UI improvements and bug fixes across the application

---

<!-- Template for new entries — copy and fill in above this line

## [X.Y.Z] — YYYY-MM-DD

### Added
-

### Changed
-

### Fixed
-

### Security
-

### Removed
-

-->
