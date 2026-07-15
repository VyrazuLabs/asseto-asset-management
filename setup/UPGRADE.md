# Upgrading

To upgrade an existing installation to a newer version of Asseto:

```bash
cd asseto-asset-management
git pull
sudo bash setup/install.sh
```

The installer detects the existing `.env` and:

1. Backs up the current `.env`, Nginx config, and systemd service to `/opt/asseto/backups/pre-install-<timestamp>/`
2. Re-prompts for configuration (press Enter to keep your existing values as the suggested default)
3. Reinstalls Python dependencies from the updated `requirements.txt`
4. Runs any new migrations
5. Recollects static files
6. Restarts the `asseto` systemd service

Your database and uploaded media are never touched by the installer — only application code, dependencies, and service configuration are updated.

## Rolling Back

If an upgrade causes problems, restore the previous configuration from the backup directory:

```bash
ls /opt/asseto/backups/
cp /opt/asseto/backups/pre-install-<timestamp>/.env /opt/asseto/.env
sudo systemctl restart asseto
```

For a database rollback, restore from your own MySQL backup — the installer does not back up database contents, only configuration files.
