from django.http import JsonResponse
from license.forms import AssignLicenseForm
from .models import AssignLicense, License
from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404

def assign_license(request, license_id):
    license = get_object_or_404(License, pk=license_id)
    if request.method == "POST":
        form = AssignLicenseForm(request.POST)

        if form.is_valid():
            assign = form.save(commit=False)
            assign.license = license
            license.is_assigned=True
            license.save()
            assign.save()
            return JsonResponse({"success": True})

        return render(request,"license/assign-license-modal.html",{"license": license, "form": form},status=400)
    else:
        form = AssignLicenseForm()

    return render(
        request,
        "license/assign-license-modal.html",
        {"license": license, "form": form}
    )


def usassign_license(request,license_id):
    license=get_object_or_404(License,pk=license_id)
    get_assigned_license=get_object_or_404(AssignLicense,license=license_id)
    license.is_assigned=False
    license.save()
    get_assigned_license.delete()
    return redirect("license:license_list")

