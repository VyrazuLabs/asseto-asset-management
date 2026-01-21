from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from configurations.models import BrandingImages,LocalizationConfiguration
from configurations.utils import add_path, create_or_update_image, update_files_name,hide_last_digits
from django.contrib import messages
from configurations.models import BrandingImages,LocalizationConfiguration
from configurations.utils import add_path, update_files_name
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .forms import TagConfigurationForm,ClientCredentialsForm
from .models import TagConfiguration,Extensions,SlackConfiguration
import base64
from dashboard.models import Organization
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .constants import DEFAULT_COUNTRY,COUNTRY_CHOICES,CURRENCY_CHOICES,NAME_FORMATS,DEFAULT_LANGUAGE,DATETIME_CHOICES,INTEGRATION_CHOICES,DEFAULT_CURRENCY

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
        return render(request, 'configurations/logo.html',{'add_path_context':add_path_context,'submenu':'branding','sidebar':'configurations'})


@login_required
def delete_logo(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.logo=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

@login_required
def delete_favicon(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.favicon=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

@login_required
def delete_login_page_logo(request, id):
    try:
        get_logo=get_object_or_404(BrandingImages,pk=id)
        get_logo.login_page_logo=None
        get_logo.save()
    except Exception as e:
        print(e)
    return redirect('configurations:upload_logo')

@csrf_exempt
@login_required
def create_or_update_tag_configuration(request, id=None):
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
@login_required
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

@login_required
def list_tag_configurations(request):
    configurations = TagConfiguration.objects.filter(organization=request.user.organization).first()
    if configurations is None:
        instance=None
        form = TagConfigurationForm(instance=instance)
        return render(request, 'configurations/add_tag.html',{'form': form,'is_update': bool(instance),'configurations': instance,'submenu':'tag-configuration','sidebar':'configurations'})
    return render(request, 'configurations/list_tag.html', {'configurations': configurations,'submenu':'tag-configuration','sidebar':'configurations'})

@login_required
def toggle_default_settings(request, id):
    config = get_object_or_404(TagConfiguration, pk=id, organization=request.user.organization)
    config.use_default_settings = not config.use_default_settings
    config.save()
    return 

@login_required
def list_localizations(request):
    configurations = LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    get_default_language={"name": "English"}
    get_default_name_display_format={}
    get_default_time_format={}
    get_default_currency_format={}
    get_default_country_format={}
    if configurations:
        for id,name in NAME_FORMATS:
            if id == configurations.name_display_format:
                get_default_name_display_format= {'name':name,'id':id}
        for id,name in DATETIME_CHOICES:
            if id == configurations.time_format:
                get_default_time_format= {'name':name,'id':id}
        for id,name in CURRENCY_CHOICES:
            if id == configurations.currency:
                get_default_currency_format= {'name':name,'id':id}
    else:
        get_default_language=None
        get_default_name_display_format=None
        get_default_time_format=None
        get_default_currency_format=None
        get_default_country_format=None
    return render(request, 'configurations/list_localization.html', {'configurations': configurations,'country_choices': COUNTRY_CHOICES,'currency_choices': CURRENCY_CHOICES,'name_display_format':NAME_FORMATS,'default_language':DEFAULT_LANGUAGE,'datetime_choices':DATETIME_CHOICES,'default_country':DEFAULT_COUNTRY,'get_default_language':get_default_language,'get_default_name_display_format':get_default_name_display_format,'get_default_time_format':get_default_time_format,'get_default_currency_format':get_default_currency_format,'get_default_country_format':get_default_country_format,'submenu':'localization','sidebar':'configurations'})

@login_required
def create_localization_configuration(request):
    get_obj=LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    if request.method == 'POST':
        country_format = request.POST.get('country-format')
        currency_format = request.POST.get('currency-format')
        name_display_format = request.POST.get('name-format')
        default_language = request.POST.get('language-format')
        time_format = request.POST.get('time-format')

        if get_obj:
            # Update existing configuration
            get_obj.country_format = country_format
            get_obj.currency = currency_format
            get_obj.name_display_format = name_display_format
            get_obj.default_language = default_language
            get_obj.time_format = time_format
            get_obj.save()
        else:
            # Create new configuration
            LocalizationConfiguration.objects.create(
                organization=request.user.organization,
                country_format=country_format,
                currency=currency_format,
                name_display_format=name_display_format,
                default_language=default_language,
                time_format=time_format
            )
        return redirect('configurations:list_localization')

    return redirect('configurations:list_localization')

@login_required
def integration(request):
    if request.method == 'POST':
        integration_type = request.POST.get('integration_type')
        form = ClientCredentialsForm(request.POST)
        if form.is_valid():
            client_id = form.cleaned_data['client_id']
            client_secret = form.cleaned_data['client_secret']
            # integration_type = form.cleaned_data['integration_type']
            if integration_type:  # Slack
                # Logic to save Slack credentials
                request.session['slack'] = True
            else:
                request.session['slack'] = False
            # Save logic here...
            return redirect('configurations:integration')
    elif request.method == 'GET':
        form = ClientCredentialsForm()
        integration_choices=INTEGRATION_CHOICES
        slack_config=SlackConfiguration.objects.filter(user=request.user).first()
        client_id=base64.b64decode(slack_config.client_id).decode() if slack_config else None
        client_secret=base64.b64decode(slack_config.client_secret).decode() if slack_config else None
        if client_id is not None:   
            client_id=hide_last_digits(client_id)
        context={
            'client_id':client_id,
            'client_secret':client_secret
        }
        print(context)
    # On GET or other methods, you may render the form page or handle differently
        return render(request, "configurations/integrations.html", context=context)

        print(integration_choices)
    return render(request, 'configurations/integrations.html', {'form': form,'integration_choices':integration_choices})

@login_required
def list_extensions(request):
    # integration_choices=INTEGRATION_CHOICES
    for choice_id, (entity_name, description) in INTEGRATION_CHOICES:
        existing_extension = Extensions.objects.filter(
            organization=request.user.organization, entity_name=entity_name
        ).first()
        if not existing_extension:
            Extensions.objects.create(
                organization=request.user.organization,
                description=description,
                entity_name=entity_name,
                status=0,  # Inactive by default
                validity=0,
            )
    get_extensions=Extensions.objects.get(entity_name="Slack",organization=request.user.organization)

    get_api_extension=Extensions.objects.get(entity_name="API")
    if get_extensions:
        request.session['slack'] = True
    else:
        request.session['slack'] = False
    return render(request, 'configurations/list-extensions.html',{'integration_choices':get_extensions,'api_extension':get_api_extension})

@login_required
def extension_status(request, id):
    status = request.POST.get("status", "off")  # will be "on" or "off"

    ext = Extensions.objects.filter(id=id).first()
    ext.status = 1 if status == "on" else 0
    ext.save()

    return redirect("configurations:list_extensions")

@login_required
def save_slack_configuration(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id", "").strip()
        client_secret = request.POST.get("client_secret", "").strip()
        client_id = base64.b64encode(client_id.encode()).decode()
        client_secret = base64.b64encode(client_secret.encode()).decode()
        # Encode client_id and client_secret in base64

        slack_config, created = SlackConfiguration.objects.get_or_create(user=request.user)
        slack_config.client_id = client_id
        slack_config.client_secret = client_secret
        slack_config.save()
        print("Slack configuration saved successfully")
        # Redirect or render success message as needed
        return redirect("configurations:integration")
    if request.method == "GET":
        slack_config=SlackConfiguration.objects.filter(user=request.user).first()
        client_id=base64.b64decode(slack_config.client_id).decode() 
        client_secret=base64.b64decode(slack_config.client_secret).decode()
        context={
            'client_id':client_id,
            'client_secret':client_secret
        }
        # On GET or other methods, you may render the form page or handle differently
        return redirect("configurations:integration")
    
@login_required
@permission_required('authentication.delete_location')
def add_organization(request):
    name=request.POST.get('organization_name')
    website=request.POST.get('organization_website')
    email=request.POST.get('organization_email')
    currency=request.POST.get('currency-format')
    phone=request.POST.get('organization_phone')
    get_organization_id=request.user.organization.id
    if request.method=="POST":
        if get_organization_id is not None:
            Organization.objects.update(
                id=get_organization_id,
                name=name,
                website=website,
                email=email,    
                currency=currency,
                phone=phone
            )
        else:
            Organization.objects.create(
                name=name,
                website=website,
                email=email,
                currency=currency,
                phone=phone
            )
        messages.success(request, 'Organization added successfully')
        return redirect('configurations:add_organization')
    elif request.method=="GET":
        get_user_organization_id=request.user.organization.id
        if get_user_organization_id:
            get_org_data=Organization.objects.filter(id=get_user_organization_id).first()
            print("get_org_data",get_org_data.id)
        else:
            get_org_data=None
        return render(request, 'configurations/add_organization.html', context={'org_data': get_org_data,'currency_choices':CURRENCY_CHOICES,'submenu':'organization','sidebar':'configurations'})

@login_required  
def api_extension_status(request,id):
    status = request.POST.get("api_status", "off")
    ext = get_object_or_404(Extensions,pk=id)
    ext.status = 1 if status == "on" else 0
    ext.save()
    return redirect("configurations:list_extensions")