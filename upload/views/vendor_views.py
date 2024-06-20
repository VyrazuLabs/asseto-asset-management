from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from vendors.models import Vendor
from dashboard.models import Address
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required


@login_required
@permission_required('authentication.add_vendor')
def vendor_list(request):

    vendors_list = Vendor.undeleted_objects.filter(
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
        try:
            file = request.FILES.get('file', None)
            file_path = csv_file_upload(request, file)
            df = pd.read_csv(file_path, delimiter=',')
            list_of_csv = [list(row) for row in df.values]

            for l in list_of_csv:
                address = Address.objects.create(
                    address_line_one=l[6],
                    address_line_two=l[7],
                    city=l[8],
                    pin_code=l[9],
                    state=l[10],
                    country=l[11],
                )

                Vendor.objects.create(
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

            messages.success(
                request, 'Vendors CSV file uploaded successfully')
        except:
            pass
        return redirect('upload:vendor_list')
    context = {'page': 'Vendors'}
    return render(request, 'upload/upload-csv-modal.html', context)
