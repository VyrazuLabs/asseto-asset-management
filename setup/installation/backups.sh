#!/usr/bin/env bash
# Backup/restore helpers for the Asseto installer. Requires logging.sh sourced first.

ASSETO_HOME="${ASSETO_HOME:-/opt/asseto}"
BACKUP_DIR="$ASSETO_HOME/backups"

backup_existing_install() {
    if [ ! -d "$ASSETO_HOME" ]; then
        return 0
    fi

    local stamp
    stamp="$(date '+%Y%m%d-%H%M%S')"
    local dest="$BACKUP_DIR/pre-install-$stamp"

    mkdir -p "$dest"
    [ -f "$ASSETO_HOME/.env" ] && cp "$ASSETO_HOME/.env" "$dest/.env"
    [ -f /etc/nginx/sites-available/asseto ] && cp /etc/nginx/sites-available/asseto "$dest/nginx-asseto.conf"
    [ -f /etc/systemd/system/asseto.service ] && cp /etc/systemd/system/asseto.service "$dest/asseto.service"

    log_success "Backed up existing config to $dest"
    echo "$dest"
}

restore_backup() {
    local backup_path="$1"
    [ -d "$backup_path" ] || die "Backup path not found: $backup_path"

    [ -f "$backup_path/.env" ] && cp "$backup_path/.env" "$ASSETO_HOME/.env"
    [ -f "$backup_path/nginx-asseto.conf" ] && cp "$backup_path/nginx-asseto.conf" /etc/nginx/sites-available/asseto
    [ -f "$backup_path/asseto.service" ] && cp "$backup_path/asseto.service" /etc/systemd/system/asseto.service

    log_warn "Restored config from $backup_path"
}
