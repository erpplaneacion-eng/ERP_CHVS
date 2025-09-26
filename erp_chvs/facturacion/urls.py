from django.urls import path
from . import views

urlpatterns = [
    # Vista principal del dashboard
    path('', views.facturacion_index, name='facturacion_index'),
    
    # Vista única consolidada con 2 etapas (visualizar y guardar)
    path('procesar-listados/', views.procesar_listados_view, name='procesar_listados'),

    # Vista para gestión de listados focalización
    path('lista-listados/', views.lista_listados, name='lista_listados'),

    # APIs para gestión de listados focalización
    path('api/listados/', views.api_listados, name='api_listados'),
    path('api/listados/<str:id_listado>/', views.api_listado_detail, name='api_listado_detail'),

    # Servicios AJAX
    path('validar-archivo/', views.validar_archivo_ajax, name='validar_archivo_ajax'),
    path('estadisticas-sedes/', views.obtener_estadisticas_sedes, name='estadisticas_sedes'),
    path('estadisticas-bd/', views.obtener_estadisticas_bd, name='estadisticas_bd'),
]