# planeacion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.planeacion_index, name='planeacion_index'),
    path('programas/', views.lista_programas, name='lista_programas'),
    path('programas/editar/<int:pk>/', views.editar_programa, name='editar_programa'),
]
