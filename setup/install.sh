#!/usr/bin/env bash
# Asseto core installer — one-command setup on Ubuntu, Debian, RHEL, CentOS,
# AlmaLinux, and Rocky Linux. Run as: sudo bash setup/install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETO_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
export ASSETO_HOME

# shellcheck source=installation/colors.sh
. "$SCRIPT_DIR/installation/colors.sh"
# shellcheck source=installation/logging.sh
. "$SCRIPT_DIR/installation/logging.sh"
# shellcheck source=installation/backups.sh
. "$SCRIPT_DIR/installation/backups.sh"
# shellcheck source=installation/detect-os.sh
. "$SCRIPT_DIR/installation/detect-os.sh"
# shellcheck source=installation/check-prereqs.sh
. "$SCRIPT_DIR/installation/check-prereqs.sh"
# shellcheck source=installation/install-deps.sh
. "$SCRIPT_DIR/installation/install-deps.sh"
# shellcheck source=installation/setup-venv.sh
. "$SCRIPT_DIR/installation/setup-venv.sh"
# shellcheck source=installation/setup-db.sh
. "$SCRIPT_DIR/installation/setup-db.sh"
# shellcheck source=installation/setup-env.sh
. "$SCRIPT_DIR/installation/setup-env.sh"
# shellcheck source=installation/setup-nginx.sh
. "$SCRIPT_DIR/installation/setup-nginx.sh"
# shellcheck source=installation/setup-systemd.sh
. "$SCRIPT_DIR/installation/setup-systemd.sh"
# shellcheck source=installation/setup-firewall.sh
. "$SCRIPT_DIR/installation/setup-firewall.sh"
# shellcheck source=installation/validate.sh
. "$SCRIPT_DIR/installation/validate.sh"

# shellcheck source=ports/default.conf
. "$SCRIPT_DIR/ports/default.conf"
[ -f "$SCRIPT_DIR/ports/custom.conf" ] && . "$SCRIPT_DIR/ports/custom.conf"

trap 'log_error "Installation failed. See $LOG_FILE for details. Restore a prior backup from $ASSETO_HOME/backups/ if this was an upgrade."' ERR

main() {
    log_init
    echo -e "${BOLD}Asseto Asset Management — Installer${RESET}"
    echo

    check_prereqs
    detect_os

    local existing_install=false
    [ -f "$ASSETO_HOME/.env" ] && existing_install=true
    if [ "$existing_install" = true ]; then
        log_warn "Existing installation detected — backing up before proceeding"
        backup_existing_install >/dev/null
    fi

    install_system_deps
    setup_env
    setup_venv
    setup_database
    run_migrations_and_static
    setup_nginx
    setup_systemd
    setup_firewall
    validate_install

    echo
    log_success "Installation complete"
    echo -e "${BOLD}Access your instance at:${RESET} http://${DOMAIN_NAME}:${NGINX_HTTP_PORT}"
    echo -e "Create an admin user with:"
    echo -e "  ${ASSETO_HOME}/env/bin/python ${ASSETO_HOME}/manage.py createsuperuser"
    echo
    echo -e "Optional next steps:"
    echo -e "  sudo bash setup/configure-ssl.sh     # enable HTTPS"
    echo -e "  sudo bash setup/configure-celery.sh  # enable background tasks"
    echo -e "See setup/INSTALL.md for details."
}

main "$@"
