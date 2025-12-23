import csv
from django.contrib.auth.decorators import login_required
from AssetManagement import settings
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import Department
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from ..utils import function_to_get_matching_objects_departments
import json
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
from django.core.files.storage import default_storage

@login_required
@permission_required('authentication.add_department')
def department_list(request):
    departments_list = ImportedUser.objects.filter(entity_type="Department",
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(departments_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'upload',
        'submenu': 'departments',
        'page_object': page_object,
        'title': 'Upload - Departments',
    }
    return render(request, 'upload/department_list.html', context=context)


@login_required
@permission_required('authentication.add_department')
def export_departments_csv(request):
    header_list = ['Department Name', 'Contact Person Name',
                   'Contact Person Email ', 'Contact Person Phone']
    context = {'header_list': header_list, 'rows': []}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="sample-departments-file.csv"'
    return response


@login_required
@permission_required('authentication.add_department')
def import_departments_csv(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "no file uploaded")
            return redirect('upload:department_list')
        
        file_name = default_storage.save(f"temp/{file.name}", file)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        request.session['uploaded_csv']=file_path
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)

        return render(request, "upload/map-department-modal.html", {
            "headers": headers,
            'fields' : ['Department Name', 'Contact Person Name',
            'Contact Person Email', 'Contact Person Phone'],
            'required_fields':['Department Name', 'Contact Person Name',
            'Contact Person Email', 'Contact Person Phone'],

            }
        )

    else:
        return render(request, "upload/upload-csv-modal.html", {"page": "Department","hx_target": "#upload-departments-modal-content"})

def department_render_to_mapper_modal(request):
    if request.method == "POST":
        file_path = request.session.get("uploaded_csv")
        if not file_path:
            messages.error(request, "CSV file not found in session.")
            return redirect("upload:department_list")

        df = pd.read_csv(file_path,encoding="utf-8-sig")
        mapping = {}
        department_fields = [
            'Department Name', 'Contact Person Name',
            'Contact Person Email', 'Contact Person Phone'
        ]
        for field in department_fields:
            selected = request.POST.get(f"mapping_{field}")
            if selected:
                mapping[field] = selected
        created_departments = []
        created_imported_users = []
        for _, row in df.iterrows():
            department_data = {f: row[c] for f, c in mapping.items() if c in row}
            department = Department.objects.create(
                name=department_data.get("Department Name"),
                contact_person_name=department_data.get("Contact Person Name"),
                contact_person_email=department_data.get("Contact Person Email"),
                contact_person_phone=department_data.get("Contact Person Phone"),
                organization=request.user.organization
            )
            created_departments.append(department)

            imported_user = ImportedUser.objects.create(
                name=department_data.get("Department Name"),
                entity_type="Department",
                contact_person_name=department_data.get("Contact Person Name"),
                contact_person_email=department_data.get("Contact Person Email"),
                contact_person_phone=str(department_data.get("Contact Person Phone")),
                organization=request.user.organization,
            )
            created_imported_users.append(imported_user)

        messages.success(request, f"{len(created_departments)} Departments imported successfully.")
        return redirect("upload:department_list")

    messages.error(request, "Invalid request.")
    return redirect("upload:department_list")


def create_matched_data_from_csv_department(request):
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
                obj=ImportedUser.objects.create(entity_type="Department",name=it.get("name"),phone=it.get("phone"),contact_person_name=it.get("contact_person_name"),contact_person_email=it.get("contact_person_email"),contact_person_phone=it.get("contact_person_phone"))

                # get_user=Department.objects.filter(name=it.get("name"),phone=it.get("phone"),contact_person_name=it.get("contact_person_name"),contact_person_email=it.get("contact_person_email"),contact_person_phone=it.get("contact_person_phone")).first()

                # get_user.imported_user = obj.id
                # get_user.save()
            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')




