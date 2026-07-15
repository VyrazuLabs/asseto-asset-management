# FAQ

**Can I run the installer more than once?**
Yes. Re-running `setup/install.sh` on an existing install backs up the current `.env`, Nginx config, and systemd service to `/opt/asseto/backups/` before proceeding — see [`UPGRADE.md`](UPGRADE.md).

**Does the installer work on a server that already has Nginx or MySQL running?**
Yes, existing MySQL/MariaDB installs are reused. If Nginx is already serving another site on port 80/443, set a custom port first — see [`configuration.md`](configuration.md).

**Is Docker required?**
No. This installer targets bare-metal/VM deployments. A Docker Compose option is planned separately for containerized deployments.

**How do I enable HTTPS?**
Run `sudo bash setup/configure-ssl.sh` after the core install. It supports Let's Encrypt (public domains) or a self-signed certificate (local/testing).

**How do I enable background tasks / notifications?**
Run `sudo bash setup/configure-celery.sh` to set up Celery with Redis or RabbitMQ.

**Where are my credentials stored?**
In `.env` at the project root, permissions locked to `600` (owner read/write only).

**How do I completely remove Asseto?**
Run `sudo bash setup/uninstall.sh`. You'll be asked whether to keep or delete the database.

**What if I want to customize ports?**
Copy `setup/ports/custom.conf.example` to `setup/ports/custom.conf` and edit it before installing — see [`configuration.md`](configuration.md).
