from dataclasses import fields
from django import forms
from .models import *
from dashboard.models import ProductCategory, ProductType
from assets.forms import MultipleFileField
from django.db.models import Q
from audit.constants import AUDIT_INTERVAL


class AddProductsForm(forms.ModelForm):

    name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "class": "form-control",
                "required": "required",
            }
        ),
    )
    product_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={"class": "form-control d-flex", "id": "inputFile"}
        ),
    )
    manufacturer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )

    model = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )

    eol = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"autocomplete": "off", "class": "form-control"}
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"autocomplete": "off", "class": "form-control", "rows": "2"}
        ),
    )
    product_category = forms.ModelChoiceField(
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    product_sub_category = forms.ModelChoiceField(
        required=False,
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    product_type = forms.ModelChoiceField(
        queryset=None,
        empty_label="--SELECT--",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    audit_interval = forms.TypedChoiceField(
        choices=AUDIT_INTERVAL,
        coerce=int,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        self.fields["product_category"].queryset = (
            ProductCategory.undeleted_objects.filter(
                Q(organization=None, status=True, parent__name="Root")
                | Q(organization=self._organization, status=True, parent__name="Root")
            )
        )

        self.fields["product_type"].queryset = ProductType.undeleted_objects.filter(
            Q(organization=None) | Q(organization=self._organization, status=True)
        )

        self.fields["product_sub_category"].queryset = (
            ProductCategory.undeleted_objects.filter(
                Q(organization=None, status=True, parent__isnull=False)
                | Q(organization=self._organization, status=True, parent__isnull=False)
            )
        )

        if self.instance.pk:
            sub_category = self.instance.product_sub_category
            if sub_category:
                if sub_category.parent and sub_category.parent.name != "Root":
                    self.fields["product_category"].initial = sub_category.parent.pk
                    self.fields["product_sub_category"].initial = sub_category.pk
                else:
                    self.fields["product_category"].initial = sub_category.pk

    class Meta:
        model = Product
        fields = [
            "name",
            "product_picture",
            "manufacturer",
            "description",
            "product_category",
            "product_sub_category",
            "product_type",
            "eol",
            "model",
            "audit_interval",
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get("product_sub_category"):
            instance.product_sub_category = self.cleaned_data["product_sub_category"]
        elif self.instance._state.adding:
            instance.product_sub_category = self.cleaned_data["product_category"]
        else:
            instance.product_sub_category = None

        if commit:
            instance.save()
        return instance


class ProductImageForm(forms.ModelForm):
    image = MultipleFileField(label="Select files", required=False)

    class Meta:
        model = ProductImage
        fields = [
            "image",
        ]
