from django.shortcuts import render, redirect
from .forms import AssetForm, AssignedAssetForm, ReassignedAssetForm,AssetImageForm,AssetStatusForm
from django.contrib import messages
from .models import Asset, AssetSpecification, AssignAsset,AssetImage,AssetStatus
from django.core.paginator import Paginator
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import json
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
from django.urls import reverse

def grouper(iterable, n):
    # Groups iterable into chunks of size n
    args = [iter(iterable)] * n
    return list(zip_longest(*args, fillvalue=None))

from itertools import zip_longest
from .models import Asset,AssignAsset
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from authentication.models import User

@login_required
@permission_required('assets.change_asset', raise_exception=True)
def release_asset(request, id):
    if request.method == 'POST':
        asset = get_object_or_404(Asset, pk=id)
        # Assumes status 3 means "Ready To Deploy"
        asset.status = 1
        asset.save()
        messages.success(request, f"Asset '{asset.name}' has been released and is now Ready To Deploy.")
    return redirect('assets:list')

from django.contrib.auth import get_user_model

@login_required
@permission_required('assets.change_asset', raise_exception=True)
def assign_assets(request, id):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        asset = get_object_or_404(Asset, pk=id, organization=request.user.organization)
        User = get_user_model()
        selected_user = get_object_or_404(User, pk=user_id, is_active=True)
        
        # Create or update the AssignAsset record
        assign_obj, created = AssignAsset.objects.update_or_create(
            asset=asset,
            defaults={'user': selected_user},
        )

        # Mark asset as assigned
        asset.is_assigned = True
        asset.status = 0  # 0 = 'Assigned' by your STATUS_CHOICES
        asset.save()

        messages.success(request, f"Asset assigned to user.")
        return redirect('assets:list')

    # Optionally, for GET requests, you might want to show a form or a 404 error:
    return redirect('assets:list')
    # form = AssignedAssetForm(request.POST or None,
    #                          organization=request.user.organization)
    # image_form = AssetImageForm(request.POST, request.FILES)
    # if request.method == 'POST':
    #     if form.is_valid():
    #         form.instance.asset.is_assigned = True
    #         # form.instance.asset.status = 0
    #         form.instance.asset.save()
    #         form.save()
    #         for f in request.FILES.getlist('image'): # 'image' is the name of your file input
    #             AssetImage.objects.create(asset=form.instance.asset, image=f)
    #         messages.success(request, 'Asset assigned to user successfully')
    #         return HttpResponse(status=204)
    # else:
    #     form = AssignedAssetForm()
    #     image_form = AssetImageForm()
    # context = {'form': form,'image_form':image_form}
    # return render(request, 'assets/assign-asset-modal.html', context=context)

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access_for_assets(user):
    permissions_list = [
        'authentication.edit_asset',
        'authentication.view_asset',
        'authentication.delete_asset',
        'authentication.add_asset',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


def manage_access_for_assign_assets(user):
    permissions_list = [
        'authentication.reassign_assign_asset',
        'authentication.add_assign_asset',
        'authentication.delete_assign_asset',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

def manage_access_for_assets_status(user):
    permissions_list = [
        'authentication.edit_asset_status',
        'authentication.view_asset_status',
        'authentication.delete_asset_status',
        'authentication.add_asset_status',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

@login_required
@user_passes_test(manage_access_for_assets)
def listed(request):
    asset_list = Asset.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    asset_form = AssetForm(organization=request.user.organization)
    assign_asset_form = AssignedAssetForm(organization=request.user.organization)
    reassign_asset_form = ReassignedAssetForm(organization=request.user.organization)
    active_users=(User.objects.filter(is_active=True))
    # active_user=[active_users]
    # Gather the first image per asset in the current page
    asset_ids_in_page = [asset.id for asset in page_object]
    images_qs = AssetImage.objects.filter(asset_id__in=asset_ids_in_page).order_by('uploaded_at')
    
    # Map asset ID to its first image
    asset_images = {}
    for img in images_qs:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

    context = {
        'active_user':active_users,
        'sidebar': 'assets',
        'submenu': 'list',
        'asset_images': asset_images,  # dict {asset.id: first AssetImage instance}
        'page_object': page_object,
        'asset_form': asset_form,
        'assign_asset_form': assign_asset_form,
        'reassign_asset_form': reassign_asset_form,
        'title': 'Assets'
    }

    return render(request, 'assets/list.html', context=context)


@login_required
@permission_required('authentication.view_asset')
def details(request, id):

    asset = Asset.objects.filter(pk=id, organization=request.user.organization).first()
    if asset is None:
        assetSpecifications=AssignAsset.objects.filter(id=id).first()
        asset=assetSpecifications.asset

    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    img_array=[]
    get_asset_img=AssetImage.objects.filter(asset=asset).values()
    for it in get_asset_img:
        img_array.append(it)

    months_int=asset.product.eol
    today=timezone.now().date()
    eol_date= today+relativedelta(months=months_int)

    arr_size=len(img_array)
    history_list = asset.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'assets', 'asset': asset, 'submenu': 'list', 'page_object': page_object,'arr_size':arr_size,
               'assetSpecifications': assetSpecifications, 'title': 'Asset - Details','get_asset_img':img_array}
    return render(request, 'assets/detail.html', context=context)


@login_required
@permission_required('authentication.edit_asset')
def update(request, id):

    asset = get_object_or_404(
        Asset.undeleted_objects, pk=id, organization=request.user.organization)
    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    form = AssetForm(request.POST or None, instance=asset,
                     organization=request.user.organization)
    image_form = AssetImageForm(request.POST or None, request.FILES)
    if request.method == "POST":

        if form.is_valid():

            assetSpecifications.delete()

            specifications_names = request.POST.getlist(
                'specifications_name')

            specifications_values = request.POST.getlist(
                'specifications_value')

            for name, value in zip(specifications_names, specifications_values):
                if name != '' or value != '':
                    AssetSpecification.objects.create(
                        asset=asset, name=name, value=value)

            asset = form.save(commit=False)
            asset.organization = request.user.organization
            asset.save()
            for f in request.FILES.getlist('image'): # 'image' is the name of your file input
                AssetImage.objects.create(asset=asset, image=f)

            messages.success(request, 'Asset updated successfully')
            return redirect('assets:list')

    context = {
        'sidebar': 'assets',
        'submenu': 'list',
        'form': form,
        'asset': asset,
        'assetSpecifications': assetSpecifications,
        'title': 'Asset - Update'
    }
    return render(request, 'assets/update-assets.html', context=context)


@login_required
@permission_required('authentication.add_asset')
def add(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)

        image_form = AssetImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            asset = form.save(commit=False)
            asset.organization = request.user.organization
            asset.save()

            form.save_m2m()
            # product = form.save()
            for f in request.FILES.getlist('image'): # 'image' is the name of your file input
                AssetImage.objects.create(asset=asset, image=f)
            return redirect('assets:list')
    else:
        form = AssetForm(organization=request.user.organization_id)
        image_form = AssetImageForm()

    context = {
        'form': form,
        'image_form': image_form,
        'title': 'Add Asset',
    }
    return render(request, 'assets/add.html', context)



@login_required
@permission_required('authentication.delete_asset')
def delete(request, id):

    if request.method == "POST":
        asset = get_object_or_404(
            Asset.undeleted_objects, pk=id, organization=request.user.organization)
        if asset.is_assigned:
            messages.error(
                request, 'Error! Asset is assigned to a user')
        else:
            asset.soft_delete()
            history_id = asset.history.first().history_id
            asset.history.filter(pk=history_id).update(history_type='-')
            messages.success(request, 'Asset deleted successfully.')

    return redirect('assets:list')


@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        asset = get_object_or_404(
            Asset.undeleted_objects, pk=id, organization=request.user.organization)
        asset.status = False if asset.status else True
        asset.save()
    return HttpResponse(status=204)


@login_required
def search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'assets/assets-data.html', {
            'page_object': Asset.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(serial_no__icontains=search_text) | Q(purchase_type__icontains=search_text) | Q(product__name__icontains=search_text)
                | Q(vendor__name__icontains=search_text) | Q(vendor__gstin_number__icontains=search_text) | Q(location__office_name__icontains=search_text) | Q(product__product_type__name__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    asset_list = Asset.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'assets/assets-data.html', {'page_object': page_object})


@login_required
@user_passes_test(manage_access_for_assign_assets)
def assigned_list(request):

    assign_asset_list = AssignAsset.objects.filter(
        asset__organization=request.user.organization).order_by('-asset__created_at')
    paginator = Paginator(assign_asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'assets',
        'submenu': 'assigned-assets',
        'page_object': page_object,
        'title': 'Assigned Assets'
    }

    return render(request, 'assets/assigned-list.html', context=context)


@login_required
@permission_required('authentication.add_assign_asset')
def assign_asset(request):
    form = AssignedAssetForm(request.POST or None,
                             organization=request.user.organization)
    image_form = AssetImageForm(request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            form.instance.asset.is_assigned = True
            # form.instance.asset.status = 0
            form.instance.asset.save()
            form.save()
            for f in request.FILES.getlist('image'): # 'image' is the name of your file input
                AssetImage.objects.create(asset=form.instance.asset, image=f)
            messages.success(request, 'Asset assigned to user successfully')
            return HttpResponse(status=204)
    else:
        form = AssignedAssetForm()
        image_form = AssetImageForm()
    context = {'form': form,'image_form':image_form}
    return render(request, 'assets/assign-asset-modal.html', context=context)


@login_required
@permission_required('authentication.reassign_assign_asset')
def reassign_asset(request, id):
    assignAsset = get_object_or_404(
        AssignAsset, pk=id, asset__organization=request.user.organization)
    form = ReassignedAssetForm(
        request.POST or None, instance=assignAsset, organization=request.user.organization)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(
                request, 'Asset re-assigned successfully')
            return HttpResponse(status=204)
    context = {'form': form}
    return render(request, 'assets/reassign-asset-modal.html', context=context)


@login_required
@permission_required('authentication.delete_assign_asset')
def delete_assign(request, id):
    if request.method == 'POST':
        assignAsset = get_object_or_404(
            AssignAsset, pk=id, asset__organization=request.user.organization)
        assignAsset.delete()
        assignAsset.asset.is_assigned = False
        assignAsset.asset.save()
        messages.success(request, 'Asset unassigned successfully')
    return redirect('assets:assigned_list')


@login_required
def assign_asset_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'assets/assigned-assets-data.html', {
            'page_object': AssignAsset.objects.filter(Q(asset__organization=request.user.organization) & (Q(
                asset__name__icontains=search_text) | Q(asset__serial_no__icontains=search_text) | Q(user__full_name__icontains=search_text) | Q(user__department__name__icontains=search_text)
            )).order_by('-asset__created_at')[:10]
        })

    asset_list = AssignAsset.objects.filter(
        asset__organization=request.user.organization).order_by('-asset__created_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'assets/assigned-assets-data.html', {'page_object': page_object})

def change_status(request, id):
    # asset_id=request.GET.get('id')
    try:
        if request.method in ['PATCH', 'POST']:
            try:
                asset = Asset.objects.filter(id=id).first()
            except Asset.DoesNotExist:
                return JsonResponse({'error': 'Asset not found'}, status=404)
            try:
                data = json.loads(request.body)
                new_status = int(data.get('status'))
            except (ValueError, KeyError, json.JSONDecodeError):
                return HttpResponseBadRequest('Invalid data')

            if new_status not in dict(Asset.STATUS_CHOICES).keys():
                return JsonResponse({'error': 'Invalid status'}, status=400)

            asset.status = new_status
            asset.save()
            return JsonResponse({'success': True, 'new_status': new_status})
    except Exception as e:
        print("ERROR",str(e))

    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@permission_required('authentication.add_asset_status')
def add_asset_status(request):
    form=AssetStatusForm(request.POST or None, request.user.organization)

    if request.method=="POST":
        if form.is_valid():
            asset_status=form.save(commit=False)
            asset_status.organization=request.user.organization
            asset_status.save()
            messages.success(request, "Status added sucessfully")
            # return redirect('assets:asset_status_list')
        
            # For HTMX: return 204 No Content to indicate success
            if request.headers.get('Hx-Request') == 'true':
                return HttpResponse(status=204)
            
            # For regular requests fallback
            return HttpResponseRedirect(reverse('assets:asset_status_list'))
    context = {'form': form, "modal_title": "Add Asset Status"}  
    return render(request,'assets/add_asset_status.html', context)

@login_required
@user_passes_test(manage_access_for_assets_status)
def asset_status_list(request):
    all_asset_status_list = AssetStatus.undeleted_objects.filter(
    organization=request.user.organization).order_by('-created_at')
    
    paginator = Paginator(all_asset_status_list,
        PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'admin',
        'submenu': 'Asset_Status',
        'page_object': page_object,
        'title': 'Asset Status'
    }
    return render(request,'assets/asset_status_list.html',context=context)

@login_required
@permission_required('authentication.asset_status_details')
def asset_status_details(request,id):
    asset_status = get_object_or_404(
    AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = AssetStatus.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'admin', 'page_object': page_object,
               'submenu': 'asset_status', 'asset_status': asset_status, 'title': 'Asset_Status - Details'}
    return render(request, 'assets/asset_status_details.html', context=context)

@login_required
@permission_required('authentication.edit_asset_status')
def edit_asset_status(request,id):
    asset_status = get_object_or_404(
    AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)
    form = AssetStatusForm(request.POST or None, instance=asset_status,
                               organization=request.user.organization,  pk=asset_status.id)

    if request.method == "POST":

        if form.is_valid():
            form.save()
            messages.success(request, 'Asset Status updated successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Update Asset Status"}
    return render(request, 'assets/add_asset_status.html', context)

@login_required
@permission_required('authentication.delete_asset_status')
def delete_asset_status(request,id):
    if request.method == 'POST':
        product_category = get_object_or_404(
        AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)
        product_category.status = False
        product_category.soft_delete()
        history_id = product_category.history.first().history_id
        product_category.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Asset Status deleted successfully')

    return redirect(request.META.get('HTTP_REFERER'))


