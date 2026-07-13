from .models import LocalizationConfiguration, BrandingImages
from .translations.utils import get_translations

def translations(request):
    """
    A context processor that adds the translation dictionary to every template context.

    Performance: lang_id is cached in the session so that the DB is only queried
    when the cached value is absent.  To invalidate the cache after a language
    change, call:  del request.session['org_lang_id']  (or session.flush())
    in the view that saves the localization settings.
    """
    if request.user.is_authenticated:
        lang_id = request.session.get("org_lang_id")
        if lang_id is None:
            config = LocalizationConfiguration.objects.filter(
                organization=request.user.organization
            ).first()
            lang_id = config.default_language if config else 0
            # Cache for the lifetime of this session
            request.session["org_lang_id"] = lang_id
    else:
        lang_id = 0

    return {"trans": get_translations(lang_id)}


def sidebar_logo(request):
    get_logo = BrandingImages.objects.first()
    if get_logo:
        if get_logo.logo:
            updated_logo = BrandingImages.logo_path + get_logo.logo
            return {"get_logo": updated_logo}
    return {"get_logo": None}


def favicon_image(request):
    get_favicon = BrandingImages.objects.first()
    if get_favicon:
        if get_favicon.favicon:
            updated_favicon = BrandingImages.favicon_path + get_favicon.favicon
            return {"get_favicon": updated_favicon}
    return {"get_favicon": None}


def login_page_logo(request):
    get_login_page_logo = BrandingImages.objects.first()
    if get_login_page_logo:
        if get_login_page_logo.login_page_logo:
            updated_login_page_logo = (
                BrandingImages.login_page_logo_path
                + get_login_page_logo.login_page_logo
            )
            return {"updated_login_page_logo": updated_login_page_logo}
    return {"updated_login_page_logo": None}
