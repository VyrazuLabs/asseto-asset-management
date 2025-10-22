import os
from django.contrib import messages
import uuid
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from configurations.models import BrandingImages

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
        print('error is----->,',str(e))
        messages.error(request,"Upload did not happen")
