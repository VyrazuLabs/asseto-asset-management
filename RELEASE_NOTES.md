# Release Notes — v1.8.4

**Tag**: `v1.8.4`  
**Target Branch**: `main`  
**Date**: October 25, 2026  
**Title**: `v1.8.4 — Python Dependencies Security Patching`

---

## 🚀 Overview

Asseto **v1.8.4** is a patch release upgrading core Python dependencies in `requirements.txt` to remediate known security vulnerabilities.

---

## 🛡️ Security Updates

* **Python Dependencies Vulnerability Updates**:
  * Upgraded `PyJWT` to `2.15.0`
  * Upgraded `virtualenv` to `21.14.13`

---

## 🗄️ Database Migrations & Commands

No new database migrations are introduced in this release.

### Post-Deployment Execution:
```bash
# 1. Update Python dependencies
pip install -r requirements.txt

# 2. Collect static files
python manage.py collectstatic --noinput
```

---

**Full Changelog**: https://github.com/VyrazuLabs/asseto-asset-management/compare/v1.8.3...v1.8.4
