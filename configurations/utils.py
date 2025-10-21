import os
import uuid
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from configurations.models import BrandingImages

def update_files_name(logo,favicon,login_page_logo):
    my_uuid=uuid.uuid4()
    file_dist={}

    def save_files(file_obj,folder_name):
        # if not file_obj:
        #     return None
        folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Generate new name
        # ext = os.path.splitext(file_obj.name)[1]
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
        image_dist={'id':brand_img.id}
    except:
        brand_img=None
    
    if brand_img.logo:
        image_dist['logo']=f'{brand_img.logo_path}{brand_img.logo}'
    if brand_img.favicon:
        image_dist['favicon']=f'{brand_img.favicon_path}{brand_img.favicon}'
    if brand_img.login_page_logo:
        image_dist['login_page_logo']=f'{brand_img.login_page_logo_path}{brand_img.login_page_logo}'

    return image_dist