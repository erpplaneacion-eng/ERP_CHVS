from django.urls import path
from . import views

urlpatterns = [
    path('', views.facturacion_index, name='facturacion_index'),
    path('generar-listados/', views.generar_listados_view, name='generar_listados'),
]