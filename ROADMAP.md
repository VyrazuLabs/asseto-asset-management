# Asseto - Roadmap

This document describes the current status and the upcoming milestones of the Asseto Asset Management project.

*Updated: Mon, 08 Jun 2026 18:25:00 GMT*

---

## Status Key
- 🟢 **Completed**: Fully implemented and tested.
- 🟡 **In Progress**: Active development or integration phase.
- 🔵 **Planned**: Scheduled for development.

---

## Core Asset Management Web App

#### Milestone Summary

| Status | Milestone | Goals |
| :---: | :--- | :---: |
| 🟡 | **[Asset Configurations & Lifecycle Management](#asset-configurations--lifecycle-management)** | 1 / 3 |
| 🟡 | **[Security & Audit Systems](#security--audit-systems)** | 2 / 3 |
| 🔵 | **[Localization & User Preferences](#localization--user-preferences)** | 0 / 1 |

#### Asset Configurations & Lifecycle Management

> This milestone will be done when
* Administrators can custom-define specifications and template fields per asset category.
* Asset repair history, maintenance costs, and vendor relationships are logged.
* Consumables and accessories stock levels can be managed and assigned to employees.

🟡 &nbsp;**IN PROGRESS** &nbsp;&nbsp;📊 &nbsp;&nbsp;**1 / 3** goals completed **(33%)**

| Status | Goal | Labels | Repository |
| :---: | :--- | --- | --- |
| ✅ | [Asset Configuration Management fields & templates](https://github.com/VyrazuLabs/asseto-asset-management/pull/31) | | <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |
| ⬜ | [Asset Repair Logs tracking and cost history](https://github.com/VyrazuLabs/asseto-asset-management/issues/74) |`in progress`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |
| ⬜ | [Consumables Management module for accessories tracking](https://github.com/VyrazuLabs/asseto-asset-management/issues/75) |`ready`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |


#### Security & Audit Systems

> This milestone will be done when
* User authentication can be strengthened with Two-Factor Verification.
* Resources can be soft-deleted and recovered via Recycle Bin.
* Every administrative data mutation creates an automated audit trail.

🟡 &nbsp;**IN PROGRESS** &nbsp;&nbsp;📊 &nbsp;&nbsp;**2 / 3** goals completed **(66%)**

| Status | Goal | Labels | Repository |
| :---: | :--- | --- | --- |
| ✅ | [2FA (Two-Factor Authentication) profile configuration](https://github.com/VyrazuLabs/asseto-asset-management/pull/42) | | <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |
| ✅ | [Audit Logs & Soft Delete System integration](https://github.com/VyrazuLabs/asseto-asset-management/pull/39) | | <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |
| ⬜ | [Automated activity feed database logger](https://github.com/VyrazuLabs/asseto-asset-management/issues/82) |`in progress`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |


#### Localization & User Preferences

> This milestone will be done when
* The interface strings are internationalized and translation files exist.
* The system detects browser locale and lets users change language options manually.

🔵 &nbsp;**PLANNED** &nbsp;&nbsp;📊 &nbsp;&nbsp;**0 / 1** goals completed **(0%)**

| Status | Goal | Labels | Repository |
| :---: | :--- | --- | --- |
| ⬜ | [Multi Language Support (i18n middleware & translations)](https://github.com/VyrazuLabs/asseto-asset-management/issues/88) |`ready`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |


---

## Integrations & APIs

#### Milestone Summary

| Status | Milestone | Goals |
| :---: | :--- | :---: |
| 🔵 | **[Third-Party API & Communication](#third-party-api--communication)** | 0 / 2 |

#### Third-Party API & Communication

> This milestone will be done when
* Authenticated REST APIs exist to let third-party services programmatically fetch or update assets.
* Slack integration webhooks can send real-time alerts to external channels.

🔵 &nbsp;**PLANNED** &nbsp;&nbsp;📊 &nbsp;&nbsp;**0 / 2** goals completed **(0%)**

| Status | Goal | Labels | Repository |
| :---: | :--- | --- | --- |
| ⬜ | [API for third party integrations with token auth](https://github.com/VyrazuLabs/asseto-asset-management/issues/91) |`in progress`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |
| ⬜ | [Slack Integrations for workspace channels notifications](https://github.com/VyrazuLabs/asseto-asset-management/issues/92) |`ready`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |


---

## Client Portal & Support

#### Milestone Summary

| Status | Milestone | Goals |
| :---: | :--- | :---: |
| 🔵 | **[Client Portal & Ticket Management](#client-portal--ticket-management)** | 0 / 2 |

#### Client Portal & Ticket Management

> This milestone will be done when
* Rented assets can be viewed by tenant clients in a dedicated Portal view.
* Ticket workflows enable clients to open and follow repairs or technical requests directly.

🔵 &nbsp;**PLANNED** &nbsp;&nbsp;📊 &nbsp;&nbsp;**0 / 2** goals completed **(0%)**

| Status | Goal | Labels | Repository |
| :---: | :--- | --- | --- |
| ⬜ | [Client Portal for Rented Asset Details and ticket management](https://github.com/VyrazuLabs/asseto-asset-management/issues/95) |`in progress`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |
| ⬜ | [Support Ticket Management core routing & agent assignment](https://github.com/VyrazuLabs/asseto-asset-management/issues/96) |`ready`| <a href=https://github.com/VyrazuLabs/asseto-asset-management>VyrazuLabs/asseto-asset-management</a> |


---

## Mobile Application

#### Milestone Summary

| Status | Milestone | Goals |
| :---: | :--- | :---: |
| 🔵 | **[Mobile Application Development](#mobile-application-development)** | 0 / 1 |

#### Mobile Application Development

> This milestone will be done when
* Android & iOS applications support barcode auditing and remote requests.
* The applications are successfully released to internal or public app stores.

🔵 &nbsp;**PLANNED** &nbsp;&nbsp;📊 &nbsp;&nbsp;**0 / 1** goals completed **(0%)**

| Status | Goal | Labels | Repository |
| :---: | :--- | --- | --- |
| ⬜ | [Mobile Application Flutter companion app code release](https://github.com/VyrazuLabs/mobile-app/issues/60) |`in progress`| <a href=https://github.com/VyrazuLabs/mobile-app>VyrazuLabs/mobile-app</a> |
