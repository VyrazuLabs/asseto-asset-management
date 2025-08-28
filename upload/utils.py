from django.template.loader import get_template
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
import csv
from io import BytesIO
from xhtml2pdf import pisa
import os
from django.shortcuts import redirect
import pandas as pd
from django.contrib import messages
import os
from datetime import date
from .models import File,ImportedUser
import json
from vendors.models import Vendor
from dashboard.models import Department,Location,ProductCategory,ProductType

today = date.today()


def render_to_csv(context_dict={}):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(context_dict['header_list'])
    for row in context_dict['rows']:
        writer.writerow(row)
    return response


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def csv_file_upload(request, file):
    if file is not None:
        file_name = file.name
        split_tup = os.path.splitext(file_name)
        file_extension = split_tup[1]

        if file_name.endswith('.csv'):
            obj = File.objects.create(file=file)
            df = pd.read_csv(obj.file, delimiter=',')
            list_of_csv = [list(row) for row in df.values]
            length_of_csv = len(list_of_csv)
            if length_of_csv <= 100:
                return obj.file.path
            else:
                messages.error(
                    request, f'Please upload less than 100 rows. Your list has {length_of_csv} rows.')
        else:
            messages.error(
                request, f'Please upload CSV file. You have uploaded {file_extension} file.')
    else:
        messages.error(request, 'Please choose a File.')

    return redirect(request.META.get('HTTP_REFERER'))

def create_matched_data_from_csv_generic(
        request,
        # create_model,           # Model class to create (e.g. ImportedUser or Vendor)
        create_field_map,       # Dict: {'csv_key': 'model_field'}
        match_model=None,       # Model class to match in DB (e.g. User), optional
        match_field_map=None,   # Dict: {'csv_key': 'match_model_field'}, optional
        link_field_in_match=None,  # str: The field in match model to be set to created obj
        link_value_field='id'      # str: The field in created obj to link (default 'id')
    ):
    field_map_imported_user = {
        'Entity_Type': 'entity_type',
        'Email': 'email',
        'Username': 'username',
        'Full_Name': 'full_name',
        'Phone': 'phone',
        'Contact_Person_Name': 'contact_person_name',
        'Contact_Person_Email': 'contact_person_email',
        'Contact_Person_Phone': 'contact_person_phone',
        'Address_ID': 'address',         # assuming CSV includes Address id or key to resolve FK
        'Organization_ID': 'organization'  # assuming CSV includes Organization id or key
    }
    """
    Generic CSV-to-model create and match flow

    Params:
    - create_model: Model to create (e.g. ImportedUser, Vendor, etc.)
    - create_field_map: Mapping of input keys to create_model fields
    - match_model: Model to look up for matching (default None)
    - match_field_map: Mapping of input keys to fields for filtering match_model (default None)
    - link_field_in_match: Field name in match_model to set (e.g., 'imported_user')
    - link_value_field: Field on created object to link (default 'id')
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode())
            created_objs = []
            for it in data:
                # Dynamic creation from mapping
                #Create a custom create_field_map
                create_kwargs = {model_field: it.get(csv_key) for csv_key, model_field in field_map_imported_user.items()}
                obj = ImportedUser.objects.create(**create_kwargs)
                created_objs.append(obj)

                # Optionally link to base/matching model
                if match_model and match_field_map and link_field_in_match:
                    filters = {match_field: it.get(csv_key) for csv_key, match_field in match_field_map.items()}
                    match_obj = match_model.objects.filter(**filters).first()
                    if match_obj:
                        setattr(match_obj, link_field_in_match, getattr(obj, link_value_field))
                        match_obj.save()
            return JsonResponse({'status': 'success', 'created': len(created_objs)})
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')
        except Exception as e:
            return HttpResponseBadRequest(f'Error processing request: {str(e)}')
    return HttpResponse('Only POST method allowed')

def function_to_get_matching_objects_vendors(arr):
    array=[]    
    for it in arr:
        get_existing_vendors=Vendor.objects.filter(**it).first()
        obj={}
        # entity_type="Vendor",
        obj['email']=get_existing_vendors.email
        username=None,
        obj['name']=get_existing_vendors.name
        obj['phone']=get_existing_vendors.phone,
        obj['contact_person']=get_existing_vendors.contact_person
        obj['contact_person_email']=""
        obj['contact_person_phone']=""
        # address=address
        # organization=request.user.organization,
        obj['gstin_number']=get_existing_vendors.gstin_number
        obj['description']=get_existing_vendors.description
        obj['designation']=get_existing_vendors.designation
        array.append(obj)
    return array

def function_to_get_matching_objects_departments(arr):
    array=[]    
    for it in arr:
        get_existing_departments=Department.objects.filter(**it).first()
        obj={}
        # entity_type="Vendor",
        obj['email']=""
        username=None,
        obj['name']=""
        obj['phone']=""
        obj['contact_person_name']=get_existing_departments.contact_person_name
        obj['contact_person_email']=get_existing_departments.contact_person_email
        obj['contact_person_phone']=get_existing_departments.contact_person_phone
        # address=address
        # organization=request.user.organization,
        obj['gstin_number']=""
        obj['description']=""
        obj['designation']=""
        array.append(obj)
    return array

def function_to_get_matching_objects_locations(arr):
    array=[]    
    for it in arr:
        get_existing_locations=Location.objects.filter(**it).first()
        obj={}
        # entity_type="Vendor",
        obj['email']=""
        username=None,
        obj['name']=""
        obj['phone']=""
        obj['office_name']=get_existing_locations.office_name
        obj['contact_person_name']=get_existing_locations.contact_person_name
        obj['contact_person_email']=get_existing_locations.contact_person_email
        obj['contact_person_phone']=get_existing_locations.contact_person_phone
        # address=address
        # organization=request.user.organization,
        obj['gstin_number']=""
        obj['description']=""
        obj['designation']=""
        array.append(obj)
    return array

def function_to_get_matching_objects_product_category(arr):
    array=[]
    for it in arr:
        get_existing_product_category=ProductCategory.objects.filter(**it).first()
        obj={}
        # entity_type="Vendor",
        obj['email']=""
        username=None
        obj['name']=get_existing_product_category.name
        obj['phone']=""
        obj['office_name']=""
        obj['contact_person_name']=""
        obj['contact_person_email']=""
        obj['contact_person_phone']=""
        # address=address
        # organization=request.user.organization,
        obj['gstin_number']=""
        obj['description']=""
        obj['designation']=""
        array.append(obj)
    return array

def function_to_get_matching_objects_product_types(arr):
    array=[]
    for it in arr:
        get_existing_product_category=ProductType.objects.filter(**it).first()
        obj={}
        # entity_type="Vendor",
        obj['email']=""
        username=None
        obj['name']=get_existing_product_category.name
        obj['phone']=""
        obj['office_name']=""
        obj['contact_person_name']=""
        obj['contact_person_email']=""
        obj['contact_person_phone']=""
        # address=address
        # organization=request.user.organization,
        obj['gstin_number']=""
        obj['description']=""
        obj['designation']=""
        array.append(obj)
    return array