
from django.contrib.auth.models import Permission, Group
from authentication.models import User
from django.contrib.contenttypes.models import ContentType

PERMISSION_LIST = [
    # products
    'view_product',
    'delete_product',
    'edit_product',
    'add_product',

    # users
    'view_users',
    'delete_users',
    'edit_users',
    'add_users',

    # vendors
    'edit_vendor',
    'add_vendor',
    'view_vendor',
    'delete_vendor',

    # assets
    'edit_asset',
    'view_asset',
    'delete_asset',
    'add_asset',

    # assign assets
    'delete_assign_asset',
    'reassign_assign_asset',
    'add_assign_asset'

    # departments
    'edit_department',
    'add_department',
    'delete_department',

    # locations
    'add_location',
    'edit_location',
    'delete_location',
    'view_location',

    # product categories
    'delete_product_category',
    'edit_product_category',
    'add_product_category',

    # product types
    'delete_product_type',
    'edit_product_type',
    'add_product_type',
]


def create_all_perm_role():

    all_perms, created = Group.objects.get_or_create(
        name='all_perms')
    all_perms.permissions.clear()
    content_type = ContentType.objects.get_for_model(User)

    for cname in PERMISSION_LIST:
        temp_name = cname.split('_')
        name = ''
        for ele in temp_name:
            name += ele+' '

        permission, created = Permission.objects.get_or_create(
            codename=cname, name=f'Can {name}', content_type=content_type)
        all_perms.permissions.add(permission)
