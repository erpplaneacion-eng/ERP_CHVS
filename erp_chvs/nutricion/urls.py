from django.urls import path
from . import views

urlpatterns = [
    path('', views.nutricion_index, name='nutricion_index'),
    path('alimentos/', views.lista_alimentos, name='lista_alimentos'),
    path('alimentos/editar/<str:codigo>/', views.editar_alimento, name='editar_alimento'),
]