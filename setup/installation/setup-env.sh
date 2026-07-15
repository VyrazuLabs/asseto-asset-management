#!/usr/bin/env bash
# Interactively generates the .env file, offering a suggested default for each
# value that the user can accept with Enter or override by typing a new one.
# Requires logging.sh sourced and ASSETO_HOME set.

# prompt_value <var_name> <prompt_label> <suggested_default> [secret]
prompt_value() {
    local var_name="$1"
    local label="$2"
    local suggested="$3"
    local secret="${4:-}"
    local input=""

    if [ "$secret" = "secret" ]; then
        read -r -s -p "$label [$suggested]: " input
        echo
    else
        read -r -p "$label [$suggested]: " input
    fi

    if [ -z "$input" ]; then
        input="$suggested"
    fi

    printf -v "$var_name" '%s' "$input"
}

generate_secret() {
    openssl rand -base64 32 | tr -d '\n=+/' | cut -c1-40
}

setup_env() {
    log_info "Configuring environment (press Enter to accept the suggested value)..."

    local suggested_domain="${DOMAIN_NAME:-localhost}"
    prompt_value DOMAIN_NAME "Domain name" "$suggested_domain"

    local suggested_email="admin@${DOMAIN_NAME}"
    prompt_value ADMIN_EMAIL "Admin email" "$suggested_email"

    DB_NAME="asseto"
    DB_USERNAME="asseto"
    local suggested_db_password
    suggested_db_password="$(generate_secret)"
    prompt_value DB_PASSWORD "Database password" "$suggested_db_password" secret

    local suggested_secret_key
    suggested_secret_key="$(generate_secret)"
    SECRET_KEY="$suggested_secret_key"

    # shellcheck source=/dev/null
    . "$(dirname "${BASH_SOURCE[0]}")/../ports/default.conf"
    [ -f "$(dirname "${BASH_SOURCE[0]}")/../ports/custom.conf" ] && \
        . "$(dirname "${BASH_SOURCE[0]}")/../ports/custom.conf"

    cat > "$ASSETO_HOME/.env" <<-ENV
		SECRET_KEY=${SECRET_KEY}
		FIREBASE_APPLICATION_CREDENTIALS_FILE_DIRECTORY=

		EMAIL_HOST=
		EMAIL_HOST_USER=
		EMAIL_HOST_PASSWORD=
		EMAIL_PORT=

		DB_ENGINE=django.db.backends.mysql
		DB_NAME=${DB_NAME}
		DB_USERNAME=${DB_USERNAME}
		DB_PASSWORD=${DB_PASSWORD}
		DB_HOST=localhost
		DB_PORT=${MYSQL_PORT}

		ALLOWED_HOSTS=${DOMAIN_NAME}
		CSRF_TRUSTED_ORIGINS=https://${DOMAIN_NAME}
	ENV

    chmod 600 "$ASSETO_HOME/.env"
    log_success ".env generated at $ASSETO_HOME/.env (permissions set to 600)"
}
