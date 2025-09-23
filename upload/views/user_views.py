import csv
from django.contrib.auth.decorators import login_required
from AssetManagement import settings
from upload.models import *
from django.contrib import messages
from django.shortcuts import render, redirect
from dashboard.models import Location, ProductType
from authentication.models import User
from django.core.paginator import Paginator
from upload.utils import render_to_csv, csv_file_upload
import pandas as pd
from django.contrib.auth.decorators import permission_required
from ..utils import function_to_get_matching_objects_product_types
import json
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
from django.core.files.storage import default_storage

@login_required
@permission_required('authentication.add_user')
def user_list(request):
    users_list = ImportedUser.objects.filter(entity_type="User",
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(users_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)    
    context = {
        'sidebar': 'upload',
        'submenu': 'users',
        'page_object': page_object,
        'title': 'Upload - Users',
    }
    return render(request, 'upload/user_list.html', context)



@login_required
@permission_required('authentication.add_user')
def export_users_csv(request):
    header_list=['Employee ID','User Name','Name','Email','Phone','Department','Role','Office Location','Address','City','State','Country','Zip Code']
    context={'header_list':header_list,'rows':[]}
    response=render_to_csv(context_dict=context)
    response['Content-Disposition']=f'attachment; filename="sample-user-file.CSV"'
    return response


@login_required
@permission_required('authentication.add_user')
def import_user_csv(request):
    print("the form method is ",request.method)
    if request.method=="POST":
        print("i'm inside post")
        file=request.FILES.get("file")
        file_name=default_storage.save(f"temp/{file.name}",file)
        file_path=os.path.join(settings.MEDIA_ROOT,file_name)
        request.session['uploaded_csv']=file_path
        with open(file_path,newline="",encoding="utf-8-sig") as f:
            reader=csv.reader(f)
            headers=next(reader)
        context={
        'headers':headers,
        'fields':['Employee ID','User Name','Name','Email','Phone','Department','Role','Office Location','Address','City','State','Country','Zip Code']
        }
        return render(request,'upload/map-user-modal.html',context)
    else:
        print("not inside post of user")
    return render(request,"upload/upload-csv-modal.html",{'page':'Users',"hx_target": "#mapping-users-modal-content"})

@login_required
@permission_required('authentication.add_user')
def user_render_to_mapper_model(request):
    if request.method=="POST":
        file_path=request.session.get('uploaded_csv')
        if not file_path:
            messages.error(request,'CSV file not found in session')
        df=pd.read_csv(file_path,encoding="utf-8-sig")
        mapping={}
        user_fields=['Employee ID','User Name','Name','Email','Phone','Department','Role','Office Location','Address','City','State','Country','Zip Code']
        for field in user_fields:
            selected=request.POST.get(f"mapping_{field}")
            if selected:
                mapping[field]=selected
        created_users=[]
        created_imported_user=[]
        for _,row in df.iterrows():
            user_data={f:row[c] for f,c in mapping.items() if c in row}

            if User.objects.filter(email=user_data.get('Email')).exists():
                messages.error(request, f'{user_data.get("Email")} is already exists')
                continue
            
            print("user data--------->",user_data)
            user_address=Address.objects.create(
                address_line_one=user_data.get('Address'),
                city=user_data.get("City"),
                state=user_data.get("State"),
                country=user_data.get('Country'),
                pin_code=user_data.get('Zip Code')
            )
            print("-------->adress created for uploaded users<---------")

            department=Department.objects.create(
                name=user_data.get("Department"),
                organization=request.user.organization

            )
            print("-------->department created for uploaded users<---------")
            role=Role.objects.create(
                name = uuid4().hex,
                related_name=user_data.get('Role'),
                organization=request.user.organization
            )
            print("-------->role created for uploaded users<---------")
            user=User.objects.create(
                employee_id=user_data.get('Employee ID'),
                username=user_data.get('User Name'),
                email=user_data.get('Email'),
                full_name=user_data.get('Name'),
                address=user_address,
                department=department,
                role=role,
                organization=request.user.organization

            )
            print("-------->user created for uploaded users<---------")
            created_users.append(user)
            import_user=ImportedUser.objects.create(
                username=user_data.get('User Name'),
                full_name=user_data.get('Name'),
                email=user_data.get('Email'),
                phone=user_data.get('Phone'),
                entity_type="User",
                department=department,
                role=role,
                address=user_address,
                organization=request.user.organization
            )
            print("-------->imported_user created for uploaded users<---------")
            created_imported_user.append(import_user)

        messages.success(request,f"{len(created_users)} users imported successfully.")
        return redirect('upload:user_list')
    
    messages.error(request,"Invalid request")
    return redirect('upload:user_list')