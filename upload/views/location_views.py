from django.contrib.auth.decorators import login_required
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

@login_required
@permission_required('authentication.add_location')
def location_list(request):
    location_list = ImportedUser.objects.filter(entity_type="Location",
        organization=request.user.organization)
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
    header_list = ['Office Name', 'Contact Person Name', 'Contact Person Email', 'Contact Person Phone',
                   'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country']
    model='create-obj-department'
    if request.method == "POST":
        try:
            file = request.FILES.get('file', None)
            file_path = csv_file_upload(request, file)
            df = pd.read_csv(file_path, delimiter=',')
            list_of_csv = [list(row) for row in df.values]
            array=[]

            for l in list_of_csv:
                obj={}
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
                obj['name']=l[0]
                obj['contact_person_name']=l[1]
                obj['contact_person_email']=l[2]
                obj['contact_person_phone']=l[3]
                obj['address']=address
                obj['organization']=request.user.organization
                array.append(obj)
                arr=function_to_get_matching_objects_locations(array)
            request.session['arr'] = arr
            request.session['header']=header_list
            request.session['model']=model
            messages.success(
                request, 'Locations CSV file uploaded successfully')
        except:
            pass
        return redirect('upload:location_list')
    context = {'page': 'Locations'}
    return render(request, 'upload/upload-csv-modal.html', context)

def render_to_mapper_modal(request):
    arr = request.session.pop('arr', [])
    header= request.session.pop('header', [])
    model=request.session.pop('model',[])
    context = {'page': 'Vendors','arr':arr,'header':header,'model':model}
    return render(request, 'upload/modal.html', context)

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
