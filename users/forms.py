from django import forms
from authentication.models import User
from roles.models import Role
from dashboard.models import Department, Location
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from dashboard.models import Address


class UserForm(forms.ModelForm):
    full_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control',
               'placeholder': 'Name', 'autocomplete': 'off'}
    ))
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'class':  'form-control',
               'placeholder':  'Email', 'autocomplete': 'off'}
    ))
    phone = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control',
               'placeholder': 'Phone', 'autocomplete': 'off'}
    ))

    access_level = forms.ChoiceField(
        required=False,
        choices=(
            ("False", "Only Assigned"),
            ("True", "All"),
        ),
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ))

    role = forms.ModelChoiceField(
        required=False,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    location = forms.ModelChoiceField(
        required=False,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    department = forms.ModelChoiceField(
        required=False,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    profile_pic = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True})
    )
    
    password1=forms.CharField(
        required=False,
        widget=forms.PasswordInput
    )

    password2=forms.CharField(
        required=False,
        widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password1'].required = False
        self.fields['password2'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Repeat password'})
        self.fields['password2'].required = False
        self.fields['department'].queryset = Department.undeleted_objects.filter(
            organization=self._organization, status=True)
        self.fields['department'].required=False
        self.fields['location'].queryset = Location.undeleted_objects.filter(
            organization=self._organization, status=True)
        self.fields['role'].required=False
        self.fields['role'].queryset = Role.objects.filter(
            organization=self._organization, status=True)
        self.fields['role'].required=False

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered with us')
        return email.lower()

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        return full_name.title()
    
    # def clean_password1(self):
    #     password1=self.data.get('password1')
    #     if password1 in ("", None):
    #         return password1
    #     else:
    #         return password1

    # def clean_password2(self):
    #     password2=self.data.get('password2')
    #     if password2 in ("", None):
    #         return password2
    #     else:
    #         return password2
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'access_level',
                  'role', 'location', 'department', 'profile_pic']


class UserUpdateForm(UserChangeForm):

    full_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control',
               'placeholder': 'Name', 'autocomplete': 'off'}
    ))
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'class':  'form-control',
               'placeholder':  'Email', 'autocomplete': 'off'}
    ))
    phone = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control',
               'placeholder': 'Phone', 'autocomplete': 'off'}
    ))

    access_level = forms.ChoiceField(
        # required=True,
        choices=(
            ("False", "Only Assigned"),
            ("True", "All"),
        ),
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ))

    role = forms.ModelChoiceField(
        # required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    location = forms.ModelChoiceField(
        # required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    department = forms.ModelChoiceField(
        # required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    profile_pic = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={'class': 'form-control', 'id': 'inputFile'}
        ))

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        self.fields['department'].queryset = Department.undeleted_objects.filter(
            organization=self._organization, status=True)
        self.fields['location'].queryset = Location.undeleted_objects.filter(
            organization=self._organization, status=True)
        self.fields['role'].queryset = Role.objects.filter(
            organization=self._organization, status=True)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email.lower()

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        return full_name.title()

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'access_level',
                  'role', 'location', 'department', 'profile_pic']


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
