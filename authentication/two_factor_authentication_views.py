from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from authentication.models import User, UserTotp

from .utils import TotpMixin, TotpService, verify_totp

_totp_mixin = TotpMixin()


@login_required
def toggle_2fa(request):
    user = request.user
    if request.method == "POST":
        user.two_factor_auth = not user.two_factor_auth
        user.save()

    if user.two_factor_auth:
        user_totp = TotpService.get_or_create_otp(user)
        return JsonResponse(TotpService.build_totp_payload(request, user, user_totp))

    user_totp = UserTotp.objects.filter(user=request.user).first()
    return JsonResponse(
        {
            "success": True,
            "two_factor_auth": user.two_factor_auth,
            "is_validate": user_totp.is_validate if user_totp else False,
            "qr_code": None,
        }
    )


def verify_and_enable(request):
    if request.method != "POST":
        return redirect("authentication:profile")

    PROFILE = "authentication:profile"

    try:
        totp = UserTotp.objects.get(user=request.user)
    except UserTotp.DoesNotExist:
        return _totp_mixin.totp_response(
            request,
            success=False,
            message="2FA not set up. Please enable 2FA first.",
            redirect_name=PROFILE,
        )

    if totp.is_validate:
        return _totp_mixin.totp_response(
            request,
            success=False,
            message="2FA is already verified and enabled.",
            redirect_name=PROFILE,
            level="info",
        )

    otp = request.POST.get("otp", "")
    if len(otp) != 6:
        return _totp_mixin.totp_response(
            request,
            success=False,
            message="Please enter a valid 6-digit OTP.",
            redirect_name=PROFILE,
        )

    if not TotpService.verify_and_mark(totp, otp):
        return _totp_mixin.totp_response(
            request,
            success=False,
            message="Invalid OTP!",
            redirect_name=PROFILE,
        )

    return _totp_mixin.totp_response(
        request,
        success=True,
        message="OTP verified successfully. 2FA is now active.",
        redirect_name=reverse(PROFILE) + "?verified=true",
        extra={"is_validate": True},
        level="success",
    )


def verify_otp(request):
    user = request.user
    if request.method == "POST":
        otp = request.POST.get("otp")
        user_email = request.session.get("user_email")
        get_user = get_object_or_404(User,email=user_email)

        get_totp = get_object_or_404(UserTotp,user=get_user)

        verify_otp = verify_totp(get_totp.secret, otp)

        if verify_otp:
            login(request, get_user)
            messages.success(request, f"Welcome, {user.full_name}")
            return redirect("authentication:index")
        else:
            return redirect("authentication:verify_otp")

    elif request.method == "GET":
        return render(request, "auth/verify-otp.html")


@login_required
@require_POST
def regenerate_qr(request):
    totp = TotpService.reset_opt(request.user)
    return JsonResponse(TotpService.build_totp_payload(request, request.user, totp))
