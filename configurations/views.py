from django.shortcuts import get_object_or_404, redirect, render
from configurations.models import BrandingImages,LocalizationConfiguration
from configurations.utils import add_path, create_or_update_image, update_files_name
from django.contrib import messages
from configurations.models import BrandingImages,LocalizationConfiguration
from configurations.utils import add_path, update_files_name
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .forms import TagConfigurationForm
from .models import TagConfiguration
from .constants import COUNTRY_CHOICES,CURRENCY_CHOICES,DEFAULT_NAME_DISPLAY_FORMAT,DEFAULT_LANGUAGE,DATETIME_CHOICES

@login_required
def logo_upload(request):
    if request.method == "POST":
        logo = request.FILES.get('logo')
        favicon = request.FILES.get('favicon')
        login_page_logo = request.FILES.get('login_page_logo')

        file_dist = update_files_name(request,logo, favicon, login_page_logo)        
        create_or_update_image(request,logo, favicon, login_page_logo,file_dist, organization=request.user.organization)
        return redirect('configurations:upload_logo') 

    else:
        add_path_context=add_path(request.user.organization)
        return render(request, 'configurations/logo.html',{'add_path_context':add_path_context})



def delete_logo(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.logo=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

def delete_favicon(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.favicon=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

def delete_login_page_logo(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.login_page_logo=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

@csrf_exempt
def create_or_update_tag_configuration(request, id=None):
    user_default_settings = request.GET.get('user_default_settings')
    # Check if we're editing an existing configuration
    instance = None
    if id:
        instance = get_object_or_404(TagConfiguration, pk=id, organization=request.user.organization)
    if request.method == 'POST':
        organization = request.user.organization
        form = TagConfigurationForm(request.POST, instance=instance)

        if form.is_valid():
            config = form.save(commit=False)
            config.organization = organization
            config.save()
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
@login_required
def list_localizations(request):
    configurations = LocalizationConfiguration.objects.filter(organization=request.user.organization).last()
    get_default_language={}
    get_default_name_display_format={}
    get_default_time_format={}
    get_default_currency_format={}
    get_default_country_format={}
    if configurations:
        for id,name in DEFAULT_LANGUAGE:
            if id == configurations.default_language:
                get_default_language= {'name':name,'id':id}
        for id,name in DEFAULT_NAME_DISPLAY_FORMAT:
            if id == configurations.name_display_format:
                get_default_name_display_format= {'name':name,'id':id}
        for id,name in DATETIME_CHOICES:
            if id == configurations.time_format:
                get_default_time_format= {'name':name,'id':id}
        for id,name in CURRENCY_CHOICES:
            if id == configurations.time_format:
                get_default_currency_format= {'name':name,'id':id}
        for id,name in COUNTRY_CHOICES:
            if id == configurations.time_format:
                get_default_country_format= {'name':name,'id':id}
    else:
        configurations=None
    return render(request, 'configurations/list_localization.html', {'configurations': configurations,'country_choices': COUNTRY_CHOICES,'currency_choices': CURRENCY_CHOICES,'name_display_format':DEFAULT_NAME_DISPLAY_FORMAT,'default_language':DEFAULT_LANGUAGE,'datetime_choices':DATETIME_CHOICES,'get_default_language':get_default_language,'get_default_name_display_format':get_default_name_display_format,'get_default_time_format':get_default_time_format,'get_default_currency_format':get_default_currency_format,'get_default_country_format':get_default_country_format})


# def get_localization(request):
#     context = {
#         'country_choices': COUNTRY_CHOICES
#     }
#     return render(request, 'configurations/add.html', context)

def create_localization_configuration(request):
    if request.method == 'POST':
        country_format = request.POST.get('country-format')
        currency_format = request.POST.get('currency-format')
        name_display_format = request.POST.get('name-format')
        default_language = request.POST.get('language-format')
        time_format=request.POST.get('time-format')

        configurations, created = LocalizationConfiguration.objects.get_or_create(
            organization=request.user.organization,
            country_format=country_format,
            currency=currency_format,
            name_display_format=name_display_format,
            default_language=default_language,
            time_format=time_format
        )

        if not created:
            configurations.country_format = country_format
            configurations.currency = currency_format
            configurations.name_display_format = name_display_format
            configurations.default_language = default_language
            configurations.time_format = time_format
            configurations.save()

        return redirect('configurations:list_localization')

    return redirect('configurations:list_localization')