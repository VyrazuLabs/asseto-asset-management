# Changelog

All notable changes to Asseto Asset Management are documented here.

This project follows [Semantic Versioning](https://semver.org/) and the format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

> Changes staged on `develop` that have not yet been released.

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
