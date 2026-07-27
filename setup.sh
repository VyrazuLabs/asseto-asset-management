#!/bin/bash

# Colors for premium CLI presentation
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Clear the screen for the setup wizard
clear
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${CYAN}${BOLD}                 Asseto Asset Management - Setup Wizard               ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "This script will guide you through setting up and running Asseto in"
echo -e "a containerized Docker environment with an Nginx reverse proxy."
echo

# Step 1: Start Setup Script
echo -e "${GREEN}${BOLD}[Step 1] Setup script initialized.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Check Python installation
echo -e "${BOLD}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${YELLOW}Python is not installed. Attempting to install python3.11...${NC}"
    if command -v apt-get &> /dev/null; then
        echo -e "Using apt-get to install python3.11..."
        sudo apt-get update && sudo apt-get install -y python3.11
    elif command -v dnf &> /dev/null; then
        echo -e "Using dnf to install python3.11..."
        sudo dnf install -y python3.11
    elif command -v yum &> /dev/null; then
        echo -e "Using yum to install python3.11..."
        sudo yum install -y python3.11
    elif command -v pacman &> /dev/null; then
        echo -e "Using pacman to install python..."
        sudo pacman -Syu --noconfirm python
    else
        echo -e "${RED}Error: Package manager not recognized. Please install python3.11 manually.${NC}"
        exit 1
    fi

    # Re-verify installation
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        echo -e "${RED}Error: Failed to install Python. Please install python3.11 manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Python is already installed.${NC}"
fi
echo -e "----------------------------------------------------------------------"
sleep 1

# Check Port 80 configuration
echo -e "${BOLD}Checking if port 80 is occupied...${NC}"
PORT_80_PID=""
PORT_IN_USE=false

if command -v ss &> /dev/null; then
    PORT_80_PID=$(sudo ss -lptn 'sport = :80' 2>/dev/null | grep -oP 'pid=\K\d+' | head -n 1)
    if sudo ss -lptn 'sport = :80' 2>/dev/null | grep -q :80; then
        PORT_IN_USE=true
    fi
elif command -v lsof &> /dev/null; then
    PORT_80_PID=$(sudo lsof -t -i :80 2>/dev/null | head -n 1)
    if sudo lsof -i :80 &>/dev/null; then
        PORT_IN_USE=true
    fi
elif command -v netstat &> /dev/null; then
    PORT_80_PID=$(sudo netstat -lptn 2>/dev/null | grep :80 | awk '{print $7}' | cut -d'/' -f1 | head -n 1)
    if sudo netstat -lptn 2>/dev/null | grep -q :80; then
        PORT_IN_USE=true
    fi
else
    if timeout 1 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/80' 2>/dev/null; then
        PORT_IN_USE=true
    fi
fi

if [ "$PORT_IN_USE" = true ]; then
    echo -e "${YELLOW}Port 80 is currently occupied.${NC}"
    if [[ -n "$PORT_80_PID" ]]; then
        PROC_NAME=$(ps -p "$PORT_80_PID" -o comm= 2>/dev/null || echo "Unknown Process")
        echo -e "Occupying application: ${CYAN}$PROC_NAME (PID: $PORT_80_PID)${NC}"
        
        if [[ "$PROC_NAME" == *"nginx"* ]]; then
            echo -e "Stopping local nginx service..."
            sudo systemctl stop nginx 2>/dev/null || sudo service nginx stop 2>/dev/null || sudo kill "$PORT_80_PID"
        elif [[ "$PROC_NAME" == *"apache"* || "$PROC_NAME" == *"httpd"* ]]; then
            echo -e "Stopping local Apache service..."
            sudo systemctl stop apache2 2>/dev/null || sudo service apache2 stop 2>/dev/null || sudo systemctl stop httpd 2>/dev/null || sudo service httpd stop 2>/dev/null || sudo kill "$PORT_80_PID"
        else
            echo -e "Stopping process $PROC_NAME (PID: $PORT_80_PID)..."
            sudo kill "$PORT_80_PID"
            sleep 1
            if ps -p "$PORT_80_PID" &> /dev/null; then
                echo -e "${YELLOW}Process did not stop, forcing termination...${NC}"
                sudo kill -9 "$PORT_80_PID"
            fi
        fi
    else
        echo -e "Attempting to stop common web services on port 80..."
        sudo systemctl stop nginx 2>/dev/null || sudo service nginx stop 2>/dev/null
        sudo systemctl stop apache2 2>/dev/null || sudo service apache2 stop 2>/dev/null
        sudo systemctl stop httpd 2>/dev/null || sudo service httpd stop 2>/dev/null
        
        if command -v fuser &> /dev/null; then
            sudo fuser -k 80/tcp &>/dev/null
        fi
    fi
    
    sleep 2
    PORT_STILL_IN_USE=false
    if command -v ss &> /dev/null; then
        if sudo ss -lptn 'sport = :80' 2>/dev/null | grep -q :80; then
            PORT_STILL_IN_USE=true
        fi
    elif command -v lsof &> /dev/null; then
        if sudo lsof -i :80 &>/dev/null; then
            PORT_STILL_IN_USE=true
        fi
    fi
    
    if [ "$PORT_STILL_IN_USE" = true ]; then
        echo -e "${RED}Error: Failed to free port 80 automatically.${NC}"
        echo -e "Please stop the application using port 80 manually and run setup again."
        exit 1
    else
        echo -e "${GREEN}✓ Port 80 has been freed successfully.${NC}"
    fi
