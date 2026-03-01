from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Importa las vistas de autenticación de Django
from django.contrib.auth.views import LogoutView 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # La URL raíz (/) es ahora la página de login principal.
    # Usará home.html y redirigirá a los usuarios autenticados.
    path('', auth_views.LoginView.as_view(template_name='home.html', redirect_authenticated_user=True), name='home'),
    
    # Opcional: Si quieres mantener un nombre de URL 'login' que apunte al mismo lugar,
    # puedes dejar esta línea. Pero la principal entrada será la ruta raíz.
    # Si la quitas, asegúrate de que cualquier {% url 'login' %} en tus plantillas
    # se cambie a {% url 'home' %}.
    path('accounts/login/', auth_views.LoginView.as_view(template_name='home.html', redirect_authenticated_user=True), name='login'),
    
    # La URL de logout explícita.
    path('accounts/logout/', LogoutView.as_view(http_method_names=['get', 'post', 'options']), name='logout'),
        
    # Puedes eliminar el include general de auth.urls si ya has definido login y logout explícitamente
    # y no usas otras vistas de autenticación (ej. password_reset).
    # Si lo dejas, asegúrate de que las rutas personalizadas de 'login' y 'logout'
    # estén ANTES de este include para que tengan prioridad.
    # path('accounts/', include('django.contrib.auth.urls')),
    
    # Delega las URLs de cada módulo a su propio archivo urls.py
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('principal/', include(('principal.urls', 'principal'), namespace='principal')),
    path('nutricion/', include(('nutricion.urls', 'nutricion'), namespace='nutricion')),
    path('planeacion/', include(('planeacion.urls', 'planeacion'), namespace='planeacion')),
    path('facturacion/', include(('facturacion.urls', 'facturacion'), namespace='facturacion')),
    path('costos/', include(('costos.urls', 'costos'), namespace='costos')),
    path('logistica/', include(('logistica.urls', 'logistica'), namespace='logistica')),
    path('calidad/', include(('calidad.urls', 'calidad'), namespace='calidad')),
]

# Servir archivos media en desarrollo Y producción
# ADVERTENCIA: Railway NO tiene almacenamiento persistente
# Los archivos se perderán al reiniciar el contenedor
# TODO: Migrar a Cloudinary o AWS S3 para producción
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)