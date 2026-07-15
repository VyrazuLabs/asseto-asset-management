#!/usr/bin/env bash
# Validates prerequisites before installation proceeds.
# Requires logging.sh and detect-os.sh sourced first.

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "This installer must be run as root (use: sudo bash setup/install.sh)"
    fi
}

check_disk_space() {
    local available_kb
    available_kb="$(df -Pk . | awk 'NR==2 {print $4}')"
    local required_kb=$((1 * 1024 * 1024)) # 1GB

    if [ "$available_kb" -lt "$required_kb" ]; then
        die "At least 1GB free disk space is required (found $((available_kb / 1024))MB)"
    fi
    log_success "Disk space check passed"
}

check_required_tools() {
    local tool
    for tool in git curl openssl; do
        command -v "$tool" >/dev/null 2>&1 || die "Required tool '$tool' not found. Install it and re-run."
    done
    log_success "Required system tools present (git, curl, openssl)"
}

check_python() {
    local py_bin=""
    for candidate in python3.11 python3.12 python3.13 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            py_bin="$candidate"
            break
        fi
    done

    [ -n "$py_bin" ] || die "Python 3.11+ not found. Install Python 3.11 or newer and re-run."

    local version
    version="$("$py_bin" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    local major minor
    major="${version%%.*}"
    minor="${version##*.}"

    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
        die "Python 3.11+ required, found $version ($py_bin)"
    fi

    PYTHON_BIN="$py_bin"
    log_success "Python $version found at $(command -v "$py_bin")"
}

check_port_available() {
    local port="$1"
    local label="$2"

    if ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[.:]${port}\$"; then
        log_warn "Port $port ($label) is already in use — installer will prompt to change it or continue"
        return 1
    fi
    return 0
}

check_prereqs() {
    require_root
    check_disk_space
    check_required_tools
    check_python
    log_success "All prerequisite checks passed"
}
