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
    path('generar-asistencia/<int:programa_id>/<str:sede_cod_interprise>/<str:mes>/<str:focalizacion>/', views.generar_pdf_asistencia, name='generar_pdf_asistencia'),
    path('generar-zip-masivo/<int:programa_id>/<str:mes>/<str:focalizacion>/', views.generar_zip_masivo_programa, name='generar_zip_masivo_programa'),

    # Nuevas rutas para generación prediligenciada
    path('generar-asistencia-prediligenciada/', views.generar_pdf_asistencia_prediligenciada, name='generar_pdf_asistencia_prediligenciada'),
    path('api/conteo-estudiantes-por-nivel/', views.api_conteo_estudiantes_por_nivel, name='api_conteo_estudiantes_por_nivel'),
    path('api/get-sedes-completas/', views.api_get_sedes_completas, name='api_get_sedes_completas'),

    # APIs para gestión de listados focalización
    # Nota: La edición, visualización y eliminación individual se maneja vía archivos Excel
    path('api/obtener-sedes-con-grados/', views.api_obtener_sedes_con_grados, name='api_obtener_sedes_con_grados'),
    path('api/obtener-sedes-con-grado-especifico/', views.api_obtener_sedes_con_grado_especifico, name='api_obtener_sedes_con_grado_especifico'),
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