from .models import FirebaseToken
from firebase_admin import messaging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema,OpenApiParameter
from django.utils.decorators import method_decorator

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@extend_schema(parameters=[OpenApiParameter(name='Firebase Token', type=str, description="Enter Firebase Token To Enable In-App Notifications")])
def save_firebase_token(request,token):
    user = request.user
    # token = request.data.get('token')
    # If in-app notification is enabled, block FCM token storage
    # if not user.inapp_notification:
    #     return Response(
    #         {
    #             "success": False,
    #             "error": "You need to enable in-app notification to use push notifications."
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )
    if not token:
        return Response(
            {
                "success": False,
                "error": "Token not provided."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    FirebaseToken.objects.update_or_create(
        user=user,
        defaults={'token': token}
    )
    return Response(
        {"success": True},
        status=status.HTTP_200_OK
    )

