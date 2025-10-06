"""
URLs para la aplicación de validación OCR con LandingAI ADE.
"""

from django.urls import path
from . import views

app_name = 'ocr_validation'

urlpatterns = [
    # Vista principal
    path('', views.ocr_validation_index, name='ocr_index'),

    # Procesamiento de PDFs con LandingAI (extracción a DataFrames)
    path('procesar/', views.procesar_pdf_ocr, name='procesar_pdf'),

    # Visualización y gestión de DataFrames
    path('dataframe/<int:validacion_id>/', views.ver_dataframe, name='ver_dataframe'),
    path('dataframe/<int:validacion_id>/exportar/', views.exportar_dataframe, name='exportar_dataframe'),
    path('api/dataframe/<int:validacion_id>/data/', views.api_dataframe_data, name='api_dataframe_data'),
    path('dashboard/', views.dashboard_dataframes, name='dashboard_dataframes'),

    # Listado de validaciones
    path('listado/', views.listado_validaciones, name='listado'),

    # Estadísticas
    path('estadisticas/', views.estadisticas_ocr, name='estadisticas'),

    # Configuración
    path('configuracion/', views.configuracion_ocr, name='configuracion'),
]