else
    echo -e "${GREEN}✓ Port 80 is free.${NC}"
fi

# Step 2: Choose Database
echo -e "${BOLD}[Step 2] Choose Database Engine:${NC}"
echo -e "  1) PostgreSQL (Recommended)"
echo -e "  2) MySQL"
echo
read -p "Select database option (1 or 2) [1]: " DB_CHOICE
DB_CHOICE=${DB_CHOICE:-1}

while [[ "$DB_CHOICE" != "1" && "$DB_CHOICE" != "2" ]]; do
    echo -e "${RED}Invalid option. Please choose 1 or 2.${NC}"
    read -p "Select database option (1 or 2) [1]: " DB_CHOICE
    DB_CHOICE=${DB_CHOICE:-1}
done

if [[ "$DB_CHOICE" == "1" ]]; then
    DB_ENGINE="django.db.backends.postgresql"
    DB_PORT="5432"
    DB_IMAGE="postgres:15-alpine"
    DB_TYPE="PostgreSQL"
else
    DB_ENGINE="django.db.backends.mysql"
    DB_PORT="3306"
    DB_IMAGE="mysql:8.0"
    DB_TYPE="MySQL"
fi
echo -e "\n${GREEN}✓ Selected database engine: $DB_TYPE${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 3: Populate .env
echo -e "${BOLD}[Step 3] Populate Environment Configurations (.env):${NC}"
echo -e "Enter details to configure the database credentials. Press [Enter] to use defaults."
echo

read -p "Database Name [asseto]: " USER_DB_NAME
DB_NAME=${USER_DB_NAME:-asseto}

read -p "Database Username [asseto_user]: " USER_DB_USER
DB_USER=${USER_DB_USER:-asseto_user}

# Generate a random password for security if none is specified
RANDOM_PASS=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 16 2>/dev/null || echo "AssetoSecurePass123")
read -s -p "Database Password [$RANDOM_PASS]: " USER_DB_PASS
echo ""
DB_PASSWORD=${USER_DB_PASS:-$RANDOM_PASS}

# Optional SMTP configuration
echo -e "\n${YELLOW}${BOLD}Give SMTP credentials now or give inside .env later${NC}"
read -p "EMAIL_HOST: " EMAIL_HOST
read -p "EMAIL_HOST_USER: " EMAIL_HOST_USER
read -s -p "EMAIL_HOST_PASSWORD: " EMAIL_HOST_PASSWORD
echo ""
read -p "EMAIL_PORT: " EMAIL_PORT

# Django SECRET_KEY generation
SECRET_KEY_GEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 50 2>/dev/null || echo "unsafe-secret-key-for-asseto-asset-management")

# Write .env file
echo -e "\nGenerating .env configuration file..."
cat << EOF > .env
SECRET_KEY="$SECRET_KEY_GEN"
FIREBASE_APPLICATION_CREDENTIALS_FILE_DIRECTORY=

