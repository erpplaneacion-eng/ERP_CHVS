"""
Excepciones personalizadas para el módulo de facturación.
"""

class FacturacionException(Exception):
    """Excepción base para el módulo de facturación."""
    pass

class ArchivoInvalidoException(FacturacionException):
    """Excepción lanzada cuando el archivo no es válido."""
    def __init__(self, mensaje="Archivo inválido"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ColumnasFaltantesException(FacturacionException):
    """Excepción lanzada cuando faltan columnas requeridas."""
    def __init__(self, columnas_faltantes):
        self.columnas_faltantes = columnas_faltantes
        self.mensaje = f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}"
        super().__init__(self.mensaje)

class DatosInvalidosException(FacturacionException):
    """Excepción lanzada cuando los datos no son válidos."""
    def __init__(self, mensaje="Datos inválidos"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class SedesInvalidasException(FacturacionException):
    """Excepción lanzada cuando hay sedes inválidas."""
    def __init__(self, sedes_invalidas):
        self.sedes_invalidas = sedes_invalidas
        self.mensaje = f"Sedes inválidas encontradas: {', '.join(sedes_invalidas)}"
        super().__init__(self.mensaje)

class ProcesamientoException(FacturacionException):
    """Excepción lanzada durante el procesamiento de datos."""
    def __init__(self, mensaje="Error durante el procesamiento"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)

class ValidacionException(FacturacionException):
    """Excepción lanzada durante la validación de datos."""
    def __init__(self, mensaje="Error durante la validación"):
        self.mensaje = mensaje
        super().__init__(self.mensaje)
