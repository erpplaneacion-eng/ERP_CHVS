"""
Servicio para extracción de texto mediante OCR.
Utiliza Tesseract OCR para extraer texto de imágenes.
"""

import os
from typing import Dict, Any
from PIL import Image

from .base import BaseOCRService
from ..exceptions import OCRProcessingException


# Importar Tesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class TextExtractorService(BaseOCRService):
    """
    Servicio para extraer texto de imágenes usando Tesseract OCR.
    """

    def __init__(self, language: str = 'spa', **kwargs):
        """
        Inicializa el servicio de extracción de texto.

        Args:
            language: Idioma para Tesseract ('spa' = español, 'eng' = inglés)
        """
        super().__init__(**kwargs)
        self.language = language

        if not TESSERACT_AVAILABLE:
            raise OCRProcessingException(
                "Tesseract no está disponible. Instale pytesseract para usar OCR."
            )

        self._configure_tesseract()

    def _configure_tesseract(self):
        """Configura Tesseract para Windows si es necesario."""
        if self.platform == 'Windows':
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.log_debug(f"✅ Tesseract configurado: {path}")
                    return

            self.log_warning("⚠️ Tesseract no encontrado en rutas estándar de Windows")

    def extract_text(self, image: Image.Image, page_num: int = 1) -> Dict[str, Any]:
        """
        Extrae texto de una imagen usando Tesseract OCR.

        Args:
            image: Imagen PIL a procesar
            page_num: Número de página (para logging)

        Returns:
            Dict con texto extraído, confianza y metadatos
        """
        try:
            self.log_debug(f"📝 Extrayendo texto de página {page_num}...")

            # Configuración de Tesseract
            config = self.config.tesseract_config

            # Intentar primero con idioma configurado
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang=self.language,
                    config=config
                )
                self.log_debug(f"  ✅ Extracción con idioma '{self.language}' exitosa")

            except Exception as lang_error:
                self.log_warning(f"  ⚠️ Error con idioma '{self.language}', usando inglés: {lang_error}")
                text = pytesseract.image_to_string(
                    image,
                    config=config
                )

            # Obtener datos de confianza
            confidence_data = pytesseract.image_to_data(
                image,
                config=config,
                output_type=pytesseract.Output.DICT
            )

            # Calcular confianza promedio
            avg_confidence = self._calculate_confidence(confidence_data)

            # Log de resultados
            char_count = len(text)
            self.log_info(f"✅ Página {page_num}: {char_count} caracteres extraídos (confianza: {avg_confidence:.1f}%)")

            if char_count > 0:
                preview = text[:100].replace('\n', ' ')
                self.log_debug(f"  Vista previa: {preview}...")

            return {
                'pagina': page_num,
                'texto_extraido': text,
                'confianza': avg_confidence,
                'caracteres': char_count,
                'error': None
            }

        except Exception as e:
            self.log_error(f"❌ Error extrayendo texto de página {page_num}: {e}", exc_info=True)
            return {
                'pagina': page_num,
                'texto_extraido': '',
                'confianza': 0.0,
                'caracteres': 0,
                'error': str(e)
            }

    def _calculate_confidence(self, confidence_data: Dict) -> float:
        """
        Calcula la confianza promedio del OCR.

        Args:
            confidence_data: Datos de confianza de Tesseract

        Returns:
            float: Confianza promedio (0-100)
        """
        if not confidence_data or 'conf' not in confidence_data:
            return 0.0

        # Filtrar valores válidos (mayores a 0)
        confidences = [conf for conf in confidence_data['conf'] if conf > 0]

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)

    def extract_from_file(self, image_path: str, page_num: int = 1) -> Dict[str, Any]:
        """
        Extrae texto directamente desde un archivo de imagen.

        Args:
            image_path: Ruta a la imagen
            page_num: Número de página

        Returns:
            Dict con texto extraído y metadatos
        """
        try:
            image = Image.open(image_path)
            return self.extract_text(image, page_num)
        except Exception as e:
            self.log_error(f"❌ Error cargando imagen {image_path}: {e}")
            return {
                'pagina': page_num,
                'texto_extraido': '',
                'confianza': 0.0,
                'caracteres': 0,
                'error': f'Error cargando imagen: {str(e)}'
            }
