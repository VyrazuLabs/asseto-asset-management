<div align="center">

<img src="static/images/asseto-logo.svg" alt="Asseto" width="220" />

**Open-source asset management for IT, facility, and operations teams — track custody, audit every change, and manage the full lifecycle of your hardware, equipment, and rentals from one dashboard.**

[![License: Vyrazu](https://img.shields.io/badge/License-Vyrazu%20(GPLv3--based)-orange)](LICENSE.md)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-092E20)](https://www.djangoproject.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.MD)
[![GitHub stars](https://img.shields.io/github/stars/VyrazuLabs/asseto-asset-management)](https://github.com/VyrazuLabs/asseto-asset-management/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/VyrazuLabs/asseto-asset-management)](https://github.com/VyrazuLabs/asseto-asset-management/network/members)
[![GitHub issues](https://img.shields.io/github/issues/VyrazuLabs/asseto-asset-management)](https://github.com/VyrazuLabs/asseto-asset-management/issues)

[🚀 Live Demo](https://asset-management-hg2x.onrender.com/login?next=/) · [📖 Roadmap](ROADMAP.md) · [🐛 Report Bug](https://github.com/VyrazuLabs/asseto-asset-management/issues) · [✨ Request Feature](https://github.com/VyrazuLabs/asseto-asset-management/issues)

<img src="static/images/011-Dasboard_large.png" alt="Asseto dashboard" width="90%" />

</div>

## Try the Demo

> [!TIP]
> Explore a live instance before installing anything — no signup required.
> **[Open the demo →](https://asset-management-hg2x.onrender.com/login?next=/)**

| | Shared demo account |
|---|---|
| **Email** | `asset-management@demo.com` |
| **Password** | `DM4g476ZmQ$U` |

*This is a shared, resettable demo account — please don't store anything sensitive in it.*

## Why Asseto?

Most teams still track laptops, equipment, and rented assets in spreadsheets — no custody trail, no audit history, and no way to prove who had what when it matters. Asseto replaces that with a single system of record: every assignment, repair, and modification is logged automatically, deleted records land in a recoverable Recycle Bin, and access is governed by custom roles and two-factor authentication. It ships with a REST API, Slack and Firebase push notifications, and a companion Flutter mobile app for physical audits in the field.

**Built on Django 5.2**, actively developed with frequent releases. Self-hostable, and free for commercial use under the [Vyrazu License](LICENSE.md).

---

### 🔒 Security

To report a security vulnerability, please email **[security@vyrazu.com](mailto:security@vyrazu.com)** instead of using the issue tracker. See [SECURITY.md](SECURITY.md) for details.

### 📋 Latest Releases

Check the [Releases page](https://github.com/VyrazuLabs/asseto-asset-management/releases) for version history and [CHANGELOG.md](CHANGELOG.md) for recent updates.

## Table of Contents

- [Latest Features](#latest-features)
- [Updated Feature](#updated-feature)
- [Features](#features)
- [Screenshots](#screenshots)
- [Quick Start](#quick-start)
- [Security](#-security)
- [Two-Factor Authentication](#two-factor-authentication-2fa)
- [Notifications & Firebase](#notifications--firebase-integration)
- [Testing](#testing)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Releasing](#releasing)
- [License](#license)
- [Contact](#contact)

## ✨ Latest Features

<table>
  <tr>
    <td width="55%" valign="top">
      <h3>🚀 Bulk Asset Upload</h3>
      <p>Say goodbye to tedious manual data entry! Asseto’s all-new <b>Bulk Asset Upload</b> feature enables IT and operations teams to upload bulk asset data all at once using structured CSV templates.</p>
      <h4>Why Use It?</h4>
      <ul>
        <li>⚡ <b>Save Time:</b> Onboard entire departments or batch purchases in a single click.</li>
        <li>🎯 <b>Eliminate Human Error:</b> Built-in validation ensures consistent asset data.</li>
        <li>🔄 <b>Effortless Migration:</b> Transition from Excel seamlessly.</li>
        <li>📈 <b>Built for Scale:</b> Effortlessly scale from 10 to 10,000+ assets.</li>
      </ul>
    </td>
    <td width="45%" align="center" valign="middle">
      <img src="static/images/asset-bulk-upload.png" alt="Bulk Asset Upload" width="100%" />
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="45%" align="center" valign="middle">
      <img src="static/images/Clients.png" alt="Client Module" width="100%" />
    </td>
    <td width="55%" valign="top">
      <h3>🏢 Client Module</h3>
      <p>Effortlessly register and manage client organizations and external stakeholders with built-in portal security controls.</p>
      <h4>Why Use It?</h4>
      <ul>
        <li>🔒 <b>Granular Access Control:</b> Toggle portal access permissions per client instantly.</li>
        <li>🔑 <b>Passwordless OTP Login:</b> Secure authentication via one-time passwords sent to registered emails.</li>
        <li>💼 <b>Centralized Management:</b> Keep all external client records, contacts, and active contracts organized.</li>
      </ul>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="55%" valign="top">
      <h3>🎫 Support Ticket Module</h3>
      <p>Bridge the gap between clients and support teams with comprehensive issue tracking and real-time communication.</p>
      <h4>Why Use It?</h4>
      <ul>
        <li>📊 <b>Flexible Kanban & List Views:</b> Manage ticket progress with an intuitive drag-and-drop board or detailed list.</li>
        <li>🔗 <b>Asset-Linked Ticketing:</b> Track repair and service requests tied directly to specific hardware assets.</li>
        <li>💬 <b>Collaborative Threads:</b> In-ticket messaging allows admins and clients to discuss issues and share updates seamlessly.</li>
      </ul>
    </td>
    <td width="45%" align="center" valign="middle">
      <img src="static/images/support-ticket.png" alt="Support Ticket Module" width="100%" />
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="45%" align="center" valign="middle">
      <img src="static/images/client-portal-login.png" alt="Client Portal Login" width="48%" style="margin-right:2%;"/>
      <img src="static/images/client-portal.png" alt="Client Portal Dashboard" width="48%" />
    </td>
    <td width="55%" valign="top">
      <h3>🌐 Client Portal</h3>
      <p>Give your clients direct, real-time access to their assigned asset fleet and support requests without exposing internal systems.</p>
      <h4>Why Offer It?</h4>
      <ul>
        <li>👁️ <b>Total Asset Visibility:</b> Clients can view all equipment assigned to them, complete with statuses and serial numbers.</li>
        <li>⚡ <b>Self-Service Requests:</b> Clients can log new support tickets against specific assets directly from the portal.</li>
        <li>🛡️ <b>Enhanced Transparency:</b> Keep clients confident with full visibility into their equipment lifecycle and support histories.</li>
      </ul>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="55%" valign="top">
      <h3>🏷️ Gate Pass Module</h3>
      <p>Initiate and manage the movement of assets inward or outward securely. Ensure full accountability at your facility gates with approval workflows and scannable QR codes.</p>
      <h4>Why Use It?</h4>
      <ul>
        <li>🛡️ <b>Secure Approvals:</b> Authorized users can seamlessly approve or reject gate pass requests.</li>
        <li>🚫 <b>Prevent Duplicates:</b> Assets with pending passes are locked to prevent duplicate movement requests.</li>
        <li>📱 <b>QR Code Verification:</b> Print gate pass documents with QR codes for instant scanning and automatic movement status updates.</li>
        <li>📝 <b>Complete Audit Trail:</b> Track the full lifecycle of approvals, rejections, and physical movements.</li>
      </ul>
    </td>
    <td width="45%" align="center" valign="middle">
      <img src="static/images/Gate-Pass.png" alt="Gate Pass Module" width="100%" />
    </td>
  </tr>
</table>

---

## 🔄 Updated Feature

<table>
  <tr>
    <td width="45%" align="center" valign="middle">
      <img src="static/images/add-custome-field.png" alt="Add Custom Field" width="48%" style="margin-right:2%;"/>
      <img src="static/images/custom-field.png" alt="Universal Custom Fields" width="48%" />
    </td>
    <td width="55%" valign="top">
      <h3>🧩 Universal Custom Fields</h3>
      <p><b>Problem:</b> Custom fields were previously only available for Assets, limiting system flexibility.</p>
      <p><b>Solution:</b> We hear you! Now, you can create a custom field once and use it universally across <b>Assets, Users, Products, Vendors, and Clients</b>. Repetitive work is officially gone.</p>
      <h4>Why You'll Love It:</h4>
      <ul>
        <li>🚀 <b>Repetitive Work Gone:</b> Create a field just once instead of recreating it for every entity type manually.</li>
        <li>🔗 <b>Total Flexibility:</b> Easily capture and track unique organizational data across all modules seamlessly.</li>
        <li>📈 <b>Unified Data Structure:</b> Keep your custom data consistent and standardized everywhere.</li>
      </ul>
    </td>
  </tr>
</table>

---

## Features

### Security, Auditing & Administration

- **Audit Logs & Soft Delete**: Every administrative change is logged automatically; deleted records are recoverable from a central Recycle Bin.
- **Two-Factor Authentication (2FA)**: TOTP authenticator-app verification on top of password login.
- **Role-Based Access Control**: Custom workspace roles restrict both interface access and per-action permissions.

### Core Asset Lifecycle & Inventory

- **Admin Dashboard**: Central records for Assigned Users, Locations, Departments, Product Types, Product Categories, and Roles.
- **Asset Assignment & Custody**: Assign assets to users, track reassignments, and keep active custody logs.
- **Asset Configuration Management**: Custom specification fields and category-based templates for diverse asset classes.
- **Asset Repair Logs**: Repair histories, maintenance costs, status changes, and servicing vendors.
- **Consumables Management**: Inventory tracking, stock-level alerts, and distribution management for office accessories.
- **Bulk Uploads**: Import Vendors, Locations, Departments, Categories, and Products via CSV templates.
- **Gate Pass Management**: Manage inward/outward asset movements with QR-code verifiable gate passes and approval workflows.

### Integration & Multi-Channel Sync

- **REST API**: Secure endpoints to read and synchronize asset data with external systems.
- **Slack Integration**: Push immediate alerts and updates to Slack workspace channels.
- **Flexible Notifications**: Multi-channel notifications across Email and Firebase (FCM) push alerts.
- **Mobile Application**: Flutter-based companion app for remote management and physical audits.
- **Multi-Language Support**: Complete interface internationalization (i18n) for global teams.

### Portals & Customer Support

- **Client Module**: Register and manage external clients within the system. Control access via the *Client Portal Access* toggle, allowing clients to log in securely with passwordless OTP verification sent to their registered email.
- **Support Ticket Module**: Manage asset service and maintenance requests with List and Kanban views. Includes drag-and-drop status transitions, ticket lifecycle tracking, and built-in comment/conversation threads for seamless communication between admins and clients.
- **Client Portal**: Empower clients with a dedicated self-service portal to view all assigned assets, track active support tickets, and submit new issues directly against their hardware inventory.

## Screenshots

<details>
<summary><b>Admin Section</b> — manage Locations, Departments, Product Types, Categories, and Roles</summary>

![Admin Section](static/images/014-New%20Location.png)

- Navigate to the **Admin** section in the side menu.
- Manage Locations, Departments, Product Types, Product Categories, and Roles.
- Perform standard CRUD actions (Add, Edit, View, Delete) on configurations.

</details>

<details>
<summary><b>Vendors</b> — add, search, and export vendor records</summary>

![Vendors Section](static/images/015-New%20Vendor.png)

- Navigate to the **Vendors** section.
- Click actions to Add, Edit, View, or Delete vendors.
- Use search filters or download vendor lists as needed.

</details>

<details>
<summary><b>Products</b> — product lines, specifications, and inventory counts</summary>

![Products Section](static/images/016-New%20Product.png)

- Navigate to the **Products** section.
- Add new product lines or view product specifications.
- Manage categories and inventory counts.

</details>

<details>
<summary><b>Users</b> — accounts, roles, and permissions</summary>

![Users Section](static/images/017-New%20Users.png)

- Navigate to the **Users** section to view registered accounts.
- Grant permissions, assign roles, or register new users.

</details>

<details>
<summary><b>Client Module</b> — register clients & control portal access</summary>

![Client Module](static/images/Clients.png)

- Navigate to the **Clients** section to register and manage client organizations.
- Control client access using the **Client Portal Access** toggle.
- Enabled clients log into the Client Portal seamlessly using OTP-based email verification.

</details>

<details>
<summary><b>Support Ticket Module</b> — List & Kanban views with interactive ticket management</summary>

![Support Ticket Module](static/images/support-ticket.png)

- View and manage support tickets using List View or interactive **Kanban View**.
- Drag and drop ticket cards across status columns (e.g., Open, In Progress, Resolved).
- Create, edit, and track tickets tied directly to specific assets.
- Collaborate with clients through the built-in comment and conversation thread within each ticket.

</details>

<details>
<summary><b>Client Portal</b> — OTP login & self-service asset management</summary>

![Client Portal Login](static/images/client-portal-login.png)

![Client Portal Dashboard](static/images/client-portal.png)

- **OTP Authentication**: Clients log in securely via OTP sent to their registered email address.
- **Asset Visibility**: View all hardware and equipment currently assigned to their organization.
- **Ticket Tracking**: View ticket resolution progress and log new support tickets directly against assigned assets.

</details>

<details>
<summary><b>Assets</b> — profiles, assignment, and state transitions</summary>

![Assets Section](static/images/018-New%20Assets.png)

- Navigate to the **Assets** section.
- Create/edit asset profiles and assign them to users.
- Manage state transitions (e.g., Reassign, Unassign).

</details>

<details>
<summary><b>Bulk Asset Upload</b> — import bulk asset data all at once via CSV</summary>

![Bulk Asset Upload](static/images/asset-bulk-upload.png)

- Navigate to the **Assets** or **Bulk Upload** section.
- Upload multiple hardware, laptop, and equipment records simultaneously using structured CSV files.
- Accelerate workspace onboarding and batch inventory updates seamlessly.

</details>

<details>
<summary><b>Upload</b> — CSV templates for bulk data insertion</summary>

![Upload Section](static/images/019-%20New%20Upload.png)

- Navigate to the **Upload** section.
- Download sample CSV templates for Locations, Departments, Product Types, Categories, and Vendors.
- Upload completed sheets for fast bulk data insertion.

</details>

<details>
<summary><b>Recycle Bin</b> — restore or purge soft-deleted records</summary>

![Recycle Bin Section](static/images/013-recycle_bin.png)

- Access the **Recycle Bin** from the settings panel.
- View soft-deleted records grouped by category.
- Restore items back to active tables or permanently purge them.

</details>

<details>
<summary><b>Gate Pass Module</b> — manage inward and outward asset movements</summary>

![Gate Pass Module](static/images/Gate-Pass.png)

- Create and manage Gate Passes for single or multiple assets securely.
- Prevent duplicate requests with automatic pending pass detection.
- Print QR codes on Gate Pass documents for instant gate scanning and status updates.
- Maintain comprehensive audit trails of all approvals, rejections, and asset movements.

</details>

## Quick Start

### Prerequisites

- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.11+](https://www.python.org/) (optional, only for manual non-containerized setup)
- [MySQL](https://www.mysql.com/) or [PostgreSQL](https://www.postgresql.org/) (optional, only for manual non-containerized setup)

### Docker Containerized Setup (Recommended)

The easiest way to get Asseto up and running is via the interactive docker setup script, which builds the application container, configures a chosen database (PostgreSQL/MySQL), routes traffic through Nginx, runs migrations, and collects static files automatically.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VyrazuLabs/asseto-asset-management.git
   cd asseto-asset-management
   ```

2. **Run the interactive setup wizard:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Follow the interactive prompts** to configure the database choice, environment variables, optional firewall, and let the script handle the build.

4. **Access the application** at `http://localhost`. To create an administrator account, run:
   ```bash
   docker compose exec -it web python manage.py createsuperuser
   ```

---

### Manual / Local Developer Setup (No Docker)

1. Clone the repository:
   ```bash
   git clone https://github.com/VyrazuLabs/asseto-asset-management.git
   cd asseto-asset-management
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use `env\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your database configurations and secret key.

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. Open your browser at `http://localhost:8000`, and create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

## Security & Advanced Features

### Two-Factor Authentication (2FA)

2FA can be toggled on/off in the User Profile section.

- **When Enabled**: Scan the provided QR code with any standard Authenticator App (Google Authenticator, Authy, etc.) to link the account. Subsequent logins require a dynamic OTP code.
- **When Disabled**: Falls back to password-only validation.

### Notifications & Firebase Integration

Custom notification channels can be enabled or disabled in the Profile settings.

- **In-App & Mobile Push Alerts**: Require Firebase integration.
- Place your `firebase-credentials.json` in the project root, or encrypt its contents using a Fernet key, placing the output data and the Fernet key in your `.env` file.

## Testing

Unit tests cover core backend functionality. Activate your virtual environment first, then:

```bash
python manage.py test              # run all tests
python manage.py test assets      # run tests for a specific app
python manage.py test -v 2        # verbose output
python manage.py test --keepdb    # skip test-database recreation
```

## Configuration

Configuration options are managed via the `.env` file. Copy the template from `.env.example` to `.env` for your local setup. Key settings include:

- Database credentials (MySQL/PostgreSQL)
- SMTP server credentials for email dispatch
- Firebase settings & Fernet keys
- Django CSRF & Allowed Hosts lists

## Roadmap

Current status and planned milestones are summarized below. For individual milestone goals, open pull requests, and tracking issues, see the full [ROADMAP.md](ROADMAP.md).

### Core Web Application

The web platform is deepening its lifecycle, security, and localization capabilities — details in [Asset Configurations & Lifecycle Management](ROADMAP.md#asset-configurations--lifecycle-management), [Security & Audit Systems](ROADMAP.md#security--audit-systems), and [Localization & User Preferences](ROADMAP.md#localization--user-preferences).

| Status | Milestone | Goals Completed |
|---|---|---|
| 🟢 | [Asset Configurations & Lifecycle Management](ROADMAP.md#asset-configurations--lifecycle-management) | 3 / 3 |
| 🟡 | [Security & Audit Systems](ROADMAP.md#security--audit-systems) | 2 / 3 |
| 🟢 | [Localization & User Preferences](ROADMAP.md#localization--user-preferences) | 1 / 1 |

### Integrations & APIs

Third-party connectivity is next up — see [Third-Party API & Communication](ROADMAP.md#third-party-api--communication). Looking further ahead, IoT compatibility is planned: GPS/BLE asset tags and sensor feeds for real-time location, usage, and condition monitoring.

| Status | Milestone | Goals Completed |
|---|---|---|
| 🔵 | [Third-Party API & Communication](ROADMAP.md#third-party-api--communication) | 0 / 2 |
| 🔵 | IoT Compatibility (future) — asset tags & sensor-based tracking | 0 / 1 |

### Client Portal & Support

External-facing portal and ticketing improvements are planned — see [Client Portal & Ticket Management](ROADMAP.md#client-portal--ticket-management).

| Status | Milestone | Goals Completed |
|---|---|---|
| 🟢 | [Client Portal & Ticket Management](ROADMAP.md#client-portal--ticket-management) | 2 / 2 |

### Mobile Application

The Flutter companion app is under active development — see [Mobile Application Development](ROADMAP.md#mobile-application-development).

| Status | Milestone | Goals Completed |
|---|---|---|
| 🟢 | [Mobile Application Development](ROADMAP.md#mobile-application-development) | 1 / 1 |

## Contributing

We welcome contributions from the community! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to your fork (`git push origin feature/your-feature`).
5. Open a Pull Request.

Please ensure your code conforms to the specifications in [CONTRIBUTING.MD](CONTRIBUTING.MD).

## Releasing

To publish a new version of Asseto, follow the step-by-step instructions in [RELEASING.md](RELEASING.md). It covers versioning conventions (SemVer), pre-release checklists (tests, security audit, changelog updating), branch workflows and tagging, and creating official GitHub Releases.

## License

This project is licensed under the **Vyrazu License** (based on GPL v3). Commercial use is permitted; selling, redistributing, or re-uploading original or modified copies is not, and shared modifications require attribution to the original repository. See [LICENSE.md](LICENSE.md) for full terms.

## Contact

- **Discussions**: [GitHub Discussions](https://github.com/VyrazuLabs/asseto-asset-management/discussions)
- **Email**: [info@vyrazu.com](mailto:info@vyrazu.com)
- **Project Maintainer**: [Vyrazu Labs Pvt Ltd](https://vyrazu.com/)

<div align="center">

**If Asseto helps your team, [give it a ⭐](https://github.com/VyrazuLabs/asseto-asset-management/stargazers) — it helps others find the project.**

</div>
