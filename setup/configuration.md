# Configuration

## Customizing Ports

Default ports are defined in [`ports/default.conf`](ports/default.conf):

```
DJANGO_PORT=8000
MYSQL_PORT=3306
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
CELERY_FLOWER_PORT=5555
```

To override any of these, copy the example file and edit it **before** running the installer:

```bash
cp setup/ports/custom.conf.example setup/ports/custom.conf
nano setup/ports/custom.conf
```

`custom.conf` is git-ignored and machine-specific — it's automatically picked up by `install.sh`, `configure-ssl.sh`, and `configure-celery.sh` if present.

## Environment Variables

All runtime configuration lives in `.env` at the project root, generated interactively by `install.sh`. Key variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django cryptographic signing key (auto-generated) |
| `DB_ENGINE`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Database connection |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Set from the domain you provide |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT` | Outbound email (edit manually after install) |
| `FIREBASE_APPLICATION_CREDENTIALS_FILE_DIRECTORY` | Push notification credentials (edit manually if using Firebase) |
| `CELERY_BROKER_URL` | Set automatically by `configure-celery.sh` |

To change a value after install, edit `.env` directly and restart the service:

```bash
sudo systemctl restart asseto
```
