"""
URLs para la aplicación de validación OCR.
"""

from django.urls import path
from . import views

app_name = 'ocr_validation'

urlpatterns = [
    # Vista principal
    path('', views.ocr_validation_index, name='ocr_index'),

    # Procesamiento de PDFs
    path('procesar/', views.procesar_pdf_ocr, name='procesar_pdf'),

    # Resultados de validación
    path('resultados/<int:validacion_id>/', views.resultados_validacion, name='resultados'),

    # Listado de validaciones
    path('listado/', views.listado_validaciones, name='listado'),

    # Reintentar procesamiento
    path('reintentar/<int:validacion_id>/', views.reintentar_validacion, name='reintentar'),

    # Marcar error como resuelto
    path('error/<int:error_id>/resolver/', views.marcar_error_resuelto, name='marcar_resuelto'),

    # Estadísticas
    path('estadisticas/', views.estadisticas_ocr, name='estadisticas'),

    # Configuración
    path('configuracion/', views.configuracion_ocr, name='configuracion'),

    # Descarga de reportes
    path('reporte/<int:validacion_id>/descargar/', views.descargar_reporte_errores, name='descargar_reporte'),
]