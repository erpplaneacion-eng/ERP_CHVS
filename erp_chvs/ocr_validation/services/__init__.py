"""
Servicios de procesamiento OCR.

Esta carpeta contiene servicios modulares para el procesamiento de PDFs con OCR:
- PDFConverterService: Conversión de PDF a imágenes
- ImageProcessorService: Preprocesamiento de imágenes para OCR
- TextExtractorService: Extracción de texto mediante Tesseract
- HeaderValidatorService: Validación del encabezado del PDF
- FieldValidatorService: Validación de campos diligenciados
- OCROrchestrator: Orquestador principal que coordina todos los servicios
"""

from .ocr_orchestrator import OCROrchestrator

__all__ = ['OCROrchestrator']
