from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve

class RoleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Si es superusuario, tiene acceso total
        if request.user.is_superuser:
            return self.get_response(request)

        # Obtener el nombre de la app actual
        try:
            current_app = resolve(request.path_info).app_name
        except:
            return self.get_response(request)

        # Definir qué aplicaciones están permitidas por grupo
        group_permissions = {
            'NUTRICION': ['nutricion', 'dashboard', 'principal'],
            'FACTURACION': ['facturacion', 'dashboard'],
            'PLANEACION': ['planeacion', 'dashboard'],
            'COSTOS': ['costos', 'dashboard'],
            'LOGISTICA': ['logistica', 'dashboard'],
            'ADMINISTRACION': ['nutricion', 'facturacion', 'planeacion', 'principal', 'costos', 'logistica', 'dashboard']
        }

        # Apps que siempre son accesibles para logueados (como el perfil o home)
        public_apps = ['admin', 'login', 'logout', ''] 

        if current_app and current_app not in public_apps:
            # Normalizar grupos evita errores por mayúsculas/minúsculas o espacios.
            user_groups = [
                str(name).strip().upper()
                for name in request.user.groups.values_list('name', flat=True)
            ]

            # Unir permisos de todos los grupos del usuario.
            allowed_apps = set()
            for group in user_groups:
                allowed_apps.update(group_permissions.get(group, []))

            has_access = current_app in allowed_apps

            if not has_access and user_groups:
                messages.error(request, f"No tienes permiso para acceder al módulo de {current_app.capitalize()}.")
                return redirect('dashboard:dashboard')

        return self.get_response(request)
