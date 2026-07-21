#!/usr/bin/env bash
# Safely removes an Asseto installation.
# Run as: sudo bash setup/uninstall.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETO_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
export ASSETO_HOME

. "$SCRIPT_DIR/installation/colors.sh"
. "$SCRIPT_DIR/installation/logging.sh"

stop_services() {
    for svc in asseto asseto-celery asseto-celery-beat; do
        systemctl stop "$svc" 2>/dev/null || true
        systemctl disable "$svc" 2>/dev/null || true
        rm -f "/etc/systemd/system/${svc}.service"
    done
    systemctl daemon-reload
    log_success "Stopped and removed systemd services"
}

remove_nginx() {
    rm -f /etc/nginx/sites-enabled/asseto /etc/nginx/sites-available/asseto
    nginx -t >>"$LOG_FILE" 2>&1 && systemctl reload nginx || true
    log_success "Removed Nginx config"
}

archive_app_dir() {
    local stamp
    stamp="$(date '+%Y%m%d-%H%M%S')"
    local archive_dir="$ASSETO_HOME/backups/uninstall-${stamp}"
    mkdir -p "$archive_dir"
    [ -f "$ASSETO_HOME/.env" ] && cp "$ASSETO_HOME/.env" "$archive_dir/.env"
    log_success "Archived .env to $archive_dir"
}

drop_database() {
    local db_name="$1"
    local mysql_cmd=(mysql -u root)

    if ! mysql -u root -e "SELECT 1;" >/dev/null 2>&1; then
        if [ -n "${MYSQL_ROOT_PASSWORD:-}" ]; then
            mysql_cmd=(mysql -u root -p"${MYSQL_ROOT_PASSWORD}")
        else
            read -r -s -p "Enter MySQL root password to drop database: " root_pass
            echo
            mysql_cmd=(mysql -u root -p"${root_pass}")
        fi
    fi

    "${mysql_cmd[@]}" -e "DROP DATABASE IF EXISTS \`${db_name}\`;" \
        || log_warn "Could not drop database ${db_name} — remove manually if needed"
    log_success "Dropped database ${db_name}"
}

main() {
    log_init
    echo -e "${YELLOW}${BOLD}Warning:${RESET} this will stop Asseto and remove its services/config."
    read -r -p "Continue? [y/N]: " confirm
    [ "$confirm" = "y" ] || [ "$confirm" = "Y" ] || { echo "Aborted."; exit 0; }

    echo "1) Remove app only (keep database for recovery)"
    echo "2) Full removal (delete database too)"
    read -r -p "Choose an option [1]: " mode
    mode="${mode:-1}"

    stop_services
    remove_nginx
    archive_app_dir

    if [ "$mode" = "2" ]; then
        local db_name="asseto"
        [ -f "$ASSETO_HOME/.env" ] && db_name="$(grep '^DB_NAME=' "$ASSETO_HOME/.env" | cut -d= -f2)"
        read -r -p "Type the database name to confirm deletion [${db_name}]: " confirm_db
        if [ "$confirm_db" = "$db_name" ]; then
            drop_database "$db_name"
        else
            log_warn "Database name did not match — skipping database deletion"
        fi
    fi

    log_success "Uninstall complete. Application files remain at $ASSETO_HOME (remove manually if no longer needed)."
}

main "$@"
