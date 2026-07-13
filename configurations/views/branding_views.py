from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from configurations.models import BrandingImages
from configurations.utils import (add_path, create_or_update_image,
                                  process_uploaded_logos)


@login_required
def logo_upload(request):
    if request.method == "POST":
        logo = request.FILES.get("logo")
        favicon = request.FILES.get("favicon")
        login_page_logo = request.FILES.get("login_page_logo")

        file_dist = process_uploaded_logos(
            request, logo=logo, favicon=favicon, login_page_logo=login_page_logo
        )
        create_or_update_image(
            request,
            logo,
            favicon,
            login_page_logo,
            file_dist,
            organization=request.user.organization,
        )
        return redirect("configurations:upload_logo")

    else:
        add_path_context = add_path(request.user.organization)
        return render(
            request,
            "configurations/logo.html",
            {
                "add_path_context": add_path_context,
                "submenu": "branding",
                "sidebar": "configurations",
            },
        )


@login_required
def delete_logo(request, id):

    get_logo = get_object_or_404(BrandingImages, pk=id)
    get_logo.logo = None
    get_logo.save()

    return redirect("configurations:upload_logo")


@login_required
def delete_favicon(request, id):

    get_logo = get_object_or_404(BrandingImages, pk=id)
    get_logo.favicon = None
    get_logo.save()

    return redirect("configurations:upload_logo")


@login_required
def delete_login_page_logo(request, id):

    get_logo = get_object_or_404(BrandingImages, pk=id)
    get_logo.login_page_logo = None
    get_logo.save()
    return redirect("configurations:upload_logo")


