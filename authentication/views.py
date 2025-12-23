from socket import create_connection
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from asyncio.log import logger
from django.shortcuts import redirect
from django.shortcuts import render, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from authentication.forms import (UserRegisterForm, OrganizationForm,UserLoginForm, UserUpdateForm, OrganizationUpdateForm)
from authentication.decorators import unauthenticated_user
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from authentication.token import account_activation_token
from django.contrib.auth.models import User
from authentication.utils import create_db_connection
from dashboard.forms import AddressForm
from dashboard.models import Location, Address,ProductType,ProductCategory
from django.contrib.auth import get_user_model
from products.models import Product
from vendors.models import Vendor
from assets.models import *
from django.db.models.signals import post_save 
from assets.seeders import seed_asset_statuses
from assets.models import AssignAsset
from django.views.decorators.cache import never_cache
from dashboard.views.seeders import seed_parent_category
from django.db.models import Q
from configurations.utils import get_currency_and_datetime_format
from configurations.utils import format_datetime
from django.contrib import messages
from .constant import db_engines
from configurations.models import LocalizationConfiguration
from configurations.constants import NAME_FORMATS
from dotenv import load_dotenv,set_key
from django.conf import settings
from license.models import License
User = get_user_model()

def introduce(request):
    return render(request,'auth/first_time_installation/introduce.html',context={'current_step':1})

def db_configure(request):
    if request.method=="POST":
        db_type=request.POST.get('database')
        db_engine=db_engines.get(db_type)

        db_data={
            'DB_ENGINE':db_engine,
            'DB_NAME':request.POST.get('db_name'),
            'DB_USERNAME':request.POST.get('user_name'),
            'DB_PASSWORD':request.POST.get('password'),
            'DB_HOST':request.POST.get('host_name'),
            'DB_PORT':request.POST.get('port')
        }

        if create_db_connection(request,db_data):
            messages.success(request, "Database configured successfully!")
            return redirect('authentication:email_configure')
        else:
            messages.error(request, "Database connection failed. Please check your credentials.")
            return render(request, 'auth/first_time_installation/db_configure.html')
        
    return render(request,'auth/first_time_installation/db_configure.html',context={'current_step':2})

def smtp_email_configure(request):
    env_path=settings.BASE_DIR / ".env"

    if request.method=="POST":
        email_data={
            'EMAIL_HOST': request.POST.get('email_host'),
            'EMAIL_HOST_USER': request.POST.get('email_host_user'),
            'EMAIL_HOST_PASSWORD': request.POST.get('email_host_password'),
            'EMAIL_PORT':request.POST.get('email_port')
        }
        for key,value in email_data.items():
            set_key(env_path,key,value)
        messages.success(request,'Email Configuration Successfully')
        load_dotenv(env_path,override=True)
        return redirect ('authentication:register')
    
    return render(request,'auth/first_time_installation/email_configure.html',context={'current_step':3})

@login_required
def index(request):
 
    all_asset_cost = 0
    today = datetime.now()
    time_threshold = datetime.now() + timedelta(days=30)
    expiring_assets = Asset.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization, warranty_expiry_date__lt=time_threshold)).exclude(Q(
        warranty_expiry_date__lt=today)|Q(warranty_expiry_date=None)).order_by('warranty_expiry_date')
 
    all_asset_list = Asset.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization))
    asset_count = all_asset_list.count()
 
    for asset in all_asset_list:
        if asset.price is None:
            asset.price=0
        all_asset_cost = all_asset_cost + asset.price
 
    all_product_list = Product.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization))
    latest_product_list = Product.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization)).order_by('created_at').reverse()[0:5]
    product_count = all_product_list.count()
 
    all_vendor_list = Vendor.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization))
    latest_vendor_list = Vendor.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization)).order_by('created_at').reverse()[0:5]
    vendor_count = all_vendor_list.count()
 
    location_list = Location.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization))
    all_location_list = Location.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization)).order_by('created_at').reverse()[0:5]
    location_count = location_list.count()
 
    assign_assets = AssignAsset.objects.filter(Q(asset__organization=None) | Q(
        asset__organization=request.user.organization,asset__is_assigned=True))
    assign_assets_counts = assign_assets.count()
 
    unassign_assets_count = asset_count - assign_assets_counts
 
    users_list = User.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization)).exclude(is_superuser=True)
    latest_users_list = User.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).exclude(
        is_superuser=True).order_by('created_at').reverse()[0:5]
    users_count = users_list.count()
    obj=get_currency_and_datetime_format(request.user.organization)

    get_license=License.undeleted_objects.all()
    get_license_count=get_license.count()
    for it in expiring_assets:
        if not obj['date_format']:
            it.warranty_expiry_date=it.warranty_expiry_date.date()
        else:
            it.warranty_expiry_date=format_datetime(x=it.warranty_expiry_date,output_format=obj['date_format'])
        # it.warranty_expiry_date=format_datetime(x=it.warranty_expiry_date,output_format=obj['date_format'])
    for it in latest_vendor_list:
        if not obj['date_format']:
            it.created_at=it.created_at.date
        else:
            it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])
    for it in latest_product_list:
        if not obj['date_format']:
            it.created_at=it.created_at.date
        else:
            it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])
        # it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])

    for it in all_location_list:
        if not obj['date_format']:
            it.created_at=it.created_at.date
        else:
            it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])
        # it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])
    
    for it in latest_users_list:
        if not obj['date_format']:
            it.created_at=it.created_at.date
        else:
            it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])
        # it.created_at=format_datetime(x=it.created_at,output_format=obj['date_format'])
    context = {
        'currency': obj['currency'],
        'date_format': obj['date_format'],
        'sidebar': 'index',
        'product_count': product_count,
        'vendor_count': vendor_count,
        'asset_count': asset_count,
        'location_count': location_count,
        'all_asset_cost': all_asset_cost,
        'latest_vendor_list': latest_vendor_list,
        'latest_product_list': latest_product_list,
        'all_location_list': all_location_list,
        'assign_assets_counts': assign_assets_counts,
        'unassign_assets_count': unassign_assets_count,
        'latest_users_list': latest_users_list,
        'users_count': users_count,
        'expiring_assets': expiring_assets,
        'title': 'Dashboard',
        'license_count': get_license_count
    }
 
    return render(request, 'index.html', context=context)


