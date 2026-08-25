import uuid
from django.db import models
from dashboard.models import TimeStampModel


class CustomFieldDefinition(TimeStampModel):
    MODULE_CHOICES = [
        ("client",         "Client"),
        ("vendor",         "Vendor"),
        ("product",        "Product"),
        ("user",           "User"),
        ("asset",          "Asset"),
        ("support_ticket", "Support Ticket"),
        ("maintenance",    "Maintenance"),
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
    is_deleted  = models.BooleanField(default=False)

    class Meta:
        db_table = "custom_fields_customfielddefinition"
        unique_together = [("organization", "module", "field_key")]
        ordering = ["module", "field_label"]

    def __str__(self):
        return f"[{self.get_module_display()}] {self.field_label}"

    def original_key(self):
        """
        The field_key before it was soft-deleted, i.e. the original key the
        user saw. The soft-delete suffix (``__deleted_<uuid>``) is stripped.
        """
        marker = "__deleted_"
        if self.field_key and marker in self.field_key:
            return self.field_key.split(marker)[0].rstrip("_")
        return self.field_key

    def soft_delete(self):
        """
        Soft-delete this field and free its field_key so a new field with the
        same module + label can be created without hitting the unique_together
        constraint. Historical values stay linked via the foreign key.
        """
        if self.is_deleted or not self.field_key or "__deleted_" in self.field_key:
            return
        suffix = f"__deleted_{self.id.hex[:10]}"
        base = self.field_key[: 100 - len(suffix)].rstrip("_")
        self.field_key = f"{base}{suffix}"
        self.is_active = False
        self.is_deleted = True
        self.save(update_fields=["field_key", "is_active", "is_deleted"])

    def restore(self):
        """
        Restore a soft-deleted field. Reclaims the original field_key only if
        it is still free (i.e. no other active/non-deleted field of the same
        organization + module already uses it); otherwise it does nothing and
        returns False so the caller (a future restore view) can show a clear
        "duplicate already exists" message to the user.

        Returns True on successful restore, False on conflict (or if the
        record was not soft-deleted).
        """
        if not self.is_deleted:
            return False
        original = self.original_key()
        taken = CustomFieldDefinition.objects.filter(
            organization_id=self.organization_id,
            module=self.module,
            field_key=original,
            is_deleted=False,
        ).exclude(pk=self.pk).exists()
        if taken:
            return False
        self.field_key = original
        self.is_deleted = False
        self.is_active = True
        self.save(update_fields=["field_key", "is_deleted", "is_active"])
        return True


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
