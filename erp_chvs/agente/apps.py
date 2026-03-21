import logging
import os
import sys
import threading
import time

from django.apps import AppConfig

logger = logging.getLogger(__name__)

# Comandos de management que NO deben arrancar el scheduler
_CMDS_SIN_SCHEDULER = {
    'makemigrations', 'migrate', 'collectstatic', 'shell', 'test',
    'createsuperuser', 'inspectdb', 'dbshell', 'dumpdata', 'loaddata',
    'ingestar_normativo', 'rellenar_pool',
}

_INTERVALO_HORAS = 24  # revisar pool cada 24 horas


def _scheduler_pool():
    """
    Hilo daemon que revisa el pool cada _INTERVALO_HORAS horas.
    Si alguna modalidad tiene menos de 20 borradores disponibles, los genera.
    """
    # Esperar 60s al arrancar (dejar que Django termine de inicializarse)
    time.sleep(60)

    while True:
        try:
            logger.info("[pool_scheduler] Ejecutando relleno automático del pool...")
            from agente.services.pool_service import rellenar_pool
            resultado = rellenar_pool(min_por_modalidad=20)
            logger.info(
                f"[pool_scheduler] Relleno completado — "
                f"generados: {resultado['generados']}, errores: {resultado['errores']}"
            )
        except Exception as e:
            logger.error(f"[pool_scheduler] Error en relleno automático: {e}")

        # Dormir hasta la próxima revisión
        time.sleep(_INTERVALO_HORAS * 3600)


class AgenteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agente'

    def ready(self):
        # No arrancar en comandos de management (migrate, collectstatic, etc.)
        argv_set = set(sys.argv)
        if argv_set & _CMDS_SIN_SCHEDULER:
            return

        # En runserver Django arranca dos procesos; solo arrancar en el proceso principal
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        hilo = threading.Thread(target=_scheduler_pool, daemon=True, name='pool-scheduler')
        hilo.start()
        logger.info("[pool_scheduler] Scheduler de pool iniciado (revisión cada 24h)")
