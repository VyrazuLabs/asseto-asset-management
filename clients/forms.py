from django import forms
from django.db import models
from roles.models import Role
from .models import Client, STATUS_CHOICES, RENTAL_TYPE_CHOICES


INDUSTRY_CHOICES = [
    ('', 'Select Industry Type'),
    ('1', 'Technology'),
    ('2', 'Healthcare'),
    ('3', 'Finance'),
    ('4', 'Manufacturing'),
    ('5', 'Retail'),
    ('6', 'Education'),
    ('7', 'Real Estate'),
    ('8', 'Transportation'),
    ('9', 'Energy'),
    ('10', 'Construction'),
    ('11', 'Hospitality'),
    ('12', 'Media & Entertainment'),
    ('13', 'Telecommunications'),
    ('14', 'Agriculture'),
    ('15', 'Other'),
]


class ClientForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'placeholder': 'Client / Company Name',
            'class': 'form-control'
        })
    )
    industry = forms.ChoiceField(
        required=False,
        choices=INDUSTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    corporate_website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'placeholder': 'https://www.sterling-assets.com',
            'class': 'form-control'
        })
    )
    street_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '123 Financial District Plaza',
            'class': 'form-control'
        })
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Mumbai',
            'class': 'form-control'
        })
    )
    state = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Maharashtra',
            'class': 'form-control'
        })
    )
    zip_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '400001',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        return self.cleaned_data.get('name', '').strip().title()

    class Meta:
        model = Client
        fields = [
            'name', 'industry', 'corporate_website',
            'street_address', 'city', 'state', 'zip_code'
        ]
