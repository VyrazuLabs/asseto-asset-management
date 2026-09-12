# Release Notes — v1.8.0

**Tag**: `v1.8.0`  
**Target Branch**: `main`  
**Date**: September 13, 2026  
**Title**: `v1.8.0 — Granular RBAC Permissions Enforcement, Asset Assignment Fixes & Security Hardening`

---

## 🚀 Overview

Asseto **v1.8.0** delivers platform-wide RBAC permission enforcement across Admin, Configurations, Upload, and Recycle Bin modules, resolves asset assignment status inconsistencies in the REST API (ASM-34), secures Firebase messaging service worker secrets (V-001), and introduces automated secret scanning via Gitleaks.

---

## ✨ Added

* **Automated Secret Scanning** — Added Gitleaks (`v8.18.4`) hook to pre-commit configuration (`.pre-commit-config.yaml`) to prevent sensitive credentials and tokens from entering version control.
* **Granular UI Permission Gates for Recycle Bin** — Added role permission guards (`has_role_permission`) across all Recycle Bin templates (`deleted-Product-Category`, `deleted-Product-types`, `deleted-asset-status`, `deleted-assets`, `deleted-clients`, `deleted-department`, `deleted-license-type`, `deleted-location`, `deleted-products`, `deleted-users`, `deleted-vendors`) and partial tables to conditionally restrict restore and permanent delete actions based on user permissions.
* **Role Permission Guards in Navigation & Assets** — Enforced role-based access checks across sidebar navigation items (`templates/commons/sidebar.html`), asset listings, filter-out assets views, and user edit modals.

---

## 🔄 Changed

* **Permission Registry & Role Modals Refactoring** — Refined permission structures and constants in `common/permissions.py`. Redesigned and updated role create and edit modals (`templates/roles/add-role-modal.html`, `templates/roles/update-role-modal.html`) to dynamically handle category grouping and enforce view permission dependencies when modifying permissions.
* **Upload & Configuration Backend Permission Scoping** — Updated permission decorators and view-level authorization across CSV upload views (`department_views`, `location_views`, `product_category_views`, `product_type_views`, `user_views`, `vendor_views`), extensions configuration views, global search, and license type management.
* **Code Cleanup** — Removed dead and duplicate helper functions from `assets/utils.py` to streamline codebase maintainability.

---

## 🐛 Fixed

* **Asset Assignment Status Consistency (ASM-34)** — Fixed `UnAssignAsset` API view in `assets/api_views.py` to follow the standard unassignment routine (updating asset status, clearing assigned attributes, and recording unassignment history), matching the Asset List UI flow.
* **Role Edit Modals & Script Handlers** — Fixed permission checkbox bindings and dynamic select behaviors in role update and creation modals.

---

## 🛡️ Security Updates

* **Firebase Messaging Service Worker Hardcoded Secrets (V-001)** — Resolved vulnerability in `static/firebase-messaging-sw.js` by removing hardcoded Firebase API credentials and dynamically reading configuration parameters passed securely via service worker registration URL search parameters.
* **Pre-commit Secret Detection** — Enabled Gitleaks scanner to identify and block potential secret leakage before commit.

---

## 🗄️ Database Migrations & Commands

No new database migrations are introduced in this release.

### Post-Deployment Execution:
```bash
# 1. (Optional) Run migrations to verify database state
python manage.py migrate

# 2. Sync permissions across all roles and system groups
python manage.py sync_permissions
```

---

**Full Changelog**: https://github.com/VyrazuLabs/asseto-asset-management/compare/v1.7.0...v1.8.0
