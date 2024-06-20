
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from authentication.token import account_activation_token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_verification_mail(sender, instance, created, **kwargs):

    if created and not instance.is_active:

        url = settings.LOCALHOST_URL if settings.DEBUG else settings.DEV_URL
        subject = 'Account activation mail for Asset Management'

        message_html = render_to_string('auth/verification/account_activation_email.html', {
            'user': instance,
            'url': url,
            'uid': urlsafe_base64_encode(force_bytes(instance.pk)),
            'token': account_activation_token.make_token(instance)
        })

        send_mail(
            subject,
            'User activation email',
            'Asset Management <noreply@assetmanagement.com>',
            [instance.email],
            html_message=message_html,
            fail_silently=False,
        )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def post_save(sender, instance, created,  **kwargs):
    if instance.previous_email != instance.email and not created:

        sender.objects.filter(pk=instance.pk).update(is_active=False)
        user = sender.objects.get(pk=instance.pk)

        url = settings.LOCALHOST_URL if settings.DEBUG else settings.DEV_URL
        subject = 'Account re-activation mail for Asset Management'
        message_html = render_to_string('auth/verification/account_re_activation_email.html', {
            'user': instance,
            'url': url,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user)
        })

        send_mail(
            subject,
            'User activation email',
            'Asset Management <noreply@assetmanagement.com>',
            [user.email],
            html_message=message_html,
            fail_silently=False,
        )


@receiver(post_init, sender=settings.AUTH_USER_MODEL)
def remember_state(sender, instance, **kwargs):

    instance.previous_email = instance.email
