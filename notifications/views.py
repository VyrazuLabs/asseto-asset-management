from django.shortcuts import render, redirect
from .models import UserNotification,Notification
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Notification
from .models import FirebaseToken
from firebase_admin import messaging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

def browser_notification( request):
    notifications = Notification.objects.filter(entity_type=0,user=request.user)
    data = [
        {
            "title": n.notification_title,
            "text": n.notification_text,
            "icon": n.icon,
            "link": n.link
        }
        for n in notifications
    ]
    return JsonResponse(data)


PAGE_SIZE = 10
ORPHANS = 1


@login_required
def list(request):
    notifications_list = UserNotification.objects.filter(
        user=request.user).order_by('-notification__created_at')
    paginator = Paginator(notifications_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'notifications',
        'page_object': page_object,
        'title': 'Notifications'
    }
    # UserNotification.objects.filter(user=request.user, is_seen=False).exclude(
    #     notification__instance_id=request.user.id).update(is_seen=True)
    return render(request, 'notifications/details.html', context=context)


def count(request):
    if not request.user.is_authenticated:
        context = {'not_authenticated': True}
    else:
        context = {'notification_count': UserNotification.objects.filter(user=request.user, is_seen=False).exclude(
            notification__instance_id=request.user.id).order_by('-notification__created_at').count()}

    return render(request, 'notifications/notification_count.html', context)


@login_required
def data(request):
    return render(request, 'notifications/notification_list.html', {
        'notifications': UserNotification.objects.filter(user=request.user).exclude(notification__instance_id=request.user.id).order_by('-notification__created_at')[0:5]
    })


# @login_required
# @ require_POST
# def clear(request):
#     if request.method == 'POST':
#         UserNotification.objects.filter(user=request.user, is_seen=False).exclude(
#             notification__instance_id=request.user.id).update(is_seen=True)
#         return HttpResponse(
#             status=204,
#             headers={
#                 'HX-Trigger': json.dumps({
#                     "notificationCountChanged": None,
#                     "notificationListChanged": None,
#                 })
#             }
#         )



def mark_all_as_read(request):
    if request.method == 'POST':
        UserNotification.objects.filter(user=request.user, is_seen=False).exclude(
            notification__instance_id=request.user.id).update(is_seen=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)  # Method Not Allowed if not POST


@login_required
@ require_POST
def seen(request, id):
    if request.method == 'POST':
        UserNotification.objects.filter(pk=id).update(is_seen=True)
        return HttpResponse(
            status=204,
            headers={
                'HX-Trigger': json.dumps({
                    "notificationCountChanged": None,
                    "notificationListChanged": None,
                })
            }
        )


@login_required
def search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'notifications/notifications-data.html', {
            'page_object': UserNotification.objects.filter(Q(user=request.user) & (Q(
                notification__notification_title__icontains=search_text) | Q(notification__notification_text__icontains=search_text)
            )).order_by('-notification__created_at')[:10]
        })
    notification_list = UserNotification.objects.filter(
        user=request.user).order_by('-notification__created_at')
    paginator = Paginator(notification_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'notifications/notifications-data.html', {'page_object': page_object})
# from firebase_admin.messaging import Message, Notification
# FCMDevice.objects.send_message(Message(data=dict()))
# # Note: You can also combine the data and notification kwarg
# FCMDevice.objects.send_message(
#     Message(notification=Notification(title="title", body="body", image="image_url"))
# )
# device = FCMDevice.objects.first()
# device.send_message(Message(...))

def send_data_message(token,title,body,image_url):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
            image=image_url
        ),
        token=token
    )
    try:
        response = messaging.send(message)
        print('Successfully sent message:--', response)
    except Exception as e:
        print(f"Error sending message: {e}")
    # return response

#This below function is to generate the token.But since token is generated from the mobile dev.. so we directly just fetch the token from the frontend.
def firebase_initialization(request):
    return render(request,'notifications/push_notification_initial.html')