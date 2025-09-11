from dataclasses import fields
from django import forms
from django.db.models import Q
from .models import Location, Address, ProductType, Department, ProductCategory


class LocationForm(forms.ModelForm):

    office_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Office Name'}
    ))
    contact_person_name = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class':  'form-control',
               'placeholder':  'Contact Person Name'}
    ))
    contact_person_email = forms.EmailField(required=False, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class':  'form-control',
               'placeholder':  'Contact Person Email'}
    ))
    contact_person_phone = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Contact Person Phone'}
    ))

    def clean_office_name(self):
        office_name = self.cleaned_data.get('office_name')
        return office_name.title()

    def clean_contact_person_name(self):
        contact_person_name = self.cleaned_data.get('contact_person_name')
        return contact_person_name.title()

    def clean_contact_person_email(self):
        contact_person_email = self.cleaned_data.get('contact_person_email')
        return contact_person_email.lower()

    class Meta:
        model = Location
        fields = ['office_name', 'contact_person_name',
                  'contact_person_email', 'contact_person_phone']


class AddressForm(forms.ModelForm):

    address_line_one = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Address Line 1', 'rows': '2'}
    ))
    address_line_two = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Address Line 2', 'rows': '2'}
    ))
    country = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off',
               'class': 'form-control', 'placeholder': 'Country'}
    ))
    state = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off',
               'class': 'form-control', 'placeholder': 'State'}
    ))
    city = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off',
               'class': 'form-control', 'placeholder': 'City'}
    ))
    pin_code = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Zip Code'}
    ))

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


class ProductTypeForm(forms.ModelForm):
    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Type Name'}
    ))

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        self._pk = kwargs.pop('pk', None)
        super(ProductTypeForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if ProductType.undeleted_objects.filter(name__iexact=name, organization=self._organization).exclude(pk=self._pk).exists():
            raise forms.ValidationError('Name must be unique!')
        return name

    class Meta:
        model = ProductType
        fields = ['name']


class DepartmentForm(forms.ModelForm):

    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Department Name'}
    ))
    contact_person_name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Contact Person Name'}
    ))
    contact_person_email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Contact Person Email'}
    ))
    contact_person_phone = forms.IntegerField(required=True, widget=forms.NumberInput(
        attrs={'autocomplete': 'off', 'class': 'form-control', 'placeholder': 'Contact Person Phone'}
    ))

    def clean_contact_person_name(self):
        contact_person_name = self.cleaned_data.get('contact_person_name')
        return contact_person_name.title()

    def clean_contact_person_email(self):
        contact_person_email = self.cleaned_data.get('contact_person_email')
        return contact_person_email.lower()

    class Meta:
        model = Department
        fields = ['name', 'contact_person_name',
                  'contact_person_email', 'contact_person_phone']


from django import forms
from django.db.models import Q
from .models import ProductCategory

class ProductCategoryForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'class': 'form-control',
                'placeholder': 'Category Name'
            }
        )
    )
    parent = forms.ModelChoiceField(
        queryset=ProductCategory.undeleted_objects.none(),  # Empty queryset initially
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False  # Adjust based on your requirements
    )

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        self._pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)
        # Set the parent queryset dynamically
        self.fields['parent'].queryset = ProductCategory.undeleted_objects.filter(
            Q(parent__name='Root') | Q(name='Root')
        ).order_by('name')
        # Set the initial parent value
        self.fields['parent'].initial = ProductCategory.undeleted_objects.filter(name='Root').first()

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if ProductCategory.undeleted_objects.filter(
            name__iexact=name,
            organization=self._organization
        ).exclude(pk=self._pk).exists():
            raise forms.ValidationError('Name must be unique!')
        return name

    class Meta:
        model = ProductCategory
        fields = ['name', 'parent']


# class ProductSubCategoryForm(forms.ModelForm):
#     name = forms.CharField(required=True, widget=forms.TextInput(
#         attrs={'autocomplete': 'off', 'class': 'form-control',
#                'placeholder': 'Category Name'}
#     ))

#     parent = forms.ModelChoiceField(
#         queryset=None,
#         empty_label="--SELECT--",
#         widget=forms.Select(
#             attrs={'class': 'form-select'}
#         ))

#     def __init__(self, *args, **kwargs):
#         self._organization = kwargs.pop('organization', None)
#         self._pk = kwargs.pop('pk', None)
#         super(ProductSubCategoryForm, self).__init__(*args, **kwargs)
#         self.fields['parent'].queryset = ProductCategory.undeleted_objects.filter(parent__isnull=True)

#     def clean_name(self):
#         name = self.cleaned_data.get('name')
#         if ProductCategory.undeleted_objects.filter(name__iexact=name, organization=self._organization).exclude(pk=self._pk).exists():
#             raise forms.ValidationError('Name must be unique!')
#         return name

#     class Meta:
#         model = ProductCategory
#         fields = ['name','parent']
