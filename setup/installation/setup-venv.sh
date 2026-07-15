#!/usr/bin/env bash
# Creates the Python virtual environment and installs app dependencies.
# Requires check-prereqs.sh sourced (PYTHON_BIN set) and ASSETO_HOME set.

setup_venv() {
    log_info "Creating virtual environment..."
    "$PYTHON_BIN" -m venv "$ASSETO_HOME/env"

    log_info "Installing Python dependencies (this may take a few minutes)..."
    "$ASSETO_HOME/env/bin/pip" install --upgrade pip >>"$LOG_FILE" 2>&1
    "$ASSETO_HOME/env/bin/pip" install -r "$ASSETO_HOME/requirements.txt" >>"$LOG_FILE" 2>&1

    log_success "Virtual environment ready at $ASSETO_HOME/env"
}
