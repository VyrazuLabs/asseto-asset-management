
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
def release_asset(request, asset_id):
    if request.method == 'POST':
        asset = get_object_or_404(Asset, pk=asset_id)
        # Assumes status 3 means "Ready To Deploy"
        asset.status = 3
        asset.save()
        messages.success(request, f"Asset '{asset.name}' has been released and is now Ready To Deploy.")
    return redirect('assets:list')

from django.contrib.auth import get_user_model

@login_required
@permission_required('assets.change_asset', raise_exception=True)
def assign_asset(request, asset_id):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        # Assumes you have a field like asset.assigned_user (ManyToOne/User FK)
        # User = get_user_model()
        selected_user = get_object_or_404(User, pk=user_id, is_active=True)
        asset.assigned_user = selected_user
        get_assigned_asset=AssignAsset.objects.filter(asset=asset).first()
        if get_assigned_asset is not None:
            asset.status = 0  # Example: 0 for "Assigned"
        asset.save()
        messages.success(request, f"Asset '{asset.name}' assigned to {selected_user.get_full_name() or selected_user.username}.")
    return redirect('assets:list')
