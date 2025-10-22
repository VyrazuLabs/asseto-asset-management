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