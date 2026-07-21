# Troubleshooting

All installer output is logged to `/var/log/asseto-install.log` — check it first for any failure.

## "Unsupported OS"

The installer supports Ubuntu, Debian, RHEL, CentOS, AlmaLinux, and Rocky Linux, detected via `/etc/os-release`. Other distributions aren't supported yet.

## "Python 3.11+ required"

Install Python 3.11 or newer for your distribution, then re-run `setup/install.sh`. On older RHEL/CentOS releases you may need the EPEL repository or a backport package.

## "Database setup failed"

Ensure MySQL/MariaDB is running:

```bash
systemctl status mysql    # or mariadb
```

Check that root access is available without a password prompt (the installer runs as root and connects via the local Unix socket). If your MySQL root user requires a password, set one up with socket auth or run `mysql_secure_installation` and update `setup/installation/setup-db.sh` accordingly.

## "Nginx config test failed"

Run `nginx -t` manually to see the exact syntax error. This usually means a port conflict — check `setup/configuration.md` to change the port in `setup/ports/custom.conf` and re-run the installer.

## Port already in use

If port 80 or 443 is taken by another web server, either stop that service or set a custom port in `setup/ports/custom.conf` before installing (see [`configuration.md`](configuration.md)).

## Service won't start

```bash
journalctl -u asseto -n 50 --no-pager
```

Common causes: `.env` missing a required value, database unreachable, or a migration failure. Re-run:

```bash
/opt/asseto/env/bin/python /opt/asseto/manage.py migrate
```

## Let's Encrypt fails in `configure-ssl.sh`

Let's Encrypt needs your domain's DNS A record pointing at this server's public IP, and port 80 reachable from the internet. Self-signed certificates (option 2) work without public DNS, for local/testing use.

## Starting over

If installation fails partway through, re-running `sudo bash setup/install.sh` is safe — it detects an existing install, backs up the current `.env`/Nginx/systemd config to `/opt/asseto/backups/`, and proceeds.
