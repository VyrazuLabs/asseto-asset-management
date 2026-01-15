from configurations.models import LocalizationConfiguration
from configurations.constants import CURRENCY_CHOICES,NAME_FORMATS
from configurations.utils import dynamic_display_name
from authentication.models import User
from roles.models import Role
from datetime import datetime
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

def forgot_password(request,email):
    
    now = int(datetime.now().timestamp())
    # email = request.data['email'].lower()
    response = {}

    if User.objects.filter(email=email).exists():
        token = secrets.token_urlsafe(32)
        user = User.objects.filter(email=email).first()
        user.password_reset_token = token
        # user.updated_by = 1
        # user.updated_at = now
        user.save(update_fields=['password_reset_token'])
        # endpoint=f'/assets/list'
        # host=request.build_absolute_uri(endpoint)
        get_host = lambda request: request.build_absolute_uri('/')
        host=get_host(request)
        reset_link = host+f"api/user/change-password?token={token}"

        # Send email
        html_content = render_to_string(
            "users/password-reset.html",
            {
                "user_name": user.full_name,
                "reset_link": reset_link,
                "company_name": "Your Company",
                "year": timezone.now().year,
            }
        )

        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject="Reset Your Password",
            body=text_content,
            from_email="no-reply@asetto.com",
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        response = {
            'success' : True,
            'message' : 'Password reset email sent. Please check your inbox for instructions.'
        }
    else:
        response = {
            'success' : False,
            'message' : 'There is no user with such email.If you are having trouble with your email address please contact the administrator.'
        }
    return response

def get_username(request,id):
    # name=request.user
    get_name=User.objects.filter(id=id).first()
    get_name=dynamic_display_name(request=request,fullname=get_name.full_name)
    get_profile_img=request.user.profile_pic.url if request.user.profile_pic else None
    arr=[]
    host=request.get_host()
    dict={
        "full_name":get_name,
        "profile_pic":f"{host}{get_profile_img}"
    }
    arr.append(dict)
    return arr

def get_profile_data(request):
    current_host=request.get_host()
    user=request.user
    obj= LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    get_user_full_name=user.dynamic_display_name(user.full_name)
    get_currency_format=None
    for id,it in CURRENCY_CHOICES:
        if obj and obj.currency == id:
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
        "profilePicture":f"http://{current_host}"+user.profile_pic.url if user.profile_pic else None,
        "phone":user.phone if user.phone else None,
        "username":user.username if user.username else None,
        "address":user.address if user.address else None,
        "department":user.department.name if user.department else None,
        "contact_person_name":user.department.contact_person_name if user.department else None,
        "contact_person_phone":user.department.contact_person_phone if user.department else None,
        "contact_person_email":user.department.contact_person_email if user.department else None,
        "organization_name":request.user.organization.name if request.user.organization else None,
        "organization_website":request.user.organization.website if request.user.organization.website else None,
        "organization_email":request.user.organization.email if request.user.organization.email else None,
        "organization_phone":request.user.organization.phone if request.user.organization.phone else None,
        "organization_currency":get_currency_format if obj and obj.currency else None
    }
    arr.append(dict)
    return arr

def get_roles(request):
    try:
        roles_list=Role.objects.filter(organization=request.user.organization).all()
        data=[]
        for role in roles_list:
            role_dict={
                "id":str(role.id),
                "name":role.related_name

            }
            data.append(role_dict)
        return data
    except Exception as e:
        raise e