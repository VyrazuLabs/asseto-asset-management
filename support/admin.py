from django.contrib import admin
from .models import SupportTicket, TicketAttachment, TicketActivity


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'subject', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'organization')
    search_fields = ('ticket_id', 'subject')

@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'ticket', 'uploaded_by', 'created_at')

@admin.register(TicketActivity)
class TicketActivityAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'ticket', 'performed_by', 'created_at')
