"""Management command: sync_siesa

Sincroniza los catálogos locales de SIESA (full sync sin delta).
Requiere las variables SIESA_API_BASE_URL, SIESA_API_USER, SIESA_API_PASSWORD en el entorno.

Uso:
    python manage.py sync_siesa
    python manage.py sync_siesa --catalogo CENTROS-OPERACIONES
    python manage.py sync_siesa --dry-run
"""

from django.core.management.base import BaseCommand, CommandError

from Api.services.siesa_client import ENDPOINTS
from Api.services.sync_service import sincronizar_todo


class Command(BaseCommand):
    help = 'Sincroniza catálogos locales de SIESA (full sync). Sin args = todos los catálogos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--catalogo',
            type=str,
            default=None,
            help=f'Sincronizar solo este catálogo. Opciones: {", ".join(ENDPOINTS)}',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Llama los endpoints y muestra cuántos registros habría, sin escribir en BD.',
        )

    def handle(self, *args, **options):
        catalogo = options.get('catalogo')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] No se escribirá en la base de datos.\n'))

        try:
            resultados = sincronizar_todo(endpoint_filtro=catalogo, dry_run=dry_run)
        except (RuntimeError, ValueError) as exc:
            raise CommandError(str(exc))

        total_insertados = total_actualizados = total_errores = 0

        for log in resultados:
            duracion = ''
            if log.fin:
                secs = (log.fin - log.inicio).total_seconds()
                duracion = f' ({secs:.1f}s)'

            if log.estado == 'error' and log.registros_insertados == 0 and log.registros_actualizados == 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'  {log.endpoint}: ERROR — {log.detalle_error}{duracion}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  {log.endpoint}: +{log.registros_insertados} / ~{log.registros_actualizados} / err={log.errores}{duracion}'
                    )
                )

            total_insertados += log.registros_insertados
            total_actualizados += log.registros_actualizados
            total_errores += log.errores

        self.stdout.write('')
        self.stdout.write(f'Total insertados : {total_insertados}')
        self.stdout.write(f'Total actualizados: {total_actualizados}')
        if total_errores:
            self.stdout.write(self.style.ERROR(f'Total errores    : {total_errores}'))
        else:
            self.stdout.write(self.style.SUCCESS('Sin errores.'))
