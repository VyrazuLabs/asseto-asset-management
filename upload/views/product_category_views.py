import csv
from django.contrib.auth.decorators import login_required
from AssetManagement import settings
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import ProductCategory
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from ..utils import function_to_get_matching_objects_product_category
import json
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
from django.core.files.storage import default_storage

@login_required
@permission_required('authentication.add_product_category')
def product_category_list(request):

    product_category_list = ImportedUser.objects.filter(entity_type="ProductCategory",
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_category_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    print("page_object----------------->",(page_object))
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
    print(request.method)
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "no file uploaded")
            return redirect('upload:product_category_list')
        
        file_name = default_storage.save(f"temp/{file.name}", file)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        request.session['uploaded_csv']=file_path
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)

        return render(request, "upload/map-product-category-modal.html", {
            "headers": headers,
            "fields": ["name"]
        })
    else:
        print("no response")
        return render(request, "upload/upload-csv-modal.html", {"page": "Product Category","hx_target": "#upload-product-catagories-modal-content"})


@login_required
@permission_required('authentication.add_product_category')
def product_category_render_to_mapper_model(request):
    if request.method == "POST":
        file_path = request.session.get("uploaded_csv")
        if not file_path:
            messages.error(request, "CSV file not found in session.")
            return redirect("upload:product_category_list")

        df = pd.read_csv(file_path,encoding="utf-8-sig")
        mapping = {}
        product_category_fields = ["name"]
        for field in product_category_fields:
            selected = request.POST.get(f"mapping_{field}")
            if selected:
                mapping[field] = selected

        created_product_types = []
        created_imported_users = []

        for _, row in df.iterrows():
            product_category_data = {f: row[c] for f, c in mapping.items() if c in row}
            print("product_category_data---------->",product_category_data)
            product_type = ProductCategory.objects.create(
                name=product_category_data.get("name"),
                organization=request.user.organization,
            )
            created_product_types.append(product_type)

            imported_user = ImportedUser.objects.create(
                name=product_category_data.get("name"),
                entity_type="ProductCategory",
                organization=request.user.organization,
            )
            created_imported_users.append(imported_user)

        messages.success(request, f"{len( created_product_types)} Product Categories imported successfully.")
        return redirect("upload:product_category_list")

    messages.error(request, "Invalid request.")
    return redirect("upload:product_category_list")

def create_matched_data_from_csv_product_category(request):
    if request.method == 'POST':
        try:
            # request.body is bytes, decode and parse JSON\
            # body = request.POST.getlist("arr")

            # data = json.loads(body)
            data = json.loads(request.body.decode())
            # Now 'data' is the python object sent from 'arr' (likely a list of dicts)
            
            # For example purposes:
            for it in data:
                #Create the the user which are mapped from the csv to databsae
                obj=ImportedUser.objects.create(entity_type="ProductCategory",name=it.get('name'))

                # get_user=Location.objects.filter(entity_type="Location",office_name=it.get("office_name"),contact_person_name=it.get("contact_person_name")).first()

                # get_user.imported_user = obj.id
                # get_user.save()

            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')

