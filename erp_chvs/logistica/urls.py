from django.urls import path
from . import views

app_name = 'logistica'

urlpatterns = [
    path('', views.logistica_principal, name='principal'),
]
