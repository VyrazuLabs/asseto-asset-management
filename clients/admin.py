from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'name', 'rental_type', 'contact_person',
                    'contact_email', 'active_rentals', 'open_tickets', 'status']
    search_fields = ['name', 'client_id', 'contact_person', 'contact_email']
    list_filter  = ['status', 'rental_type']
