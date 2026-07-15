#!/usr/bin/env bash
# Installs system-level dependencies via the OS package manager.
# Requires detect-os.sh sourced and detect_os already run (PKG_MANAGER set).

install_system_deps() {
    log_info "Installing system dependencies via $PKG_MANAGER..."

    case "$PKG_MANAGER" in
        apt)
            export DEBIAN_FRONTEND=noninteractive
            apt-get update -y >>"$LOG_FILE" 2>&1
            apt-get install -y \
                build-essential \
                python3-venv \
                python3-dev \
                default-libmysqlclient-dev \
                pkg-config \
                mysql-server \
                nginx \
                git \
                curl \
                openssl \
                ufw >>"$LOG_FILE" 2>&1
            ;;
        dnf|yum)
            "$PKG_MANAGER" install -y \
                gcc \
                python3-devel \
                mysql-devel \
                mariadb-server \
                nginx \
                git \
                curl \
                openssl \
                firewalld >>"$LOG_FILE" 2>&1
            systemctl enable --now mariadb >>"$LOG_FILE" 2>&1
            ;;
        *)
            die "Unsupported package manager: $PKG_MANAGER"
            ;;
    esac

    log_success "System dependencies installed"
}
