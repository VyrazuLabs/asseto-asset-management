"""AssetManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from authentication.forms import UserPasswordChangeForm, UserPasswordResetForm, UserPasswordResetRequestForm
from authentication.decorators import unauthenticated_user


urlpatterns = [
    path('secret/', admin.site.urls),
    path('', include('authentication.urls', namespace='authentication')),
    path('vendors/', include('vendors.urls', namespace='vendors')),
    path('products/', include('products.urls', namespace='products')),
    path('admin/', include('dashboard.urls', namespace='dashboard')),
    path('upload/', include('upload.urls', namespace='upload')),
    path('recycle-bin/', include('recycle_bin.urls', namespace='recycle_bin')),
    path('assets/', include('assets.urls', namespace='assets')),
    path('roles/', include('roles.urls', namespace='roles')),
    path('support/', include('support.urls', namespace='support')),
    path('users/', include('users.urls', namespace='users')),
    path('notifications/', include('notifications.urls', namespace='notifications')),

    # django smart select urls
    path('chaining/', include('smart_selects.urls')),

    # Password Change Views
    path('change-password/', auth_views.PasswordChangeView.as_view(form_class=UserPasswordChangeForm,
    	template_name='auth/password/password-change.html'), name='password_change'),

    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password/password-change-done.html'), name='password_change_done'),

    # Password Reset Views
    path('reset-password/', unauthenticated_user(auth_views.PasswordResetView.as_view(form_class=UserPasswordResetRequestForm,
        template_name='auth/password/password-reset.html', html_email_template_name='auth/verification/password_reset_html_email.html')), name="password_reset"),

    path('reset-password/done/', unauthenticated_user(auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password/password-reset-done.html')), name="password_reset_done"),

    path('reset/<uidb64>/<token>', unauthenticated_user(auth_views.PasswordResetConfirmView.as_view(form_class=UserPasswordResetForm,
        template_name='auth/password/password-reset-confirm.html')), name="password_reset_confirm"),

    path('reset/done/', unauthenticated_user(auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password/password-reset-complete.html')), name="password_reset_complete"),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error Handlers
handler403 = 'error_handlers.views.handle_403'
handler404 = 'error_handlers.views.handle_404'
handler500 = 'error_handlers.views.handle_500'