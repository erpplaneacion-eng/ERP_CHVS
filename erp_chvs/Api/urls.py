from django.urls import path
from . import views

urlpatterns = [
    path('', views.siesa_index, name='siesa_index'),
    path('centros-operacion/', views.lista_centros_operacion, name='lista_centros_operacion'),
    path('instalaciones/', views.lista_instalaciones, name='lista_instalaciones'),
    path('tipos-documento/', views.lista_tipos_documento, name='lista_tipos_documento'),
    path('unidades-negocio/', views.lista_unidades_negocio, name='lista_unidades_negocio'),
    path('centros-costo/', views.lista_centros_costo, name='lista_centros_costo'),
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('conceptos/', views.lista_conceptos, name='lista_conceptos'),
    path('motivos/', views.lista_motivos, name='lista_motivos'),
    path('ubicaciones/', views.lista_ubicaciones, name='lista_ubicaciones'),
    path('solicitantes/', views.lista_solicitantes, name='lista_solicitantes'),
    path('items/', views.lista_items, name='lista_items'),
]
