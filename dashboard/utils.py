from assets.models import AssignAsset
from dashboard.models import Department
from dashboard.forms import DepartmentForm
from django.core.paginator import Paginator
from django.db.models import Q,Count

PAGE_SIZE = 10
ORPHANS = 1
def get_department_list(request):
    department_list = (
        Department.undeleted_objects
        .filter(organization=request.user.organization)
    )
    
    deleted_department_count = (
        Department.deleted_objects
        .filter(organization=request.user.organization)
        .count()
    )

    paginator = Paginator(department_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    department_form = DepartmentForm()

    # Count distinct assets per department
    asset_counts = (
        AssignAsset.objects
        .filter(
            asset__is_deleted=False,
            asset__organization=request.user.organization,
            user__department__in=department_list
        )
        .values("user__department")
        .annotate(asset_count=Count("asset", distinct=True))   # ✅ unique assets
    )

    # Map: {department_id: asset_count}
    department_asset_count = {
        item["user__department"]: item["asset_count"]
        for item in asset_counts
    }
    return page_object, department_form, department_asset_count,deleted_department_count