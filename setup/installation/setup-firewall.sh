#!/usr/bin/env bash
# Opens required ports via the OS firewall. Requires logging.sh and detect-os.sh (PKG_MANAGER set).

setup_firewall() {
    log_info "Configuring firewall..."

    case "$PKG_MANAGER" in
        apt)
            if command -v ufw >/dev/null 2>&1; then
                ufw allow 22/tcp >>"$LOG_FILE" 2>&1
                ufw allow "${NGINX_HTTP_PORT}/tcp" >>"$LOG_FILE" 2>&1
                ufw allow "${NGINX_HTTPS_PORT}/tcp" >>"$LOG_FILE" 2>&1
                ufw --force enable >>"$LOG_FILE" 2>&1
                log_success "UFW rules applied (22, ${NGINX_HTTP_PORT}, ${NGINX_HTTPS_PORT})"
            else
                log_warn "ufw not found — skipping firewall configuration"
            fi
            ;;
        dnf|yum)
            if command -v firewall-cmd >/dev/null 2>&1; then
                systemctl enable --now firewalld >>"$LOG_FILE" 2>&1
                firewall-cmd --permanent --add-service=ssh >>"$LOG_FILE" 2>&1
                firewall-cmd --permanent --add-port="${NGINX_HTTP_PORT}/tcp" >>"$LOG_FILE" 2>&1
                firewall-cmd --permanent --add-port="${NGINX_HTTPS_PORT}/tcp" >>"$LOG_FILE" 2>&1
                firewall-cmd --reload >>"$LOG_FILE" 2>&1
                log_success "firewalld rules applied (ssh, ${NGINX_HTTP_PORT}, ${NGINX_HTTPS_PORT})"
            else
                log_warn "firewalld not found — skipping firewall configuration"
            fi
            ;;
    esac
}
