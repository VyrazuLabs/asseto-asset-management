import json
import os
from django.contrib import messages
from django.core.management import call_command
from django.db import connections
from django.shortcuts import redirect, render
from dotenv import load_dotenv, set_key
from AssetManagement import settings
from AssetManagement.settings import BASE_DIR


def create_db_connection(request,db_data):
    env_path = settings.BASE_DIR / '.env'

    for key, value in db_data.items():
        set_key(env_path,key,value)

    load_dotenv(env_path,override=True)

    settings.DATABASES["default"].update({
        "ENGINE": os.environ.get("DB_ENGINE"),
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    })
    connections.close_all()

    try: 
        call_command('migrate')
        return True
    except Exception as e:
        return False
