#!/usr/bin/env bash
# Optional SSL/TLS setup for an existing Asseto install.
# Run as: sudo bash setup/configure-ssl.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETO_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
export ASSETO_HOME

. "$SCRIPT_DIR/installation/colors.sh"
. "$SCRIPT_DIR/installation/logging.sh"
. "$SCRIPT_DIR/installation/detect-os.sh"
. "$SCRIPT_DIR/ports/default.conf"
[ -f "$SCRIPT_DIR/ports/custom.conf" ] && . "$SCRIPT_DIR/ports/custom.conf"

NGINX_CONF="/etc/nginx/sites-available/asseto"

install_certbot() {
    case "$PKG_MANAGER" in
        apt) apt-get install -y certbot python3-certbot-nginx >>"$LOG_FILE" 2>&1 ;;
        dnf|yum) "$PKG_MANAGER" install -y certbot python3-certbot-nginx >>"$LOG_FILE" 2>&1 ;;
    esac
}

setup_letsencrypt() {
    local domain="$1"
    install_certbot
    certbot --nginx -d "$domain" --non-interactive --agree-tos -m "admin@${domain}" --redirect \
        || die "Let's Encrypt issuance failed — check DNS points to this server and port 80 is reachable"
    log_success "Let's Encrypt certificate installed for $domain (auto-renewal enabled via certbot timer)"
}

setup_selfsigned() {
    local domain="$1"
    local cert_dir="/etc/ssl/certs/asseto"
    mkdir -p "$cert_dir"

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$cert_dir/privkey.pem" \
        -out "$cert_dir/fullchain.pem" \
        -subj "/CN=${domain}" >>"$LOG_FILE" 2>&1

    sed -i "s#listen ${NGINX_HTTP_PORT};#listen ${NGINX_HTTP_PORT};\n    listen ${NGINX_HTTPS_PORT} ssl;\n    ssl_certificate ${cert_dir}/fullchain.pem;\n    ssl_certificate_key ${cert_dir}/privkey.pem;#" "$NGINX_CONF"
    nginx -t >>"$LOG_FILE" 2>&1 && systemctl reload nginx

    log_success "Self-signed certificate installed for $domain (browsers will show a warning — fine for testing)"
}

main() {
    log_init
    [ -f "$NGINX_CONF" ] || die "No existing Nginx config found — run setup/install.sh first"

    local domain
    domain="$(grep -oP 'server_name\s+\K[^;]+' "$NGINX_CONF" | head -1)"
    read -r -p "Domain to secure [$domain]: " input
    domain="${input:-$domain}"

    echo "1) Let's Encrypt (recommended, requires public DNS pointing to this server)"
    echo "2) Self-signed certificate (for local/testing use)"
    read -r -p "Choose an option [1]: " choice
    choice="${choice:-1}"

    case "$choice" in
        1) setup_letsencrypt "$domain" ;;
        2) setup_selfsigned "$domain" ;;
        *) die "Invalid option" ;;
    esac
}

main "$@"
