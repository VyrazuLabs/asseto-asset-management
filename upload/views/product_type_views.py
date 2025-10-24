import csv
from django.contrib.auth.decorators import login_required
from AssetManagement import settings
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import ProductType
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from ..utils import function_to_get_matching_objects_product_types
import json
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
from django.core.files.storage import default_storage


@login_required
@permission_required('authentication.add_product_type')
def product_type_list(request):

    product_type_list = ImportedUser.objects.filter(entity_type="ProductType",
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_type_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'upload',
        'submenu': 'product_types',
        'page_object': page_object,
        'title': 'Upload - Product Types'
    }
    return render(request, 'upload/product_type_list.html', context=context)


@login_required
@permission_required('authentication.add_product_type')
def export_product_types_csv(request):
    header_list = ['Product Type Name']
    context = {'header_list': header_list, 'rows': []}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="sample-product-types-file.csv"'
    return response


@login_required
@permission_required('authentication.add_product_type')
def import_product_types_csv(request):

    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "no file uploaded")
            return redirect('upload:product_type_list')
        
        file_name = default_storage.save(f"temp/{file.name}", file)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        request.session['uploaded_csv']=file_path
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)

        return render(request, "upload/map-product-type-modal.html", {
            "headers": headers,
            "fields": ["name"]
        })
    else:
        return render(request, "upload/upload-csv-modal.html", {"page": "Product Type","hx_target": "#upload-product-types-modal-content"})


@login_required
@permission_required('authentication.add_product_type')
def product_type_render_to_mapper_model(request):
    if request.method == "POST":
        file_path = request.session.get("uploaded_csv")
        if not file_path:
            messages.error(request, "CSV file not found in session.")
            return redirect("upload:product_type_list")

        df = pd.read_csv(file_path,encoding="utf-8-sig")
        mapping = {}
        product_type_fields = ["name"]
        for field in product_type_fields:
            selected = request.POST.get(f"mapping_{field}")
            if selected:
                mapping[field] = selected

        created_product_types = []
        created_imported_users = []

        for _, row in df.iterrows():
            product_type_data = {f: row[c] for f, c in mapping.items() if c in row}
            
            product_type = ProductType.objects.create(
                name=product_type_data.get("name"),
                organization=request.user.organization,
            )
            created_product_types.append(product_type)

            imported_user = ImportedUser.objects.create(
                name=product_type_data.get("name"),
                entity_type="ProductType",
                organization=request.user.organization,
            )
            created_imported_users.append(imported_user)

        messages.success(request, f"{len( created_product_types)} Product Types imported successfully.")
        return redirect("upload:product_type_list")

    messages.error(request, "Invalid request.")
    return redirect("upload:product_type_list")


def create_matched_data_from_csv_product_type(request):
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
                obj=ImportedUser.objects.create(entity_type="ProductType",name=it.get('name'))

                # get_user=Vendor.objects.filter(email=it.get("email"),full_name=it.get("first_name"),phone=it.get("phone"),contact_person=it.get("contact_person"),gstin_number=it.get("gstin_number"),designation=it.get("designation"),description=it.get("description")).first()

                # get_user.imported_user = obj.id
                # get_user.save()

            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')
