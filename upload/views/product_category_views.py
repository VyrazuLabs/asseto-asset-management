from django.contrib.auth.decorators import login_required
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import ProductCategory
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('authentication.add_product_category')
def product_category_list(request):

    product_category_list = ProductCategory.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_category_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'upload',
        'submenu': 'product_categories',
        'page_object': page_object,
        'title': 'Upload - Product Categories',
    }
    return render(request, 'upload/product_category_list.html', context=context)


@login_required
@permission_required('authentication.add_product_category')
def export_product_categories_csv(request):
    header_list = ['Product Category Name']
    context = {'header_list': header_list, 'rows': []}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="sample-product-categories-file.csv"'
    return response


@login_required
@permission_required('authentication.add_product_category')
def import_product_catagories_csv(request):
    if request.method == "POST":
        try:
            file = request.FILES.get('file', None)
            file_path = csv_file_upload(request, file)
            df = pd.read_csv(file_path, delimiter=',')
            list_of_csv = [list(row) for row in df.values]

            for l in list_of_csv:
                ProductCategory.objects.create(
                    name=l[0],
                    organization=request.user.organization
                )

            messages.success(
                request, 'Product Catagories CSV file uploaded successfully')
        except:
            pass
        return redirect('upload:product_category_list')
    context = {'page': 'Product Catagories'}
    return render(request, 'upload/upload-csv-modal.html', context)
