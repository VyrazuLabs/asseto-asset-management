from django.core.paginator import Paginator
from django.db.models import Q,Count
from dashboard.models import Department, ProductType, LicenseType, ProductCategory
from dashboard.forms import DepartmentForm, ProductTypeForm, LicenseTypeForm
from assets.models import Asset, AssignAsset
from license.models import License

PAGE_SIZE = 10
ORPHANS = 1
def get_department_list(request, page_number=None):
    search_text = request.GET.get('search_text', '')
    status = request.GET.get('status', '')

    base_query = Department.undeleted_objects.filter(organization=request.user.organization)

    # Summary stats
    total_departments = base_query.count()
    active_departments = base_query.filter(status=True).count()
    inactive_departments = base_query.filter(status=False).count()
    deleted_department_count = Department.deleted_objects.filter(organization=request.user.organization).count()

    # Filtering
    if search_text:
        base_query = base_query.filter(
            Q(name__icontains=search_text) |
            Q(contact_person_name__icontains=search_text) |
            Q(contact_person_email__icontains=search_text) |
            Q(contact_person_phone__icontains=search_text)
        )

    if status == 'active':
        base_query = base_query.filter(status=True)
    elif status == 'inactive':
        base_query = base_query.filter(status=False)

    department_list = base_query.order_by('-created_at')

    paginator = Paginator(department_list, PAGE_SIZE, orphans=ORPHANS)
    if not page_number:
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
        .annotate(asset_count=Count("asset", distinct=True))
    )

    department_asset_count = {
        item["user__department"]: item["asset_count"]
        for item in asset_counts
    }

    stats = {
        'total_departments': total_departments,
        'active_departments': active_departments,
        'inactive_departments': inactive_departments,
        'deleted_department_count': deleted_department_count,
    }

    

    return page_object, department_form, department_asset_count, stats

    # ---------------- PRODUCT TYPE LIST ---------------- #

def get_product_type_list(request, page_number=None):
    search_text = request.GET.get('search_text', '')
    status = request.GET.get('status', '')

    base_query = ProductType.undeleted_objects.filter(
        Q(organization=request.user.organization) | Q(organization=None)
    )

    # Stats
    total_product_types = base_query.count()
    active_product_types = base_query.filter(status=True).count()
    inactive_product_types = base_query.filter(status=False).count()
    deleted_product_types_count = ProductType.deleted_objects.filter(can_modify=True).count()

    # Filtering
    if search_text:
        base_query = base_query.filter(name__icontains=search_text)

    if status == 'active':
        base_query = base_query.filter(status=True)
    elif status == 'inactive':
        base_query = base_query.filter(status=False)

    product_type_list = base_query.order_by('-created_at')

    paginator = Paginator(product_type_list, PAGE_SIZE, orphans=ORPHANS)
    if not page_number:
        page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    product_type_form = ProductTypeForm(organization=request.user.organization)

    # Asset count
    asset_counts = (
        Asset.undeleted_objects
        .filter(
            organization=request.user.organization,
            product__product_type__in=product_type_list
        )
        .values("product__product_type")
        .annotate(asset_count=Count("id", distinct=True))
    )

    product_type_asset_count = {
        item["product__product_type"]: item["asset_count"]
        for item in asset_counts
    }

    stats = {
        'total_product_types': total_product_types,
        'active_product_types': active_product_types,
        'inactive_product_types': inactive_product_types,
        'deleted_product_types_count': deleted_product_types_count,
    }

    return page_object, product_type_form, product_type_asset_count, stats

# ---------------- LICENSE TYPE LIST ---------------- #

def get_license_type_list(request, page_number=None):
    search_text = request.GET.get('search_text', '')
    status = request.GET.get('status', '')

    base_query = LicenseType.undeleted_objects.all()

    # Stats
    total_license_types = base_query.count()
    active_license_types = base_query.filter(status=True).count()
    inactive_license_types = base_query.filter(status=False).count()
    deleted_license_types_count = LicenseType.deleted_objects.count()

    # Filtering
    if search_text:
        base_query = base_query.filter(name__icontains=search_text)

    if status == 'active':
        base_query = base_query.filter(status=True)
    elif status == 'inactive':
        base_query = base_query.filter(status=False)

    license_type_list = base_query.order_by('-created_at')

    paginator = Paginator(license_type_list, PAGE_SIZE, orphans=ORPHANS)
    if not page_number:
        page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    license_type_form = LicenseTypeForm()

    # License count per type
    license_counts = (
        License.undeleted_objects
        .filter(license_type__in=license_type_list)
        .values("license_type")
        .annotate(license_count=Count("id", distinct=True))
    )

    license_type_count = {
        item["license_type"]: item["license_count"]
        for item in license_counts
    }

    stats = {
        'total_license_types': total_license_types,
        'active_license_types': active_license_types,
        'inactive_license_types': inactive_license_types,
        'deleted_license_types_count': deleted_license_types_count,
    }

    return page_object, license_type_form, license_type_count, stats


def get_product_category_list(request, page_number=None):
    """
    Returns:
        page_object,
        product_category_asset_count (dict),
        stats (dict)
    """

    search_text = request.GET.get('search_text', '').strip()
    status = request.GET.get('status', '')

    # BASE QUERY
    base_query = ProductCategory.undeleted_objects.filter(organization=request.user.organization)

    # STATS
    total_categories = base_query.count()
    active_categories = base_query.filter(status=True).count()
    inactive_categories = base_query.filter(status=False).count()
    deleted_categories_count = ProductCategory.deleted_objects.filter(organization=request.user.organization).count()

    # SEARCH FILTER
    if search_text:
        base_query = base_query.filter(
            Q(name__icontains=search_text) |
            Q(parent__name__icontains=search_text)
        )

    # STATUS FILTER
    if status == 'active':
        base_query = base_query.filter(status=True)
    elif status == 'inactive':
        base_query = base_query.filter(status=False)

    # ORDERING
    category_list = base_query.order_by('-created_at')

    # PAGINATION
    paginator = Paginator(category_list, PAGE_SIZE, orphans=ORPHANS)
    if not page_number:
        page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    # ASSET COUNT
    product_category_ids = list(page_object.object_list.values_list('id', flat=True))

    asset_counts = (
        Asset.undeleted_objects
        .filter(
            organization=request.user.organization,
            product__product_sub_category_id__in=product_category_ids
        )
        .values('product__product_sub_category_id')
        .annotate(count=Count('id', distinct=True))
    )

    product_category_asset_count = {
        item['product__product_sub_category_id']: item['count']
        for item in asset_counts
    }

    stats = {
        'total_categories': total_categories,
        'active_categories': active_categories,
        'inactive_categories': inactive_categories,
        'deleted_categories_count': deleted_categories_count,
    }

    return page_object, product_category_asset_count, stats