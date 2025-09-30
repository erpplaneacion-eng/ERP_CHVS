"""
Servicio base para todos los servicios de OCR.
Proporciona configuración común y utilidades compartidas.
"""

import logging
import platform
from typing import Optional
from ..models import OCRConfiguration


class BaseOCRService:
    """
    Clase base para todos los servicios de OCR.
    Proporciona configuración compartida y logging.
    """

    def __init__(self, config: Optional[OCRConfiguration] = None):
        """
        Inicializa el servicio base.

        Args:
            config: Configuración OCR. Si no se proporciona, se carga la configuración por defecto.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or self._load_default_config()
        self.platform = platform.system()

    def _load_default_config(self) -> OCRConfiguration:
        """
        Carga la configuración OCR por defecto desde la base de datos.

        Returns:
            OCRConfiguration: Configuración OCR
        """
        config, created = OCRConfiguration.objects.get_or_create(
            pk=1,
            defaults={
                'tesseract_config': '--oem 3 --psm 6',
                'confianza_minima': 60.0,
            }
        )

        if created:
            self.logger.info("✅ Configuración OCR creada con valores por defecto")
        else:
            self.logger.debug(f"📝 Configuración OCR cargada: {config.tesseract_config}")

        return config

    def log_info(self, message: str):
        """Log de información."""
        self.logger.info(message)

    def log_debug(self, message: str):
        """Log de debug."""
        self.logger.debug(message)

    def log_warning(self, message: str):
        """Log de advertencia."""
        self.logger.warning(message)

    def log_error(self, message: str, exc_info: bool = False):
        """Log de error."""
        self.logger.error(message, exc_info=exc_info)
