# Release Notes — v1.8.2

**Tag**: `v1.8.2`  
**Target Branch**: `main`  
**Date**: September 25, 2026  
**Title**: `v1.8.2 — Select2 Dynamic Search Integration, Common Filtered Pagination, Multi-Language Translations & Security Updates`

---

## 🚀 Overview

Asseto **v1.8.2** introduces Select2 dynamic search dropdowns across key platform forms and filters, implements a unified HTMX filtered pagination component across 14 module list views, resolves asset assignment and search pagination issues, expands internationalization support with Bengali, Hindi, and French translations for Consumables and Upload modules, and resolves open Dependabot security advisories.

---

## ✨ Added

* **Select2 Dynamic Search Dropdowns (PR #278)**:
  * Replaced native select elements with searchable Select2 dropdowns across Client Portal, Support Tickets, Asset Details, Consumables, Clients, and Bulk Upload mapping steps.
  * Added vendor Select2 distribution files (`static/vendor/select2/css/select2.min.css`, `static/vendor/select2/js/select2.min.js`).
  * Implemented an Asseto design system theme (`static/css/common/select2-theme.css`) and automated initialization script (`static/js/select2-init.js`).
* **Common Filtered HTMX Pagination (PR #277)**:
  * Implemented a unified pagination component (`templates/commons/htmx-pagination.html`) that maintains active search queries and filter parameters across page changes.
  * Standardized across 14 list views: Assets, Clients, Consumables, Custom Fields, Departments, Locations, Product Categories, Product Types, Products, License Types, Roles, Support Tickets, Users, and Vendors.
* **Multi-Language Translation Support (PR #275)**:
  * Added localized translation dictionaries for Bengali (`bn`), Hindi (`hi`), and French (`fr`) covering Consumables, Upload, Asset, and General configuration strings.
* **Client Filtering in Asset List (PR #275)**:
  * Added client filter dropdown and conditional client column display in the asset list page.

---

## 🔄 Changed

* **Asset Table Partial Template (PR #276)**:
  * Extracted asset table rows into a modular partial template (`templates/assets/_asset_row.html`) for improved reusability and HTMX updates.
* **Bulk Upload Interface Polish (PR #275)**:
  * Enhanced Bulk Upload UI with refined step indicators and streamlined modal styling (`static/css/pages/upload-modals.css`).

---

## 🐛 Fixed

* **Asset Assignment & User Allocation (PR #276)**:
  * Fixed errors occurring during asset assignment and user re-assignment in `assets/utils.py` and `assets/views.py`.
* **Asset Search & Date Format Filtering (PR #276)**:
  * Resolved pagination reset and filtering discrepancies when searching assets, and corrected date formatting based on default system settings.
* **Dashboard Analytics Calculations (PR #275)**:
  * Fixed count and percentage calculation discrepancies in department and location dashboard views.

---

## 🛡️ Security Updates

* **Dependency Vulnerability Remediation**:
  * Upgraded `cryptography` to `>=43.0.1` in `requirements.txt` to resolve CVE-2024-12797 and related advisories.
  * Upgraded `requests` to `>=2.32.2` in `requirements.txt` to resolve CVE-2024-35195.

---

## 🗄️ Database Migrations & Commands

No new database migrations are introduced in this release.

### Post-Deployment Execution:
```bash
# 1. (Optional) Run migrations to verify database state
python manage.py migrate

# 2. Collect static files
python manage.py collectstatic --noinput
```

---

**Full Changelog**: https://github.com/VyrazuLabs/asseto-asset-management/compare/v1.8.1...v1.8.2
