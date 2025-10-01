"""
Servicio principal de OCR - Wrapper de compatibilidad.
Utiliza la nueva arquitectura de servicios modulares.

Este archivo mantiene compatibilidad con código legacy que importaba
las clases y funciones del antiguo ocr_service.py
"""

from typing import Dict, Any
from django.core.files.uploadedfile import UploadedFile

from .services import OCROrchestrator
from .exceptions import OCRProcessingException


def procesar_pdf_ocr_view(archivo_pdf: UploadedFile, usuario=None) -> Dict[str, Any]:
    """
    Función principal para procesar un PDF con OCR.
    Esta función es llamada desde las vistas de Django.

    Args:
        archivo_pdf: Archivo PDF subido por el usuario
        usuario: Usuario que realizó la carga

    Returns:
        Dict con resultados del procesamiento:
            - success: bool
            - validacion_id: int (si success=True)
            - error: str (si success=False)
            - tiempo_procesamiento: float
            - total_errores: int
            - sede_educativa: str
    """
    try:
        orchestrator = OCROrchestrator()
        resultado = orchestrator.process_pdf(archivo_pdf, usuario)
        return resultado
    except Exception as e:
        return {
            'success': False,
            'error': f"Error procesando PDF: {str(e)}"
        }


class OCRProcessor:
    """
    Clase de compatibilidad para mantener compatibilidad con código existente.
    Delega todo el trabajo al nuevo OCROrchestrator.
    """

    def __init__(self):
        """Inicializa el procesador usando el nuevo orquestador."""
        self.orchestrator = OCROrchestrator()

    def procesar_pdf_ocr(self, archivo_pdf: UploadedFile, usuario=None) -> Dict[str, Any]:
        """
        Procesa un PDF con OCR (método legacy).

        Args:
            archivo_pdf: Archivo PDF a procesar
            usuario: Usuario que procesó el archivo

        Returns:
            Dict con resultados del procesamiento
        """
        return self.orchestrator.process_pdf(archivo_pdf, usuario)


# Función de fábrica para crear instancias del procesador
def create_ocr_processor() -> OCRProcessor:
    """
    Crea una nueva instancia del procesador OCR.

    Returns:
        OCRProcessor: Instancia del procesador
    """
    return OCRProcessor()
