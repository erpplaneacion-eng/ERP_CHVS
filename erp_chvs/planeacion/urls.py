# planeacion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.planeacion_index, name='planeacion_index'),
    path('sedes/', views.lista_comedores, name='lista_comedores'),
    path('programas/', views.lista_programas, name='lista_programas'),
    path('programas/editar/<int:pk>/', views.editar_programa, name='editar_programa'),
    path('sedes/editar/<str:pk>/', views.editar_comedor, name='editar_comedor'),
]
