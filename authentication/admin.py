from django.contrib import admin
from .models import User

# Register your models here.


@admin.register(User)
class SupportAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'role',
                    'organization', 'is_active', 'is_deleted', 'created_at']
