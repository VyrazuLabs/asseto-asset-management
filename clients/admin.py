from django.contrib import admin
from .models import Client, ClientContact


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        "client_id",
        "name",
        "rental_type",
        "active_rentals",
        "open_tickets",
        "status",
    ]
    search_fields = ["name", "client_id", "industry"]
    list_filter = ["status", "rental_type"]


@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "client"]
    search_fields = ["name", "email", "client__name"]
