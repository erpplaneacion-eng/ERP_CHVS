from django.urls import path
from . import views

app_name = 'iagenerativa'

urlpatterns = [
    path('', views.index, name='index'),
    path('generar-menu/', views.generar_menu, name='generar_menu'),
]