@unauthenticated_user
def user_login(request):
    # form = UserLoginForm()
    # if request.method == 'POST':
    form = UserLoginForm()
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(email=email, password=password)
            asset = None
            product = None
            if user is not None:
                
                if not AssetStatus.objects.filter(can_modify=False).first() or not AssetStatus.objects.filter(name='Available'):
                    AssetStatus.objects.create(name='Available', organization=None, can_modify=False)
                    seed_asset_statuses(asset=True)
                if not ProductType.objects.filter(can_modify=False).first():
                    seed_asset_statuses(product=True)
                if not ProductCategory.objects.filter(name='Root').exists():
                    seed_parent_category(category=True)
                else:
                    print('seed fail for category')

                login(request, user)
                # full_name=dynamic_display_name(fullname=user.full_name, format_key)
                messages.success(request,  f'Welcome, {user.full_name}')

                # redirecting to the requested url
                if request.GET.get('next'):
                    return redirect(request.GET.get('next'))
                return redirect('/')
            else:
                messages.error(request, 'Invalid credentials!')
    last_logins=User.objects.values_list('last_login',flat=True)

    return render(request, 'auth/login.html', context={'form': form,'current_step':5,'last_logins':last_logins})



@unauthenticated_user
def user_register(request):
    u_form = UserRegisterForm()
    o_form = OrganizationForm()
    if request.method == "POST":
        if User.objects.filter(is_superuser=True).first():
            messages.error(request,'You are already registered')
        else:
            o_form = OrganizationForm(request.POST)
            u_form = UserRegisterForm(request.POST)
            if o_form.is_valid() and u_form.is_valid():
                organization = o_form.save()
                user = u_form.save(commit=False)
                user.organization = organization
                user.is_active = True
                user.is_superuser = True
                user.access_level = True
                user.is_active = True
                user.save()

                messages.success(
                    request, f'Account for {user.full_name} created successfully.')
                return redirect('authentication:login')
            else:
                messages.error(request, 'Please correct the below errors.')
    return render(request, 'auth/register.html', context={'u_form': u_form, 'o_form': o_form,'current_step':4})


@unauthenticated_user
def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request, 'Your account verified successfully. You can login now.')
        return redirect('authentication:login')
    else:
        messages.error(request, 'Invalid token.')
        return redirect('authentication:login')


@login_required
def profile(request):
    obj= LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    format_key= None
    # for id,it in NAME_FORMATS:
    #     if format_key and obj.name_display_format == id:
    #         format_key=id
    user = request.user
    print(request.user)
    assigned_assets = AssignAsset.objects.filter(user=request.user).first()
    print("_____________",assigned_assets)
    # asset_paginator=Paginator(assigned_assets,10,orphans=1)
    # asset_page_number=request.GET.get('assets_page')
    # asset_page_object=asset_paginator.get_page(asset_page_number)
    get_user_full_name=user.dynamic_display_name(user.full_name)
    context = {'profile': True, 'title': 'Profile', 'full_name':get_user_full_name,
               'assigned_assets': assigned_assets,'email_notification':user.email_notification,'browser_notification':user.browser_notification,'slack_notification':user.slack_notification,'inapp_notification':user.inapp_notification}
    return render(request, 'auth/profile.html', context=context)


@login_required
def profile_basic_info_update(request):
    user = request.user
    old_email = user.email
    form = UserUpdateForm(instance=user)
    address_form = None

    if not user.is_superuser:
        address = get_object_or_404(Address, pk=user.address.id)
        address_form = AddressForm(request.POST or None, instance=address)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if user.is_superuser:
            if form.is_valid():
                new_email = form.cleaned_data['email']
                form.save()
                if (old_email) != (new_email):
                    logout(request)
                    messages.success(
                        request, 'Profile updated successfully. and verification mail has been sent to the new email address.')
                else:
                    messages.success(request, 'Profile updated successfully')
                return HttpResponse(status=204)
        else:
            if form.is_valid() and address_form.is_valid():
                new_email = form.cleaned_data['email']
                form.save()
                address_form.save()
                if (old_email) != (new_email):
                    logout(request)
                    messages.success(
                        request, 'Profile updated successfully. and verification mail has been sent to the new email address.')
                else:
                    messages.success(request, 'Profile updated successfully')
                return HttpResponse(status=204)

    context = {'form': form, 'address_form': address_form}
    return render(request, 'auth/profile_basic_info_update.html', context=context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def organization_info_update(request):
    organization = request.user.organization
    organization_form = OrganizationUpdateForm(instance=organization)

    if request.method == "POST":
        organization_form = OrganizationUpdateForm(
            request.POST, request.FILES, instance=organization)
        if organization_form.is_valid():
            organization_form.save()
            messages.success(
                request, 'Organization details updated successfully')
            return HttpResponse(status=204)

    context = {'organization_form': organization_form,
               'organization': organization}
    return render(request, 'auth/organization_info_update.html', context=context)

@never_cache
@login_required
def logout_view(request):
    logout(request)
    return redirect('/')