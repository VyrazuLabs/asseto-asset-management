from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from configurations.models import BrandingImages


def sidebar_logo(request):
    if request.user.is_authenticated:
        get_logo=BrandingImages.objects.first()
        if get_logo.logo:
            updated_logo=BrandingImages.logo_path+get_logo.logo
            return {'get_logo':updated_logo}
    return {'get_logo': None}



def favicon_image(request):
    if request.user.is_authenticated:
        get_favicon=BrandingImages.objects.first()
        if get_favicon.favicon:
            updated_favicon=BrandingImages.favicon_path+get_favicon.favicon
            return {'get_favicon': updated_favicon}

    return {'get_favicon': None}

def login_page_logo(request):
    get_login_page_logo=BrandingImages.objects.first()
    if get_login_page_logo.login_page_logo:
        updated_login_page_logo=BrandingImages.login_page_logo_path + get_login_page_logo.login_page_logo
        return{'updated_login_page_logo':updated_login_page_logo}
    return {'updated_login_page_logo':None}