from .models import Audit
from django import forms
# class AuditForm(forms.ModelForm):
#     tag =  forms.CharField(required=True, widget=forms.TextInput(
#         attrs={'autocomplete': 'off', 'class': 'form-control',
#                'placeholder': 'Enter Audit Tag'}
#     ))
#     condition=forms.Select(choices=Audit.CONDITION_CHOICES, attrs={'class': 'form-select'})
#     notes=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter comments'})
#     assigned_to=forms.Select(attrs={'class': 'form-select'})

#     def __init__(self, *args, **kwargs):
#         self._organization = kwargs.pop('organization', None)
#     class Meta:
#         model = Audit
#         fields = ['tag','condition', 'notes', 'assigned_to']
#         widgets = {
#             'Condition': forms.Select(choices=Audit.CONDITION_CHOICES, attrs={'class': 'form-select'}),
#             'Comments': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter comments'}),
#         }
class AuditForm(forms.ModelForm):
    class Meta:
        model = Audit
        fields = ['condition', 'notes', 'assigned_to']
        widgets = {
            'condition': forms.Select(choices=Audit.CONDITION_CHOICES, attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter comments'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assigned to'}),
        }

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result