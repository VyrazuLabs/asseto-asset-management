# Installing Asseto

One-command installation for Ubuntu, Debian, RHEL, CentOS, AlmaLinux, and Rocky Linux.

## Prerequisites

- A fresh or existing Linux VM (2GB+ RAM, 10GB+ disk recommended)
- Root or sudo access
- Internet access (to install packages and Python dependencies)

You do **not** need to pre-install Python, MySQL, or Nginx — the installer handles this.

## Quick Start

```bash
git clone https://github.com/VyrazuLabs/asseto-asset-management.git
cd asseto-asset-management
sudo bash setup/install.sh
```

You'll be prompted for a few values. Press Enter to accept the suggested default, or type your own:

```
Domain name [localhost]:
Admin email [admin@localhost]:
Database password [a1B2c3D4...]:
```

Everything else (SECRET_KEY, database name/user, Nginx, systemd service, firewall rules) is configured automatically.

## What the Installer Does

1. Detects your OS and package manager (apt / dnf / yum)
2. Installs system dependencies (Python, MySQL, Nginx, build tools)
3. Creates a Python virtual environment and installs app dependencies
4. Generates `.env` with your answers plus auto-generated secrets
5. Creates the database and database user
6. Runs migrations and collects static files
7. Configures Nginx as a reverse proxy
8. Creates and starts a systemd service (`asseto`) with auto-restart
9. Opens the required firewall ports
10. Verifies the app is reachable

## After Installation

Access your instance at `http://<your-domain>`.

Create an admin account:

```bash
/opt/asseto/env/bin/python /opt/asseto/manage.py createsuperuser
```

Check service status:

```bash
systemctl status asseto
```

## Optional Features

Enable HTTPS:

```bash
sudo bash setup/configure-ssl.sh
```

Enable background tasks (Celery):

```bash
sudo bash setup/configure-celery.sh
```

See [`configuration.md`](configuration.md) for port customization, [`TROUBLESHOOT.md`](TROUBLESHOOT.md) for common issues, and [`UPGRADE.md`](UPGRADE.md) for upgrading an existing install.

## Removing Asseto

```bash
sudo bash setup/uninstall.sh
```
