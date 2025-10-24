from .models import TagConfiguration
from django import forms
class TagConfigurationForm(forms.ModelForm):
    class Meta:
        model = TagConfiguration
        fields = ['prefix', 'number_suffix', 'use_default_settings']    

    def __init__(self, *args, **kwargs):
        # Pop organization parameter from kwargs; default None if not passed
        self.organization = kwargs.pop('organization', None)

        # Now call parent's __init__ with remaining args/kwargs
        super().__init__(*args, **kwargs)

    def clean_prefix(self):
        prefix = self.cleaned_data.get('prefix')

        if not prefix.isalpha():  # checks only letters
            raise forms.ValidationError("Prefix must contain only alphabets (A-Z).")
        return prefix

    def clean_number_suffix(self):
        suffix = self.cleaned_data.get('number_suffix')

        if not suffix.isdigit():  # checks only numbers
            raise forms.ValidationError("Suffix must contain only numbers (0-9).")
        return suffix

    