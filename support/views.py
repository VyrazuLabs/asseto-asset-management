from django.shortcuts import render
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test


def check_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(check_admin)
def support_faq(request):

    all_faq_list = Support.objects.all()
    context = {
        'sidebar': 'support',
        'submenu': 'faq',
        'all_faq_list': all_faq_list,
        'title': "FAQs"
    }

    return render(request, 'support/frequently_ask_questions.html', context=context)
