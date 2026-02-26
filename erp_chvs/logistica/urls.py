from django.urls import path
from . import views

app_name = 'logistica'

urlpatterns = [
    # Páginas
    path('', views.logistica_principal, name='principal'),
    path('tipos-ruta/', views.lista_tipos_ruta, name='lista_tipos_ruta'),
    path('rutas/', views.lista_rutas, name='lista_rutas'),
    path('ruta-sedes/', views.lista_ruta_sedes, name='lista_ruta_sedes'),

    # API: Tipos de Ruta
    path('api/tipos-ruta/', views.api_tipos_ruta, name='api_tipos_ruta'),
    path('api/tipos-ruta/<int:pk>/', views.api_tipo_ruta_detail, name='api_tipo_ruta_detail'),

    # API: Rutas
    path('api/rutas/', views.api_rutas, name='api_rutas'),
    path('api/rutas/<int:pk>/', views.api_ruta_detail, name='api_ruta_detail'),

    # API: Ruta Sedes
    path('api/ruta-sedes/', views.api_ruta_sedes, name='api_ruta_sedes'),
    path('api/ruta-sedes/<int:pk>/', views.api_ruta_sede_detail, name='api_ruta_sede_detail'),

    # API auxiliares (para poblar selects)
    path('api/programas/', views.api_programas_list, name='api_programas_list'),
    path('api/sedes/', views.api_sedes_list, name='api_sedes_list'),
    path('api/rutas-activas/', views.api_rutas_list, name='api_rutas_list'),
]
