
from django.contrib.auth.models import Permission, Group
from authentication.models import User
from django.contrib.contenttypes.models import ContentType
from assets.models import AssignAsset

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

def make_fields_optional(form, fields=None):
    """
    Mark specified fields as not required.
    If fields is None, applies to all fields.
    """
    if fields is None:
        fields = form.fields.keys()
    for field_name in fields:
        if field_name in form.fields:
            form.fields[field_name].required = False

def get_asset_by_users(id):
    get_user=User.objects.filter(id=id).first()
    get_asset=AssignAsset.objects.filter(user=get_user)
    return get_asset

    