from django import forms

from authentication.models import User
from dashboard.models import LicenseType
from license.models import AssignLicense, License
from vendors.models import Vendor

class LicenseForm(forms.ModelForm):
    name=forms.CharField(required=True, widget=forms.TextInput(
        attrs={'autocomplete':'off', 'placeholder':'License Name',
                'class':'form-control','required':'required'}
    ))
    seats=forms.IntegerField(required=True,widget=forms.NumberInput(
        attrs={'autocomplete':'off','placeholder':'Seats',
                'class': 'form-control','required':'required'}
    ))
    start_date=forms.DateField(required=False ,widget=forms.DateInput(
        attrs={'autocomplete':'off','placeholder':'Start Date',
                'type':'date','class': 'form-control'}
    ))
    expiry_date=forms.DateField(required=False,widget=forms.DateInput(
        attrs={'autocomplete':'off','placeholder':'Expiry Date',
                'type':'date','class': 'form-control'}
    ))
    key=forms.CharField(required=False,widget=forms.TextInput(
        attrs={'autocomplete':'off','placeholder':'Key',
                'class': 'form-control'}
    ))
    notes=forms.CharField(required=False,widget=forms.Textarea(
        attrs={'autocomplete':'off','placeholder':'Description',
                'rows':'3','class': 'form-control form-control-sm'}
    ))
    vendor=forms.ModelChoiceField(
        required=False,
        queryset=None,
        empty_label='--SELECT--',
        widget=forms.Select(
            attrs={'class':'form-control'}
        )
    )
    license_type=forms.ModelChoiceField(
        required=True,
        queryset=None,
        empty_label='--SELECT--',
        widget=forms.Select(
            attrs={'class':'form-control'}
        )
    )
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['license_type'].queryset=LicenseType.undeleted_objects.filter(status=True)

        self.fields['vendor'].queryset=Vendor.undeleted_objects.filter(status=True)
    
    class Meta:
        model=License
        fields=['name','license_type','vendor','seats','start_date','expiry_date','key','notes']

class AssignLicenseForm(forms.ModelForm):

    user=forms.ModelChoiceField(required=True,queryset=None,empty_label='--SELECT--', widget=forms.Select(attrs={'class':'form-control'}))
    notes=forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete':'off', 'placeholder':'Notes','class':'form-control'}))

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['user'].queryset=User.undeleted_objects.filter(is_active=True)
    class Meta:
        model=AssignLicense
        fields=['user','notes']
    
    
