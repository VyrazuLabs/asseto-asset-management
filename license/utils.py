from license.models import AssignLicense


def get_assigned_users():
    assigned_license=AssignLicense.objects.select_related("user","license")
    license_and_user_details={}
    for assigned_licnese in assigned_license:
        license_and_user_details[assigned_licnese.license.id]={
            'name':assigned_licnese.user.full_name,
            'image':assigned_licnese.user.profile_pic
        }
    return license_and_user_details
