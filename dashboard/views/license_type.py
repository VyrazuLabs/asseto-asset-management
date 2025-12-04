from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required,permission_required
from dashboard.forms import LicenseTypeForm
from dashboard.models import LicenseType
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q

@login_required
@permission_required('authentication.view_license_type')
def license_type_list(request):
    ORPHANS=1
    PAGE_SIZE=10

    license_types=LicenseType.undeleted_objects.all().order_by("-created_at")
    print(license_types)
    paginator=Paginator(license_types,ORPHANS,PAGE_SIZE)
    page_number=request.GET.get('page')
    page_object=paginator.get_page(page_number)
    context={
        'page_object':page_object,
        'sidebar':'License_type',
        'title':'License Type'
    }
    return render(request,'dashboard/license_type/list.html',context=context)


@login_required
@permission_required('authentication.add_license_type')
def license_type_add(request):
    if request.method=="POST":
        license_type_form=LicenseTypeForm(request.POST)
        if license_type_form.is_valid():
            license_type_form.save()
            messages.success(request,'License Type added successfully')
            return HttpResponse(status=204)
    else:
        license_type_form=LicenseTypeForm()
    return render(request,'dashboard/license_type/license-type-modal.html',context={'form':license_type_form})


@login_required
@permission_required('authentication.view_license_type')
def license_type_details(request,id):
    get_license_type=get_object_or_404(LicenseType,pk=id)

    history_list = LicenseType.history.filter(id=get_license_type.id)
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context={'page_object':page_object,'license_type':get_license_type,'title':f'Details-{get_license_type.name}'}
    return render(request,'dashboard/license_type/details.html',context=context)


@login_required
@permission_required('authentication.edit_license_type')
def update_license_type(request,id):
    get_license_type=get_object_or_404(LicenseType,pk=id)
    if request.method=="POST":
        license_type_form=LicenseTypeForm(request.POST,instance=get_license_type)
        if license_type_form.is_valid():
            license_type_form.save()
            messages.success(request,'Licese Type updated successfully')
            return HttpResponse(status=204)
    else:
        license_type_form=LicenseTypeForm(instance=get_license_type)
        
    context={
        'form':license_type_form,
        'modal_title':'Update License Type'
    }
    return render(request,'dashboard/license_type/license-type-modal.html',context=context)


@login_required
def license_type_status(request, id):
    if request.method == "POST":
        product_type = get_object_or_404(
            LicenseType.undeleted_objects, pk=id)
        product_type.status = False if product_type.status else True
        product_type.save()
    return HttpResponse(status=204)


@login_required
@permission_required('authentication.delete_license_type')
def delete_license_type(request,id):
    get_license_type=get_object_or_404(LicenseType, pk=id)
    print(get_license_type.name)
    get_license_type.status=False
    get_license_type.soft_delete()
    messages.success(request,'License Type deleted sucessfully')
    return redirect('dashboard:license_type_list')

def search_license_type(request):
    search_text=request.GET.get('search_text')
    get_license_types=LicenseType.undeleted_objects.filter(name__icontains=search_text).order_by('-created_at')[:10]
    return render(request, 'dashboard/license_type/license-types-data.html', {'get_license_types': get_license_types})
