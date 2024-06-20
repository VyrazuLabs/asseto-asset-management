from django.contrib.auth.decorators import login_required
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import Location, Address
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('authentication.add_location')
def location_list(request):

    location_list = Location.undeleted_objects.filter(
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
        try:
            file = request.FILES.get('file', None)
            file_path = csv_file_upload(request, file)
            df = pd.read_csv(file_path, delimiter=',')
            list_of_csv = [list(row) for row in df.values]

            for l in list_of_csv:
                address = Address.objects.create(
                    address_line_one=l[4],
                    address_line_two=l[5],
                    country=l[9],
                    state=l[8],
                    city=l[6],
                    pin_code=l[7]
                )

                Location.objects.create(
                    office_name=l[0],
                    contact_person_name=l[1],
                    contact_person_email=l[2],
                    contact_person_phone=l[3],
                    address=address,
                    organization=request.user.organization
                )

            messages.success(
                request, 'Locations CSV file uploaded successfully')
        except:
            pass
        return redirect('upload:location_list')
    context = {'page': 'Locations'}
    return render(request, 'upload/upload-csv-modal.html', context)
