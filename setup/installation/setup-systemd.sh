#!/usr/bin/env bash
# Renders and enables the systemd service for the Django app.
# Requires logging.sh sourced; ASSETO_HOME and port vars set.

ensure_service_user() {
    if [[ "$ASSETO_HOME" == /home/* ]] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
        SERVICE_USER="$SUDO_USER"
        SERVICE_GROUP="$(id -gn "$SUDO_USER" 2>/dev/null || echo "$SUDO_USER")"
        chown -R "$SERVICE_USER:$SERVICE_GROUP" "$ASSETO_HOME"
    else
        SERVICE_USER="asseto"
        SERVICE_GROUP="asseto"
        if ! id -u asseto >/dev/null 2>&1; then
            useradd --system --no-create-home --shell /usr/sbin/nologin asseto
            log_success "Created system user 'asseto'"
        fi
        chown -R asseto:asseto "$ASSETO_HOME"
    fi

    local parent_dir="$ASSETO_HOME"
    while [ "$parent_dir" != "/" ] && [ "$parent_dir" != "." ]; do
        chmod o+x "$parent_dir" 2>/dev/null || true
        parent_dir="$(dirname "$parent_dir")"
    done
}

setup_systemd() {
    log_info "Configuring systemd service..."

    ensure_service_user

    local template="$ASSETO_HOME/setup/templates/asseto-systemd.service"
    local dest="/etc/systemd/system/asseto.service"

    sed \
        -e "s#__SERVICE_USER__#${SERVICE_USER}#g" \
        -e "s#__SERVICE_GROUP__#${SERVICE_GROUP}#g" \
        -e "s#__ASSETO_HOME__#${ASSETO_HOME}#g" \
        -e "s#__DJANGO_PORT__#${DJANGO_PORT}#g" \
        "$template" > "$dest"

    systemctl daemon-reload
    systemctl enable asseto >>"$LOG_FILE" 2>&1
    systemctl restart asseto

    log_success "systemd service 'asseto' enabled and started"
}
