"""
Configuración de logging para el módulo de facturación.
"""

import logging
from .config import ProcesamientoConfig

# Configurar logger específico para facturación
logger = logging.getLogger('facturacion')

class FacturacionLogger:
    """Logger especializado para operaciones de facturación."""
    
    @staticmethod
    def log_procesamiento_inicio(archivo_nombre: str, tipo_procesamiento: str, focalizacion: str = None):
        """Log del inicio de procesamiento de archivo."""
        logger.info(f"Inicio procesamiento: {archivo_nombre} - Tipo: {tipo_procesamiento} - Focalización: {focalizacion}")

    @staticmethod
    def log_procesamiento_exito(archivo_nombre: str, total_registros: int, registros_validos: int):
        """Log de procesamiento exitoso."""
        logger.info(f"Procesamiento exitoso: {archivo_nombre} - Total: {total_registros} - Válidos: {registros_validos}")

    @staticmethod
    def log_procesamiento_error(archivo_nombre: str, error: str):
        """Log de error en procesamiento."""
        logger.error(f"Error en procesamiento: {archivo_nombre} - Error: {error}")
    
    @staticmethod
    def log_validacion_sedes(sedes_validas: int, sedes_invalidas: int, coincidencias_parciales: int = 0, coincidencias_genericas: int = 0):
        """Log de validación de sedes."""
        logger.info(f"🏫 Validación sedes - Válidas: {sedes_validas}, Inválidas: {sedes_invalidas}, Parciales: {coincidencias_parciales}, Genéricas: {coincidencias_genericas}")
    
    @staticmethod
    def log_validacion_archivo(archivo_nombre: str, es_valido: bool, tipo_mime: str = None):
        """Log de validación de archivo."""
        if es_valido:
            logger.info(f"📄 Archivo válido: {archivo_nombre} - Tipo: {tipo_mime}")
        else:
            logger.warning(f"⚠️ Archivo inválido: {archivo_nombre} - Tipo: {tipo_mime}")
    
    @staticmethod
    def log_transformacion_datos(transformaciones_aplicadas: list):
        """Log de transformaciones de datos aplicadas."""
        if transformaciones_aplicadas:
            logger.info(f"🔄 Transformaciones aplicadas: {', '.join(transformaciones_aplicadas)}")
    
    @staticmethod
    def log_estadisticas_generadas(estadisticas: dict):
        """Log de estadísticas generadas."""
        if estadisticas:
            logger.info(f"📊 Estadísticas generadas: {estadisticas}")
    
    @staticmethod
    def log_coincidencia_difusa(sede_excel: str, sede_bd: str, porcentaje: float, tipo: str = "completo"):
        """Log de coincidencia difusa encontrada."""
        logger.debug(f"🔍 Coincidencia {tipo}: '{sede_excel}' -> '{sede_bd}' ({porcentaje}%)")
    
    @staticmethod
    def log_filtrado_datos(filtro_aplicado: str, registros_antes: int, registros_despues: int):
        """Log de filtrado de datos."""
        logger.info(f"🔽 Filtrado '{filtro_aplicado}': {registros_antes} -> {registros_despues} registros")
    
    @staticmethod
    def log_mapeo_datos(tipo_mapeo: str, mapeos_aplicados: int):
        """Log de mapeo de datos."""
        logger.info(f"🗺️ Mapeo {tipo_mapeo}: {mapeos_aplicados} registros procesados")

def configurar_logging():
    """Configura el logging para el módulo de facturación."""
    # Crear handler para archivo de log
    file_handler = logging.FileHandler('facturacion.log')
    file_handler.setLevel(logging.INFO)

    # Crear formatter
    formatter = logging.Formatter(ProcesamientoConfig.LOG_FORMAT)
    file_handler.setFormatter(formatter)

    # Configurar logger
    logger.setLevel(getattr(logging, ProcesamientoConfig.LOG_LEVEL))
    logger.addHandler(file_handler)

    # Evitar duplicación de logs
    logger.propagate = False
