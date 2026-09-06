from django.contrib import admin

from .models import GoogleCloudFirebaseConfig


@admin.register(GoogleCloudFirebaseConfig)
class GoogleCloudFirebaseConfigAdmin(admin.ModelAdmin):
    """Read-only troubleshooting view — the primary UX is the Extensions page."""

    readonly_fields = [f.name for f in GoogleCloudFirebaseConfig._meta.fields]
    list_display = ("id", "is_connected", "gcp_project_id", "connected_by", "connected_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
