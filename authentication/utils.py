from django.db.utils import ConnectionHandler
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from dotenv import load_dotenv, set_key
import os


def create_db_connection(request, db_data):
    env_path = settings.BASE_DIR / ".env"

    # Step 1: Save new DB credentials to .env
    for key, value in db_data.items():
        set_key(env_path, key, value)

    # Step 2: Reload environment variables
    load_dotenv(env_path, override=True)

    # Step 3: Build fresh DATABASE config (stand-alone dict)
    new_config = {
        "default": {
            "ENGINE": os.environ.get("DB_ENGINE"),
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT"),
            "TEST": {"NAME": "test_asseto"},
        }
    }

    print("✅ New config ready:", new_config)

    # Step 4: Replace settings.DATABASES completely
    settings.DATABASES = new_config

    # Step 5: Create a new connection handler using the raw dict (NOT global settings)
    new_connections = ConnectionHandler(new_config)

    # Step 6: Replace Django’s global connection registry
    connections._connections = new_connections._connections

    # Step 7: Test connection
    try:
        conn = new_connections["default"]
        conn.ensure_connection()
        print("✅ Database connection successful!")

        # Step 8: Apply migrations
        call_command("migrate", interactive=False, verbosity=1)
        print("✅ Migrations completed!")
        return True

    except Exception as e:
        print("❌ Database connection failed:", e)
        return False
