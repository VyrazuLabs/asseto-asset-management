#!/usr/bin/env bash
# Detects OS family and package manager. Sets OS_ID, OS_VERSION_ID, PKG_MANAGER.
# Requires logging.sh sourced first.

detect_os() {
    [ -f /etc/os-release ] || die "Cannot detect OS: /etc/os-release not found"

    # shellcheck source=/dev/null
    . /etc/os-release
    OS_ID="$ID"
    OS_VERSION_ID="$VERSION_ID"

    case "$OS_ID" in
        ubuntu|debian)
            PKG_MANAGER="apt"
            ;;
        rhel|centos|almalinux|rocky)
            PKG_MANAGER="yum"
            command -v dnf >/dev/null 2>&1 && PKG_MANAGER="dnf"
            ;;
        *)
            die "Unsupported OS: $OS_ID. Asseto installer supports Ubuntu, Debian, RHEL, CentOS, AlmaLinux, and Rocky Linux."
            ;;
    esac

    log_success "Detected OS: $OS_ID $OS_VERSION_ID (package manager: $PKG_MANAGER)"
}
