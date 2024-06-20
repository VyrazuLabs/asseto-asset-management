from django import forms
from .models import User
from dashboard.models import Organization, Location
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from smart_selects.form_fields import ChainedModelChoiceField
from django.forms import URLField
from django.core.exceptions import ValidationError


class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Full name', 'autofocus': True}))
    email = forms.EmailField(max_length=30, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Email'}))
    username = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Username'}))
    phone = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Phone'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Confirm password'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered with us')
        return email.lower()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username.lower()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already taken')
        return username

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        return full_name.title()

    class Meta:
        model = User
        fields = ['full_name', 'email', 'username',
                  'phone', 'password1', 'password2']


class OrganizationForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Company Name'}))
    website = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Company Website'}))

    def clean_name(self):
        name = self.cleaned_data.get('name')
        return name.title()

    def clean_website(self):
        url = self.cleaned_data.get('website')
        url_form_field = URLField()
        try:
            url = url_form_field.clean(url)
        except ValidationError:
            raise forms.ValidationError(
                'This is not a valid website name.')
        return url.lower()

    class Meta:
        model = Organization
        fields = ['name', 'website']


class UserLoginForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Email'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Password'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email.lower()


class UserPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['old_password'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Old password'})
        self.fields['new_password1'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'New password'})
        self.fields['new_password2'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Confirm password'})


class UserPasswordResetRequestForm(PasswordResetForm):

    def __init__(self, *args, **kwargs):
        super(UserPasswordResetRequestForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Email'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email.lower(), is_active=True).exists():
            raise forms.ValidationError(
                'There is no user registered with the specified email address!')
        return email.lower()


class UserPasswordResetForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password1'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'New password'})
        self.fields['new_password2'].widget.attrs.update(
            {'autocomplete': 'off', 'class': 'form-control form-control-xl', 'placeholder': 'Confirm password'})


class UserUpdateForm(forms.ModelForm):

    full_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Full name', 'autofocus': True}))
    email = forms.EmailField(max_length=30, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Email'}))

    phone = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Phone'}))

    profile_pic = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={'class': 'form-control', 'id': 'inputFile'}
        ))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email.lower()

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        return full_name.title()

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'profile_pic']


class OrganizationUpdateForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Company Name'}))
    website = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Company Website'}))
    email = forms.EmailField(required=False, max_length=30, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Company Email'}))
    phone = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Company Phone'}))
    currency = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Company Currency'}))
    date_format = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Date Format'}))
    logo = forms.ImageField(required=False, widget=forms.FileInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'id': 'inputFile'}))

    def clean_name(self):
        name = self.cleaned_data.get('name')
        return name.title()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email.lower()

    def clean_currency(self):
        currency = self.cleaned_data.get('currency')
        return currency.upper()

    def clean_website(self):
        url = self.cleaned_data.get('website')
        url_form_field = URLField()
        try:
            url = url_form_field.clean(url)
        except ValidationError:
            raise forms.ValidationError(
                'This is not a valid website.')
        return url.lower()

    class Meta:
        model = Organization
        fields = ['name', 'website', 'email', 'phone',
                  'currency', 'date_format', 'logo']
