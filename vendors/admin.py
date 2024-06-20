from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import *
# Register your models here.


@admin.register(Vendor)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'organization', 'created_at']
