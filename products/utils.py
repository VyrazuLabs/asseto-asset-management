from assets.models import Asset, AssignAsset
from dashboard.models import CustomField
from products.models import ProductImage


def convert_to_list(request,products):
    current_host=request.get_host()
    product_list=[]
    for product in products:
        product_dict={
            'id':product.id,
            'name':product.name,
            'type':product.product_type.name,
            'category':product.product_sub_category.name if product.product_sub_category else None,
            'total_asset':Asset.objects.filter(product=product.id).count(),
            'status':product.status,
        }
        get_product_image=ProductImage.objects.filter(product=product.id).first()
        if get_product_image:
            product_dict['image']=f"http://{current_host}"+get_product_image.image.url
        else:
            product_dict['image']=None
        product_list.append(product_dict)
        
    return product_list

def product_details(request,product):
    current_host=request.get_host()
    product_detail={
        'id':product.id,
        'name':product.name,
        'type':product.product_type.name,
        'category':product.product_sub_category.name if product.product_sub_category.name else None,
        'parent_category':product.product_sub_category.parent.name if product.product_sub_category else None,
        'manufacture':product.manufacturer if product.manufacturer else None,
        'model_name':product. model if product. model else None,
        'status':product.status if product.status else None,
        'eol':product.eol if product.eol else None,
        'description':product.description if product.description else None,
        'asset_count':Asset.undeleted_objects.filter(product=product.id).count()
    }
    get_product_image=ProductImage.objects.filter(product=product.id)
    product_detail['images']=image_list=[]
    if get_product_image:
        for product_image in get_product_image:
            image_list.append(f"http://{current_host}"+product_image.image.url)
        product_detail['images']=image_list
    
    product_detail['custom_fields']=custome_fields_list=[]
    get_custom_fields=CustomField.objects.filter(object_id=product.id)
    if get_custom_fields:
        for custom_field in get_custom_fields:
            custom_fields_dict={custom_field.field_name:custom_field.field_value}
            custome_fields_list.append(custom_fields_dict)
        product_detail['custom_fields']=custome_fields_list


    get_asset=Asset.objects.filter(product=product.id,organization=request.user.organization)
    asset_list=[]
    product_detail['assets']=asset_list
    if get_asset:
        for asset in get_asset:
            asset_dict={
                'id':asset.id,
                'name':asset.name,
                'status':asset.asset_status.name
            }
            asset_dict['assigned_user']=None
            assigned_user=AssignAsset.objects.get(asset=asset.id)
            if assigned_user:
                asset_dict['assigned_user']=assigned_user.user.full_name
            asset_list.append(asset_dict)

        product_detail['assets']=asset_list
    return product_detail

def product_list_for_form(products):
    list=[]
    for product in products:
        products_dict={
            'id':product.id,
            'name':product.name
        }
        list.append(products_dict)
    return list

def delete_product_images(deleted_image_ids):
    for id in deleted_image_ids:
        try:
            ProductImage.objects.filter(id=id).delete()
        except Exception as e:
            print(e)