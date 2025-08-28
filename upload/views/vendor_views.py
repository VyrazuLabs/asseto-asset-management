from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from vendors.models import Vendor
from dashboard.models import Address
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
import json
from ..models import ImportedUser
from authentication.models import User
from ..utils import function_to_get_matching_objects_vendors
# import django.contrib

@login_required
@permission_required('authentication.add_vendor')
def vendor_list(request):
    vendors_list = ImportedUser.objects.filter(entity_type="Vendor",
        organization=request.user.organization)
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
    header_list = ['Vendor Name', 'Vendor Email', 'Phone', 'Contact Person Name', 'Designation', 'GSTIN Number',
                   'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country', 'Description']
    arr=None
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
                    address_line_one=l[6],
                    address_line_two=l[7],
                    city=l[8],
                    pin_code=l[9],
                    state=l[10],
                    country=l[11],
                )

                vendor=Vendor.objects.create(
                    name=l[0],
                    email=l[1],
                    phone=l[2],
                    contact_person=l[3],
                    designation=l[4],
                    gstin_number=l[5],
                    description=l[12],
                    address=address,
                    organization=request.user.organization
                    )

                obj['name']=l[0]
                obj['email']=l[1]
                obj['phone']=l[2]
                obj['contact_person']=l[3]
                obj['designation']=l[4]
                obj['gstin_number']=l[5]
                obj['description']=l[12]
                obj['address']=address
                obj['organization']=request.user.organization
                # ImportedUser = ImportedUser.objects.create(
                #     entity_type="Vendor",
                #     email=obj.get('email'),
                #     username=None,
                #     full_name=obj.get('name'),
                #     phone=obj.get('phone'),
                #     contact_person_name=obj.get('contact_person'),
                #     contact_person_email=obj.get('contact_person_email'),
                #     contact_person_phone=obj.get('contact_person_phone'),
                #     address=address,
                #     organization=request.user.organization,
                #     gstin_number=obj.get('gstin_number'),
                #     description=obj.get('description'),
                #     designation=obj.get('designation')
                # )
                # vendor.imported_user=ImportedUser.id
                array.append(obj)
            arr=function_to_get_matching_objects_vendors(array)

            request.session['arr'] = arr
            request.session['header']=header_list
            messages.success(
                request, 'Vendors CSV file uploaded successfully')
            return redirect('upload:compare_data')
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
        return redirect('upload:vendor_list')
    context = {'page': 'Vendors'}
    return render(request, 'upload/upload-csv-modal.html', context)

def render_to_mapper_modal(request):
    arr = request.session.pop('arr', [])
    header= request.session.pop('header', [])
    context = {'page': 'Vendors','arr':arr,'header':header}
    return render(request, 'upload/modal.html', context)

# {'email': 'email@gmail.com', 'name': 'Vendoe 2', 'phone': ['847965123'], 'contact_person': 'Anando Singh', 'contact_person_email': '', 'contact_person_phone': '',
#  'gstin_number': 'GSTIN4945511564', 'description': 'Developer', 'designation': 'CTO'}

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

                # get_user=Vendor.objects.filter(email=it.get("email"),full_name=it.get("first_name"),phone=it.get("phone"),contact_person=it.get("contact_person"),gstin_number=it.get("gstin_number"),designation=it.get("designation"),description=it.get("description")).first()

                # get_user.imported_user = obj.id
                # get_user.save()

            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')