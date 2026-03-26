from products.models import Product
from products.utils import convert_to_list


def get_searched_data(request,search_text):   
    status=request.GET.get('status')
    vendor=request.GET.get('vendor')
    product_type=request.GET.get('product_type')
    product_sub_category=request.GET.get('product_sub_category')
    user=request.GET.get('user')
    location=request.GET.get('location')
    department=request.GET.get('department')
    searched_data=Product.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
        name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_sub_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
    ))
    if status:
        searched_data=searched_data.filter(status=status)
    if vendor:
        searched_data=searched_data.filter(vendor__id=vendor)
    if product_type:
        searched_data=searched_data.filter(product_type__id=product_type)
    if product_sub_category:
        searched_data=searched_data.filter(product_sub_category__id=product_sub_category)
    if user:
        searched_data=searched_data.filter(asset__assigned_asset__user__id=user)
    if location:
        searched_data=searched_data.filter(asset__location__id=location)
    if department:
        searched_data=searched_data.filter(asset__assigned_asset__user__department__id=department)
    # searched_data=searched_data.distinct().order_by('-created_at')
    searched_product_data=convert_to_list(request,searched_data)
    return searched_product_data