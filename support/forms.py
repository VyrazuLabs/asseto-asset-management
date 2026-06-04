from django import forms
from django.forms import TextInput, Textarea, Select, DateTimeInput, NumberInput
from .models import SupportTicket, PRIORITY_CHOICES, STATUS_CHOICES, TICKET_TYPE_CHOICES, IMPACT_CHOICES
from assets.models import Asset
from authentication.models import User
from dashboard.models import Department, Location

class SupportTicketForm(forms.ModelForm):
    subject = forms.CharField(
        widget=TextInput(attrs={
            'placeholder': 'Summary of the technical difficulty...',
            'class': 'form-control',
            'required': 'required'
        })
    )
    description = forms.CharField(
        required=False,
        widget=Textarea(attrs={
            'placeholder': 'Provide a thorough account of the problem, including steps to reproduce and any error codes observed...',
            'class': 'form-control',
            'rows': 5
        })
    )
    asset = forms.ModelChoiceField(
        queryset=Asset.undeleted_objects.none(),
        required=True,
        widget=Select(attrs={
            'class': 'form-control asset-select',
            'data-placeholder': 'Search serial number, asset ID, or name...',
            'required': 'required'
        })
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.HiddenInput(),
        initial='1'
    )
    ticket_type = forms.ChoiceField(
        choices=TICKET_TYPE_CHOICES,
        widget=Select(attrs={'class': 'form-control'})
    )
    estimated_eta = forms.DateTimeField(
        required=False,
        widget=DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    hours_worked = forms.DecimalField(
        initial=0.0,
        widget=NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    impact_level = forms.ChoiceField(
        choices=IMPACT_CHOICES,
        widget=forms.HiddenInput(),
        initial='1'
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.HiddenInput(),
        initial='0'
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=Select(attrs={
            'class': 'form-control assigned-select',
            'data-placeholder': 'Search technician by name...'
        })
    )
    
    class Meta:
        model = SupportTicket
        fields = [
            'subject', 'description', 'asset', 'priority',
            'ticket_type', 'estimated_eta', 'hours_worked',
            'impact_level', 'assigned_to', 'department', 'location',
            'status'
        ]

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['asset'].queryset = Asset.undeleted_objects.filter(organization=organization)
            self.fields['assigned_to'].queryset = User.objects.filter(organization=organization)
            self.fields['department'].queryset = Department.undeleted_objects.filter(organization=organization)
            self.fields['location'].queryset = Location.undeleted_objects.filter(organization=organization)
        
        # Ensure fields missing from the Add template are not required
        optional_fields = ['status', 'department', 'location']
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # Add classes to other fields if needed
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

class TicketNoteForm(forms.Form):
    content = forms.CharField(
        widget=Textarea(attrs={
            'placeholder': 'Document updates, internal observations, or steps taken...',
            'class': 'form-control',
            'rows': 4
        })
    )
    is_internal = forms.BooleanField(
        required=False,
        label='Mark as Internal Note (hidden from client)'
    )
