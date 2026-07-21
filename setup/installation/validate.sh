#!/usr/bin/env bash
# Post-install health checks. Requires logging.sh sourced; ASSETO_HOME and DOMAIN_NAME set.

run_migrations_and_static() {
    log_info "Running migrations and collecting static files..."
    "$ASSETO_HOME/env/bin/python" "$ASSETO_HOME/manage.py" migrate --noinput >>"$LOG_FILE" 2>&1 \
        || die "Migrations failed — check $LOG_FILE"
    "$ASSETO_HOME/env/bin/python" "$ASSETO_HOME/manage.py" collectstatic --noinput >>"$LOG_FILE" 2>&1 \
        || die "collectstatic failed — check $LOG_FILE"
    log_success "Migrations applied and static files collected"
}

validate_install() {
    log_info "Validating installation..."

    systemctl is-active --quiet asseto || die "asseto systemd service is not running — check: journalctl -u asseto"
    log_success "asseto service is active"

    local http_code
    http_code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${NGINX_HTTP_PORT}/" || echo "000")"
    if [ "$http_code" = "000" ]; then
        log_warn "Could not reach app over HTTP yet — it may need a moment to start"
    else
        log_success "App responded with HTTP $http_code"
    fi
}
