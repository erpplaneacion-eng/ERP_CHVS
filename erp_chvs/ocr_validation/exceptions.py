"""
Excepciones personalizadas para el módulo de validación OCR.
"""

class OCRValidationException(Exception):
    """Excepción base para el módulo de validación OCR."""
    pass

class OCRProcessingException(OCRValidationException):
    """Excepción lanzada durante el procesamiento OCR."""
    def __init__(self, mensaje="Error durante el procesamiento OCR"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ValidationException(OCRValidationException):
    """Excepción lanzada durante la validación de datos."""
    def __init__(self, mensaje="Error durante la validación"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class TesseractNotAvailableException(OCRProcessingException):
    """Excepción lanzada cuando Tesseract no está disponible."""
    def __init__(self, mensaje="Tesseract OCR no está instalado o disponible"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class PDFProcessingException(OCRProcessingException):
    """Excepción lanzada durante el procesamiento de PDFs."""
    def __init__(self, mensaje="Error procesando archivo PDF"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ImageProcessingException(OCRProcessingException):
    """Excepción lanzada durante el procesamiento de imágenes."""
    def __init__(self, mensaje="Error procesando imagen"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class FieldValidationException(ValidationException):
    """Excepción lanzada durante la validación de campos específicos."""
    def __init__(self, campo, mensaje="Error validando campo"):
        self.campo = campo
        self.mensaje = f"Error validando campo '{campo}': {mensaje}"
        super().__init__(self.mensaje)

class ConfigurationException(OCRValidationException):
    """Excepción lanzada por problemas de configuración."""
    def __init__(self, mensaje="Error de configuración"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)