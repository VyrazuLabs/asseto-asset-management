from license.models import AssignLicense


def get_assigned_users():
    assigned_licenses=AssignLicense.objects.select_related("user","license")
    license_and_user_details={}
    for assigned_license in assigned_licenses:
        license_and_user_details[assigned_license.license.id]={
            'name':assigned_license.user.full_name,
            'image':assigned_license.user.profile_pic
        }
    return license_and_user_details
