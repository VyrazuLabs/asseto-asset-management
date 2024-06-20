from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import *
# Register your models here.


@admin.register(Organization)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'website', 'created_at']


@admin.register(Location)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['office_name', 'address',
                    'organization', 'is_deleted', 'created_at']


@admin.register(Department)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'organization', 'is_deleted', 'created_at']


@admin.register(ProductType)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'organization', 'is_deleted', 'created_at']


@admin.register(ProductCategory)
class SupportAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'organization', 'is_deleted', 'created_at']
