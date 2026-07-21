#!/usr/bin/env bash
# Creates the MySQL/MariaDB database and application user.
# Requires logging.sh sourced. Expects DB_NAME, DB_USERNAME, DB_PASSWORD to be set.

setup_database() {
    log_info "Configuring database..."

    local mysql_cmd=(mysql -u root)

    # Test passwordless root access (socket auth)
    if ! mysql -u root -e "SELECT 1;" >/dev/null 2>&1; then
        if [ -n "${MYSQL_ROOT_PASSWORD:-}" ]; then
            mysql_cmd=(mysql -u root -p"${MYSQL_ROOT_PASSWORD}")
        else
            echo -e "${BOLD}MySQL root user requires a password.${RESET}"
            read -r -s -p "Enter MySQL root password: " root_pass
            echo
            mysql_cmd=(mysql -u root -p"${root_pass}")
        fi

        if ! "${mysql_cmd[@]}" -e "SELECT 1;" >/dev/null 2>&1; then
            die "MySQL authentication failed with the provided root password."
        fi
    fi

    "${mysql_cmd[@]}" <<-SQL
		CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
		CREATE USER IF NOT EXISTS '${DB_USERNAME}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
		GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USERNAME}'@'localhost';
		FLUSH PRIVILEGES;
	SQL

    if [ $? -ne 0 ]; then
        die "Database setup failed. Ensure MySQL/MariaDB is running and root access is available."
    fi

    log_success "Database '$DB_NAME' and user '$DB_USERNAME' ready"
}
