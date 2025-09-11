from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from asyncio.log import logger
from django.shortcuts import redirect
from django.shortcuts import render, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from authentication.forms import (
    UserRegisterForm, OrganizationForm, UserPasswordChangeForm, UserLoginForm, UserUpdateForm, OrganizationUpdateForm)
from authentication.decorators import unauthenticated_user
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from authentication.token import account_activation_token
from django.contrib.auth.models import User
from dashboard.forms import LocationForm, AddressForm
from dashboard.models import Location, Address,ProductType,ProductCategory
from django.contrib.auth import get_user_model
from products.models import Product
from vendors.models import Vendor
from assets.models import *
from django.db.models.signals import post_save 
from django.dispatch import receiver
from assets.seeders import seed_asset_statuses
from assets.models import AssignAsset
from django.views.decorators.cache import never_cache
from dashboard.views.seeders import seed_parent_category
from django.db.models import Q
User = get_user_model()


@login_required
def index(request):
 
    all_asset_cost = 0
    today = datetime.now()
    time_threshold = datetime.now() + timedelta(days=30)
    expiring_assets = Asset.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization, warranty_expiry_date__lt=time_threshold)).exclude(
        warranty_expiry_date__lt=today).order_by('warranty_expiry_date')
 
    all_asset_list = Asset.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization))
    asset_count = all_asset_list.count()
 
    for asset in all_asset_list:
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
        asset__organization=request.user.organization))
    assign_assets_counts = assign_assets.count()
 
    unassign_assets_count = asset_count - assign_assets_counts
 
    users_list = User.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization)).exclude(is_superuser=True)
    latest_users_list = User.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).exclude(
        is_superuser=True).order_by('created_at').reverse()[0:5]
    users_count = users_list.count()
 
    context = {
 
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
        'title': 'Dashboard'
 
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
                messages.success(request,  f'Welcome, {user.full_name}')

                # redirecting to the requested url
                if request.GET.get('next'):
                    return redirect(request.GET.get('next'))
                return redirect('/')
            else:
                messages.error(request, 'Invalid credentials!')
    return render(request, 'auth/login.html', context={'form': form})



@unauthenticated_user
def user_register(request):

    u_form = UserRegisterForm()
    o_form = OrganizationForm()
    if request.method == "POST":
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
                request, f'Account for {user.full_name} created successfully. Please verify your email to continue.')
            return redirect('authentication:login')
        else:
            messages.error(request, 'Please correct the below errors.')
    return render(request, 'auth/register.html', context={'u_form': u_form, 'o_form': o_form})


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
    context = {'profile': True, 'title': 'Profile'}
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