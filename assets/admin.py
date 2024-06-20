from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import *
# Register your models here.


@admin.register(Asset)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'serial_no',
                    'organization', 'is_deleted', 'created_at']
