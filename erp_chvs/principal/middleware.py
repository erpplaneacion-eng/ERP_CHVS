import time
import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve

logger = logging.getLogger('timing')


class ResponseTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0 = time.monotonic()
        response = self.get_response(request)
        ms = (time.monotonic() - t0) * 1000

        # Solo loguear vistas dinámicas (no estáticos)
        path = request.path
        if not path.startswith('/static/') and not path.startswith('/favicon'):
            nivel = logging.WARNING if ms > 1000 else logging.INFO
            logger.log(nivel, f"[{ms:7.1f}ms] {request.method} {path} → {response.status_code}")

        return response


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
        except Exception:
            return self.get_response(request)

        # Definir que aplicaciones estan permitidas por grupo
        group_permissions = {
            'NUTRICION': ['nutricion', 'dashboard', 'principal', 'agente'],
            'FACTURACION': ['facturacion', 'dashboard'],
            'PLANEACION': ['planeacion', 'dashboard'],
            'COSTOS': ['costos', 'dashboard'],
            'LOGISTICA': ['logistica', 'dashboard'],
            'CALIDAD': ['calidad', 'dashboard'],
            'LIDER_CONTABLE': ['contabilidad', 'dashboard'],
            'COMPRAS_CONTABLE': ['contabilidad', 'dashboard'],
            'CONTABILIDAD': ['contabilidad', 'dashboard'],
            'GERENCIA': ['contabilidad', 'dashboard'],
            'ADMINISTRACION': ['nutricion', 'facturacion', 'planeacion', 'principal', 'costos', 'logistica', 'calidad', 'dashboard', 'agente', 'contabilidad'],
        }

        # Apps que siempre son accesibles para logueados
        public_apps = ['admin', 'login', 'logout', '']

        if current_app and current_app not in public_apps:
            user_groups = [
                str(name).strip().upper()
                for name in request.user.groups.values_list('name', flat=True)
            ]

            # Union de permisos de todos los grupos del usuario
            allowed_apps = set()
            for group in user_groups:
                allowed_apps.update(group_permissions.get(group, []))

            has_access = current_app in allowed_apps

            if not has_access:
                if user_groups:
                    messages.error(request, f"No tienes permiso para acceder al modulo de {current_app.capitalize()}.")
                    return redirect('dashboard:dashboard')

                messages.error(request, "Tu usuario no tiene grupos asignados. Contacta al administrador.")
                return redirect('home')

        return self.get_response(request)
