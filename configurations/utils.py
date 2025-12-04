import os
from django.contrib import messages
import uuid
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from configurations.models import BrandingImages,LocalizationConfiguration
from .constants import DATETIME_CHOICES,CURRENCY_CHOICES,NAME_FORMATS
from datetime import datetime
from dateutil.parser import parse
from authentication.models import User
def update_files_name(request,logo,favicon,login_page_logo):
    max_file_size=5*1024*1024
    my_uuid=uuid.uuid4()
    file_dist={}

    def save_files(file_obj,folder_name):
        if not file_obj:
            return None
        
        if file_obj.size >max_file_size:
            messages.error(request,"File size is more than 5 MB")
            return None
        
        folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)

        video_extentions={'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        ext = os.path.splitext(file_obj.name)[1].lower()

        if ext in video_extentions:
            messages.error(request,"Video files are not allowed")
            return None

        os.makedirs(folder_path, exist_ok=True)

        # Generate new name
        unique_name = f"{my_uuid}__{file_obj.name}"

        # Save file
        fs = FileSystemStorage(location=folder_path)
        fs.save(unique_name, file_obj)
        return unique_name

    if logo:
        file_dist["logo"]=save_files(logo,'logo')
    if favicon:
        file_dist["favicon"]=save_files(favicon,'favicon')

    if login_page_logo:
        file_dist["login_page_logo"]=save_files(login_page_logo,'login_page_logo')

    return file_dist


def add_path(organization):
    fs = FileSystemStorage(location=settings.MEDIA_ROOT)
    image_dist={}
    try:
        brand_img=BrandingImages.objects.get(organization=organization)
    except:
        brand_img=None

    if brand_img:
        image_dist={'id':brand_img.id}
        if brand_img.logo:
            image_dist['logo']=f'{brand_img.logo_path}{brand_img.logo}'
        if brand_img.favicon:
            image_dist['favicon']=f'{brand_img.favicon_path}{brand_img.favicon}'
        if brand_img.login_page_logo:
            image_dist['login_page_logo']=f'{brand_img.login_page_logo_path}{brand_img.login_page_logo}'
    return image_dist

def create_or_update_image(request,logo, favicon, login_page_logo,file_dist,organization):
    try:
        if any([file_dist.get("logo"), file_dist.get("favicon"), file_dist.get("login_page_logo")]):
            if BrandingImages.objects.filter(organization=organization).exists():
                existing_image=BrandingImages.objects.get(organization=organization)
                if logo:
                    existing_image.logo=file_dist.get("logo")
                    existing_image.save()
                if favicon:
                    existing_image.favicon=file_dist.get("favicon")
                    existing_image.save()
                if login_page_logo:
                    existing_image.login_page_logo=file_dist.get("login_page_logo")
                    existing_image.save()
                messages.success(request,"Upload sucessfully")
            else:
                if any([file_dist.get("logo"), file_dist.get("favicon"), file_dist.get("login_page_logo")]):
                    BrandingImages.objects.create(
                        organization=request.user.organization,
                        logo= file_dist.get("logo"),
                        favicon= file_dist.get("favicon"),
                        login_page_logo=file_dist.get("login_page_logo")
                        )
                    messages.success(request,"Upload sucessfully")

    except Exception as e:
        messages.error(request,"Upload did not happen")


def generate_asset_tag(prefix, number_suffix):
    """
    Generate an auto-incrementing tag with given prefix and number suffix as strings.
    Example: prefix='VY', number_suffix='001' -> VY001, VY002, ...
    """
    from assets.models import Asset

    # Determine numeric part from number_suffix string
    start_num = int(number_suffix)
    size = len(number_suffix)

    # Get last asset tag that starts with prefix
    last_tag = Asset.undeleted_objects.filter(tag__startswith=prefix,).order_by('-created_at').first()
    if last_tag:
        # Extract numeric part after prefix
        numeric_part = last_tag.tag[len(prefix):]
        if numeric_part.isdigit():
            last_num = int(numeric_part)
            next_num = last_num + 1
        else:
            next_num = start_num
    else:
        next_num = start_num

    # Format number with leading zeros to match size of input number_suffix
    number_str = str(next_num).zfill(size)

    return f"{prefix}{number_str}"

def get_currency_and_datetime_format(organization):
    getLocalization=LocalizationConfiguration.objects.filter(organization=organization).first()
    if getLocalization:
        get_currency=getLocalization.currency   #we get the currency no.
        get_time=getLocalization.time_format    #we get the time no.
    if getLocalization is None:
        get_currency=None
        get_time=None
    currency_format=None
    date_format=None
    for it,data in CURRENCY_CHOICES:
        if it==get_currency:
            currency_format=data
            break
    for it,data in DATETIME_CHOICES:
        if it==get_time:
            date_format=data
            break
    # new_date_format=format_datetime(output_format=date_format)
    obj={'currency':currency_format,'date_format':date_format}
    return obj
    # return organization.currency, organization.date_format

def format_datetime(x,output_format):
    """Convert datetime object to the specified output format."""
    # x = datetime.datetime.now()
    print(x)
    if isinstance(x, str):
        x = parse(x)

    formats = {
        'YYYY-MM-DD': '%Y-%m-%d',
        'Day Month DD, Year': '%A %B %d, %Y',
        'Month DD, YYYY': '%B %d, %Y',
        'DD/MM/YYYY': '%d/%m/%Y',
        'MM/DD/YYYY': '%m/%d/%Y'
    }

    if output_format not in formats:
        raise ValueError("Invalid format. Choose from: " + ", ".join(formats.keys()))

    return x.strftime(formats[output_format])
    
# def dynamic_display_name(request, format_key="first_last"):
#     user_id=request.user
#     user=User.objects.filter(id=user_id.id).first()
#     if not user:
#         return ""
#     # For generalized templates, support initials and such
#     formats = NAME_FORMATS
#     # Prepare mapping with all possible user name parts
#     context = {
#         "first": getattr(user, "first_name", "") or "",
#         "last": getattr(user, "last_name", "") or "",
#     }
#     try:
#         fmt = formats.get(format_key, formats["first_last"])
#         return fmt.format(**context)
#     except Exception:
#         # fallback to simple "first last"
#         return f'{context["first"]} {context["last"]}'

def dynamic_display_name(request,fullname):
    format_key= LocalizationConfiguration.objects.filter(organization=request.user.organization).first()

    format_key=format_key.name_display_format if format_key else "0"

    parts = (fullname or "").strip().split()
    first = parts[0] if len(parts) >= 1 else ""
    last = parts[-1] if len(parts) >= 2 else ""
    first_initial = first[0] if first else ""
    context = {
        "first": first,
        "last": last,
        "first_initial": first_initial,
    }
    format_key=str(format_key)
    for it,data in NAME_FORMATS:
        if str(it)==format_key:
            format_key=data
    fmt = format_key
    try:
        return fmt.format(**context).strip()
    except Exception:
        # fallback to standard "First Last"
        return f"{first} {last}".strip()
