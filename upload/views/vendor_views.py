import os
import traceback
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from AssetManagement import settings
from vendors.models import Vendor
from dashboard.models import Address
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
import json
from upload.models import ImportedUser
from authentication.models import User
from ..utils import function_to_get_matching_objects_vendors
from django.core.files.storage import default_storage
import csv
# import django.contrib

@login_required
@permission_required('authentication.add_vendor')
def vendor_list(request):
    vendors_list = ImportedUser.objects.filter(entity_type="Vendor",
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(vendors_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)    
    context = {
        'sidebar': 'upload',
        'submenu': 'vendors',
        'page_object': page_object,
        'title': 'Upload - Vendors',
    }

    return render(request, 'upload/vendor_list.html', context=context)


@login_required
@permission_required('authentication.add_vendor')
def export_vendors_csv(request):
    header_list = ['Vendor Name', 'Vendor Email', 'Phone', 'Contact Person Name', 'Designation', 'GSTIN Number',
                   'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country', 'Description']
    context = {'header_list': header_list, 'rows': []}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="sample-vendors-file.csv"'
    return response

@login_required
@permission_required('authentication.add_vendor')
def import_vendors_csv(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "no file uploaded")
        
        file_name = default_storage.save(f"temp/{file.name}", file)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        request.session['uploaded_csv']=file_path
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)

        return render(request, "upload/map-vendor-modal.html", {
            "headers": headers,
            "fields": [
                "name", "email", "phone", "contact_person",
                "designation", "gstin_number", "address_line_one",
                "address_line_two", "city", "pin_code", "state",
                "country", "description",
            ]
        })
    else:
        return render(request, "upload/upload-csv-modal.html", {"page": "Vendors","hx_target": "#mapping-vendors-modal-content"})


@login_required
@permission_required('authentication.add_vendor')
def vendor_render_to_mapper_modal(request):
    if request.method == "POST":
        file_path = request.session.get("uploaded_csv")
        if not file_path:
            messages.error(request, "CSV file not found in session.")
            return redirect("upload:vendor_list")

        df = pd.read_csv(file_path,encoding="utf-8-sig")
        mapping = {}
        vendor_fields = [
            "name", "email", "phone", "contact_person",
            "designation", "gstin_number", "address_line_one",
            "address_line_two", "city", "pin_code", "state",
            "country", "description"
        ]
        for field in vendor_fields:
            selected = request.POST.get(f"mapping_{field}")
            if selected:
                mapping[field] = selected
        created_vendors = []
        created_imported_users = []
        for _, row in df.iterrows():
            vendor_data = {f: row[c] for f, c in mapping.items() if c in row}
            address = Address.objects.create(
                address_line_one=vendor_data.get("address_line_one"),
                address_line_two=vendor_data.get("address_line_two"),
                city=vendor_data.get("city"),
                pin_code=vendor_data.get("pin_code"),
                state=vendor_data.get("state"),
                country=vendor_data.get("country")
            )

            vendor = Vendor.objects.create(
                name=vendor_data.get("name"),
                email=vendor_data.get("email"),
                phone=str(vendor_data.get("phone")),
                contact_person=vendor_data.get("contact_person"),
                designation=vendor_data.get("designation"),
                gstin_number=vendor_data.get("gstin_number"),
                description=vendor_data.get("description"),
                address=address,
                organization=request.user.organization,
            )
            created_vendors.append(vendor)

            imported_user = ImportedUser.objects.create(
                name=vendor_data.get("name"),
                entity_type="Vendor",
                email=vendor_data.get("email"),
                username=None,
                full_name=vendor_data.get("name"),
                phone=str(vendor_data.get("phone")),
                contact_person_name=vendor_data.get("contact_person"),
                contact_person_email=vendor_data.get("email"),
                contact_person_phone=str(vendor_data.get("phone")),
                address=address,
                organization=request.user.organization,
                gstin_number=vendor_data.get("gstin_number"),
                description=vendor_data.get("description"),
                designation=vendor_data.get("designation")
            )
            created_imported_users.append(imported_user)

        messages.success(request, f"{len(created_vendors)} vendors imported successfully.")
        return redirect("upload:vendor_list")

    messages.error(request, "Invalid request.")
    return redirect("upload:vendor_list")


def create_matched_data_from_csv_vendor(request):
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
                obj=ImportedUser.objects.create(entity_type="Vendor",**it)

                get_user=Vendor.objects.filter(email=it.get("email"),full_name=it.get("first_name"),phone=it.get("phone"),contact_person=it.get("contact_person"),gstin_number=it.get("gstin_number"),designation=it.get("designation"),description=it.get("description")).first()
                obj.save()
                # get_user.imported_user = obj.id
                get_user.save()

            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')