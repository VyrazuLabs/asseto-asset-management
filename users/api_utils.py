from configurations.models import LocalizationConfiguration
from configurations.constants import CURRENCY_CHOICES

def get_profile_data(request):
    user=request.user
    obj= LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    get_user_full_name=user.dynamic_display_name(user.full_name)
    get_currency_format=None
    for id,it in CURRENCY_CHOICES:
        if obj.currency == id:
            get_currency_format=it
    print(request.user)
    arr=[]
    dict={
        "id":user.id,
        "full_name":get_user_full_name,
        "email":user.email,
        "role":"Administrator" if request.user.is_superuser else None,
        "isActive":user.is_active,
        "lastLogin":user.last_login,
        "profilePicture":user.profile_pic.url if user.profile_pic else None,
        "phone":user.phone if user.phone else None,
        "username":user.username if user.username else None,
        # "designation":"Administrator" if request.user.is_superuser else None,
        "address":user.address if user.address else None,
        "department":user.department.name if user.department else None,
        "contact_person_name":user.department.contact_person_name if user.department else None,
        "contact_person_phone":user.department.contact_person_phone if user.department else None,
        "contact_person_email":user.department.contact_person_email if user.department else None,
        "organization_name":request.user.organization.name if request.user.organization else None,
        "organization_website":request.user.organization.website if request.user.organization.website else None,
        "organization_email":request.user.organization.email if request.user.organization.email else None,
        "organization_phone":request.user.organization.phone if request.user.organization.phone else None,
        "organization_currency":get_currency_format if obj.currency else None
    }
    arr.append(dict)
    return arr