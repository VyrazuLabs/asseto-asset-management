import os
from django.contrib.auth.decorators import login_required,permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from assets.forms import AssetStatusForm
from assets.models import Asset, AssetStatus
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q,Count
PAGE_SIZE = 10
ORPHANS = 1


@login_required
@permission_required('authentication.view_asset_status')
def asset_status_list(request):
    all_asset_status_list = (
        AssetStatus.undeleted_objects
        .filter(Q(organization=None) | Q(organization=request.user.organization))
    )

    deleted_asset_status_count = (
        AssetStatus.deleted_objects
        .filter(
            Q(organization=None, can_modify=True) |
            Q(organization=request.user.organization, can_modify=True)
        )
        .count()
    )

    paginator = Paginator(all_asset_status_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    # Count distinct assets per asset status
    asset_counts = (
        Asset.objects
        .filter(
            organization=request.user.organization,
            asset_status__in=all_asset_status_list
        )
        .values("asset_status")
        .annotate(asset_count=Count("id", distinct=True))
    )

    # Map: {asset_status_id: asset_count}
    asset_status_asset_count = {
        item["asset_status"]: item["asset_count"]
        for item in asset_counts
    }
    is_demo = os.environ.get('IS_DEMO')
    if is_demo:
        is_demo=True
    else:
        is_demo=False

    context = {
        'sidebar': 'admin',
        'submenu': 'Asset_Status',
        'page_object': page_object,
        'deleted_asset_status_count': deleted_asset_status_count,
        'asset_status_asset_count': asset_status_asset_count,
        'title': 'Asset Status',
        'is_demo':is_demo
    }
    return render(request, 'assets/asset_status_list.html', context=context)


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
@permission_required('authentication.asset_status_details')
def asset_status_details(request,id):
    asset_status = get_object_or_404(
    AssetStatus.undeleted_objects, pk=id)

    history_list = AssetStatus.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'page_object': page_object,
               'sidebar': 'admin','submenu': 'Asset_Status', 'asset_status': asset_status, 'title': f'Details-{asset_status.name}'}
    return render(request, 'assets/asset_status_details.html', context=context)

@login_required
@permission_required('authentication.edit_asset_status')
def edit_asset_status(request,id):
    asset_status = get_object_or_404(
    AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)
    form = AssetStatusForm(request.POST or None, instance=asset_status,organization=request.user.organization,  pk=asset_status.id)

    if request.method == "POST":

        if form.is_valid():
            form.save()
            messages.success(request, 'Asset Status updated successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Update Asset Status"}
    return render(request, 'assets/add_asset_status.html', context)

@login_required
def asset_status_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'assets/asset-status-data.html', {
            'page_object': AssetStatus.undeleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })

    status_list = AssetStatus.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(status_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'assets/asset-status-data.html', {'page_object': page_object})


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