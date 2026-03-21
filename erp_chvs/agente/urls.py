from django.urls import path
from . import views

app_name = 'agente'

urlpatterns = [
    path('', views.index, name='index'),
    path('borrador/<int:generacion_id>/', views.borrador_view, name='borrador'),

    path('api/programas/', views.api_programas, name='api_programas'),
    path('api/menus/', views.api_menus_por_programa_modalidad, name='api_menus'),
    path('api/generar/', views.api_generar, name='api_generar'),
    path('api/generar/<int:generacion_id>/estado/', views.api_estado_generacion, name='api_estado_generacion'),
    path('api/aprobar/<int:generacion_id>/', views.api_aprobar, name='api_aprobar'),
    path('api/descartar/<int:generacion_id>/', views.api_descartar, name='api_descartar'),
    path('api/corregir-ingrediente/', views.api_corregir_ingrediente, name='api_corregir_ingrediente'),
    path('api/eliminar-ingrediente/', views.api_eliminar_ingrediente, name='api_eliminar_ingrediente'),
    path('api/buscar-alimento/', views.api_buscar_alimento, name='api_buscar_alimento'),

    # Generación en lote / pool
    path('generar-lote/', views.generar_lote_view, name='generar_lote'),
    path('api/lote/iniciar/', views.api_iniciar_lote, name='api_iniciar_lote'),
    path('api/lote/<int:lote_id>/estado/', views.api_estado_lote, name='api_estado_lote'),
    path('api/lote/crear-menus/', views.api_crear_menus_lote, name='api_crear_menus_lote'),
    path('api/lote/borradores/', views.api_borradores_pendientes, name='api_borradores_pendientes'),
]
