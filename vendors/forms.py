from django import forms
from .models import *
from dashboard.models import Address


class VendorForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Vendor Name', 'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Email', 'class': 'form-control'}))
    phone = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Phone number', 'class': 'form-control'}))
    contact_person = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Contact Person', 'class': 'form-control'}))
    designation = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Designation', 'class': 'form-control'}))
    gstin_number = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'GSTIN Number', 'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'autocomplete': 'off', 'rows': '2', 'placeholder': 'Description', 'class': 'form-control'}))

    def clean_name(self):
        name = self.cleaned_data.get('name')
        return name.title()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email.lower()

    def clean_contact_person(self):
        contact_person = self.cleaned_data.get('contact_person')
        return contact_person.title()

    class Meta:
        model = Vendor
        fields = ['name', 'email', 'phone', 'contact_person',
                  'designation', 'gstin_number', 'description']


class AddressForm(forms.ModelForm):
    address_line_one = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'rows': '2', 'placeholder': 'Address Line 1'}))
    address_line_two = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'rows': '2', 'placeholder': 'Address Line 2'}))
    country = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Country', 'class': 'form-control'}))
    state = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'State', 'class': 'form-control'}))
    city = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'City', 'class': 'form-control'}))
    pin_code = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'placeholder': 'Zip Code', 'class': 'form-control'}))

    def clean_country(self):
        country = self.cleaned_data.get('country')
        return country.title()

    def clean_state(self):
        state = self.cleaned_data.get('state')
        return state.title()

    def clean_city(self):
        city = self.cleaned_data.get('city')
        return city.title()

    class Meta:
        model = Address
        fields = ['address_line_one', 'address_line_two',
                  'country', 'state', 'city', 'pin_code']
