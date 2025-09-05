from django import forms
from assets.models import Asset, AssignAsset,AssetImage,AssetStatus
from products.models import Product
from vendors.models import Vendor
from dashboard.models import Location
from authentication.models import User
from django.forms import ModelForm

class AssetForm(forms.ModelForm):
    # status = forms.ChoiceField(
    #     required=False,
    #     choices=((0, 'Assigned'),
    #     (1, 'Available'),
    #     (2, 'Repair Required'),
    #     (3, 'Lost/Stolen'),
    #     (4, 'Broken'),
    #     (5, 'Ready To Deploy'),
    #     (6, 'Out for Repair')),
    #     widget=forms.Select(attrs={'class': 'form-select'})
    # )
    status = forms.ModelChoiceField(
        required=False,
        queryset=AssetStatus.undeleted_objects.all().values_list('name', flat=True),
        widget=forms.Select(
            attrs={'class': 'form-select'}
        )
    )
    tag =  forms.CharField(required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Enter Asset Tag'}
    ))
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
        self.fields['product'].queryset = Product.objects.filter(organization=self._organization, status=True)
        # self.fields['vendor'].queryset = Vendor.undeleted_objects.filter(organization=self._organization, status=True)
        self.fields['vendor'].queryset = Vendor.undeleted_objects.filter(organization=self._organization, status=True)
        self.fields['location'].queryset = Location.undeleted_objects.filter(organization=self._organization, status=True)
    
    def get_status(self):
        """Returns the display value for the current status."""
        status_value = self.cleaned_data.get('status') or self.initial.get('status')
        if status_value is not None:
            # status_value might be string ('1') or int (1)
            for value, label in self.fields['status'].choices:
                if str(value) == str(status_value):
                    return label
        return ""
    class Meta:
        model = Asset
        fields = ['name', 'serial_no', 'price', 'purchase_date', 'warranty_expiry_date', 'description',
                  'purchase_type', 'product', 'vendor', 'location','tag',
                  'status'
                  ]
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

class AssetImageForm(forms.ModelForm):
    image = MultipleFileField(label='Select files', required=False)
    class Meta:
            model = AssetImage
            fields = ['image', ]
    # def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         # Add the `multiple` attribute to allow selecting multiple files
    #         self.fields["image"].widget.attrs.update({"multiple": "true"})

class AssignedAssetForm(forms.ModelForm):
    asset = forms.ModelChoiceField(
        required=True,
        queryset=Asset.undeleted_objects.filter(is_assigned=False, status=True),
        label='he;ll',
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))

    user = forms.ModelChoiceField(
        required=True,
        queryset=User.undeleted_objects.filter(is_active=True).exclude(is_superuser=True),
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    image = MultipleFileField(label='Select files', required=False)
    
    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.undeleted_objects.filter(is_assigned=False, status=True, organization=self._organization)
        self.fields['user'].queryset = User.undeleted_objects.filter(is_active=True, organization=self._organization).exclude(is_superuser=True)
        
    
    class Meta:
            model = AssignAsset
            fields = ['asset', 'user']

class AssignedAssetListForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        required=True,
        # queryset=User.undeleted_objects.filter(is_active=True).exclude(is_superuser=True),
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(
            attrs={'class': 'form-select'}
        ))
    
    # image = MultipleFileField(label='Select files', required=False)

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.undeleted_objects.filter(is_active=True, organization=self._organization).exclude(is_superuser=True)
        
    
    class Meta:
            model = AssignAsset
            fields = ['user']


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

class AssetStatusForm(forms.ModelForm):
    name=forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete': 'off', 'class': 'form-control',
               'placeholder': 'Asset Status Name'} ))
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.pk = kwargs.pop('pk', None)
        super().__init__(*args, **kwargs)
    
    class Meta:
        model=AssetStatus
        fields=['name']

