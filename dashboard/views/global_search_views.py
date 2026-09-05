from django.shortcuts import render
from products.models import Product
from assets.models import Asset
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test, login_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from authentication.models import User


def manage_access(user):
    permissions_list = [
        "products.view_product",
        "products.delete_product",
        "products.edit_product",
        "products.add_product",
        "assets.edit_asset",
        "assets.view_asset",
        "assets.delete_asset",
        "assets.add_asset",
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


@login_required
@user_passes_test(manage_access)
def global_search(request):
    search_text = request.GET.get("search_text", "").strip()
    users = None

    products = (
        Product.undeleted_objects.filter(
            (Q(organization=request.user.organization) | Q(organization=None))
            & (Q(name__icontains=search_text))
        )
        .annotate(
            total_assets=Count("asset"),
            available_assets=Count("asset", filter=Q(asset__is_assigned=False)),
        )
        .order_by("-created_at")[:10]
    )

    assets = Asset.undeleted_objects.filter(
        (Q(organization=request.user.organization) | Q(organization=None))
        & (Q(tag__icontains=search_text) | Q(name__icontains=search_text))
    ).order_by("-created_at")[:10]

    if request.user.is_superuser:
        try:
            users = (
                User.undeleted_objects.filter(
                    (Q(organization=request.user.organization) | Q(organization=None))
                    & Q(is_superuser=False)
                    & (Q(Q(full_name__icontains=search_text)))
                )
                .exclude(pk=request.user.id)
                .order_by("-created_at")[:10]
            )
        except Exception as e:
            print(e)

    context = {
        "products": products,
        "assets": assets,
        "users": users,
        "search_text": search_text,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("search_results_partial.html", context, request=request)
        return HttpResponse(html)
    return render(request, "search_result.html", context)
