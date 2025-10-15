from django.urls import path
from . import views

app_name = 'nutricion'

urlpatterns = [
    # Vista principal
    path('', views.nutricion_index, name='nutricion_index'),

    # Alimentos ICBF
    path('alimentos/', views.lista_alimentos, name='lista_alimentos'),
    path('alimentos/editar/<str:codigo>/', views.editar_alimento, name='editar_alimento'),

    # Menús
    path('menus/', views.lista_menus, name='lista_menus'),
    path('api/menus/', views.api_menus, name='api_menus'),
    path('api/menus/<int:id_menu>/', views.api_menu_detail, name='api_menu_detail'),
    path('api/programas-por-municipio/', views.api_programas_por_municipio, name='api_programas_por_municipio'),
    path('api/modalidades-por-programa/', views.api_modalidades_por_programa, name='api_modalidades_por_programa'),
    path('api/generar-menus-automaticos/', views.api_generar_menus_automaticos, name='api_generar_menus_automaticos'),
    path('api/crear-menu-especial/', views.api_crear_menu_especial, name='api_crear_menu_especial'),
    path('exportar-excel/<int:menu_id>/', views.download_menu_excel, name='exportar_menu_excel'),

    # Preparaciones
    path('preparaciones/', views.lista_preparaciones, name='lista_preparaciones'),
    path('preparaciones/<int:id_preparacion>/', views.detalle_preparacion, name='detalle_preparacion'),
    path('api/preparaciones/', views.api_preparaciones, name='api_preparaciones'),
    path('api/preparaciones/<int:id_preparacion>/', views.api_preparacion_detail, name='api_preparacion_detail'),
    path('api/preparaciones/copiar/', views.api_copiar_preparacion, name='api_copiar_preparacion'),
    path('api/preparaciones-por-modalidad/<str:modalidad_id>/', views.api_preparaciones_por_modalidad, name='api_preparaciones_por_modalidad'),

    # Ingredientes
    path('ingredientes/', views.lista_ingredientes, name='lista_ingredientes'),
    path('api/ingredientes/', views.api_ingredientes, name='api_ingredientes'),
    path('api/ingredientes/<str:id_ingrediente>/', views.api_ingrediente_detail, name='api_ingrediente_detail'),

    # Componentes de Alimentos
    path('api/componentes-alimentos/', views.api_componentes_alimentos, name='api_componentes_alimentos'),

    # Preparación - Ingredientes
    path('api/preparaciones/<int:id_preparacion>/ingredientes/', views.api_preparacion_ingredientes, name='api_preparacion_ingredientes'),
    path('api/preparaciones/<int:id_preparacion>/ingredientes/<str:id_ingrediente>/', views.api_preparacion_ingrediente_delete, name='api_preparacion_ingrediente_delete'),

    # Análisis Nutricional
    path('api/menus/<int:id_menu>/analisis-nutricional/', views.api_analisis_nutricional_menu, name='api_analisis_nutricional_menu'),
    path('api/guardar-analisis-nutricional/', views.guardar_analisis_nutricional, name='guardar_analisis_nutricional'),

    # Exportación Excel
    path('exportar-excel/<int:menu_id>/', views.download_menu_excel, name='exportar_menu_excel'),
    path('exportar-excel/<int:menu_id>/nivel/<str:nivel_escolar_id>/', views.download_menu_excel_with_nivel, name='exportar_menu_excel_con_nivel'),
    path('exportar-excel-servicio/<int:menu_id>/', views.download_menu_excel_service, name='exportar_menu_excel_servicio'),
    path('exportar-modalidad-excel/<int:programa_id>/<str:modalidad_id>/', views.download_modalidad_excel, name='exportar_modalidad_excel'),
]