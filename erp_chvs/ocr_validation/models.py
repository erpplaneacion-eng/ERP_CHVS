"""
Modelos para la aplicación de validación OCR de PDFs diligenciados.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class PDFValidation(models.Model):
    """
    Modelo para almacenar resultados de validación OCR de PDFs.
    """

    # Información del archivo
    archivo_nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre del Archivo"
    )

    archivo_path = models.CharField(
        max_length=500,
        verbose_name="Ruta del Archivo"
    )

    # Información de la sede educativa
    sede_educativa = models.CharField(
        max_length=200,
        verbose_name="Sede Educativa"
    )

    mes_atencion = models.CharField(
        max_length=20,
        verbose_name="Mes de Atención"
    )

    ano = models.IntegerField(
        verbose_name="Año"
    )

    tipo_complemento = models.CharField(
        max_length=20,
        verbose_name="Tipo de Complemento"
    )

    # Usuario que creó la validación
    usuario_creador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario Creador"
    )

    # Estado del procesamiento
    ESTADO_PROCESAMIENTO = [
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_PROCESAMIENTO,
        default='procesando',
        verbose_name="Estado"
    )

    # Resultados de validación
    total_errores = models.IntegerField(
        default=0,
        verbose_name="Total de Errores"
    )

    errores_criticos = models.IntegerField(
        default=0,
        verbose_name="Errores Críticos"
    )

    errores_advertencia = models.IntegerField(
        default=0,
        verbose_name="Advertencias"
    )

    # Información del procesamiento
    fecha_procesamiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Procesamiento"
    )

    fecha_completado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Completado"
    )

    tiempo_procesamiento = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Tiempo de Procesamiento (segundos)"
    )

    # Método OCR utilizado
    METODO_OCR = [('landingai', 'LandingAI ADE')]

    metodo_ocr = models.CharField(
        max_length=20,
        choices=METODO_OCR,
        default="landingai",
        verbose_name="Método OCR"
    )

    # Datos estructurados extraídos (JSON)
    datos_estructurados = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Datos Estructurados JSON",
        help_text="Datos tabulares extraídos del PDF en formato JSON"
    )

    # Metadatos de extracción
    metadatos_extraccion = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Metadatos de Extracción",
        help_text="Información sobre el proceso de extracción"
    )

    # Texto completo extraído
    texto_completo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Texto Completo Extraído"
    )

    # Información adicional
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    class Meta:
        db_table = 'ocr_pdf_validation'
        verbose_name = "Validación PDF OCR"
        verbose_name_plural = "Validaciones PDF OCR"
        ordering = ['-fecha_procesamiento']
        indexes = [
            models.Index(fields=['sede_educativa', 'mes_atencion', 'ano']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_procesamiento']),
        ]

    def __str__(self):
        return f"Validación {self.sede_educativa} - {self.mes_atencion}/{self.ano}"


class ValidationError(models.Model):
    """
    Modelo para almacenar errores específicos encontrados en la validación.
    """

    # Relación con la validación padre
    validacion = models.ForeignKey(
        PDFValidation,
        on_delete=models.CASCADE,
        related_name='errores',
        verbose_name="Validación"
    )

    # Información del error
    tipo_error = models.CharField(
        max_length=50,
        verbose_name="Tipo de Error"
    )

    descripcion = models.CharField(
        max_length=255,
        verbose_name="Descripción"
    )

    # Ubicación del error
    pagina = models.IntegerField(
        verbose_name="Página"
    )

    fila_estudiante = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Fila del Estudiante"
    )

    columna_campo = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Campo/Columna"
    )

    # Información específica del error
    valor_esperado = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Valor Esperado"
    )

    valor_encontrado = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Valor Encontrado"
    )

    # Coordenadas aproximadas del error (para debugging)
    coordenada_x = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Coordenada X"
    )

    coordenada_y = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Coordenada Y"
    )

    # Severidad del error
    SEVERIDAD_ERROR = [
        ('critico', 'Crítico'),
        ('advertencia', 'Advertencia'),
        ('info', 'Información'),
    ]

    severidad = models.CharField(
        max_length=20,
        choices=SEVERIDAD_ERROR,
        default='advertencia',
        verbose_name="Severidad"
    )

    # Estado de resolución
    resuelto = models.BooleanField(
        default=False,
        verbose_name="Resuelto"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    class Meta:
        db_table = 'ocr_validation_errors'
        verbose_name = "Error de Validación"
        verbose_name_plural = "Errores de Validación"
        ordering = ['pagina', 'fila_estudiante', 'tipo_error']
        indexes = [
            models.Index(fields=['validacion', 'tipo_error']),
            models.Index(fields=['severidad']),
            models.Index(fields=['resuelto']),
        ]

    def __str__(self):
        return f"{self.tipo_error}: {self.descripcion}"


class OCRConfiguration(models.Model):
    """
    Modelo para configuración de parámetros OCR y validación.
    """

    # Configuración OCR
    tesseract_config = models.TextField(
        default='--oem 3 --psm 6',
        verbose_name="Configuración Tesseract"
    )

    confianza_minima = models.FloatField(
        default=60.0,
        verbose_name="Confianza Mínima OCR (%)"
    )

    # Configuración de detección de campos
    tolerancia_posicion_x = models.FloatField(
        default=5.0,
        verbose_name="Tolerancia Posición X (puntos)"
    )

    tolerancia_posicion_y = models.FloatField(
        default=5.0,
        verbose_name="Tolerancia Posición Y (puntos)"
    )

    # Configuración de validación
    permitir_texto_parcial = models.BooleanField(
        default=False,
        verbose_name="Permitir Texto Parcial"
    )

    detectar_firmas = models.BooleanField(
        default=True,
        verbose_name="Detectar Presencia de Firmas"
    )

    # Configuración de procesamiento
    procesar_imagenes = models.BooleanField(
        default=True,
        verbose_name="Procesar Imágenes Adjuntas"
    )

    guardar_imagenes_temporales = models.BooleanField(
        default=False,
        verbose_name="Guardar Imágenes Temporales"
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )

    class Meta:
        db_table = 'ocr_configuration'
        verbose_name = "Configuración OCR"
        verbose_name_plural = "Configuraciones OCR"

    def __str__(self):
        return f"Configuración OCR - {self.fecha_actualizacion}"


class FieldValidationRule(models.Model):
    """
    Modelo para definir reglas de validación específicas por campo.
    """

    # Información del campo
    nombre_campo = models.CharField(
        max_length=100,
        verbose_name="Nombre del Campo"
    )

    descripcion_campo = models.CharField(
        max_length=255,
        verbose_name="Descripción del Campo"
    )

    # Tipo de campo
    TIPO_CAMPO = [
        ('texto', 'Texto'),
        ('numero', 'Número'),
        ('fecha', 'Fecha'),
        ('firma', 'Firma'),
        ('celda_x', 'Celda con X'),
        ('total', 'Campo de Total'),
    ]

    tipo_campo = models.CharField(
        max_length=20,
        choices=TIPO_CAMPO,
        verbose_name="Tipo de Campo"
    )

    # Ubicación típica en el PDF
    pagina_tipica = models.IntegerField(
        default=1,
        verbose_name="Página Típica"
    )

    posicion_x_relativa = models.FloatField(
        default=0.0,
        verbose_name="Posición X Relativa"
    )

    posicion_y_relativa = models.FloatField(
        default=0.0,
        verbose_name="Posición Y Relativa"
    )

    # Reglas de validación
    obligatorio = models.BooleanField(
        default=True,
        verbose_name="Campo Obligatorio"
    )

    patron_validacion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Patrón de Validación (Regex)"
    )

    valor_minimo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Valor Mínimo"
    )

    valor_maximo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Valor Máximo"
    )

    # Configuración específica
    detectar_posicion_x = models.BooleanField(
        default=False,
        verbose_name="Detectar Posición Exacta de X"
    )

    tolerancia_posicion = models.FloatField(
        default=3.0,
        verbose_name="Tolerancia de Posición (puntos)"
    )

    # Estado
    activo = models.BooleanField(
        default=True,
        verbose_name="Regla Activa"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    class Meta:
        db_table = 'ocr_field_validation_rules'
        verbose_name = "Regla de Validación de Campo"
        verbose_name_plural = "Reglas de Validación de Campos"
        ordering = ['nombre_campo']
        indexes = [
            models.Index(fields=['tipo_campo']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.nombre_campo} ({self.tipo_campo})"