from django.shortcuts import render, redirect
from .models import UserNotification
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q


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
