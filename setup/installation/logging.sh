#!/usr/bin/env bash
# Logging helpers shared across setup scripts. Requires colors.sh sourced first.

LOG_FILE="${ASSETO_LOG_FILE:-/var/log/asseto-install.log}"

log_init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
}

log_line() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >>"$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${RESET} $*"
    log_line "[INFO] $*"
}

log_success() {
    echo -e "${GREEN}[ OK ]${RESET} $*"
    log_line "[OK] $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${RESET} $*"
    log_line "[WARN] $*"
}

log_error() {
    echo -e "${RED}[FAIL]${RESET} $*" >&2
    log_line "[FAIL] $*"
}

die() {
    log_error "$*"
    exit 1
}
