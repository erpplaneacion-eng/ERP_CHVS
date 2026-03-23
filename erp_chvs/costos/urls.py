from django.urls import path
from . import views

app_name = 'costos'

urlpatterns = [
    path('', views.costos_index, name='costos_index'),
    path('matriz-nutricional/', views.matriz_nutricional, name='matriz_nutricional'),
    path('matriz-nutricional/exportar-excel/', views.exportar_matriz_excel, name='exportar_matriz_excel'),
    path('api/programas/', views.api_programas, name='api_programas'),
    path('api/modalidades/', views.api_modalidades, name='api_modalidades'),
]
