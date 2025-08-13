from django.shortcuts import render
from products.models import Product
from assets.models import Asset
from django.db.models import Q,Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test,login_required

def manage_access(user):
    permissions_list = [
        'authentication.view_product',
        'authentication.delete_product',
        'authentication.edit_product',
        'authentication.add_product',
        'authentication.edit_asset',
        'authentication.view_asset',
        'authentication.delete_asset',
        'authentication.add_asset'
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

@login_required
@user_passes_test(manage_access)
def global_search(request):
    search_text = request.GET.get('search_text', '').strip()
    
    products = Product.undeleted_objects.filter(
        Q(organization=request.user.organization) & (
            Q(name__icontains=search_text) |
            Q(manufacturer__icontains=search_text) |
            Q(product_category__name__icontains=search_text) |
            Q(product_type__name__icontains=search_text)
        )
    ).annotate(
            total_assets=Count('asset'),
            available_assets=Count('asset', filter=Q(asset__is_assigned=False))
        ).order_by('-created_at')

    
    assets = Asset.undeleted_objects.filter(
        Q(organization=request.user.organization) & (
            Q(name__icontains=search_text) |
            Q(serial_no__icontains=search_text) |
            Q(purchase_type__icontains=search_text) |
            Q(product__name__icontains=search_text) |
            Q(vendor__name__icontains=search_text) |
            Q(vendor__gstin_number__icontains=search_text) |
            Q(location__office_name__icontains=search_text) |
            Q(product__product_type__name__icontains=search_text)
        )
    ).order_by('-created_at')
    
    context = {
        'products': products,
        'assets': assets,
        'search_text': search_text,
    }
    
    return render(request, 'search_result.html', context)
