#!/usr/bin/env bash
# Optional Celery worker/beat setup for an existing Asseto install.
# Run as: sudo bash setup/configure-celery.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETO_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
export ASSETO_HOME

. "$SCRIPT_DIR/installation/colors.sh"
. "$SCRIPT_DIR/installation/logging.sh"
. "$SCRIPT_DIR/installation/detect-os.sh"

install_broker() {
    local broker="$1"
    case "$broker" in
        redis)
            case "$PKG_MANAGER" in
                apt) apt-get install -y redis-server >>"$LOG_FILE" 2>&1; systemctl enable --now redis-server ;;
                dnf|yum) "$PKG_MANAGER" install -y redis >>"$LOG_FILE" 2>&1; systemctl enable --now redis ;;
            esac
            echo "redis://localhost:6379/0"
            ;;
        rabbitmq)
            case "$PKG_MANAGER" in
                apt) apt-get install -y rabbitmq-server >>"$LOG_FILE" 2>&1 ;;
                dnf|yum) "$PKG_MANAGER" install -y rabbitmq-server >>"$LOG_FILE" 2>&1 ;;
            esac
            systemctl enable --now rabbitmq-server
            echo "amqp://guest:guest@localhost:5672//"
            ;;
        *)
            die "Unknown broker: $broker"
            ;;
    esac
}

write_service() {
    local name="$1" desc="$2" cmd="$3"
    cat > "/etc/systemd/system/${name}.service" <<-EOF
		[Unit]
		Description=${desc}
		After=network.target asseto.service

		[Service]
		User=asseto
		Group=asseto
		WorkingDirectory=${ASSETO_HOME}
		EnvironmentFile=${ASSETO_HOME}/.env
		ExecStart=${cmd}
		Restart=on-failure
		RestartSec=5

		[Install]
		WantedBy=multi-user.target
	EOF
}

main() {
    log_init
    [ -f "$ASSETO_HOME/.env" ] || die "No .env found — run setup/install.sh first"
    detect_os

    echo "1) Redis (recommended)"
    echo "2) RabbitMQ"
    read -r -p "Choose a message broker [1]: " choice
    choice="${choice:-1}"

    local broker_name broker_url
    case "$choice" in
        1) broker_name="redis"; broker_url="$(install_broker redis)" ;;
        2) broker_name="rabbitmq"; broker_url="$(install_broker rabbitmq)" ;;
        *) die "Invalid option" ;;
    esac

    if ! grep -q '^CELERY_BROKER_URL=' "$ASSETO_HOME/.env"; then
        echo "CELERY_BROKER_URL=${broker_url}" >> "$ASSETO_HOME/.env"
    else
        sed -i "s#^CELERY_BROKER_URL=.*#CELERY_BROKER_URL=${broker_url}#" "$ASSETO_HOME/.env"
    fi

    write_service "asseto-celery" "Asseto Celery Worker" \
        "${ASSETO_HOME}/env/bin/celery -A AssetManagement worker --loglevel=info"
    write_service "asseto-celery-beat" "Asseto Celery Beat Scheduler" \
        "${ASSETO_HOME}/env/bin/celery -A AssetManagement beat --loglevel=info"

    systemctl daemon-reload
    systemctl enable --now asseto-celery asseto-celery-beat

    log_success "Celery configured with $broker_name broker; asseto-celery and asseto-celery-beat services running"
}

main "$@"
