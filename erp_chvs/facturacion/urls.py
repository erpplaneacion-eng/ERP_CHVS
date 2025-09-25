from django.urls import path
from . import views

urlpatterns = [
    path('', views.facturacion_index, name='facturacion_index'),
    path('generar-listados/', views.generar_listados_view, name='generar_listados'),
    path('procesar-y-guardar/', views.procesar_y_guardar_view, name='procesar_y_guardar'),
    path('validar-archivo/', views.validar_archivo_ajax, name='validar_archivo_ajax'),
    path('estadisticas-sedes/', views.obtener_estadisticas_sedes, name='estadisticas_sedes'),
    path('estadisticas-bd/', views.obtener_estadisticas_bd, name='estadisticas_bd'),
]