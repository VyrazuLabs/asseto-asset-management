import uuid
from django.db import models
from dashboard.models import TimeStampModel


class CustomFieldDefinition(TimeStampModel):
    MODULE_CHOICES = [
        ("client",  "Client"),
        ("vendor",  "Vendor"),
        ("product", "Product"),
        ("user",    "User"),
        ("asset",   "Asset"),
    ]
    FIELD_TYPE_CHOICES = [
        ("text",     "Text"),
        ("integer",  "Integer"),
        ("decimal",  "Decimal"),
        ("date",     "Date"),
        ("boolean",  "Boolean (Yes/No)"),
        ("email",    "Email"),
    ]
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization= models.ForeignKey("dashboard.Organization", on_delete=models.CASCADE, null=True, blank=True)
    module      = models.CharField(max_length=30, choices=MODULE_CHOICES)
    field_label = models.CharField(max_length=255)
    field_key   = models.SlugField(max_length=100)
    field_type  = models.CharField(max_length=30, choices=FIELD_TYPE_CHOICES, default="text")
    is_required = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)

    class Meta:
        db_table = "custom_fields_customfielddefinition"
        unique_together = [("organization", "module", "field_key")]
        ordering = ["module", "field_label"]

    def __str__(self):
        return f"[{self.get_module_display()}] {self.field_label}"


class CustomFieldValue(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definition  = models.ForeignKey(
        CustomFieldDefinition, on_delete=models.CASCADE, related_name="values"
    )
    entity_uuid = models.UUIDField()
    value_text  = models.TextField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "custom_fields_customfieldvalue"
        unique_together = [("definition", "entity_uuid")]

    def __str__(self):
        return f"{self.definition.field_label}: {self.value_text}"
