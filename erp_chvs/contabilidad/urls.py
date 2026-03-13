from django.urls import path
from . import views

app_name = 'contabilidad'

urlpatterns = [
    # ---- Páginas ----
    path('', views.contabilidad_principal, name='principal'),
    path('mis-registros/', views.mis_registros, name='mis_registros'),
    path('registro/<int:pk>/', views.detalle_registro, name='detalle_registro'),
    path('bandeja-compras/', views.bandeja_compras, name='bandeja_compras'),
    path('revision-compras/<int:pk>/', views.revision_compras, name='revision_compras'),
    path('bandeja-contabilidad/', views.bandeja_contabilidad, name='bandeja_contabilidad'),
    path('revision-contabilidad/<int:pk>/', views.revision_contabilidad, name='revision_contabilidad'),
    path('dashboard-gerencia/', views.dashboard_gerencia, name='dashboard_gerencia'),

    # ---- APIs JSON ----
    path('api/registros/', views.api_listar_registros, name='api_listar_registros'),
    path('api/registros/crear/', views.api_crear_registro, name='api_crear_registro'),
    path('api/registros/<int:pk>/', views.api_detalle_registro, name='api_detalle_registro'),
    path('api/registros/<int:pk>/facturas/', views.api_agregar_factura, name='api_agregar_factura'),
    path('api/facturas/<int:pk>/eliminar/', views.api_eliminar_factura, name='api_eliminar_factura'),
    path('api/registros/<int:pk>/enviar/', views.api_enviar, name='api_enviar'),
    path('api/registros/<int:pk>/confirmar-recepcion/', views.api_confirmar_recepcion, name='api_confirmar_recepcion'),
    path('api/registros/<int:pk>/devolver/', views.api_devolver_compras, name='api_devolver_compras'),
    path('api/registros/<int:pk>/aprobar-compras/', views.api_aprobar_compras, name='api_aprobar_compras'),
    path('api/facturas/<int:pk>/aprobar/', views.api_aprobar_factura, name='api_aprobar_factura'),
    path('api/facturas/<int:pk>/devolver/', views.api_devolver_factura, name='api_devolver_factura'),
    path('api/registros/<int:pk>/finalizar-revision/', views.api_finalizar_revision, name='api_finalizar_revision'),
    path('api/registros/<int:pk>/checklist/', views.api_checklist, name='api_checklist'),
    path('api/registros/<int:pk>/guardar-checklist/', views.api_guardar_checklist, name='api_guardar_checklist'),
    path('api/registros/<int:pk>/observar/', views.api_observar_contabilidad, name='api_observar_contabilidad'),
    path('api/registros/<int:pk>/aprobar-contabilidad/', views.api_aprobar_contabilidad, name='api_aprobar_contabilidad'),
    path('api/registros/<int:pk>/responder-observacion/', views.api_responder_observacion, name='api_responder_observacion'),
    path('api/registros/<int:pk>/historial/', views.api_historial, name='api_historial'),
    path('api/dashboard/', views.api_dashboard, name='api_dashboard'),
]
