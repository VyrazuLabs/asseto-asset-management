from .models import LocalizationConfiguration, BrandingImages
from .translations import get_translations

def translations(request):
    """
    A context processor that adds the translation dictionary to every template context.
    """
    if request.user.is_authenticated:
        # Fetch the organization's localization settings
        config = LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
        lang_id = config.default_language if config else 0
    else:
        lang_id = 0
        
    return {
        'trans': get_translations(lang_id)
    }

def sidebar_logo(request):
    get_logo = BrandingImages.objects.first()
    if get_logo:
        if get_logo.logo:
            updated_logo = BrandingImages.logo_path + get_logo.logo
            return {'get_logo': updated_logo}
    return {'get_logo': None}

def favicon_image(request):
    get_favicon = BrandingImages.objects.first()
    if get_favicon:
        if get_favicon.favicon:
            updated_favicon = BrandingImages.favicon_path + get_favicon.favicon
            return {'get_favicon': updated_favicon}
    return {'get_favicon': None}

def login_page_logo(request):
    get_login_page_logo = BrandingImages.objects.first()
    if get_login_page_logo:
        if get_login_page_logo.login_page_logo:
            updated_login_page_logo = BrandingImages.login_page_logo_path + get_login_page_logo.login_page_logo
            return {'updated_login_page_logo': updated_login_page_logo}
    return {'updated_login_page_logo': None}