
from django import forms
from .models import Role


class RoleForm(forms.ModelForm):
    related_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Role name', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        self._pk = kwargs.pop('pk', None)
        super(RoleForm, self).__init__(*args, **kwargs)

    def clean_related_name(self):
        related_name = self.cleaned_data.get('related_name')
        if Role.objects.filter(related_name__iexact=related_name, organization= self._organization).exclude(pk=self._pk).exists():
            raise forms.ValidationError('Role must be unique!')
        return related_name

    class Meta:
        model = Role
        fields = ['related_name']
