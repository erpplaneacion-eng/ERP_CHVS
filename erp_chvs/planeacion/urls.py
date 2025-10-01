# planeacion/urls.py
from django.urls import path
from . import views

app_name = 'planeacion'

urlpatterns = [
    path('', views.planeacion_index, name='planeacion_index'),
    path('programas/', views.lista_programas, name='lista_programas'),
    path('programas/editar/<int:pk>/', views.editar_programa, name='editar_programa'),

    # Ciclos de menús
    path('ciclos-menus/', views.ciclos_menus_view, name='ciclos_menus'),
    path('api/ciclos-menus/inicializar/', views.inicializar_ciclos_menus, name='inicializar_ciclos_menus'),
    path('api/ciclos-menus/actualizar/', views.actualizar_racion, name='actualizar_racion'),
    path('api/ciclos-menus/obtener/', views.obtener_datos_ciclos, name='obtener_datos_ciclos'),
]
