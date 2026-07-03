import datetime
from zoneinfo import ZoneInfo

from django.db.models import Q, QuerySet
from django.utils import timezone
from abc import ABC, abstractmethod
from common.pagination import add_pagination
from gate_pass.models import GatePass
from django.shortcuts import get_object_or_404

FILTER_FIELDS = {
    "status": "status",
    "type": "movement_type",
    "vendor": "destination_vendor__id",
    "raised_by": "raised_by__id",
    "authorised_by": "authorised_by__id",
    "asset": "asset__id",
}

SEARCH_FIELDS = [
    "asset__name",
    "asset__tag",
    "asset__serial_no",
    "destination_vendor__name",
    "raised_by__full_name",
    "authorised_by__full_name",
]


def get_gate_pass_list():
    get_items = GatePass.objects.all().order_by("-created_at")
    get_inward_pass_count = get_items.filter(movement_type=1, status=1).count()
    get_pending_authorization_count = get_items.filter(status=0).count()
    now = timezone.localtime(timezone.now())
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    get_passes_created_today_count = get_items.filter(
        created_at__gte=start_of_day
    ).count()

    # Filter By item List
    raised_by_users = GatePass.objects.values(
        "raised_by__id", "raised_by__full_name"
    ).distinct()
    get_authorised_by_list = GatePass.objects.values(
        "authorised_by__id", "authorised_by__full_name"
    ).distinct()
    get_destination_vendor_list = GatePass.objects.values(
        "destination_vendor__id", "destination_vendor__name"
    ).distinct()
    get_asset_list = GatePass.objects.values("asset_id", "asset__name").distinct()

    context = {
        "items": get_items,
        "inward_pass_count": get_inward_pass_count,
        "pending_authorization_count": get_pending_authorization_count,
        "passes_created_today_count": get_passes_created_today_count,
        "destination_vendor_list": get_destination_vendor_list,
        "raised_by_list": raised_by_users,
        "authorised_by_list": get_authorised_by_list,
        "asset_list": get_asset_list,
    }
    return context


def search_and_filter_gate_passes(request):
    search = request.GET.get("search_text")

    queryset = GatePass.objects.all()
    if search:
        query = Q()
        for field in SEARCH_FIELDS:
            query |= Q(**{f"{field}__icontains": search})
        queryset = queryset.filter(query)

    for param, field in FILTER_FIELDS.items():
        if value := request.GET.get(param):
            queryset = queryset.filter(**{field: value})

    return queryset.distinct().order_by("-created_at")


class GatePassRepository(ABC):

    @abstractmethod
    def get_all(self) -> QuerySet: ...

    @abstractmethod
    def get_by_id(self, gate_pass_id) -> GatePass: ...

    @abstractmethod
    def save(self, gate_pass: GatePass) -> GatePass: ...


class GatePassRepositoryImpl(GatePassRepository):

    def get_all(self) -> QuerySet:
        return GatePass.objects.all()

    def get_by_id(self, gate_pass_id) -> GatePass:
        return get_object_or_404(GatePass, pk=gate_pass_id)

    def save(self, gate_pass: GatePass) -> GatePass:

        gate_pass.save()

        return gate_pass


class BaseFilter(ABC):

    @abstractmethod
    def apply(self, query_set: QuerySet, value) -> QuerySet: ...


class SearchGatePass(BaseFilter):

    def apply(self, query_set: QuerySet, value: str) -> QuerySet:
        return query_set.filter(
            Q(asset__name__icontains=value)
            | Q(asset__tag__icontains=value)
            | Q(destination_vendor__name__icontains=value)
            | Q(asset__serial_no__icontains=value)
            | Q(raised_by__full_name__icontains=value)
            | Q(authorised_by__full_name__icontains=value)
        )


class MovementTypeFilter(BaseFilter):
    def apply(self, queryset: QuerySet, value: str) -> QuerySet:
        return queryset.filter(movement_type=value)


class RaisedByFilter(BaseFilter):
    def apply(self, queryset: QuerySet, value: str) -> QuerySet:
        return queryset.filter(raised_by__id=value)


class DestinationVendorFilter(BaseFilter):
    def apply(self, queryset: QuerySet, value: str) -> QuerySet:
        return queryset.filter(destination_vendor__id=value)


class ExpectedReturnDateFilter(BaseFilter):
    def apply(self, queryset: QuerySet, value: str) -> QuerySet:
        return queryset.filter(expected_return_date=value)


class AssetFilter(BaseFilter):
    def apply(self, queryset: QuerySet, value: str) -> QuerySet:
        return queryset.filter(asset__id=value)


FILTER_MAP: dict[str, BaseFilter] = {
    "search_text": SearchGatePass(),
    "movement-type": MovementTypeFilter(),
    "raised-by": RaisedByFilter(),
    "destination-vendor": DestinationVendorFilter(),
    "expected-return-date": ExpectedReturnDateFilter(),
    "asset": AssetFilter(),
}


class GatePassFilterService:
    def apply_filters(self, query_set, parms: dict):
        for key, filter_object in FILTER_MAP.items():
            if value := parms.get(key):
                query_set = filter_object.apply(query_set, value)

        return query_set


class GatePassSerializer:
    @staticmethod
    def serialize_list_item(item, request):
        current_host = request.get_host()
        return {
            "id": item.id,
            "status": item.status,
            "asset_detail": {
                "name": item.asset.name,
                "tag": item.asset.tag,
            },
            "movement_type": item.movement_type,
            "destination_vendor": {
                "name": item.destination_vendor.name,
            },
            "expected_return_date": item.expected_return_date,
            "purpose_of_movement": item.purpose_of_movement,
            "raised_by": {
                "profile_image": (
                    f"http//{current_host}" + item.raised_by.profile_pic.url
                    if item.raised_by.profile_pic
                    else ""
                ),
                "name": item.raised_by.full_name,
            },
            "authorised_by": {
                "profile_image": (
                    f"http//{current_host}" + item.authorised_by.profile_pic.url
                    if item.authorised_by and item.authorised_by.profile_pic
                    else ""
                ),
                "name": (
                    item.authorised_by.full_name
                    if item.authorised_by is not None
                    else ""
                ),
            },
        }


class GatePassService:

    def __init__(self, repository: GatePassRepository):
        self.repository = repository

    def get_list_with_stats(self, page, request) -> dict:
        gate_passes = self.repository.get_all()
        today = datetime.datetime.now(tz=ZoneInfo("Asia/Kolkata")).date()
        stats = {
            "inward_pass_count": gate_passes.filter(movement_type=1).count(),
            "pending_authorization_count": gate_passes.filter(
                authorised_by=None
            ).count(),
            "passes_created_today_count": gate_passes.filter(
                created_at__date=today
            ).count(),
        }
        data = [
            GatePassSerializer.serialize_list_item(gate_pass, request)
            for gate_pass in gate_passes
        ]
        paginated_data = add_pagination(data, page=page)
        return {**paginated_data, **stats}

    # def approved_or_reject(self, request, gate_pass: GatePass):
    #     # [(0, 'Pending'), (1, 'Approved'), (2, 'Draft'), (3, 'Rejected'), (4, 'Checked Out')]

    #     if gate_pass.status == 1:
    #         gate_pass.authorised_by = None
    #         gate_pass.status = 3

    #         self.repository.save(gate_pass)
    #         return "GatePass Rejected"
    #     gate_pass.authorised_by = request.user
    #     gate_pass.status = 1

    #     self.repository.save(gate_pass)
    #     return "GatePass Approved"
