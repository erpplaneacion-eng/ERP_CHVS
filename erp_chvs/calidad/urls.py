from django.urls import path
from . import views

app_name = 'calidad'

urlpatterns = [
    # Páginas
    path('', views.calidad_principal, name='principal'),
    path('certificados/', views.lista_certificados, name='lista_certificados'),

    # APIs internas (ERP)
    path('api/buscar-empleado/', views.api_buscar_empleado, name='api_buscar_empleado'),
    path('api/certificados/', views.api_certificados_list, name='api_certificados_list'),
    path('certificados/generar/', views.generar_certificado, name='generar_certificado'),
    path('certificados/<int:pk>/descargar/', views.descargar_certificado, name='descargar_certificado'),

    # API WhatsApp (sin sesión, autenticada por API key)
    path('api/whatsapp/generar/', views.api_whatsapp_generar_certificado, name='api_whatsapp_generar'),
]
