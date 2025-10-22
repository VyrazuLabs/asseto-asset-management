from django.shortcuts import get_object_or_404, redirect, render
from configurations.models import BrandingImages
from configurations.utils import add_path, create_or_update_image, update_files_name
from django.contrib.auth.decorators import login_required

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