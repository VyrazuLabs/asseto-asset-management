# Asseto Setup Guide

Welcome to the **Asseto Asset Management** setup guide. This document provides step-by-step instructions for installing, configuring, and running the application.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Method 1: Docker Containerized Setup (Recommended)](#method-1-docker-containerized-setup-recommended)
  - [What the Setup Script Does](#what-the-setup-script-does)
  - [Steps to Run](#steps-to-run)
- [Method 2: Manual Developer Setup (No Docker)](#method-2-manual-developer-setup-no-docker)
  - [Steps to Run](#steps-to-run-1)
- [Post-Setup Configurations](#post-setup-configurations)
  - [Creating an Administrator Account](#creating-an-administrator-account)
  - [Connecting Google Cloud (Firebase Push Notifications)](#connecting-google-cloud-firebase-push-notifications)
  - [Managing the Application](#managing-the-application)
- [Troubleshooting](#troubleshooting)
  - [Port 80 Already Occupied](#port-80-already-occupied)
  - [Python Missing on Host](#python-missing-on-host)
  - [Docker Permissions](#docker-permissions)

---

## Prerequisites

Before setting up Asseto, ensure your system meets the following requirements:

### For Docker Setup (Recommended)
* **Operating System**: Linux (Ubuntu, Debian, CentOS, RHEL, Fedora, etc.) or macOS
* **Docker Engine**: Installed and running (v20.10+)
* **Docker Compose**: Installed (v2.0+)
* **Sudo Privileges**: Required if Docker daemon requires root access or to install packages/stop local services.

### For Manual Setup (No Docker)
* **Python**: v3.11+
* **Database**: PostgreSQL (v15+) or MySQL (v8.0+)
* **Package Manager**: `pip` and virtual environment support (`venv`)

---

## Method 1: Docker Containerized Setup (Recommended)

Asseto features an interactive setup wizard script (`setup.sh`) that automates container configuration, database selection, local web proxy installation, firewall adjustments, database migrations, and static asset collection.

### What the Setup Script Does
1. **Verifies Python & Docker on Host**: Verifies if Python and Docker are installed at the very beginning of the setup script. If Python is missing, the script attempts to install `python3.11` using the system's package manager. If Docker is missing, it automatically attempts to download and install the latest Docker engine via the official installation script.
2. **Checks Port 80**: Checks if the default port `80` (used by Nginx) is occupied. If another application (like a local Nginx, Apache, or custom server) is using it, the script attempts to stop or terminate that application first.
3. **Database Selection**: Guides you through choosing between **PostgreSQL** (recommended) or **MySQL**.
4. **Environment, SMTP & Nginx Configuration**: Automatically populates a `.env` file, creates a corresponding `docker-compose.yml`, and dynamically generates `nginx.conf` tailored to your configuration. Optionally prompts for the Server Domain or IP address (defaults to `localhost`), and SMTP credentials (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`).
5. **Verifies Docker**: Assures the Docker daemon and Docker Compose are installed and running.
6. **Builds & Launches Containers**: Downloads required base images (Nginx, database) and builds the Django web app container.
7. **Runs Migrations & Asset Collection**: Automatically executes Django migrations and collects static assets.
8. **Initial User & Organization Registration**: Prompts for administrator and company details (Full Name, Email, Username, Phone, Password asked twice with hidden inputs, Company Name, and Company Website). Executes `python manage.py user_register`. If the specified username or email already exists, the setup wizard automatically prompts you to re-enter valid details.

### Steps to Run
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/VyrazuLabs/asseto-asset-management.git
   cd asseto-asset-management
   ```

2. Make the script executable:
   ```bash
   chmod +x setup.sh
   ```

3. Run the setup script:
   ```bash
   ./setup.sh
   ```

4. Follow the interactive prompts:
   * Select your preferred database (PostgreSQL or MySQL).
   * Input custom database credentials or press `Enter` to use secure defaults.
   * Provide SMTP details optional step (or press `Enter` to skip and configure in `.env` later).
   * Provide a Server Domain or IP address (e.g. `example.com` or `123.45.67.89`) to configure allowed hosts and the Nginx server name, or press `Enter` to default to `localhost`.
   * If prompted, opt to configure your UFW firewall rules to allow incoming HTTP traffic.
   * Enter your account and company details for initial administrator registration (Password entered twice with verification).

5. Open your browser and navigate to the configured Server Domain or IP address (or `http://localhost`) to view the Asseto dashboard.

---

## Method 2: Manual Developer Setup (No Docker)

If you prefer to run Asseto directly on your local system without containerization:

### Steps to Run
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/VyrazuLabs/asseto-asset-management.git
   cd asseto-asset-management
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv env
   source env/bin/activate
   # On Windows: env\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
   ```bash
   cp .env.example .env
   ```
   Open the newly created `.env` file and edit it to input:
   * Your database connection details (PostgreSQL/MySQL `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`).
   * Optional SMTP details (`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`).
   * A secure Django `SECRET_KEY`.

5. Apply the database migrations:
   ```bash
   python manage.py migrate
   ```

6. Register initial administrator and organization:
   ```bash
   ASSETO_ADMIN_PASSWORD="YourSecret123" python manage.py user_register --fullname "John Doe" --email john.doe@example.com --username john --phone "+919876543210" --company_name "Acme Corp" --company_website "acme.com"
   ```
   The password is read from the `ASSETO_ADMIN_PASSWORD` environment variable (or `--password`, not recommended since it's visible in the process list).

7. Start the local development server:
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to `http://127.0.0.1:8000`.

---

## Post-Setup Configurations

### Registering Administrator Accounts via CLI
You can register new administrator user accounts and organizations at any time using the Django management command:

* **For Docker Setup**:
  ```bash
  docker compose exec -T -e ASSETO_ADMIN_PASSWORD="YourSecret123" web python manage.py user_register \
    --fullname "John Doe" \
    --email john.doe@example.com \
    --username john \
    --phone "+919876543210" \
    --company_name "Acme Corp" \
    --company_website "acme.com"
  ```
* **For Manual Setup**:
  ```bash
  ASSETO_ADMIN_PASSWORD="YourSecret123" python manage.py user_register \
    --fullname "John Doe" \
    --email john.doe@example.com \
    --username john \
    --phone "+919876543210" \
    --company_name "Acme Corp" \
    --company_website "acme.com"
  ```

### Connecting Google Cloud (Firebase Push Notifications)

Push notifications (browser + mobile) are delivered via Firebase Cloud
Messaging. Asseto does **not** ship with a hardcoded Firebase project —
each installation connects its own, once, via an in-app OAuth flow. Nothing
below is a code change; it's a one-time setup step per installation, done by
whoever administers this Asseto instance.

**Why this step exists**: Google's OAuth requires every application to
register its own OAuth client, pinned to the exact domain it's running on.
Since every self-hosted Asseto installation runs on a different domain, one
shared OAuth client checked into the repo can't work — this is the same
reason self-hosted Nextcloud, Mastodon, and similar open-source projects all
require an admin to create their own OAuth client rather than shipping one.

**Step 1 — Create a Google Cloud OAuth Client** (one-time, per installation):

1. Go to [console.cloud.google.com](https://console.cloud.google.com/) →
   **APIs & Services → Credentials → + Create Credentials → OAuth client ID**.
2. Application type: **Web application**.
3. Under **Authorized redirect URIs**, add exactly:
   ```
   https://<your-domain>/google-integration/oauth/callback/
   ```
   (use `http://127.0.0.1:8000/google-integration/oauth/callback/` for local/manual setup).
4. Click **Create** and copy the **Client ID** and **Client Secret** shown.
5. Go to the **OAuth consent screen** tab → **Test users** → add the Google
   account that will click "Connect" in step 2. This keeps the app in
   Google's "Testing" mode, which skips their formal verification review —
   fine for a single installation's own use.

**Step 2 — Add the credentials to `.env`:**

```bash
FERNET_KEY=<generate: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
GOOGLE_OAUTH_CLIENT_ID=<from step 1>
GOOGLE_OAUTH_CLIENT_SECRET=<from step 1>
GOOGLE_OAUTH_REDIRECT_URI=https://<your-domain>/google-integration/oauth/callback/
```

Restart the application after editing `.env` for the new values to take effect.

**Step 3 — Connect, in the app:**

1. Log in as a superuser.
2. Go to **Settings → Extensions**.
3. On the **Firebase** card, click **Connect**, and approve the Google
   consent screen using the account you added as a test user in step 1.
4. Asseto automatically creates a new Google Cloud project, enables Firebase
   on it, registers a web app, and generates a service account — all fields
   are stored encrypted in the database. No further manual Firebase console
   work is needed. The card shows **Connected ✓** with the created project ID
   once done.

**Who should perform step 3**: the Google account used to click Connect ends
up owning the resulting Firebase project (and any billing if usage ever
exceeds the free tier). If you're setting this up on behalf of a client, have
*them* log in with their own Google account for this one click — see the
[Post-Setup Configurations](#post-setup-configurations) note above; the
OAuth client from step 1 is app-level and can be created by whoever manages
hosting, but project ownership from step 3 should belong to whoever is
actually operating the instance.

### Managing the Application
For Docker deployments, use these standard commands to control the server:

* **View live logs**:
  ```bash
  docker compose logs -f
  ```
* **Shut down the server**:
  ```bash
  docker compose down
  ```
* **Start up the server**:
  ```bash
  docker compose up -d
  ```

---

## Troubleshooting

### Port 80 Already Occupied
If the setup script fails to free port `80` automatically (e.g. due to insufficient sudo privileges or system configuration locks), you can manually free the port:
* Identify what process is running on port 80:
  ```bash
  sudo ss -lptn 'sport = :80'
  # or
  sudo lsof -i :80
  ```
* Terminate the process (replace `PID` with the actual PID of the process):
  ```bash
  sudo kill -9 PID
  ```
* Or stop the service manually:
  ```bash
  sudo systemctl stop nginx
  # or
  sudo systemctl stop apache2
  ```

### Python Missing on Host
If the script fails to install Python automatically, install it manually:
* **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install python3.11 python3-pip -y
  ```
* **CentOS/RHEL/Fedora**:
  ```bash
  sudo dnf install python3.11 -y
  ```

### Docker Permissions
If you get permission denied errors related to Docker, ensure your current user is added to the `docker` group:
```bash
sudo usermod -aG docker $USER
```
*Note: Log out and log back in for group changes to take effect.*