EMAIL_HOST="$EMAIL_HOST"
EMAIL_HOST_USER="$EMAIL_HOST_USER"
EMAIL_HOST_PASSWORD="$EMAIL_HOST_PASSWORD"
EMAIL_PORT="$EMAIL_PORT"

DB_ENGINE="$DB_ENGINE"
DB_NAME="$DB_NAME"
DB_USERNAME="$DB_USER"
DB_PASSWORD="$DB_PASSWORD"
DB_HOST="db"
DB_PORT="$DB_PORT"

ALLOWED_HOSTS="*"
CSRF_TRUSTED_ORIGINS="http://localhost,http://127.0.0.1"
EOF

echo -e "${GREEN}✓ .env file generated successfully.${NC}"

# Generate corresponding docker-compose.yml file
echo -e "Generating docker-compose.yml configuration..."
if [[ "$DB_CHOICE" == "1" ]]; then
    # PostgreSQL docker-compose
    cat << EOF > docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn AssetManagement.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - django-static:/app/staticfiles
      - django-media:/app/media
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: $DB_NAME
      POSTGRES_USER: $DB_USER
      POSTGRES_PASSWORD: $DB_PASSWORD
    volumes:
      - pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $DB_USER -d $DB_NAME"]
      interval: 5s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - django-static:/app/staticfiles:ro
      - django-media:/app/media:ro
    depends_on:
      - web

volumes:
  django-static:
  django-media:
  pg-data:
EOF
else
    # MySQL docker-compose
    cat << EOF > docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn AssetManagement.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - django-static:/app/staticfiles
      - django-media:/app/media
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

  db:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_DATABASE: $DB_NAME
      MYSQL_USER: $DB_USER
      MYSQL_PASSWORD: $DB_PASSWORD
      MYSQL_RANDOM_ROOT_PASSWORD: 'yes'
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h localhost -u $DB_USER --password=$DB_PASSWORD || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - django-static:/app/staticfiles:ro
      - django-media:/app/media:ro
    depends_on:
      - web

volumes:
  django-static:
  django-media:
  mysql-data:
EOF
fi

echo -e "${GREEN}✓ docker-compose.yml generated successfully.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 4: Check Docker Installation
echo -e "${BOLD}[Step 4] Checking Docker Installation...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Error: Docker is not installed on this host.${NC}"
    echo -e "Please install Docker (https://docs.docker.com/get-docker/) and run setup again."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Error: Docker Compose is not installed on this host.${NC}"
        echo -e "Please install the Docker Compose plugin or standalone package and run setup again."
        exit 1
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Verify if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Error: Docker daemon is not running.${NC}"
    echo -e "Please start the Docker daemon (e.g. 'sudo systemctl start docker') and run setup again."
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose ($DOCKER_COMPOSE_CMD) are active and ready.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 5: Configure Firewall (Optional)
echo -e "${BOLD}[Step 5] Configure Firewall (Optional):${NC}"
if command -v ufw &> /dev/null; then
    read -p "UFW Firewall detected. Do you want to allow incoming HTTP traffic on port 80? (y/N): " UFW_CHOICE
    if [[ "$UFW_CHOICE" =~ ^[Yy]$ ]]; then
        echo -e "Opening port 80/tcp..."
        sudo ufw allow 80/tcp
        echo -e "${GREEN}✓ Firewall rules updated.${NC}"
    else
        echo -e "Skipping firewall configuration."
    fi
else
    echo -e "No UFW firewall detected. Skipping firewall configuration."
fi
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 6: docker compose up -d (Build web image, Pull DB and Nginx images)
echo -e "${BOLD}[Step 6] Building Web Image and Pulling Database & Nginx Images...${NC}"
echo -e "This builds the local 'web' container and downloads official Nginx & $DB_TYPE images."
echo -e "Executing: $DOCKER_COMPOSE_CMD up -d --build"
echo -e "Installing Python dependencies from requirements.txt inside the container image..."
echo

