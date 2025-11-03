from django.urls import path
from . import views

urlpatterns = [
    # Vista principal del dashboard
    path('', views.facturacion_index, name='facturacion_index'),
    
    # Vista única consolidada con 2 etapas (visualizar y guardar)
    path('procesar-listados/', views.procesar_listados_view, name='procesar_listados'),

    # Vista para gestión de listados focalización
    path('lista-listados/', views.lista_listados, name='lista_listados'),

    # Nueva vista para la interfaz de generación de reportes de asistencia
    path('reportes-asistencia/', views.reportes_asistencia_view, name='reportes_asistencia'),
    path('generar-asistencia/<str:sede_cod_interprise>/<str:mes>/<str:focalizacion>/', views.generar_pdf_asistencia, name='generar_pdf_asistencia'),
    path('generar-zip-masivo/<str:etc>/<str:mes>/<str:focalizacion>/', views.generar_zip_masivo_etc, name='generar_zip_masivo_etc'),

    # APIs para gestión de listados focalización
    # Nota: La edición, visualización y eliminación individual se maneja vía archivos Excel
    path('api/transferir-grados/', views.api_transferir_grados, name='api_transferir_grados'),

    # Servicios AJAX
    path('validar-archivo/', views.validar_archivo_ajax, name='validar_archivo_ajax'),
    path('estadisticas-sedes/', views.obtener_estadisticas_sedes, name='estadisticas_sedes'),
    path('api/focalizaciones-existentes/', views.api_focalizaciones_existentes, name='api_focalizaciones_existentes'),
    path('estadisticas-bd/', views.obtener_estadisticas_bd, name='estadisticas_bd'),
    path('api/get-municipio-for-programa/', views.get_municipio_for_programa, name='get_municipio_for_programa'),
    path('api/get-focalizaciones-for-programa/', views.get_focalizaciones_for_programa, name='get_focalizaciones_for_programa'),
    path('api/get-sedes-for-programa-focalizacion/', views.get_sedes_for_programa_focalizacion, name='get_sedes_for_programa_focalizacion'),
    path('api/reemplazar-focalizacion-sedes/', views.reemplazar_focalizacion_sedes, name='reemplazar_focalizacion_sedes'),
]