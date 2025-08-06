from django.contrib.auth.decorators import login_required
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import Department
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('authentication.add_department')
def department_list(request):
    departments_list = Department.undeleted_objects.filter(
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
        try:
            file = request.FILES.get('file', None)
            file_path = csv_file_upload(request, file)
            df = pd.read_csv(file_path, delimiter=',')
            list_of_csv = [list(row) for row in df.values]

            for l in list_of_csv:
                Department.objects.create(
                    name=l[0],
                    contact_person_name=l[1],
                    contact_person_email=l[2],
                    contact_person_phone=l[3],
                    organization=request.user.organization,
                )
            messages.success(
                request, 'Departments CSV file uploaded successfully')
        except:
            pass
        return redirect('upload:department_list')
    context = {'page': 'Departments'}
    return render(request, 'upload/upload-csv-modal.html', context)
