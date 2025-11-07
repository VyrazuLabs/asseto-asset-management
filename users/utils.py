
from django.contrib.auth.models import Permission, Group
from authentication.models import User
from django.contrib.contenttypes.models import ContentType
from assets.models import AssignAsset
from django.http import JsonResponse
from configurations.utils import dynamic_display_name
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


def assigned_asset_to_user(page_object):
    user_ids = [u.id for u in page_object]

    assigned_assets = AssignAsset.objects.filter(user_id__in=user_ids).select_related("asset")

    user_asset_map = {}
    for aa in assigned_assets:
        user_asset_map.setdefault(aa.user_id, []).append(aa.asset)
    
    return user_asset_map


def user_data(user_list):
    user_data_list=[]
    for user in user_list:
        user_data_list.append({
            'id':user.id,
            'full_name':user.full_name,
            'email':user.email,
            'role':user.role.related_name if user.role else None
        })
    return user_data_list

def user_details(get_user,assigned_assets,asset_images):
    asset_images_list=[]
    for asset_image in asset_images:
        asset_images_list.append(asset_image.image.url)
    print(asset_images_list,type(asset_images_list))

    user_details={
        'name':get_user.full_name,
        'email':get_user.email,
        'phone_number':get_user.phone,
        'assigned_asset_name':assigned_assets.asset.name,
        'asset_tag':assigned_assets.asset.tag,
        'vendor':assigned_assets.asset.vendor.name,
        'assigned_date':assigned_assets.assigned_date,
        'asset_image_list':asset_images_list
    }
    return user_details