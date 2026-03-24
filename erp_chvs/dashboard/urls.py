from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/nia/chat/', views.api_nia_chat, name='nia_chat'),
    path('api/nia/reset/', views.api_nia_reset, name='nia_reset'),
]
