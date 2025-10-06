"""
Servicios de procesamiento OCR con LandingAI ADE.

Esta carpeta contiene servicios modulares para el procesamiento de PDFs con OCR:
- LandingAIAdapter: Adaptador para LandingAI ADE API
- OCROrchestrator: Orquestador principal que utiliza LandingAI ADE
- HeaderValidatorService: Validación del encabezado del PDF
- FieldValidatorService: Validación de campos diligenciados
"""

from .ocr_orchestrator import OCROrchestrator
from .landingai_adapter import LandingAIAdapter

__all__ = [
    "OCROrchestrator",
    "LandingAIAdapter"
]
