from django.contrib import admin
from .models import Support

# Register your models here.

@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ['id','question','answer']
