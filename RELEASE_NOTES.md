# Release Notes — v1.7.0

**Tag**: `v1.7.0`  
**Target Branch**: `main`  
**Date**: September 5, 2026  
**Title**: `v1.7.0 — Granular RBAC Permissions Architecture, User Security Updates & Dependency Fixes`

---

## 🚀 Overview

Asseto **v1.7.0** introduces a centralized **Granular RBAC Permission Architecture**, enhanced user management security controls (including in-modal password resets), clean role-switching transitions, and critical dependency security patches for `sqlparse`, `pypdf`, and `djangorestframework`.

---

## ✨ Added

* **Granular RBAC Permissions Architecture** — Introduced `common/permissions.py` as the centralized single source of truth for all role modules and permissions across the platform, eliminating hardcoded and scattered permission strings.
* **Role Editor Permission Matrix** — Implemented an interactive role add/edit modal that automatically enforces and locks prerequisite view permissions whenever add, edit, or delete actions are toggled.
* **Role Listing Enhancements** — Redesigned the roles listing page with per-module granted/denied icon rows (`static/css/pages/roles-list.css` and `role_permission_tags`), replacing legacy flat action badges for clear visual auditing.
* **Permission Sync & Verification Commands** — Added custom Django management commands `sync_permissions` and `verify_permission_migration` for automated role permission synchronization and migration verification.
* **Direct Password Reset in User Modal** — Added an optional toggle to set or update user passwords directly from the update user modal with password confirmation validation.

---

## 🔄 Changed

* **Permission Scoping for Assets & Support Tickets** — Replaced global access level checks with granular, permission-based scoping across assets and support tickets.
* **Namespaced Permission Checks** — Migrated legacy permission checks from the `authentication` app namespace to domain-specific feature namespaces (`assets`, `clients`, `vendors`, `products`, `dashboard`, `configurations`).
* **Cleaned Obsolete Onboarding Templates** — Removed deprecated progression bar and first-time installation templates to keep the UI clean and maintainable.

---

## 🐛 Fixed

* **Role Assignment & Group Clearing** — Fixed a role switching bug in the user edit flow where previously assigned role groups persisted, ensuring a clean transition between roles without accumulating legacy permissions.
* **User Detail & Modal Form Labels** — Corrected form field labels and layout consistency across the user listing, add modal, and update modal views.
* **Atomic Permission Updates** — Wrapped role permission updates within atomic database transactions to guarantee integrity and prevent partial state on error.

---

## 🛡️ Security Updates

* **sqlparse (`0.5.5 → 0.6.0`)** — Patched 5 HIGH/MODERATE security vulnerabilities including CPU DoS via `TokenList.__init__` (CVE-2026-54284), quadratic DoS in `group_comments`, and ReDoS in dollar-quoted SQL literals.
* **pypdf (`6.15.0 → 6.16.2`)** — Patched infinite loop in `TreeObject.insert_child` (CVE-2026-84309), outline traversal resource exhaustion (CVE-2026-84310), and exponential XForm text extraction memory usage (CVE-2026-84311).
* **djangorestframework (`3.16.1 → 3.17.2`)** — Enforced `DATA_UPLOAD_MAX_MEMORY_SIZE` limits during request parsing to mitigate payload DoS (CVE-2026-73228) and resolved GET-protected data disclosure in `AdminRenderer` (CVE-2026-73229).

---

## 🗄️ Database Migrations & Commands

This release introduces the following database migrations:
* `configurations`: `0010_configurationpermission`
* `recycle_bin`: `0001_initial`
* `roles`: `0005_grandfather_gate_pass_audit_configurations`

### Post-Deployment Execution:
```bash
# 1. Run migrations
python manage.py migrate

# 2. Sync permissions across all roles and system groups
python manage.py sync_permissions

# 3. (Optional) Verify permission migration integrity
python manage.py verify_permission_migration
```

---

**Full Changelog**: https://github.com/VyrazuLabs/asseto-asset-management/compare/v1.6.7...v1.7.0
