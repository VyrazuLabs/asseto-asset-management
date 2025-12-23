from django.shortcuts import get_object_or_404, redirect, render
from license.forms import LicenseForm
from license.models import License
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib import messages
from django.db.models import Q
@login_required
@permission_required('authentication.view_license')
def license_list(request):
    PAGE_SIZE=10
    ORPHANS=1
    licenses=License.undeleted_objects.all().order_by("-created_at")
    paginator=Paginator(licenses,PAGE_SIZE,orphans=ORPHANS)
    page_number=request.GET.get('page')
    page_oject=paginator.get_page(page_number)
    context={
        'page_object':page_oject,
        'sidebar':'license',
        'title':'License'
    }
    return render(request,'license/license_list.html',context=context)

@login_required
@permission_required('authentication.add_license')
def add_license(request):
    if request.method=="POST":
        license_form=LicenseForm(request.POST)
        if license_form.is_valid():
            license_form.save()
            messages.success(request, "License add sucessfully")
            return redirect('license:license_list')
    else:
        license_form=LicenseForm()
    
    return render(request,'license/add_license.html',context={'form':license_form,'title':'Add License','sidebar':'license'})



@login_required
@permission_required('authentication.view_license')
def license_details(request,id):
    license=get_object_or_404(License,pk=id)
    history_list = License.history.filter(id=license.id)
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context={'license':license,'pag_object':page_object,'title':f'Detail-{license.name}','sidebar':'license'}
    return render(request,'license/license-details.html',context=context)

@login_required
@permission_required('authentication.edit_license')
def update_license(request,id):
    get_license=get_object_or_404(License,pk=id)
    if request.method=="POST":
        license_form=LicenseForm(request.POST,instance=get_license)
        if license_form.is_valid():
            license_form.save()
            messages.success(request, "License update sucessfully")
            return redirect('license:license_list')
    else:
        license_form=LicenseForm(instance=get_license)
    
    return render(request,'license/update-license.html',context={'form':license_form,'title':f'Update-{get_license.name}','sidebar':'license'})


@login_required
@permission_required('authentication.delete_license')
def delete_license(request,id):
    get_license=get_object_or_404(License,pk=id)
    get_license.soft_delete()
    messages.success(request,'Item sent to Trash')
    return redirect('license:license_list')

@login_required
@permission_required('authentication.view_license')
def search_license(request):
    search_text=request.GET.get('search_text')
    licenses=License.objects.filter(Q(name__icontains=search_text)|Q(license_type__name__icontains=search_text)|Q(vendor__name__icontains=search_text)|Q(seats__icontains=search_text))
    print(licenses)
    return render(request,'license/searched_data.html',{'licenses':licenses})
