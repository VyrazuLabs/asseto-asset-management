"""Shared service-layer base classes and helpers for the project.

This module provides the multi-tenant org-scoping base that every later
per-app ``Service`` class builds on (``BaseMultiTenantService``), plus a
shared helper that consolidates duplicated asset-condition aggregation logic
found across several apps' ``utils.py`` modules (``build_asset_conditions_map``).
"""

from collections import defaultdict


class BaseMultiTenantService:
    """Base class for per-app service classes that operate on org-scoped models.

    Subclasses should call ``base_queryset`` to obtain a queryset that is
    always filtered to the current user's organization, preventing
    cross-tenant data leakage.
    """

    @staticmethod
    def base_queryset(model, user):
        """Return an org-scoped, non-deleted queryset for ``model``.

        Args:
            model: A Django model class that exposes an ``undeleted_objects``
                manager (the project's ``SoftDeleteManager`` convention, see
                ``dashboard/models.py``) and an ``organization`` foreign key.
            user: The current ``User`` instance whose ``organization`` is used
                to scope the queryset.

        Returns:
            QuerySet: ``model.undeleted_objects`` filtered to
            ``organization=user.organization``. Never returns rows belonging
            to a different organization.
        """
        return model.undeleted_objects.filter(organization=user.organization)


def build_asset_conditions_map(audits_queryset):
    """Build a mapping of asset id to the list of conditions from its audits.

    Consolidates duplicated logic independently found in ``clients/utils.py``,
    ``vendors/utils.py``, ``audit/utils.py``, and ``assets/utils.py``, all of
    which iterate an ``Audit`` queryset and append ``audit.condition`` to a
    list keyed by ``audit.asset_id``.

    Args:
        audits_queryset: An iterable/queryset of ``Audit`` instances, each
            exposing ``asset_id`` and ``condition`` attributes.

    Returns:
        dict[Any, list]: A ``defaultdict(list)`` mapping each ``asset_id`` to
        the ordered list of ``condition`` values from its audits, in the
        order the queryset was iterated.
    """
    asset_conditions_map = defaultdict(list)
    for audit in audits_queryset:
        asset_conditions_map[audit.asset_id].append(audit.condition)
    return asset_conditions_map
