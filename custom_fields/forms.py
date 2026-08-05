import re

from django import forms

from .models import CustomFieldDefinition


class CustomFieldDefinitionForm(forms.ModelForm):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "module", "field_label", "field_key",
            "field_type", "is_required"
        ]

    def __init__(self, *args, **kwargs):
        # Pop organization if passed (used for duplicate detection).
        self.organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        # The key is always auto-generated from module + label, so it is read-only.
        self.fields["field_key"].disabled = True
        self.fields["field_key"].required = False

    @staticmethod
    def slugify_label(label):
        slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
        return re.sub(r"_+", "_", slug)

    def clean(self):
        cleaned = super().clean()
        instance = self.instance
        module = cleaned.get("module")
        label = (cleaned.get("field_label") or "").strip()

        if not instance._state.adding:
            # Never change the key once the field exists (values reference it).
            cleaned["field_key"] = instance.field_key
        elif module and label:
            slug = self.slugify_label(label)
            key = f"{module}_{slug}" if slug else module
            cleaned["field_key"] = key[:100].strip("_")
        else:
            cleaned["field_key"] = ""

        # Friendly duplicate detection for the same organization + module.
        if cleaned["field_key"] and self.organization:
            qs = CustomFieldDefinition.objects.filter(
                organization=self.organization,
                module=cleaned.get("module"),
                field_key=cleaned["field_key"],
                is_deleted=False,
            )
            if instance and not instance._state.adding:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                self.add_error(
                    "field_label",
                    "A field with this name already exists for the selected module.",
                )
        return cleaned