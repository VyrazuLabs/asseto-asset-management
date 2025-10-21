from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from configurations.models import BrandingImages
from configurations.utils import add_path, update_files_name
from django.contrib.auth.decorators import login_required

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
