from django import forms
from assets.models import Asset, AssignAsset
from products.models import Product
from vendors.models import Vendor
from dashboard.models import Location
from authentication.models import User



class AssetForm(forms.ModelForm):

    name = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Enter Asset Name'}
    ))
    serial_no = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Enter Serial No.'}
    ))
    price = forms.FloatField(required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control',
               'placeholder':  'Enter Price'}
    ))
    purchase_date = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control'}
    ))
    warranty_expiry_date = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control'}
    ))
    description = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class': 'form-control form-control-sm',
               'rows': '3', 'placeholder': 'Enter Description'}
    ))
    purchase_type = forms.ChoiceField(
        required=True,
        choices=(
            ("1", "Owned"),
            ("2", "Rented"),
        ),
        initial=0,
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    product = forms.ModelChoiceField(
        required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    vendor = forms.ModelChoiceField(
        required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    location = forms.ModelChoiceField(
        required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))


    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.undeleted_objects.filter(organization=self._organization, status=True)
        self.fields['vendor'].queryset = Vendor.undeleted_objects.filter(organization=self._organization, status=True)
        self.fields['location'].queryset = Location.undeleted_objects.filter(organization=self._organization, status=True)
        
        
        
    class Meta:
        model = Asset
        fields = ['name', 'serial_no', 'price', 'purchase_date', 'warranty_expiry_date', 'description',
                  'purchase_type', 'product', 'vendor', 'organization', 'location']


class AssignedAssetForm(forms.ModelForm):

    asset = forms.ModelChoiceField(
        required=True,
        queryset=None,
        label='he;ll',
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    user = forms.ModelChoiceField(
        required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    
    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.undeleted_objects.filter(is_assigned=False, status=True, organization=self._organization)
        self.fields['user'].queryset = User.undeleted_objects.filter(is_active=True, organization=self._organization).exclude(is_superuser=True)
        
    
    class Meta:
            model = AssignAsset
            fields = ['asset', 'user']


class ReassignedAssetForm(forms.ModelForm):

    user = forms.ModelChoiceField(
        required=True,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    
    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.undeleted_objects.filter(is_active=True, organization=self._organization).exclude(is_superuser=True)


    class Meta:
        model = AssignAsset
        fields = ['user']

