from django import forms
from .models import Consumable
from products.models import Product
from vendors.models import Vendor
from dashboard.models import Location
from django.db.models import Q


class ConsumableForm(forms.ModelForm):
    """ModelForm for creating/editing a Consumable, scoped to an organization for its FK choices."""

    consumable_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    product = forms.ModelChoiceField(
        queryset=None,
        required=True,
        empty_label="-- Select Product --",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_product"}),
    )
    vendor = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="-- Select Vendor --",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_vendor"}),
    )
    location = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="-- Select Location --",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_location"}),
    )
    item_no = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    order_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    purchase_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"}
        ),
    )
    purchase_cost = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    quantity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
    )
    min_qty = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "id": "id_image"}),
    )

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        org_filter = Q(organization=None) | Q(organization=self._organization)

        self.fields["product"].queryset = Product.undeleted_objects.filter(
            org_filter
        ).order_by("name")
        self.fields["vendor"].queryset = Vendor.undeleted_objects.filter(
            org_filter
        ).order_by("name")
        self.fields["location"].queryset = Location.undeleted_objects.filter(
            org_filter
        ).order_by("office_name")

    class Meta:
        model = Consumable
        fields = [
            "consumable_name",
            "product",
            "vendor",
            "location",
            "item_no",
            "order_number",
            "purchase_date",
            "purchase_cost",
            "quantity",
            "min_qty",
            "notes",
            "image",
        ]
