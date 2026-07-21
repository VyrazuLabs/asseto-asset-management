#!/usr/bin/env bash
# Renders and installs the Nginx reverse-proxy config.
# Requires logging.sh sourced; DOMAIN_NAME, ASSETO_HOME, port vars set.

setup_nginx() {
    log_info "Configuring Nginx..."

    local template="$ASSETO_HOME/setup/templates/nginx-asseto.conf"
    local dest="/etc/nginx/sites-available/asseto"

    sed \
        -e "s#__NGINX_HTTP_PORT__#${NGINX_HTTP_PORT}#g" \
        -e "s#__DOMAIN_NAME__#${DOMAIN_NAME}#g" \
        -e "s#__ASSETO_HOME__#${ASSETO_HOME}#g" \
        -e "s#__DJANGO_PORT__#${DJANGO_PORT}#g" \
        "$template" > "$dest"

    mkdir -p /etc/nginx/sites-enabled
    rm -f /etc/nginx/sites-enabled/default
    ln -sf "$dest" /etc/nginx/sites-enabled/asseto

    nginx -t >>"$LOG_FILE" 2>&1 || die "Nginx config test failed — check $LOG_FILE"
    if ! (systemctl reload nginx || systemctl restart nginx) >>"$LOG_FILE" 2>&1; then
        die "Nginx service failed to start. Port ${NGINX_HTTP_PORT} is likely in use by another service (e.g., Apache). Check 'sudo lsof -i :${NGINX_HTTP_PORT}' or stop the conflicting service, or set a custom port in setup/ports/custom.conf."
    fi

    log_success "Nginx configured and reloaded"
}
