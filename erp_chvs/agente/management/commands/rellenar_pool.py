"""
Management command: rellenar_pool

Rellena el pool de borradores IA hasta alcanzar el mínimo por modalidad.

Uso:
    python manage.py rellenar_pool
    python manage.py rellenar_pool --min 10
    python manage.py rellenar_pool --modalidad "COMPLEMENTO PM"
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Rellena el pool de borradores pre-generados de la IA hasta el mínimo por modalidad.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min',
            type=int,
            default=20,
            dest='min_por_modalidad',
            help='Mínimo de borradores por modalidad en el pool (default: 20)',
        )
        parser.add_argument(
            '--modalidad',
            type=str,
            default=None,
            help='Nombre (parcial) de modalidad específica a rellenar. Si se omite, rellena todas.',
        )

    def handle(self, *args, **options):
        from agente.services.pool_service import rellenar_pool, MODALIDADES_POOL
        from principal.models import ModalidadesDeConsumo

        min_m = options['min_por_modalidad']
        filtro_modalidad = options.get('modalidad')

        ids_modalidad = None  # None → usa MODALIDADES_POOL por defecto

        if filtro_modalidad:
            qs = ModalidadesDeConsumo.objects.filter(modalidad__icontains=filtro_modalidad)
            if not qs.exists():
                self.stderr.write(self.style.ERROR(
                    f"No se encontró ninguna modalidad con '{filtro_modalidad}'."
                ))
                return
            ids_modalidad = list(qs.values_list('id_modalidades', flat=True))

        # Mostrar qué modalidades se van a procesar
        ids_a_mostrar = ids_modalidad or MODALIDADES_POOL
        nombres = ModalidadesDeConsumo.objects.filter(
            id_modalidades__in=ids_a_mostrar
        ).values_list('modalidad', flat=True)
        self.stdout.write(f"Modalidades a procesar: {', '.join(nombres)}")
        self.stdout.write(f"Mínimo por modalidad: {min_m}")
        self.stdout.write("Iniciando relleno de pool...\n")

        resultado = rellenar_pool(min_por_modalidad=min_m, ids_modalidad=ids_modalidad)

        self.stdout.write(self.style.SUCCESS(
            f"✓ Completado — "
            f"Modalidades: {resultado['modalidades']} | "
            f"Generados: {resultado['generados']} | "
            f"Errores: {resultado['errores']}"
        ))
