import logging
import psycopg2
import psycopg2.extras
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_empleados_conn():
    """Abre una conexión directa a la BD externa de empleados."""
    url = settings.EMPLEADOS_DB_URL
    if not url:
        raise RuntimeError(
            "La variable de entorno EMPLEADOS_DB_URL no está configurada. "
            "Agrégala en Railway → Variables antes de hacer el deploy."
        )
    return psycopg2.connect(url)


def buscar_empleado_por_cedula(cedula: str) -> dict | None:
    """
    Busca un empleado en las tres tablas de la BD externa:
    tabla_manipuladoras, tabla_planta, tabla_aprendices.

    Retorna un dict con los datos del empleado o None si no se encuentra.
    Levanta excepción si hay error de conexión.
    """
    cedula = cedula.strip()
    if not cedula:
        return None

    query = """
        SELECT cedula, nombre_completo, cargo, eps,
               programa_pertenece AS programa_empresa,
               'manipuladora' AS tipo_empleado
        FROM tabla_manipuladoras WHERE cedula = %s
        UNION ALL
        SELECT cedula, nombre_completo, cargo, eps,
               empresa AS programa_empresa,
               'planta' AS tipo_empleado
        FROM tabla_planta WHERE cedula = %s
        UNION ALL
        SELECT cedula, nombre_completo, cargo, eps,
               programa_pertenece AS programa_empresa,
               'aprendiz' AS tipo_empleado
        FROM tabla_aprendices WHERE cedula = %s
        LIMIT 1
    """

    conn = _get_empleados_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (cedula, cedula, cedula))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
