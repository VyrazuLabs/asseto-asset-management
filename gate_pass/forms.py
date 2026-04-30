from .models import GatePass
from django import forms
class GatePassForm(forms.ModelForm):
    class Meta:
        model = GatePass
        fields = ['asset', 'destination_vendor', 'movement_type', 'expected_return_date', 'purpose_of_movement', 'raised_by', 'authorised_by', 'status']