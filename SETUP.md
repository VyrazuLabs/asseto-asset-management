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
1. **Verifies Python on Host**: Generates the Django `SECRET_KEY`. If Python is missing, the script attempts to install `python3.11` using the system's package manager (`apt-get`, `dnf`, `yum`, or `pacman`).
2. **Checks Port 80**: Checks if the default port `80` (used by Nginx) is occupied. If another application (like a local Nginx, Apache, or custom server) is using it, the script attempts to stop or terminate that application first.
3. **Database Selection**: Guides you through choosing between **PostgreSQL** (recommended) or **MySQL**.
4. **Environment Generation**: Automatically populates a `.env` file and creates a corresponding `docker-compose.yml` tailored to your choices.
5. **Verifies Docker**: Assures the Docker daemon and Docker Compose are installed and running.
6. **Builds & Launches Containers**: Downloads required base images (Nginx, database) and builds the Django web app container.
7. **Runs Migrations & Asset Collection**: Automatically executes Django migrations and collects static assets.

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
   * Input custom database name, username, and password, or press `Enter` to use the secure defaults.
   * If prompted, opt to configure your UFW firewall rules to allow incoming HTTP traffic.

5. Open your browser and navigate to `http://localhost` to view the Asseto dashboard.

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
   * A secure Django `SECRET_KEY`.

5. Apply the database migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the local development server:
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to `http://127.0.0.1:8000`.

---

## Post-Setup Configurations

### Creating an Administrator Account
To access administrative sections and customize settings, create a superuser:

* **For Docker Setup**:
  ```bash
  docker compose exec -it web python manage.py createsuperuser
  ```
* **For Manual Setup**:
  ```bash
  python manage.py createsuperuser
  ```

Follow the prompts to enter a username, email address, and a secure password.

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
