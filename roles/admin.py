from django.contrib import admin
from .models import *
# Register your models here.


@admin.register(Role)
class SupportAdmin(admin.ModelAdmin):
    list_display = ['related_name', 'organization', 'created_at']
