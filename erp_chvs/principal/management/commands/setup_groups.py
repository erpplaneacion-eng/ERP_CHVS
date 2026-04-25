from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Configura los grupos y permisos iniciales para el ERP'

    def handle(self, *args, **options):
        groups_config = {
            'NUTRICION': {
                'apps': ['nutricion', 'agente', 'dashboard', 'principal'],
                'description': 'Acceso a gestion de menus y analisis nutricional'
            },
            'FACTURACION': {
                'apps': ['facturacion', 'dashboard'],
                'description': 'Acceso a carga de listados y focalizacion'
            },
            'PLANEACION': {
                'apps': ['planeacion', 'dashboard'],
                'description': 'Acceso a configuracion de programas y sedes'
            },
            'COSTOS': {
                'apps': ['costos', 'dashboard'],
                'description': 'Acceso a matriz nutricional y reportes de costos'
            },
            'LOGISTICA': {
                'apps': ['logistica', 'dashboard'],
                'description': 'Acceso a rutas de entrega y asignación de sedes'
            },
            'CALIDAD': {
                'apps': ['calidad', 'dashboard'],
                'description': 'Acceso a certificados de calidad del personal'
            },
            'LIDER_CONTABLE': {
                'apps': ['contabilidad', 'dashboard'],
                'description': 'Acceso para líderes que crean y envían registros contables'
            },
            'COMPRAS_CONTABLE': {
                'apps': ['contabilidad', 'dashboard'],
                'description': 'Acceso para el área de Compras: confirma recepción, verifica checklist, aprueba o devuelve'
            },
            'CONTABILIDAD': {
                'apps': ['contabilidad', 'dashboard'],
                'description': 'Acceso para el área de Contabilidad: revisión final, aprobación y cierre'
            },
            'GERENCIA': {
                'apps': ['contabilidad', 'dashboard'],
                'description': 'Acceso de solo lectura con dashboard gerencial y trazabilidad completa'
            },
            'ADMINISTRACION': {
                'apps': ['nutricion', 'facturacion', 'planeacion', 'principal', 'dashboard', 'costos', 'logistica', 'calidad', 'contabilidad', 'agente'],
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
