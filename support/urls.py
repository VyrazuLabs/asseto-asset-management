from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('faqs', views.support_faq, name='support_faq'),
]
