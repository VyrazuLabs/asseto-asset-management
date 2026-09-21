# Release Notes — v1.8.1

**Tag**: `v1.8.1`  
**Target Branch**: `main`  
**Date**: September 17, 2026  
**Title**: `v1.8.1 — Consumables Management Module, Custom Fields Filtering & Bulk Upload Fixes`

---

## 🚀 Overview

Asseto **v1.8.1** introduces a full-featured **Consumables Management Module** for tracking non-capital inventory with low stock alert automation and document attachments, extends the **Custom Fields API** with module-based query filtering, fixes bulk location upload empty cell parsing, and delivers substantial documentation enhancements across the platform.

---

## ✨ Added

* **Consumables Management Module (PR #268, #274)**:
  * **Inventory Tracking** — Complete lifecycle management for consumables including consumable name, item category, total quantity, remaining quantity, purchase date, unit price, assigned vendor, and storage location.
  * **Low Stock Alerts & Notifications** — Configurable minimum stock alert thresholds with automated email notifications triggered when stock levels dip (`consumables/utils.py`).
  * **Supporting Document Attachments** — Dedicated supporting document upload and viewing pipeline (`ConsumableDocument`) on add, edit, and detail views.
  * **Recycle Bin Integration** — Full soft-delete lifecycle support with restore and permanent purge capabilities in the Recycle Bin module (`recycle_bin/views.py`, `templates/recycle_bin/deleted-consumables.html`).
  * **Granular RBAC Permissions** — Centralized permission scoping for the Consumables module registered in `common/permissions.py` and dynamic permission checkboxes in role creation and update modals.
  * **Modern Styling** — Standalone responsive UI styling in `static/css/pages/consumables.css` and table partials.
* **Custom Fields API Module Filtering (PR #273)**:
  * Added optional `module` query parameter support in the `Get Custom Fields List API` (`custom_fields/views.py`) allowing filtered field retrieval by target module (e.g., `?module=asset`, `?module=consumables`).

---

## 🔄 Changed

* **Audit Scheduling Guard Clauses (PR #268)**:
  * Refactored `audit/utils.py` and `audit/api_utils.py` with defensive guard clauses handling `None` next due dates to prevent calculation exceptions during audit scheduling.
* **Platform Documentation & Showcase Overhaul (PR #272)**:
  * Revamped `README.md` and `ROADMAP.md` with comprehensive feature breakdowns, architecture summaries, and high-resolution interface visuals for Clients, Gate Pass, Custom Fields, Bulk Upload, Client Portal, Consumables, and Support Tickets.

---

## 🐛 Fixed

* **Consumables Quantity Tracking Inconsistencies (PR #274)**:
  * Fixed quantity update and remaining quantity recalculation logic in `consumables/forms.py` and `consumables/views.py`.
* **Location Bulk Upload Empty Cell Parsing (PR #270)**:
  * Resolved `NaN` parsing errors in `upload/views/location_views.py` and `templates/dashboard/partials/recent_locations.html` when processing CSV uploads containing empty location cells.

---

## 🗄️ Database Migrations & Commands

This release introduces the following database migrations:
* `configurations`: `0011_extensionspermission`
* `consumables`: `0001_initial`, `0002_consumable_consumable_name_and_more`, `0003_consumable_remaining_quantity_and_more`, `0004_consumabledocument`

### Post-Deployment Execution:
```bash
# 1. Run migrations
python manage.py migrate

# 2. Sync permissions across all roles and system groups
python manage.py sync_permissions
```

---

**Full Changelog**: https://github.com/VyrazuLabs/asseto-asset-management/compare/v1.8.0...v1.8.1
