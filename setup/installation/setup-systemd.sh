#!/usr/bin/env bash
# Renders and enables the systemd service for the Django app.
# Requires logging.sh sourced; ASSETO_HOME and port vars set.

ensure_asseto_user() {
    if ! id -u asseto >/dev/null 2>&1; then
        useradd --system --no-create-home --shell /usr/sbin/nologin asseto
        log_success "Created system user 'asseto'"
    fi
    chown -R asseto:asseto "$ASSETO_HOME"
}

setup_systemd() {
    log_info "Configuring systemd service..."

    ensure_asseto_user

    local template="$ASSETO_HOME/setup/templates/asseto-systemd.service"
    local dest="/etc/systemd/system/asseto.service"

    sed \
        -e "s#__ASSETO_HOME__#${ASSETO_HOME}#g" \
        -e "s#__DJANGO_PORT__#${DJANGO_PORT}#g" \
        "$template" > "$dest"

    systemctl daemon-reload
    systemctl enable asseto >>"$LOG_FILE" 2>&1
    systemctl restart asseto

    log_success "systemd service 'asseto' enabled and started"
}
