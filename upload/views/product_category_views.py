from django.contrib.auth.decorators import login_required
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import ProductCategory
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from ..utils import function_to_get_matching_objects_product_category
import json
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest

@login_required
@permission_required('authentication.add_product_category')
def product_category_list(request):

    product_category_list = ImportedUser.objects.filter(entity_type="ProductCategory",
        organization=request.user.organization)
    paginator = Paginator(product_category_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'upload',
        'submenu': 'product_categories',
        'page_object': page_object,
        'title': 'Upload - Product Categories',
    }
    return render(request, 'upload/product_category_list.html', context=context)


@login_required
@permission_required('authentication.add_product_category')
def export_product_categories_csv(request):
    header_list = ['Product Category Name']
    context = {'header_list': header_list, 'rows': []}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="sample-product-categories-file.csv"'
    return response


@login_required
@permission_required('authentication.add_product_category')
def import_product_catagories_csv(request):
    header_list = ['Product Category Name']
    model="product-category"
    if request.method == "POST":
        try:
            file = request.FILES.get('file', None)
            file_path = csv_file_upload(request, file)
            df = pd.read_csv(file_path, delimiter=',')
            list_of_csv = [list(row) for row in df.values]
            array=[]
            for l in list_of_csv:
                obj={}
                ProductCategory.objects.create(
                    name=l[0],
                    organization=request.user.organization
                )
                obj['name']=l[0]
                obj['organization']=request.user.organization
                array.append(obj)
                arr=function_to_get_matching_objects_product_category(array)
            request.session['arr'] = arr
            request.session['header']=header_list
            request.session['model']=model
            messages.success(
                request, 'Product Catagories CSV file uploaded successfully')
            return redirect('upload:compare_data')
        except:
            pass
        return redirect('upload:product_category_list')
    context = {'page': 'Product Catagories'}
    return render(request, 'upload/upload-csv-modal.html', context)

def create_matched_data_from_csv_product_category(request):
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
                obj=ImportedUser.objects.create(entity_type="ProductCategory",name=it.get('name'))

                # get_user=Location.objects.filter(entity_type="Location",office_name=it.get("office_name"),contact_person_name=it.get("contact_person_name")).first()

                # get_user.imported_user = obj.id
                # get_user.save()

            return JsonResponse({'status': 'success', 'received_items': len(data)})
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON')
        except Exception as e:
            return HttpResponse(f'Error processing request: {str(e)}')

    return HttpResponse('Only POST method allowed')

