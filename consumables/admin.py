from django.contrib import admin
from .models import Consumable


@admin.register(Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "vendor", "location", "quantity", "min_qty", "organization"]
    search_fields = ["product__name", "vendor__name", "item_no", "order_number"]
