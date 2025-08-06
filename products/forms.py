from dataclasses import fields
from django import forms
from .models import *
from dashboard.models import ProductCategory, ProductType


class AddProductsForm(forms.ModelForm):

    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off',
               'placeholder': 'Product Name', 'class': 'form-control'}
    ))
    product_picture = forms.ImageField(required=False, widget=forms.FileInput(
        attrs={'class': 'form-control d-flex', 'id': 'inputFile'}
    ))
    manufacturer = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off',
               'placeholder': 'Manufacturer', 'class': 'form-control'}
    ))
    description = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'autocomplete': 'off', 'placeholder': 'Description',
               'class': 'form-control', 'rows': '2'}
    ))
    product_category = forms.ModelChoiceField(
        queryset=None,
        empty_label='--SELECT--',
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ))

    product_type = forms.ModelChoiceField(
        queryset=None,
        empty_label='--SELECT--',
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ))

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['product_category'].queryset = ProductCategory.undeleted_objects.filter(
            organization=self._organization, status=True)
        self.fields['product_type'].queryset = ProductType.undeleted_objects.filter(
            organization=self._organization, status=True)

    class Meta:
        model = Product
        fields = ['name', 'product_picture', 'manufacturer',
                  'description', 'product_category', 'product_type']
