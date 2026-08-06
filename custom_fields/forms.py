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
        # Pop translations if passed (used to translate labels/choices/errors).
        self.trans = kwargs.pop("trans", None) or {}
        super().__init__(*args, **kwargs)
        # The key is always auto-generated from module + label, so it is read-only.
        self.fields["field_key"].disabled = True
        self.fields["field_key"].required = False

        label_map = {
            "module": self.trans.get("module_label", "Module"),
            "field_type": self.trans.get("field_type_label", "Field type"),
            "field_label": self.trans.get("field_label_label", "Field label"),
            "field_key": self.trans.get("field_key_label", "Field key"),
            "is_required": self.trans.get("is_required_label", "Is required"),
        }
        for name, label in label_map.items():
            self.fields[name].label = label

        self.fields["module"].choices = [
            (val, self.trans.get(f"module_{val}", label))
            for val, label in self.fields["module"].choices
        ]
        self.fields["field_type"].choices = [
            (val, self.trans.get(f"ft_{val}", label))
            for val, label in self.fields["field_type"].choices
        ]

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
                    self.trans.get(
                        "duplicate_field_label_error",
                        "A field with this name already exists for the selected module.",
                    ),
                )
        return cleaned