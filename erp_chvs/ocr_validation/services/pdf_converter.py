"""
Servicio para conversión de PDF a imágenes.
Responsable de convertir archivos PDF a imágenes PNG para procesamiento OCR.
"""

import os
import tempfile
from typing import List
from PIL import Image

from .base import BaseOCRService
from ..exceptions import OCRProcessingException


# Importar pdf2image
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class PDFConverterService(BaseOCRService):
    """
    Servicio para convertir archivos PDF a imágenes.
    """

    def __init__(self, dpi: int = 400, **kwargs):
        """
        Inicializa el servicio de conversión PDF.

        Args:
            dpi: Resolución DPI para la conversión (mayor = mejor calidad OCR)
        """
        super().__init__(**kwargs)
        self.dpi = dpi

        if not PDF2IMAGE_AVAILABLE:
            raise OCRProcessingException(
                "pdf2image no está disponible. Instale pdf2image y poppler para convertir PDFs."
            )

    def convert_to_images(self, pdf_path: str) -> List[str]:
        """
        Convierte un PDF a lista de imágenes PNG.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            List[str]: Lista de rutas a las imágenes temporales creadas

        Raises:
            OCRProcessingException: Si falla la conversión
        """
        self.log_info(f"🔄 Convirtiendo PDF a imágenes (DPI: {self.dpi})")

        try:
            # Buscar poppler en Windows
            poppler_path = self._get_poppler_path() if self.platform == 'Windows' else None

            # Convertir PDF a imágenes
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                poppler_path=poppler_path,
                fmt='png'
            )

            self.log_info(f"✅ PDF convertido a {len(images)} imágenes")

            # Guardar imágenes temporales
            image_paths = []
            for i, image in enumerate(images):
                tmp_file = tempfile.NamedTemporaryFile(
                    suffix=f'_page_{i+1}.png',
                    delete=False
                )
                tmp_file.close()

                image.save(tmp_file.name, 'PNG')
                image_paths.append(tmp_file.name)
                self.log_debug(f"  Página {i+1} → {tmp_file.name}")

            return image_paths

        except Exception as e:
            self.log_error(f"❌ Error convirtiendo PDF: {e}", exc_info=True)
            raise OCRProcessingException(f"Error convirtiendo PDF a imágenes: {str(e)}")

    def _get_poppler_path(self) -> str:
        """
        Busca la ruta de Poppler en Windows.

        Returns:
            str: Ruta a Poppler o None
        """
        possible_paths = [
            r'C:\Program Files\poppler\Library\bin',
            r'C:\Program Files (x86)\poppler\Library\bin',
            r'C:\poppler\Library\bin',
        ]

        for path in possible_paths:
            if os.path.exists(path):
                self.log_debug(f"✅ Poppler encontrado: {path}")
                return path

        self.log_warning("⚠️ Poppler no encontrado en rutas estándar")
        return None

    def cleanup_images(self, image_paths: List[str]):
        """
        Limpia archivos de imágenes temporales.

        Args:
            image_paths: Lista de rutas a eliminar
        """
        for image_path in image_paths:
            try:
                if os.path.exists(image_path):
                    os.unlink(image_path)
                    self.log_debug(f"🗑️ Eliminada imagen temporal: {image_path}")
            except Exception as e:
                self.log_warning(f"⚠️ No se pudo eliminar {image_path}: {e}")
