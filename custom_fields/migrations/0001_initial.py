import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("dashboard", "0029_customfielddefinition_customfieldvalue_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomFieldDefinition",
            fields=[
                ("status", models.BooleanField(default=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("created_by", models.CharField(blank=True, max_length=255, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "module",
                    models.CharField(
                        choices=[
                            ("client", "Client"),
                            ("vendor", "Vendor"),
                            ("product", "Product"),
                            ("user", "User"),
                            ("asset", "Asset"),
                        ],
                        max_length=30,
                    ),
                ),
                ("field_label", models.CharField(max_length=255)),
                ("field_key", models.SlugField(max_length=100)),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("integer", "Integer"),
                            ("decimal", "Decimal"),
                            ("date", "Date"),
                            ("boolean", "Boolean (Yes/No)"),
                            ("url", "URL"),
                            ("email", "Email"),
                        ],
                        default="text",
                        max_length=30,
                    ),
                ),
                ("is_required", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="dashboard.organization",
                    ),
                ),
            ],
            options={
                "db_table": "dashboard_customfielddefinition",
                "ordering": ["module", "field_label"],
                "unique_together": {("organization", "module", "field_key")},
            },
        ),
        migrations.CreateModel(
            name="CustomFieldValue",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("entity_uuid", models.UUIDField()),
                ("value_text", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="values",
                        to="custom_fields.customfielddefinition",
                    ),
                ),
            ],
            options={
                "db_table": "dashboard_customfieldvalue",
                "unique_together": {("definition", "entity_uuid")},
            },
        ),
    ]
