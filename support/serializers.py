from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from custom_fields.utils import (
    get_definitions_for_module,
    get_values_for_entity,
    save_values_for_entity_dict,
)

from .models import (
    SupportTicket,
    TicketAttachment,
    TicketActivity,
    TicketComment,
    TicketCommentAttachment,
)
from .utils import SupportTicketService

CF_MODULE = "support_ticket"


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "file_name", "file_size", "uploaded_by", "created_at"]
        read_only_fields = fields


class TicketCommentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCommentAttachment
        fields = ["id", "file", "file_name", "file_size"]
        read_only_fields = fields


class TicketActivitySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketActivity
        fields = [
            "id",
            "activity_type",
            "description",
            "is_internal",
            "performed_by",
            "performed_by_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_performed_by_name(self, obj):
        return obj.performed_by.get_full_name() if obj.performed_by else None


class TicketCommentSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    attachments = TicketCommentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketComment
        fields = [
            "id",
            "content",
            "author",
            "display_name",
            "is_staff_comment",
            "attachments",
            "created_at",
        ]
        read_only_fields = ["id", "author", "display_name", "is_staff_comment", "attachments", "created_at"]


class TicketStatusUpdateSerializer(serializers.Serializer):
    """Request-body shape for the dedicated status-update endpoint — used
    for API documentation only (the view reads ``request.data`` directly)."""

    status = serializers.ChoiceField(
        choices=["0", "1", "2", "3", "4"],
        help_text="0=Open, 1=In Progress, 2=In Testing, 3=Resolved, 4=Closed",
    )
    happy_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Required when moving to Closed (4) on a ticket that has a client.",
    )


class TicketCommentCreateSerializer(serializers.Serializer):
    """Write-only shape for posting a comment via the mobile API."""

    content = serializers.CharField()
    attachments = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, default=list
    )

    def create(self, validated_data):
        request = self.context["request"]
        ticket = self.context["ticket"]
        content = validated_data["content"].strip()
        files = validated_data.get("attachments", [])
        is_staff = request.user.is_staff or request.user.is_superuser

        comment = TicketComment.objects.create(
            ticket=ticket,
            content=content,
            author=request.user,
            is_staff_comment=is_staff,
        )
        for f in files:
            TicketCommentAttachment.objects.create(
                comment=comment, file=f, file_name=f.name, file_size=f.size
            )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type="comment",
            description=content,
            is_internal=False,
            performed_by=request.user,
        )
        return comment


class SupportTicketSerializer(serializers.ModelSerializer):
    """Read serializer — ticket list/detail, including custom fields."""

    asset_name = serializers.CharField(source="asset.name", read_only=True)
    asset_tag = serializers.CharField(source="asset.tag", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    ticket_type_label = serializers.CharField(source="get_ticket_type_display", read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    cf_definitions = serializers.SerializerMethodField()
    cf_values = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "ticket_id",
            "subject",
            "description",
            "happy_code",
            "asset",
            "asset_name",
            "asset_tag",
            "priority",
            "priority_label",
            "status",
            "status_label",
            "ticket_type",
            "ticket_type_label",
            "estimated_eta",
            "hours_worked",
            "impact_level",
            "assigned_to",
            "assigned_to_name",
            "department",
            "location",
            "client",
            "attachments",
            "cf_definitions",
            "cf_values",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.STR)
    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_cf_definitions(self, obj):
        from custom_fields.serializers import CustomFieldDefinitionSerializer

        definitions = get_definitions_for_module(obj.organization, CF_MODULE)
        return CustomFieldDefinitionSerializer(definitions, many=True).data

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_cf_values(self, obj):
        definitions = get_definitions_for_module(obj.organization, CF_MODULE)
        return get_values_for_entity(obj.id, definitions)


class SupportTicketWriteSerializer(serializers.ModelSerializer):
    """Create/update serializer for the mobile API.

    Accepts multipart form data (for ``attachments``) or JSON, plus an
    optional ``custom_fields`` dict of ``{field_key: value}`` and an
    optional ``happy_code_confirm`` used only to verify closing a ticket
    that has a client — never persisted as-is on the model.
    """

    attachments = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True, default=list
    )
    custom_fields = serializers.DictField(required=False, default=dict)
    happy_code_confirm = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )

    class Meta:
        model = SupportTicket
        fields = [
            "subject",
            "description",
            "asset",
            "priority",
            "status",
            "ticket_type",
            "estimated_eta",
            "hours_worked",
            "impact_level",
            "assigned_to",
            "department",
            "location",
            "client",
            "attachments",
            "custom_fields",
            "happy_code_confirm",
        ]

    def validate(self, attrs):
        new_status = attrs.get("status")
        if self.instance is not None and new_status:
            SupportTicketService.validate_close_transition(
                self.instance, new_status, attrs.get("happy_code_confirm")
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        attachments = validated_data.pop("attachments", [])
        custom_fields = validated_data.pop("custom_fields", {})
        validated_data.pop("happy_code_confirm", None)

        validated_data["organization"] = request.user.organization
        validated_data["created_by"] = str(request.user.id)
        ticket = SupportTicket.objects.create(**validated_data)

        for f in attachments:
            TicketAttachment.objects.create(
                ticket=ticket, file=f, file_name=f.name, file_size=f.size,
                uploaded_by=request.user,
            )
        TicketActivity.objects.create(
            ticket=ticket,
            activity_type="created",
            description=f"Ticket initiated by {request.user.get_full_name()}.",
            performed_by=request.user,
        )
        if custom_fields:
            cf_errors = save_values_for_entity_dict(
                request.user.organization, ticket.id, CF_MODULE, custom_fields
            )
            if cf_errors:
                raise serializers.ValidationError({"custom_fields": cf_errors})
        return ticket

    def update(self, instance, validated_data):
        request = self.context["request"]
        attachments = validated_data.pop("attachments", [])
        custom_fields = validated_data.pop("custom_fields", {})
        validated_data.pop("happy_code_confirm", None)

        old_status = instance.status
        old_assigned = instance.assigned_to

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = str(request.user.id)
        instance.save()

        SupportTicketService.log_status_change(instance, old_status, request.user)
        SupportTicketService.log_reassignment(instance, old_assigned, request.user)

        for f in attachments:
            TicketAttachment.objects.create(
                ticket=instance, file=f, file_name=f.name, file_size=f.size,
                uploaded_by=request.user,
            )
        if custom_fields:
            cf_errors = save_values_for_entity_dict(
                request.user.organization, instance.id, CF_MODULE, custom_fields
            )
            if cf_errors:
                raise serializers.ValidationError({"custom_fields": cf_errors})
        return instance
