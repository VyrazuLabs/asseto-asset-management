# Support Ticket System & Role Implementation Plan

## Overview
This plan outlines the architecture and tasks required to introduce a "Support Staff" role and a new "Tickets" module. This module will allow users to generate support tickets for assets and assign them to Support Staff for resolution.

## 1. Role Enhancements
**Goal:** Introduce a specific role for handling tickets.
- **`roles` app seeding:** Update the database seeding script (e.g. in `roles/management/commands/` or `roles/seeders.py` if present) to include a new `Role` named `"Support Staff"`.
- This role should have permissions strictly for viewing assets and managing tickets (read/update/resolve).

## 2. New Module: `tickets`
**Goal:** Create a standalone Django app to handle all ticketing logic.
Run `python manage.py startapp tickets` and add it to `INSTALLED_APPS`.

### Models (`tickets/models.py`)
Create a `Ticket` model inheriting from `TimeStampModel` and `SoftDeleteModel` (to match project standards).
- **`title`**: `CharField` (Short summary of the issue)
- **`description`**: `TextField` (Detailed explanation)
- **`asset`**: `ForeignKey` to `assets.Asset` (The asset having issues)
- **`created_by`**: `ForeignKey` to `authentication.User` (User who raised the ticket)
- **`assigned_to`**: `ForeignKey` to `authentication.User` (Support staff assigned to the ticket, nullable)
- **`status`**: `CharField` with choices (e.g., `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`)
- **`priority`**: `CharField` with choices (e.g., `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- **`organization`**: `ForeignKey` to `dashboard.Organization` (For multi-tenant data isolation)

*Optional:* `TicketComment` model for threaded discussion on a ticket.

### Serializers (`tickets/serializers.py`)
- `TicketSerializer`: Standard read/write serializer. Ensure `created_by` is read-only and set automatically from the request user.
- `TicketDetailSerializer`: Include nested representations (e.g. Asset name/Serial, Assigned User's full name) for the frontend to consume easily.

### Views / API Views (`tickets/api_views.py` & `tickets/views.py`)
Use Django REST Framework for API endpoints. Return responses using `common.API_custom_response.api_response`.
- **List/Create API:** 
  - `GET`: Filter tickets by `organization`. Support Staff see all tickets in their org, normal users see their own.
  - `POST`: Create a ticket. Auto-assign `created_by` and `organization`.
- **Retrieve/Update API:**
  - `GET`: Fetch single ticket details.
  - `PATCH`: Update ticket (e.g., change status, update description).
- **Custom Actions:**
  - `POST /tickets/<id>/assign/`: Assign a ticket to a Support Staff user.
  - `POST /tickets/<id>/resolve/`: Mark a ticket as resolved.

### URLs (`tickets/urls.py`)
Wire up the endpoints using DRF `DefaultRouter` or explicitly defined paths, then include them in the main project `urls.py`.

## 3. Permissions & Security
- Implement custom permission classes in `tickets/permissions.py`.
- Ensure a user can only edit a ticket if they are the creator or the assigned Support Staff.
- Ensure only Superusers, Admins, or Organization Admins can delete tickets.

## 4. Notifications (Optional but recommended)
- Integrate with the `notifications` app to alert:
  - The assigned user when a ticket is assigned to them.
  - The creator when the ticket status changes (e.g., to RESOLVED).

## 5. Testing
- Write test cases in `tickets/tests.py` covering:
  - Ticket creation creates a valid database entry.
  - Users can only see tickets within their own organization.
  - Only authorized roles can assign and resolve tickets.
