from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum


class RegistroContable(models.Model):
    TIPO_CHOICES = [
        ('SERVICIOS', 'Servicios'),
        ('MATERIAS_PRIMAS', 'Materias Primas'),
    ]

    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADO', 'Enviado'),
        ('EN_REVISION_COMPRAS', 'En Revisión Compras'),
        ('DEVUELTO_COMPRAS', 'Devuelto por Compras'),
        ('APROBADO_COMPRAS', 'Aprobado por Compras'),
        ('OBSERVADO_CONTABILIDAD', 'Observado por Contabilidad'),
        ('APROBADO_CONTABILIDAD', 'Aprobado por Contabilidad'),
        ('CERRADO', 'Cerrado'),
    ]

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo"
    )
    periodo_mes = models.PositiveSmallIntegerField(
        verbose_name="Mes del Período"
    )
    periodo_ano = models.PositiveSmallIntegerField(
        verbose_name="Año del Período"
    )
    lider = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='registros_contables',
        verbose_name="Líder"
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='BORRADOR',
        verbose_name="Estado"
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    # Fechas automáticas — todas seteadas por el servicio con timezone.now()
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_envio = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Envío")
    fecha_entrega_fisica = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Entrega Física")
    fecha_inicio_revision_compras = models.DateTimeField(null=True, blank=True, verbose_name="Inicio Revisión Compras")
    fecha_devolucion_compras = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Devolución Compras")
    fecha_reenvio = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Reenvío")
    fecha_reentrega_fisica = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Reentrega Física")
    fecha_aprobacion_compras = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación Compras")
    fecha_inicio_revision_contabilidad = models.DateTimeField(null=True, blank=True, verbose_name="Inicio Revisión Contabilidad")
    fecha_observacion_contabilidad = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Observación Contabilidad")
    fecha_respuesta_compras = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Respuesta Compras")
    fecha_aprobacion_contabilidad = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Aprobación Contabilidad")
    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Cierre")

    class Meta:
        db_table = 'contabilidad_registros'
        verbose_name = "Registro Contable"
        verbose_name_plural = "Registros Contables"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['lider', 'periodo_ano', 'periodo_mes']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo', 'periodo_ano', 'periodo_mes']),
        ]

    def __str__(self):
        return f"RC-{self.pk} | {self.get_tipo_display()} | {self.periodo_mes}/{self.periodo_ano} | {self.get_estado_display()}"

    @property
    def valor_total(self):
        resultado = self.facturas.aggregate(total=Sum('valor'))
        return resultado['total'] or 0

    @property
    def total_documentos(self):
        return self.facturas.count()


class Factura(models.Model):
    registro = models.ForeignKey(
        RegistroContable,
        on_delete=models.CASCADE,
        related_name='facturas',
        verbose_name="Registro Contable"
    )
    numero_factura = models.CharField(max_length=100, verbose_name="Número de Factura")
    proveedor = models.CharField(max_length=200, verbose_name="Proveedor")
    concepto = models.CharField(max_length=300, verbose_name="Concepto")
    valor = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Valor")
    fecha_factura = models.DateField(verbose_name="Fecha de Factura")
    fecha_carga = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Carga")

    class Meta:
        db_table = 'contabilidad_facturas'
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['fecha_carga']

    def __str__(self):
        return f"{self.numero_factura} | {self.proveedor} | ${self.valor}"


class ItemChecklist(models.Model):
    TIPO_PROCESO_CHOICES = [
        ('SERVICIOS', 'Servicios'),
        ('MATERIAS_PRIMAS', 'Materias Primas'),
        ('AMBOS', 'Ambos'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre del Ítem")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    tipo_proceso = models.CharField(
        max_length=20,
        choices=TIPO_PROCESO_CHOICES,
        default='AMBOS',
        verbose_name="Tipo de Proceso"
    )
    obligatorio = models.BooleanField(default=True, verbose_name="Obligatorio")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    orden = models.PositiveSmallIntegerField(default=0, verbose_name="Orden")

    class Meta:
        db_table = 'contabilidad_items_checklist'
        verbose_name = "Ítem de Checklist"
        verbose_name_plural = "Ítems de Checklist"
        ordering = ['orden', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_proceso_display()})"


class VerificacionChecklist(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('OK', 'OK'),
        ('NO_OK', 'No OK'),
        ('NA', 'No Aplica'),
    ]

    factura = models.ForeignKey(
        'Factura',
        on_delete=models.CASCADE,
        related_name='verificaciones',
        verbose_name="Factura"
    )
    item = models.ForeignKey(
        ItemChecklist,
        on_delete=models.PROTECT,
        verbose_name="Ítem de Checklist"
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name="Estado"
    )
    observacion = models.TextField(blank=True, verbose_name="Observación")
    verificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verificaciones_checklist',
        verbose_name="Verificado Por"
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Verificación")

    class Meta:
        db_table = 'contabilidad_verificaciones'
        verbose_name = "Verificación Checklist"
        verbose_name_plural = "Verificaciones Checklist"
        unique_together = [['factura', 'item']]

    def __str__(self):
        return f"{self.registro} | {self.item.nombre} | {self.get_estado_display()}"


class HistorialEstado(models.Model):
    ACCION_CHOICES = [
        ('CREACION', 'Creación'),
        ('ENVIO', 'Envío'),
        ('CONFIRMACION_RECEPCION', 'Confirmación de Recepción'),
        ('DEVOLUCION_COMPRAS', 'Devolución por Compras'),
        ('REENVIO', 'Reenvío'),
        ('CONFIRMACION_REENTREGA', 'Confirmación de Reentrega'),
        ('APROBACION_COMPRAS', 'Aprobación por Compras'),
        ('INICIO_REVISION_CONTABILIDAD', 'Inicio Revisión Contabilidad'),
        ('OBSERVACION_CONTABILIDAD', 'Observación de Contabilidad'),
        ('RESPUESTA_COMPRAS', 'Respuesta de Compras a Observación'),
        ('APROBACION_CONTABILIDAD', 'Aprobación por Contabilidad'),
        ('CIERRE', 'Cierre'),
    ]

    registro = models.ForeignKey(
        RegistroContable,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name="Registro Contable"
    )
    accion = models.CharField(
        max_length=40,
        choices=ACCION_CHOICES,
        verbose_name="Acción"
    )
    estado_anterior = models.CharField(max_length=30, blank=True, verbose_name="Estado Anterior")
    estado_nuevo = models.CharField(max_length=30, blank=True, verbose_name="Estado Nuevo")
    comentario = models.TextField(blank=True, verbose_name="Comentario")
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historial_contabilidad',
        verbose_name="Usuario"
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        db_table = 'contabilidad_historial'
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"
        ordering = ['fecha']
        indexes = [
            models.Index(fields=['registro', 'fecha']),
        ]

    def __str__(self):
        return f"{self.registro} | {self.get_accion_display()} | {self.fecha:%Y-%m-%d %H:%M}"
