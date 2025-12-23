
from django.contrib.auth.models import Permission, Group
from authentication.models import User
from django.contrib.contenttypes.models import ContentType
from assets.models import AssetImage, AssignAsset
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

    # branding
    'view_branding',
    'add_branding'
    'edit_branding',
    'delete_branding',

    #localization
    'view_localization',
    'add_localization',
    'delete_localization',
    'edit_localization',

    #tag_configuration
    'view_tag_configuration',
    'add_tag_configuration',
    'edit_tag_configuration',
    'delete_tag_configuration',

    #upload
    'view_upload',
    'add_upload'
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


def user_data(request,user_list):
    current_host=request.get_host()                                                                                                           
    user_data_list=[]
    for user in user_list:
        user_data_list.append({
            'id':user.id,
            'department_id':user.department.id if user.department else None,
            'location_id':user.location.id if user.location else None,
            'role_id':user.role.id if user.role else None,
            'fullName':user.full_name,
            'email':user.email,
            'role':user.role.related_name if user.role else None,
            'isActive':user.is_active,
            'lastLogin':user.last_login,
            'profilePicture':f'http://{current_host}'+user.profile_pic.url if user.profile_pic else None,
            'assetCount':AssignAsset.objects.filter(user=user.id).count(),
            'department':user.department.name if user.department else None,
            'location':user.location.office_name if user.location else None,
        })
    return user_data_list

def user_details(request,get_user,assigned_assets):
    current_host=request.get_host()
    user_details={
        'user_id':get_user.id,
        'name':get_user.full_name,
        'department_id':get_user.department.id if get_user.department else None,
        'location_id':get_user.location.id if get_user.location else None,
        'role_id':get_user.role.id if get_user.role else None,
        'email':get_user.email,
        'isActive':get_user.is_active,
        'phone_number':get_user.phone,
        'profile_picture':f'http://{current_host}'+get_user.profile_pic.url if get_user.profile_pic else None,
        'department':get_user.department.name if get_user.department else None,
        'location':get_user.location.office_name if get_user.location else None,
        'role':get_user.role.related_name if get_user.role else None,
        'address_line_one':get_user.address.address_line_one if get_user.address and get_user.address.address_line_one else None,
        'address_line_two':get_user.address.address_line_two if get_user.address and get_user.address.address_line_two else None,
        'city':get_user.address.city if get_user.address and get_user.address.city else None,
        'country':get_user.address.country if get_user.address and get_user.address.country else None,
        'state':get_user.address.state if get_user.address and get_user.address.state else None,
        'pin_code':get_user.address.pin_code if get_user.address and get_user.address.pin_code else None,
        'address':get_user.address.address_line_one if get_user.address and get_user.address.address_line_one else None
    }
    assigned_assets_list=[]
    for assigned_asset in assigned_assets:
        assigned_assets_data={
            'assigned_asset_id':assigned_asset.id,
            'asset_id':assigned_asset.asset.id,
            'assigned_asset_name':assigned_asset.asset.name,
            'asset_tag':assigned_asset.asset.tag,
            'vendor':assigned_asset.asset.vendor.name if assigned_asset.asset and assigned_asset.asset.vendor else None,
            'assigned_date':assigned_asset.assigned_date,
        }
        asset_images=AssetImage.objects.filter(asset=assigned_asset.asset.id).all()
        asset_images_list=[]
        for asset_image in asset_images:
            asset_images_list.append(f'http://{current_host}'+asset_image.image.url)
        assigned_assets_data["asset_images_list"]=asset_images_list

        assigned_assets_list.append(assigned_assets_data)
    user_details["assigned_assets_list"]=assigned_assets_list
    return user_details