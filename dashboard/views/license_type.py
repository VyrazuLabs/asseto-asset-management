from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, permission_required
from dashboard.forms import LicenseTypeForm
from dashboard.models import LicenseType
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from dashboard.utils import get_license_type_list

@login_required
@permission_required('authentication.view_license_type')
def license_type_list(request):
    page_object, license_type_form, license_type_count, stats = get_license_type_list(request)
    
    context = {
        'page_object': page_object,
        'license_type_form': license_type_form,
        'license_type_count': license_type_count,
        'sidebar': 'admin',
        'submenu': 'license_type',
        'title': 'License Types',
        **stats
    }
    return render(request, 'dashboard/license_type/list.html', context=context)

@login_required
@permission_required('authentication.add_license_type')
def license_type_add(request):
    if request.method == "POST":
        license_type_form = LicenseTypeForm(request.POST)
        if license_type_form.is_valid():
            license_type_form.save()
            messages.success(request, 'License Type added successfully')
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "licenseTypeAdded"
            return response
    else:
        license_type_form = LicenseTypeForm()
    
    return render(request, 'dashboard/license_type/license-type-modal.html', {
        'form': license_type_form,
        'modal_title': 'Add License Type'
    })

@login_required
@permission_required('authentication.view_license_type')
def license_type_details(request, id):
    get_license_type = get_object_or_404(LicenseType, pk=id)
    history_list = LicenseType.history.filter(id=get_license_type.id)
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'page_object': page_object,
        'license_type': get_license_type,
        'title': f'Details-{get_license_type.name}',
        'sidebar': 'admin',
        'submenu': 'license_type',
    }
    return render(request, 'dashboard/license_type/details.html', context=context)

@login_required
@permission_required('authentication.edit_license_type')
def update_license_type(request, id):
    get_license_type = get_object_or_404(LicenseType, pk=id)
    if request.method == "POST":
        license_type_form = LicenseTypeForm(request.POST, instance=get_license_type)
        if license_type_form.is_valid():
            license_type_form.save()
            messages.success(request, 'License Type updated successfully')
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "licenseTypeUpdated"
            return response
    else:
        license_type_form = LicenseTypeForm(instance=get_license_type)
        
    context = {
        'form': license_type_form,
        'modal_title': 'Update License Type',
        'sidebar': 'admin',
        'submenu': 'license_type',
    }
    return render(request, 'dashboard/license_type/license-type-modal.html', context=context)

@login_required
def license_type_status(request, id):
    if request.method == "POST":
        license_type = get_object_or_404(LicenseType.undeleted_objects, pk=id)
        license_type.status = not license_type.status
        license_type.save()
    return HttpResponse(status=204)

@login_required
@permission_required('authentication.delete_license_type')
def delete_license_type(request, id):
    if request.method == 'POST':
        get_license_type = get_object_or_404(LicenseType, pk=id)
        get_license_type.status = False
        get_license_type.soft_delete()
        messages.success(request, 'License Type deleted successfully')
    return redirect('dashboard:license_type_list')

@login_required
def search_license_type(request, page):
    page_object, _, license_type_count, _ = get_license_type_list(request, page_number=page)
    return render(request, 'dashboard/license_type/license-types-data.html', {
        'page_object': page_object,
        'license_type_count': license_type_count
    })
