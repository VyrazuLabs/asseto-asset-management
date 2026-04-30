from django.urls import path
from . import views
from .api_views import GatePassList, GatePassSearch
from . import api_views
app_name = 'gate-pass'

urlpatterns = [
    #template_urls
    path('list', views.listed, name='list'),
    path('add',views.add,name='add'),
    path('detail/<uuid:id>', views.detail, name='detail'),
    path('print/<uuid:id>', views.print_doc, name='print_doc'),
    path('search', views.search, name='search'),
    path('authorise/<uuid:id>/<int:status>/', views.authorisation, name='authorise'),
    path('impact/<str:tag>/', views.check_impact, name='impact'),
    # API urls
    # path('api/create', views.create_gate_pass, name='create_gate_pass'),
    # path('api/update/<str:gate_pass_id>', views.update_gate_pass, name='update_gate_pass'),
    # path('api/details/<str:gate_pass_id>', views.get_gate_pass, name='get_gate_pass'),
]

# API urls
gate_pass_api_url_patterns = [
    path('api/gate-pass/list', api_views.GatePassList.as_view(), name='list_gate_passes'),
    path('api/gate-pass/search', api_views.GatePassSearch.as_view(), name='search_gate_passes'),
    path('api/gate-pass/create', api_views.GatePassCreate.as_view(), name='create_gate_pass'),
    path('api/gate-pass/approve/<str:gate_pass_id>', api_views.GatePassApprove.as_view(), name='approve_gate_pass'),
]