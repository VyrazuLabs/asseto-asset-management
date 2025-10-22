from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from configurations.models import BrandingImages
from configurations.utils import add_path, update_files_name
from django.contrib.auth.decorators import login_required
from .forms import TagConfigurationForm
from .models import TagConfiguration
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import TagConfigurationForm
from .models import TagConfiguration

@login_required
def logo_upload(request):
    if request.method == "POST":
        logo = request.FILES.get('logo')
        favicon = request.FILES.get('favicon')
        login_page_logo = request.FILES.get('login_page_logo')

        file_dist = update_files_name(logo, favicon, login_page_logo)        
        try:
            if BrandingImages.objects.filter(organization=request.user.organization).exists():
                existing_image=BrandingImages.objects.get(organization=request.user.organization)
                if logo:
                    existing_image.logo=file_dist.get("logo")
                if favicon:
                    existing_image.favicon=file_dist.get("favicon")
                if login_page_logo:
                    existing_image.login_page_logo=file_dist.get("login_page_logo")
                messages.success(request,"Upload sucessfully")
            else:
                BrandingImages.objects.create(
                    organization=request.user.organization,
                    logo= file_dist.get("logo"),
                    favicon= file_dist.get("favicon"),
                    login_page_logo=file_dist.get("login_page_logo")
                    )
                messages.success(request,"Upload sucessfully")
        except Exception as e:
            print('error is----->,',str(e))
            messages.error(request,"Upload did not happen")
        return redirect('configurations:upload_logo') 

    else:
        add_path_context=add_path(request.user.organization)
        print(add_path_context)
        return render(request, 'configurations/logo.html',{'add_path_context':add_path_context})
    
def delete_logo(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.logo=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import TagConfigurationForm
from .models import TagConfiguration


@csrf_exempt
def create_or_update_tag_configuration(request, id=None):
    user_default_settings = request.GET.get('user_default_settings')
    print("user_default_settings", user_default_settings)
    print(id)
    # Check if we're editing an existing configuration
    instance = None
    if id:
        instance = get_object_or_404(TagConfiguration, pk=id, organization=request.user.organization,use_default_settings=True)
        print("Editing existing configuration:", instance)
    if request.method == 'POST':
        organization = request.user.organization
        form = TagConfigurationForm(request.POST, instance=instance)

        if form.is_valid():
            config = form.save(commit=False)
            config.organization = organization
            config.save()

            print("Saved configuration:", config)
            return redirect('configurations:list_tag')

        # Invalid form -> show field errors in context
        return render(request, 'configurations/add_tag.html', {'form': form})

    # GET request -> prefill if updating, empty for new
    form = TagConfigurationForm(instance=instance)
    context = {
        'form': form,
        'is_update': bool(instance),  # For optional UI changes
        'configurations': instance
    }
    template_name = 'configurations/add_tag.html' if instance else 'configurations/add_tag.html'
    return render(request, template_name, context)
@csrf_exempt
def update_tag_configuration(request, id=None):
    config = get_object_or_404(TagConfiguration, pk=id)

    if request.method == 'POST':
        # Bind both POST data and existing instance for updates
        update_form = TagConfigurationForm(request.POST, instance=config)
        if update_form.is_valid():
            update_form.save()
            return redirect('configurations:list_tag')  # Redirect after save
    else:
        # Pre-fill the form with existing data
        update_form = TagConfigurationForm(instance=config)

    context = {
        "form": update_form,
        "configurations": config
    }
    return render(request, 'configurations/add_tag.html', context)

def list_tag_configurations(request):
    configurations = TagConfiguration.objects.filter(organization=request.user.organization).first()
    return render(request, 'configurations/list_tag.html', {'configurations': configurations})

def toggle_default_settings(request, id):
    configurations = TagConfiguration.objects.filter(organization=request.user.organization).first()
    config = get_object_or_404(TagConfiguration, pk=id, organization=request.user.organization)
    config.use_default_settings = not config.use_default_settings
    config.save()
    return 