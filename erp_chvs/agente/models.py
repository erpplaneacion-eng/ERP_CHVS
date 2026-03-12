from django.db import models
from django.contrib.auth.models import User

from nutricion.models import (
    TablaMenus, ComponentesAlimentos, GruposAlimentos, TablaAlimentos2018Icbf
)
from principal.models import ModalidadesDeConsumo


class GeneracionIA(models.Model):
    ESTADO_PROCESANDO = 'procesando'
    ESTADO_PENDIENTE = 'pendiente_revision'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_DESCARTADO = 'descartado'
    ESTADO_ERROR = 'error'

    ESTADOS = [
        (ESTADO_PROCESANDO, 'Procesando'),
        (ESTADO_PENDIENTE, 'Pendiente de Revisión'),
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_DESCARTADO, 'Descartado'),
        (ESTADO_ERROR, 'Error'),
    ]

    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.CASCADE,
        db_column='id_modalidad',
        related_name='generaciones_ia',
        null=True, blank=True,
        verbose_name="Modalidad"
    )
    id_menu = models.ForeignKey(
        TablaMenus,
        on_delete=models.CASCADE,
        db_column='id_menu',
        related_name='generaciones_ia',
        null=True, blank=True,
        verbose_name="Menú (destino)"
    )
    usuario_solicitante = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generaciones_ia_solicitadas',
        verbose_name="Usuario Solicitante"
    )
    ocasion_especial = models.CharField(max_length=100, blank=True, verbose_name="Ocasión Especial")
    modelo_llm = models.CharField(max_length=100, default='gemini-2.0-flash', verbose_name="Modelo LLM")
    estado = models.CharField(max_length=30, choices=ESTADOS, default=ESTADO_PROCESANDO, verbose_name="Estado")
    prompt_final = models.TextField(blank=True, verbose_name="Prompt Enviado")
    respuesta_cruda = models.TextField(blank=True, verbose_name="Respuesta Cruda del LLM")
    errores_validacion = models.JSONField(default=list, blank=True, verbose_name="Errores de Validación")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Aprobación")
    usuario_aprobador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='borradores_aprobados',
        verbose_name="Usuario Aprobador"
    )

    class Meta:
        db_table = 'agente_generacion_ia'
        verbose_name = "Generación IA"
        verbose_name_plural = "Generaciones IA"
        ordering = ['-fecha_creacion']

    def __str__(self):
        ocasion_str = f" [{self.ocasion_especial}]" if self.ocasion_especial else ""
        menu_str = f" → Menú {self.id_menu.menu}" if self.id_menu else ""
        return f"Generación {self.id} — {self.id_modalidad.modalidad}{ocasion_str}{menu_str} ({self.estado})"


class BorradorPreparacionIA(models.Model):
    VALIDA = 'valida'
    CON_DUDA = 'con_duda'
    INVALIDA = 'invalida'

    ESTADOS_VALIDACION = [
        (VALIDA, 'Válida'),
        (CON_DUDA, 'Con Duda'),
        (INVALIDA, 'Inválida'),
    ]

    generacion = models.ForeignKey(
        GeneracionIA,
        on_delete=models.CASCADE,
        related_name='preparaciones',
        verbose_name="Generación"
    )
    nombre_preparacion = models.CharField(max_length=255, verbose_name="Nombre de la Preparación")
    componente_sugerido = models.ForeignKey(
        ComponentesAlimentos,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_componente',
        verbose_name="Componente Sugerido"
    )
    estado_validacion = models.CharField(
        max_length=20,
        choices=ESTADOS_VALIDACION,
        default=VALIDA,
        verbose_name="Estado de Validación"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    procedimiento = models.TextField(blank=True, verbose_name="Procedimiento de Preparación")

    class Meta:
        db_table = 'agente_borrador_preparacion_ia'
        verbose_name = "Borrador Preparación IA"
        verbose_name_plural = "Borradores Preparaciones IA"
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre_preparacion} [{self.estado_validacion}]"


class BorradorIngredienteIA(models.Model):
    VALIDO = 'valido'
    NO_ENCONTRADO = 'no_encontrado'

    ESTADOS_VALIDACION = [
        (VALIDO, 'Válido'),
        (NO_ENCONTRADO, 'No encontrado en catálogo'),
    ]

    borrador_preparacion = models.ForeignKey(
        BorradorPreparacionIA,
        on_delete=models.CASCADE,
        related_name='ingredientes',
        verbose_name="Preparación del Borrador"
    )
    codigo_icbf_sugerido = models.CharField(max_length=20, verbose_name="Código ICBF Sugerido")
    nombre_sugerido = models.CharField(max_length=200, verbose_name="Nombre Sugerido")
    alimento_icbf = models.ForeignKey(
        TablaAlimentos2018Icbf,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='codigo_icbf_resuelto',
        verbose_name="Alimento ICBF Resuelto"
    )
    estado_validacion = models.CharField(
        max_length=20,
        choices=ESTADOS_VALIDACION,
        default=VALIDO,
        verbose_name="Estado de Validación"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        db_table = 'agente_borrador_ingrediente_ia'
        verbose_name = "Borrador Ingrediente IA"
        verbose_name_plural = "Borradores Ingredientes IA"
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre_sugerido} [{self.estado_validacion}]"
