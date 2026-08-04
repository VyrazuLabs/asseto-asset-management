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
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.instance._state.adding:
            self.fields["field_key"].disabled = True
