from django.urls import path
from . import views

urlpatterns = [
    path('', views.principal_index, name='principal_index'),
    path('departamentos/', views.lista_departamentos, name='lista_departamentos'),
    path('municipios/', views.lista_municipios, name='lista_municipios'),
    path('tipos-documento/', views.lista_tipos_documento, name='lista_tipos_documento'),
    path('tipos-genero/', views.lista_tipos_genero, name='lista_tipos_genero'),
    path('modalidades-consumo/', views.lista_modalidades_consumo, name='lista_modalidades_consumo'),
    path('instituciones/', views.lista_instituciones, name='lista_instituciones'),
    path('sedes/', views.lista_sedes, name='lista_sedes'),
    path('niveles-grado/', views.lista_niveles_grado, name='lista_niveles_grado'),

    # APIs para departamentos y municipios
    path('api/departamentos/', views.api_departamentos, name='api_departamentos'),
    path('api/municipios/', views.api_municipios, name='api_municipios'),
    path('api/departamentos/<str:codigo>/', views.api_departamento_detail, name='api_departamento_detail'),
    path('api/municipios/<int:id>/', views.api_municipio_detail, name='api_municipio_detail'),
    
    # APIs para tipos de documento
    path('api/tipos-documento/', views.api_tipos_documento, name='api_tipos_documento'),
    path('api/tipos-documento/<str:id_documento>/', views.api_tipo_documento_detail, name='api_tipo_documento_detail'),
    
    # APIs para tipos de género
    path('api/tipos-genero/', views.api_tipos_genero, name='api_tipos_genero'),
    path('api/tipos-genero/<str:id_genero>/', views.api_tipo_genero_detail, name='api_tipo_genero_detail'),
    
    # APIs para modalidades de consumo
    path('api/modalidades-consumo/', views.api_modalidades_consumo, name='api_modalidades_consumo'),
    path('api/modalidades-consumo/<str:id_modalidades>/', views.api_modalidad_consumo_detail, name='api_modalidad_consumo_detail'),

    # APIs para instituciones educativas
    path('api/instituciones/', views.api_instituciones, name='api_instituciones'),
    path('api/instituciones/<str:codigo_ie>/', views.api_institucion_detail, name='api_institucion_detail'),

    # APIs para sedes educativas
    path('api/sedes/', views.api_sedes, name='api_sedes'),
    path('api/sedes/<str:cod_interprise>/', views.api_sede_detail, name='api_sede_detail'),

    # APIs para niveles grado escolar
    path('api/niveles-grado/', views.api_niveles_grado, name='api_niveles_grado'),
    path('api/niveles-grado/<str:id_grado_escolar>/', views.api_nivel_grado_detail, name='api_nivel_grado_detail'),

    # Modalidades por Programa
    path('programa-modalidades/', views.programa_modalidades, name='programa_modalidades'),
    path('api/programa-modalidades/guardar/', views.api_guardar_programa_modalidades, name='api_guardar_programa_modalidades'),
]