from django.core.paginator import Paginator
from django.db.models import Q, Count
from roles.models import Role
from authentication.models import User

PAGE_SIZE = 10
ORPHANS = 1

def get_roles_list_utils(request, page_number=None):
    """
    Returns:
        page_object,
        role_user_count (dict),
        stats (dict)
    """

    search_text = request.GET.get('search_text', '').strip()
    status = request.GET.get('status', '')

    # BASE QUERY
    base_query = Role.objects.filter(organization=request.user.organization)

    # STATS
    total_roles = base_query.count()
    active_roles = base_query.filter(status=True).count()
    inactive_roles = base_query.filter(status=False).count()
    # Roles don't seem to have a soft delete manager in the model, let's check
    # TimeStampModel doesn't have is_deleted, but SoftDeleteModel does.
    # Role inherits from Group and TimeStampModel, but NOT SoftDeleteModel.
    deleted_roles_count = 0 

    # SEARCH FILTER
    if search_text:
        base_query = base_query.filter(related_name__icontains=search_text)

    # STATUS FILTER
    if status == 'active':
        base_query = base_query.filter(status=True)
    elif status == 'inactive':
        base_query = base_query.filter(status=False)

    # ORDERING
    roles_list = base_query.order_by('-created_at')

    # PAGINATION
    paginator = Paginator(roles_list, PAGE_SIZE, orphans=ORPHANS)
    if not page_number:
        page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    # USER COUNT PER ROLE
    # Since User has a 'role' or 'groups'?
    # Usually roles are implemented via groups.
    role_ids = [role.id for role in page_object]
    
    # Let's count users in each group/role
    user_counts = (
        User.objects.filter(groups__id__in=role_ids, organization=request.user.organization)
        .values('groups__id')
        .annotate(count=Count('id'))
    )
    
    role_user_count = {
        item['groups__id']: item['count']
        for item in user_counts
    }

    stats = {
        'total_roles': total_roles,
        'active_roles': active_roles,
        'inactive_roles': inactive_roles,
        'deleted_roles_count': deleted_roles_count,
    }

    return page_object, role_user_count, stats
