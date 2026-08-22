from django import forms
from django.forms import TextInput, Textarea, Select, DateTimeInput, NumberInput
from extensions.core.support.models import SupportTicket, PRIORITY_CHOICES, TICKET_TYPE_CHOICES, IMPACT_CHOICES
from assets.models import Asset

class ClientSupportTicketForm(forms.ModelForm):
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
    impact_level = forms.ChoiceField(
        choices=IMPACT_CHOICES,
        widget=forms.HiddenInput(),
        initial='1'
    )
    estimated_eta = forms.DateTimeField(
        required=False,
        widget=DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    hours_worked = forms.DecimalField(
        initial=0.0,
        widget=NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    class Meta:
        model = SupportTicket
        fields = [
            'subject', 'description', 'asset', 'priority',
            'ticket_type', 'impact_level', 'estimated_eta', 'hours_worked'
        ]

    def __init__(self, *args, **kwargs):
        client = kwargs.pop('client', None)
        super().__init__(*args, **kwargs)
        if client:
            self.fields['asset'].queryset = Asset.undeleted_objects.filter(client=client)
        
        # Add classes to other fields if needed
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'
