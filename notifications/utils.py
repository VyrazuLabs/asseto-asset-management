from .models import UserNotification,Notification
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from authentication.models import User

# Function to send email to a user regarding operation in asset
# Since email is optional now we have to validate whether the user has email or not
def send_email(user_email,notifications_title,notification_text):
    subject = notifications_title
    message = notification_text
    from_email = "sghosh@gmail.com"
    recipient_list = [user_email]
    print("MAIL            SEND --------->")
    return send_mail(subject=subject, message=message, recipient_list=recipient_list,from_email=from_email)

def notifications_call(user,entity_type,notification_title,notification_text):
    # We receive the entity_type that is stored in the django sessions.
    get_user=user
    get_user_notification_types={
        'email_notification':get_user.email_notification if get_user.email_notification else False,
        'slack_notification':get_user.slack_notification if get_user.slack_notification else False,
        'browser_notification':get_user.browser_notification if get_user.browser_notification else False,
        'inapp_notification':get_user.inapp_notification if get_user.inapp_notification else False
    }
    if get_user_notification_types['slack_notification'] is True:
        UserNotification.objects.create(
            entity_type=2,user=get_user, notification_title=notification_title, notification_text=notification_text
        )
    if get_user_notification_types['email_notification'] is True:
        UserNotification.objects.create(
            entity_type=1,user=get_user, notification_title=notification_title, notification_text=notification_text
        )
    if get_user_notification_types['browser_notification'] is True:
        UserNotification.objects.create(
            entity_type=0,user=get_user, notification_title=notification_title, notification_text=notification_text
        )
    # In app to be implemented later.
    return JsonResponse({"success": True})
