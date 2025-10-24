import csv
from django.contrib.auth.decorators import login_required
from AssetManagement import settings
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import Location, Address
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from ..utils import function_to_get_matching_objects_locations
import json
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
from django.core.files.storage import default_storage
@login_required
@permission_required('authentication.add_location')
def location_list(request):
    location_list = ImportedUser.objects.filter(entity_type="Location",
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(location_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'upload',
        'submenu': 'locations',
        'page_object': page_object,
        'title': 'Upload - Locations',
    }
    return render(request, 'upload/location_list.html', context=context)


@login_required
@permission_required('authentication.add_location')
def export_locations_csv(request):
    header_list = ['Office Name', 'Contact Person Name', 'Contact Person Email', 'Contact Person Phone',
                   'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country']
    context = {'header_list': header_list, 'rows': []}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="sample-locations-file.csv"'
    return response


@login_required
@permission_required('authentication.add_location')
def import_locations_csv(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "no file uploaded")
            return redirect('upload:location_list')
        
        file_name = default_storage.save(f"temp/{file.name}", file)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        request.session['uploaded_csv']=file_path
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
        return render(request, "upload/map-location-modal.html", {
            "headers": headers,
            'fields' : [
                'Name', 'Contact Person Name', 'Contact Person Email', 'Contact Person Phone',
                'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country'
            ]
        })
    else:
        return render(request, "upload/upload-csv-modal.html", {"page": "Locations ","hx_target": "#upload-locations-modal-content"})


@login_required
@permission_required('authentication.add_location')
def location_render_to_mapper_modal(request):
    if request.method == "POST":
        file_path = request.session.get("uploaded_csv")
        if not file_path:
            messages.error(request, "CSV file not found in session.")
            return redirect("upload:location_list")

        df = pd.read_csv(file_path,encoding="utf-8-sig")
        mapping = {}
        locations_fields = [
            'Name', 'Contact Person Name', 'Contact Person Email', 'Contact Person Phone',
            'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country'
        ]
        for field in locations_fields:
            selected = request.POST.get(f"mapping_{field}")
            if selected:
                mapping[field] = selected
        created_location = []
        created_imported_users = []
        for _, row in df.iterrows():
            location_data = {f: row[c] for f, c in mapping.items() if c in row}
            address = Address.objects.create(
                address_line_one=location_data.get("Address Line One"),
                address_line_two=location_data.get("Address Line Two"),
                city=location_data.get("City"),
                pin_code=location_data.get("Pin Code"),
                state=location_data.get("State"),
                country=location_data.get("Country")
            )

            locations = Location.objects.create(
                office_name=location_data.get("Name"),
                contact_person_name=location_data.get('Contact Person Name'),
                contact_person_email=location_data.get('Contact Person Email'),
                contact_person_phone=location_data.get('Contact Person Phone'),
                address=address,
                organization=request.user.organization,
            )
            created_location.append(locations)

            imported_user = ImportedUser.objects.create(
                name=location_data.get("Name"),
                entity_type="Location",
                contact_person_name=location_data.get("Contact Person Name"),
                contact_person_email=location_data.get("Contact Person Email"),
                contact_person_phone=str(location_data.get("Contact Person Phone")),
                address=address,
                organization=request.user.organization,


            )
            created_imported_users.append(imported_user)

        messages.success(request, f"{len(created_location)} location imported successfully.")
        return redirect("upload:location_list")

    messages.error(request, "Invalid request.")
    return redirect("upload:location_list")

def create_matched_data_from_csv_locations(request):
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
                obj=ImportedUser.objects.create(entity_type="Location",office_name=it.get("office_name"),contact_person_name=it.get("contact_person_name"),contact_person_email=it.get("contact_person_email"),contact_person_phone=it.get("contact_person_phone")).first()

                # get_user=Location.objects.filter(entity_type="Location",office_name=it.get("office_name"),contact_person_name=it.get("contact_person_name")).first()

                # get_user.imported_user = obj.id
                # get_user.save()

            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')