$DOCKER_COMPOSE_CMD up -d --build
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Docker Compose failed to build or download images.${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✓ Web image built and base images pulled successfully.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 7: Create containers
echo -e "${BOLD}[Step 7] Instantiating and Creating Containers...${NC}"
echo -n "Waiting for database and web services to initialize..."

MAX_ATTEMPTS=45
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    # Check if the web container is fully initialized and Gunicorn is up
    STATUS=$($DOCKER_COMPOSE_CMD ps web --format "{{.State}}" 2>/dev/null || $DOCKER_COMPOSE_CMD ps web | grep -o "Up" | head -n 1)
    if [[ "$STATUS" == *"running"* || "$STATUS" == *"Up"* ]]; then
        break
    fi
    echo -n "."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo
    echo -e "${RED}✗ Error: Containers took too long to start. Please check 'docker compose logs'.${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✓ Containers created and running successfully.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 8: Run migrations
echo -e "${BOLD}[Step 8] Running Database Migrations...${NC}"
echo -e "Executing: $DOCKER_COMPOSE_CMD exec web python manage.py migrate"
echo

$DOCKER_COMPOSE_CMD exec -T web python manage.py migrate
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Database migrations failed to run.${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✓ Database migrations completed successfully.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 9: Collect static files
echo -e "${BOLD}[Step 9] Collecting Static Assets...${NC}"
echo -e "Executing: $DOCKER_COMPOSE_CMD exec web python manage.py collectstatic --noinput"
echo

$DOCKER_COMPOSE_CMD exec -T web python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Static asset collection failed.${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✓ Static files collected successfully.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 10: Register User Account
echo -e "${BOLD}[Step 10] Register Administrator Account...${NC}"
echo -e "Please provide user and company details. All fields are required."
echo

prompt_required() {
    local prompt_text="$1"
    local var_name="$2"
    local is_secret="${3:-false}"
    local val=""

    while true; do
        if [ "$is_secret" = "true" ]; then
            read -s -p "$prompt_text" val
            echo ""
        else
            read -p "$prompt_text" val
        fi

        val=$(echo "$val" | xargs)

        if [ -n "$val" ]; then
            eval "$var_name=\"\$val\""
            break
        else
            echo -e "${RED}Error: This field is required. Please enter a value.${NC}"
        fi
    done
}

while true; do
    echo -e "${CYAN}--- Enter User Details ---${NC}"
    prompt_required "Full Name: " REG_FULLNAME
    prompt_required "Email Address: " REG_EMAIL
    prompt_required "Username: " REG_USERNAME
    prompt_required "Phone Number: " REG_PHONE

    while true; do
        prompt_required "Password: " REG_PASSWORD "true"
        prompt_required "Confirm Password: " REG_PASSWORD_CONFIRM "true"

        if [ "$REG_PASSWORD" = "$REG_PASSWORD_CONFIRM" ]; then
            break
        else
            echo -e "${RED}Error: Passwords do not match. Please try again.${NC}\n"
        fi
    done

    prompt_required "Company Name: " REG_COMPANY_NAME
    prompt_required "Company Website: " REG_COMPANY_WEBSITE

    echo -e "\nRegistering user..."
    if $DOCKER_COMPOSE_CMD exec -T web python manage.py user_register \
        --fullname "$REG_FULLNAME" \
        --email "$REG_EMAIL" \
        --username "$REG_USERNAME" \
        --phone "$REG_PHONE" \
        --password "$REG_PASSWORD" \
        --company_name "$REG_COMPANY_NAME" \
        --company_website "$REG_COMPANY_WEBSITE"; then
        break
    else
        echo -e "\n${RED}User already exists or registration failed. Please re-enter user details.${NC}\n"
    fi
done

echo
echo -e "${GREEN}✓ User account registered successfully.${NC}"
echo -e "----------------------------------------------------------------------"
sleep 1

# Step 11: Setup Complete
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}             [Step 11] Application is ready for use!                 ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo
echo -e "Asseto Asset Management has been successfully configured and started."
echo -e "  Link: ${CYAN}${BOLD}http://localhost${NC}"
echo
echo -e "To manage your Asseto server, use the following commands:"
echo -e "  - View live logs: ${BOLD}$DOCKER_COMPOSE_CMD logs -f${NC}"
echo -e "  - Shut down server: ${BOLD}$DOCKER_COMPOSE_CMD down${NC}"
echo -e "  - Spin up server:  ${BOLD}$DOCKER_COMPOSE_CMD up -d${NC}"
echo -e "======================================================================"
echo


