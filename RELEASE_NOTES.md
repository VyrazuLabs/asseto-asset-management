# Release Notes — v1.8.3

**Tag**: `v1.8.3`  
**Target Branch**: `main`  
**Date**: October 25, 2026  
**Title**: `v1.8.3 — Consumable IDs & Serialized Consumable Units, User List API Fixes & Dependency Security Updates`

---

## 🚀 Overview

Asseto **v1.8.3** introduces unique consumable IDs and support for serialized consumable units (enabling unit-level lifecycle tracking, item serialization, status workflows, and interactive checkouts), resolves user retrieval and default search parameter handling in the Users API, and updates core Python dependencies in `requirements.txt` to patch security vulnerabilities.

---

## ✨ Added

* **Consumable Unique IDs & Serialized Units (PR #279)**:
  * **Consumable ID Identification** — Added custom/auto-generated unique `consumable_id` field to the `Consumable` model with configurable slug and sequence fallback.
  * **Serialized Consumable Units** — Introduced `SerializedConsumableUnit` model to manage individual unit serial numbers, unit status states (`AVAILABLE`, `ALLOCATED`, `DAMAGED`, `DISPOSED`), assigned users, and locations.
  * **Unit Checkout Modal** — Added dedicated modal interface (`templates/consumables/_checkout-modal.html`) enabling single or batch unit checkouts directly from the consumable detail page with real-time availability checks.
  * **Backfill Management Command** — Created `backfill_consumable_ids` (`python manage.py backfill_consumable_ids`) to safely generate unique identifiers for pre-existing consumable inventory.
  * **Multi-Language Support** — Added comprehensive translation keys across English, Bengali (`bn`), French (`fr`), and Hindi (`hi`) for serialization and unit statuses.
  * **Automated Test Coverage** — Added model factory definitions and extensive unit/integration test suites (`consumables/tests/test_serialized_units.py`, `consumables/tests/test_serialized_views.py`).

---

## 🐛 Fixed

* **Default User List Missing Logged-in User (PR #280 / ASM-55)**:
  * Resolved issue in `users/api_views.py` and `users/serializers.py` where the currently authenticated user was omitted from default user list responses.
* **Search User List API Query Parameter Handling**:
  * Allowed calling the user search API endpoint without mandatory query parameters, defaulting cleanly to active paginated user records.

---

## 🛡️ Security Updates

* **Python Dependencies Vulnerability Updates**:
  * Upgraded `Django` to `5.2.17`
  * Upgraded `djangorestframework` to `3.18.2`
  * Upgraded `PyJWT` to `2.14.0`
  * Upgraded `pypdf` to `6.21.2`
  * Upgraded `urllib3` to `2.8.0`
  * Upgraded `certifi` to `2026.10.19`
  * Upgraded `pillow` to `13.0.0`
  * Upgraded `black` to `26.10.1`
  * Upgraded `packaging` to `26.3`
  * Upgraded `virtualenv` to `21.14.9`
  * Upgraded `filelock` to `4.2.1`

---

## 🗄️ Database Migrations & Commands

This release introduces the following database migrations:
* `consumables`: `0005_consumable_consumable_id.py`, `0006_serialized_consumable_units.py`

### Post-Deployment Execution:
```bash
# 1. Run migrations
python manage.py migrate

# 2. Backfill consumable IDs for existing records (if applicable)
python manage.py backfill_consumable_ids

# 3. Collect static files
python manage.py collectstatic --noinput
```

---

**Full Changelog**: https://github.com/VyrazuLabs/asseto-asset-management/compare/v1.8.2...v1.8.3
