from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Configura los grupos y permisos iniciales para el ERP'

    def handle(self, *args, **options):
        groups_config = {
            'NUTRICION': {
                'apps': ['nutricion'],
                'description': 'Acceso a gestion de menus y analisis nutricional'
            },
            'FACTURACION': {
                'apps': ['facturacion'],
                'description': 'Acceso a carga de listados y focalizacion'
            },
            'PLANEACION': {
                'apps': ['planeacion'],
                'description': 'Acceso a configuracion de programas y sedes'
            },
            'COSTOS': {
                'apps': ['costos'],
                'description': 'Acceso a matriz nutricional y reportes de costos'
            },
            'LOGISTICA': {
                'apps': ['logistica'],
                'description': 'Acceso a rutas de entrega y asignación de sedes'
            },
            'CALIDAD': {
                'apps': ['calidad'],
                'description': 'Acceso a certificados de calidad del personal'
            },
            'ADMINISTRACION': {
                'apps': ['nutricion', 'facturacion', 'planeacion', 'principal', 'dashboard', 'costos', 'logistica', 'calidad'],
                'description': 'Acceso total al sistema'
            }
        }

        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo creado: {group_name}'))
            else:
                self.stdout.write(f'Grupo existente: {group_name}')

            # Limpiar permisos actuales para reasignar (opcional)
            # group.permissions.clear()

            # Asignar permisos por app
            for app_label in config['apps']:
                permissions = Permission.objects.filter(content_type__app_label=app_label)
                for perm in permissions:
                    group.permissions.add(perm)

            self.stdout.write(f'Permisos asignados a {group_name} para las apps: {", ".join(config["apps"])}')

        self.stdout.write(self.style.SUCCESS('Configuracion de grupos completada con exito.'))
