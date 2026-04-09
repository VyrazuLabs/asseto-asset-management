"""
Business logic orchestration for the assets module.

Contains multi-model operations that span across Asset, AssignAsset,
AssetStatus, and notifications. Views should delegate to these functions
rather than containing inline business logic.
"""
import structlog
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Asset, AssignAsset, AssetStatus

log = structlog.get_logger(__name__)


@transaction.atomic
def change_asset_status(asset_id, new_status_name, organization, updated_by):
    """
    Change an asset's status and handle side effects (unassign if not 'Assigned').

    Args:
        asset_id: UUID of the asset.
        new_status_name: Name of the new AssetStatus.
        organization: Organization instance for scoping.
        updated_by: Full name of the user making the change.

    Returns:
        tuple: (asset, new_status_name) on success.

    Raises:
        Asset.DoesNotExist: If asset not found.
    """
    asset = Asset.objects.filter(id=asset_id).first()
    if not asset:
        raise Asset.DoesNotExist("Asset not found")

    get_status = AssetStatus.objects.filter(
        Q(organization=organization) | Q(organization__isnull=True),
        name=new_status_name
    ).first()

    asset.asset_status = get_status
    asset.updated_by = updated_by

    if get_status and get_status.name != "Assigned":
        asset.is_assigned = False
        AssignAsset.objects.filter(asset=asset).delete()

    asset.save()
    log.info("asset_status_changed", asset_id=str(asset_id), new_status=new_status_name)
    return asset, new_status_name


@transaction.atomic
def unassign_asset_from_list(asset_id, organization):
    """
    Unassign an asset and set its status to Available.

    Args:
        asset_id: UUID of the asset.
        organization: Organization instance for scoping.
    """
    asset = Asset.objects.filter(id=asset_id).first()
    if not asset:
        return

    asset.is_assigned = False
    available_status = AssetStatus.objects.filter(
        Q(organization=organization) | Q(organization__isnull=True),
        name='Available'
    ).first()
    asset.asset_status = available_status
    asset.save()

    AssignAsset.objects.filter(
        asset=asset,
        asset__organization=organization
    ).delete()

    log.info("asset_unassigned", asset_id=str(asset_id))


@transaction.atomic
def assign_asset_to_user(asset, user, organization):
    """
    Assign an asset to a user and update its status.

    Args:
        asset: Asset instance.
        user: User instance to assign to.
        organization: Organization for status lookup.

    Returns:
        AssignAsset instance.
    """
    assign_obj, created = AssignAsset.objects.update_or_create(
        asset=asset,
        defaults={'user': user},
    )
    asset.is_assigned = True
    assigned_status = AssetStatus.objects.filter(
        Q(organization=organization) | Q(organization__isnull=True),
        name='Assigned'
    ).first()
    asset.asset_status = assigned_status
    asset.save()

    log.info("asset_assigned", asset_id=str(asset.id), user_id=str(user.id))
    return assign_obj
