from django.shortcuts import render, redirect
from .forms import AssetForm, AssignedAssetForm, ReassignedAssetForm
from django.contrib import messages
from .models import Asset, AssetSpecification, AssignAsset
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q


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


@login_required
@user_passes_test(manage_access_for_assets)
def list(request):
    asset_list = Asset.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    asset_form = AssetForm(organization=request.user.organization)
    assign_asset_form = AssignedAssetForm(
        organization=request.user.organization)
    reassign_asset_form = ReassignedAssetForm(
        organization=request.user.organization)

    context = {
        'sidebar': 'assets',
        'submenu': 'list',
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

    asset = get_object_or_404(
        Asset.undeleted_objects, pk=id, organization=request.user.organization)
    assetSpecifications = AssetSpecification.objects.filter(asset=asset)

    history_list = asset.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'assets', 'asset': asset, 'submenu': 'list', 'page_object': page_object,
               'assetSpecifications': assetSpecifications, 'title': 'Asset - Details'}
    return render(request, 'assets/detail.html', context=context)


@login_required
@permission_required('authentication.edit_asset')
def update(request, id):

    asset = get_object_or_404(
        Asset.undeleted_objects, pk=id, organization=request.user.organization)
    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    form = AssetForm(request.POST or None, instance=asset,
                     organization=request.user.organization)

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
    form = AssetForm(request.POST or None,
                     organization=request.user.organization)

    if request.method == "POST":

        if form.is_valid():
            asset = form.save(commit=False)
            asset.organization = request.user.organization
            asset.save()

            specifications_names = request.POST.getlist(
                'specifications_name')
            specifications_values = request.POST.getlist(
                'specifications_value')

            for name, value in zip(specifications_names, specifications_values):

                if name != '' or value != '':

                    AssetSpecification.objects.create(
                        asset=asset, name=name, value=value)

            messages.success(request, 'Asset added successfully')
            return redirect('assets:list')

    context = {
        'sidebar': 'assets',
        'submenu': 'add',
        'form': form,
        'title': 'Assets - Add'
    }

    return render(request, 'assets/add.html', context=context)


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
    if request.method == 'POST':
        if form.is_valid():
            form.instance.asset.is_assigned = True
            form.instance.asset.save()
            form.save()
            messages.success(request, 'Asset assigned to user successfully')
            return HttpResponse(status=204)
    context = {'form': form}
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
