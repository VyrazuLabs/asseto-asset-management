from django.shortcuts import render, redirect
from .models import UserNotification, Notification
from authentication.models import User
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


def browser_notification(request):
    notifications = Notification.objects.filter(entity_type=0, user=request.user)
    data = [
        {
            "title": n.notification_title,
            "text": n.notification_text,
            "icon": n.icon,
            "link": n.link,
        }
        for n in notifications
    ]
    return JsonResponse(data)


PAGE_SIZE = 10
ORPHANS = 1


def _base_queryset(request):
    return UserNotification.objects.filter(user=request.user).order_by(
        "-notification__created_at"
    )


def _get_page(request, page_number=None):
    paginator = Paginator(_base_queryset(request), PAGE_SIZE, orphans=ORPHANS)
    return paginator.get_page(page_number)


def _user_names(page_object):
    """Map Notification.updated_by (a user id) -> display name for a page.

    One extra query per page render instead of a per-row lookup.
    """
    import uuid as _uuid

    values = {
        str(un.notification.updated_by)
        for un in page_object
        if un.notification and un.notification.updated_by
    }
    ids = []
    for value in values:
        try:
            _uuid.UUID(value)
            ids.append(value)
        except (ValueError, AttributeError, TypeError):
            continue  # legacy rows store a name string directly
    if not ids:
        return {}
    return {
        str(user.id): (user.full_name or user.username)
        for user in User.objects.filter(id__in=ids)
    }


@login_required
def list(request):
    page_object = _get_page(request, request.GET.get("page"))

    context = {
        "sidebar": "notifications",
        "page_object": page_object,
        "user_names": _user_names(page_object),
        "title": "Notifications",
    }
    return render(request, "notifications/details.html", context=context)


def count(request):
    if not request.user.is_authenticated:
        context = {"not_authenticated": True}
    else:
        context = {
            "notification_count": UserNotification.objects.filter(
                user=request.user, is_seen=False
            )
            .exclude(notification__instance_id=request.user.id)
            .order_by("-notification__created_at")
            .count()
        }

    return render(request, "notifications/notification_count.html", context)


@login_required
def data(request):
    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": UserNotification.objects.filter(user=request.user)
            .exclude(notification__instance_id=request.user.id)
            .order_by("-notification__created_at")[0:5]
        },
    )


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


@login_required
def mark_all_as_read(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False}, status=400
        )  # Method Not Allowed if not POST

    UserNotification.objects.filter(user=request.user, is_seen=False).exclude(
        notification__instance_id=request.user.id
    ).update(is_seen=True)

    # HTMX callers (list page + bell dropdown) get the refreshed partial so the
    # unread dots disappear; the header badge/dropdown refresh via HX-Trigger.
    if request.headers.get("HX-Request"):
        page_object = _get_page(request, page_number=request.GET.get("page"))
        response = render(
            request,
            "notifications/notifications-data.html",
            {"page_object": page_object, "user_names": _user_names(page_object)},
        )
        response["HX-Trigger"] = json.dumps(
            {"notificationCountChanged": None, "notificationListChanged": None}
        )
        return response

    return JsonResponse({"success": True})


@login_required
@require_POST
def seen(request, id):
    if request.method == "POST":
        UserNotification.objects.filter(pk=id, user=request.user).update(is_seen=True)
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "notificationCountChanged": None,
                        "notificationListChanged": None,
                    }
                )
            },
        )


@login_required
def search(request, page):
    search_text = (request.GET.get("search_text") or "").strip()
    notifications_list = _base_queryset(request)
    if search_text:
        notifications_list = notifications_list.filter(
            Q(notification__notification_title__icontains=search_text)
            | Q(notification__notification_text__icontains=search_text)
        )
    paginator = Paginator(notifications_list, PAGE_SIZE, orphans=ORPHANS)
    page_object = paginator.get_page(page)
    return render(
        request,
        "notifications/notifications-data.html",
        {"page_object": page_object, "user_names": _user_names(page_object)},
    )


# from firebase_admin.messaging import Message, Notification
# FCMDevice.objects.send_message(Message(data=dict()))
# # Note: You can also combine the data and notification kwarg
# FCMDevice.objects.send_message(
#     Message(notification=Notification(title="title", body="body", image="image_url"))
# )
# device = FCMDevice.objects.first()
# device.send_message(Message(...))


def send_data_message(token, title, body, image_url):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body, image=image_url),
        token=token,
    )
    try:
        response = messaging.send(message)
        # print('Successfully sent message:--', response)
    except Exception as e:
        print(f"Error sending message: {e}")
    # return response


# This below function is to generate the token.But since token is generated from the mobile dev.. so we directly just fetch the token from the frontend.
def firebase_initialization(request):
    return render(request, "notifications/push_notification_initial.html")
