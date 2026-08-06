from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import CustomFieldDefinition, CustomFieldValue
from .forms import CustomFieldDefinitionForm
from .serializers import CustomFieldDefinitionSerializer, CustomFieldValueSerializer

PAGE_SIZE = 10
ORPHANS = 1


def get_translations(request):
    from configurations.models import LocalizationConfiguration
    from configurations.translations.utils import get_translations as load_translations

    lang_id = request.session.get("org_lang_id")
    if lang_id is None:
        config = LocalizationConfiguration.objects.filter(
            organization=request.user.organization
        ).first()
        lang_id = config.default_language if config else 0
        request.session["org_lang_id"] = lang_id
    return load_translations(lang_id)


def get_custom_field_queryset(request):
    return CustomFieldDefinition.objects.filter(
        organization=request.user.organization,
        is_deleted=False,
    ).order_by("module", "field_label")


def get_module_display_map(trans):
    return {val: trans[f"module_{val}"] for val, _ in CustomFieldDefinition.MODULE_CHOICES}


def get_field_type_display_map(trans):
    return {val: trans[f"ft_{val}"] for val, _ in CustomFieldDefinition.FIELD_TYPE_CHOICES}


@login_required
def list_custom_fields(request):
    paginator = Paginator(get_custom_field_queryset(request), PAGE_SIZE, orphans=ORPHANS)
    page_object = paginator.get_page(request.GET.get("page"))
    trans = get_translations(request)
    context = {
        "title": trans["custom_fields"],
        "page_object": page_object,
        "module_choices": CustomFieldDefinition.MODULE_CHOICES,
        "module_display": get_module_display_map(trans),
        "field_type_display": get_field_type_display_map(trans),
        "sidebar": "configurations",
        "submenu": "custom_fields"
    }
    return render(request, "custom_fields/list.html", context)


@login_required
def search_custom_fields(request, page):
    search_text = (request.GET.get("search_text") or "").strip()
    module = request.GET.get("module") or ""
    base_qs = get_custom_field_queryset(request)
    if search_text:
        base_qs = base_qs.filter(field_label__icontains=search_text)
    if module:
        base_qs = base_qs.filter(module=module)
    paginator = Paginator(base_qs, PAGE_SIZE, orphans=ORPHANS)
    page_object = paginator.get_page(page)
    trans = get_translations(request)
    return render(
        request,
        "custom_fields/cf-data.html",
        {
            "page_object": page_object,
            "module_display": get_module_display_map(trans),
            "field_type_display": get_field_type_display_map(trans),
            "sidebar": "configurations",
            "submenu": "custom_fields"
        },
    )


@login_required
def create_custom_field(request):
    trans = get_translations(request)
    if request.method == "POST":
        form = CustomFieldDefinitionForm(
            request.POST, organization=request.user.organization, trans=trans
        )
        if form.is_valid():
            cf = form.save(commit=False)
            cf.organization = request.user.organization
            cf.created_by = str(request.user.id)
            cf.updated_by = str(request.user.id)
            cf.save()
            messages.success(request, trans["custom_field_created"])
            return redirect("custom_fields:list")
    else:
        form = CustomFieldDefinitionForm(trans=trans)
        
    context = {
        "form": form,
        "title": trans["add_custom_field"],
        "sidebar": "configurations",
        "submenu": "custom_fields"
    }
    return render(request, "custom_fields/form.html", context)


@login_required
def update_custom_field(request, pk):
    cf = get_object_or_404(CustomFieldDefinition, pk=pk, organization=request.user.organization)
    trans = get_translations(request)
    if request.method == "POST":
        form = CustomFieldDefinitionForm(
            request.POST, instance=cf, organization=request.user.organization, trans=trans
        )
        if form.is_valid():
            cf = form.save(commit=False)
            cf.updated_by = str(request.user.id)
            cf.save()
            messages.success(request, trans["custom_field_updated"])
            return redirect("custom_fields:list")
    else:
        form = CustomFieldDefinitionForm(instance=cf, trans=trans)
        
    context = {
        "form": form,
        "title": trans["update_custom_field"],
        "cf": cf,
        "sidebar": "configurations",
        "submenu": "custom_fields"
    }
    return render(request, "custom_fields/form.html", context)


@login_required
def delete_custom_field(request, pk):
    cf = get_object_or_404(CustomFieldDefinition, pk=pk, organization=request.user.organization)
    if request.method == "POST":
        cf.soft_delete()
        messages.success(request, get_translations(request)["custom_field_deleted"])
    return redirect("custom_fields:list")


@login_required
def toggle_custom_field(request, pk):
    cf = get_object_or_404(CustomFieldDefinition, pk=pk, organization=request.user.organization)
    if request.method == "POST":
        cf.is_active = not cf.is_active
        cf.updated_by = str(request.user.id)
        cf.save()
        if request.headers.get("HX-Request"):
            return HttpResponse(status=204)
        trans = get_translations(request)
        state = trans["activated"] if cf.is_active else trans["deactivated"]
        messages.success(
            request,
            trans["custom_field_toggle_message"].format(label=cf.field_label, state=state),
        )
    return redirect("custom_fields:list")


# API Views

class CustomFieldDefinitionAPIList(generics.ListCreateAPIView):
    serializer_class = CustomFieldDefinitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomFieldDefinition.objects.filter(
            organization=self.request.user.organization, is_deleted=False
        )

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization,
            created_by=str(self.request.user.id),
            updated_by=str(self.request.user.id),
        )


class CustomFieldDefinitionAPIDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomFieldDefinitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomFieldDefinition.objects.filter(
            organization=self.request.user.organization, is_deleted=False
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=str(self.request.user.id))


class CustomFieldValueAPIView(generics.ListAPIView):
    serializer_class = CustomFieldValueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        entity_uuid = self.request.query_params.get("entity_uuid")
        if not entity_uuid:
            return CustomFieldValue.objects.none()
        return CustomFieldValue.objects.filter(
            entity_uuid=entity_uuid,
            definition__organization=self.request.user.organization
        )
