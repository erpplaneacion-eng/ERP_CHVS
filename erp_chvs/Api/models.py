"""Modelos locales de catálogos SIESA ERP.

Cada modelo es réplica 1:1 de la respuesta JSON del endpoint correspondiente.
Los nombres de campo preservan la nomenclatura original de SIESA (f<num>_<campo>).
Sin FKs ni cruces hacia modelos del ERP — los cruces se hacen en las apps consumidoras.

Campo de infraestructura: fecha_sincronizacion (auto_now=True) en todos los modelos.
"""

from django.db import models


class SiesaCentroOperacion(models.Model):
    """Endpoint CENTROS-OPERACIONES — centros de operación del operador."""

    f285_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID CO')
    f285_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_centros_operaciones'
        verbose_name = 'Centro de Operación SIESA'
        verbose_name_plural = 'Centros de Operación SIESA'

    def __str__(self):
        return f'{self.f285_id} — {self.f285_descripcion}'


class SiesaInstalacion(models.Model):
    """Endpoint INSTALACIONES — instalaciones físicas del operador (cocinas, plantas)."""

    f157_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Instalación')
    f157_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    f157_id_co = models.CharField(max_length=50, blank=True, verbose_name='ID Centro Operación')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_instalaciones'
        verbose_name = 'Instalación SIESA'
        verbose_name_plural = 'Instalaciones SIESA'

    def __str__(self):
        return f'{self.f157_id} — {self.f157_descripcion}'


class SiesaTipoDocumento(models.Model):
    """Endpoint TIPOS-DOCUMENTOS — tipos de documento transaccional en SIESA."""

    f021_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Tipo Documento')
    f021_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_tipos_documentos'
        verbose_name = 'Tipo de Documento SIESA'
        verbose_name_plural = 'Tipos de Documento SIESA'

    def __str__(self):
        return f'{self.f021_id} — {self.f021_descripcion}'


class SiesaSolicitante(models.Model):
    """Endpoint SOLICITANTES — actualmente sin datos en SIESA.

    Modelo genérico con payload JSONField hasta que SIESA llene el catálogo
    y se pueda inspeccionar la estructura real para definir campos concretos.
    """

    payload = models.JSONField(verbose_name='Payload SIESA')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_solicitantes'
        verbose_name = 'Solicitante SIESA'
        verbose_name_plural = 'Solicitantes SIESA'

    def __str__(self):
        return str(self.payload)


class SiesaItem(models.Model):
    """Endpoint ITEMS (Plan de Cuentas / artículos) — actualmente sin datos en SIESA.

    Modelo genérico con payload JSONField hasta que SIESA llene el catálogo
    y se pueda inspeccionar la estructura real para definir campos concretos.
    Cuando haya datos, migrar a campos explícitos y actualizar EquivalenciaICBFCompras.
    """

    payload = models.JSONField(verbose_name='Payload SIESA')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_items'
        verbose_name = 'Item SIESA'
        verbose_name_plural = 'Items SIESA'

    def __str__(self):
        return str(self.payload)


class SiesaUnidadNegocio(models.Model):
    """Endpoint UNIDADES-NEGOCIOS — unidades de negocio / contratos del operador."""

    f281_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Unidad Negocio')
    f281_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_unidades_negocios'
        verbose_name = 'Unidad de Negocio SIESA'
        verbose_name_plural = 'Unidades de Negocio SIESA'

    def __str__(self):
        return f'{self.f281_id} — {self.f281_descripcion}'


class SiesaCentroCosto(models.Model):
    """Endpoint CCOSTOS — centros de costo para afectación presupuestal."""

    f284_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Centro Costo')
    f284_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    f284_id_co = models.CharField(max_length=50, blank=True, verbose_name='ID Centro Operación')
    f284_id_un = models.CharField(max_length=50, blank=True, verbose_name='ID Unidad Negocio')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_ccostos'
        verbose_name = 'Centro de Costo SIESA'
        verbose_name_plural = 'Centros de Costo SIESA'

    def __str__(self):
        return f'{self.f284_id} — {self.f284_descripcion}'


class SiesaProyecto(models.Model):
    """Endpoint PROYECTOS — proyectos / sedes educativas registrados en SIESA."""

    f107_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Proyecto')
    f107_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    f107_id_referencia = models.CharField(max_length=100, blank=True, verbose_name='ID Referencia')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_proyectos'
        verbose_name = 'Proyecto SIESA'
        verbose_name_plural = 'Proyectos SIESA'

    def __str__(self):
        return f'{self.f107_id} — {self.f107_descripcion}'


class SiesaConcepto(models.Model):
    """Endpoint CONCEPTOS — conceptos de movimiento (ventas, compras, inventario, etc.)."""

    f145_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Concepto')
    f145_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    f145_ind_naturaleza = models.CharField(max_length=5, blank=True, verbose_name='Indicador Naturaleza')
    f145_ind_liquidacion = models.CharField(max_length=50, blank=True, verbose_name='Indicador Liquidación')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_conceptos'
        verbose_name = 'Concepto SIESA'
        verbose_name_plural = 'Conceptos SIESA'

    def __str__(self):
        return f'{self.f145_id} — {self.f145_descripcion}'


class SiesaMotivo(models.Model):
    """Endpoint MOTIVOS — motivos asociados a conceptos.

    f146_id no es único por sí solo; la unicidad real es (f146_id_concepto, f146_id).
    No tiene campo descripción — SIESA solo entrega id, id_concepto e ind_naturaleza.
    """

    f146_id = models.CharField(max_length=50, verbose_name='ID Motivo')
    f146_id_concepto = models.CharField(max_length=50, verbose_name='ID Concepto')
    f146_ind_naturaleza = models.CharField(max_length=5, blank=True, verbose_name='Indicador Naturaleza')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_motivos'
        verbose_name = 'Motivo SIESA'
        verbose_name_plural = 'Motivos SIESA'
        unique_together = [('f146_id_concepto', 'f146_id')]

    def __str__(self):
        return f'Motivo {self.f146_id} / Concepto {self.f146_id_concepto}'


class SiesaUbicacion(models.Model):
    """Endpoint BODEGAS (URL: UBICACIONES) — ubicaciones/bodegas físicas del operador."""

    f155_id = models.CharField(max_length=50, primary_key=True, verbose_name='ID Ubicación')
    f155_descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    f150_id = models.CharField(max_length=50, blank=True, verbose_name='ID f150')
    fecha_sincronizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'siesa_ubicaciones'
        verbose_name = 'Ubicación / Bodega SIESA'
        verbose_name_plural = 'Ubicaciones / Bodegas SIESA'

    def __str__(self):
        return f'{self.f155_id} — {self.f155_descripcion}'


class SiesaSyncLog(models.Model):
    """Registro de sincronizaciones ejecutadas por el comando sync_siesa."""

    ESTADO_OK = 'ok'
    ESTADO_ERROR = 'error'
    ESTADO_CHOICES = [(ESTADO_OK, 'OK'), (ESTADO_ERROR, 'Error')]

    endpoint = models.CharField(max_length=100, verbose_name='Endpoint')
    inicio = models.DateTimeField(verbose_name='Inicio')
    fin = models.DateTimeField(null=True, blank=True, verbose_name='Fin')
    registros_insertados = models.IntegerField(default=0, verbose_name='Insertados')
    registros_actualizados = models.IntegerField(default=0, verbose_name='Actualizados')
    errores = models.IntegerField(default=0, verbose_name='Errores')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_OK)
    detalle_error = models.TextField(blank=True, verbose_name='Detalle error')

    class Meta:
        db_table = 'siesa_sync_log'
        verbose_name = 'Log de Sincronización SIESA'
        verbose_name_plural = 'Logs de Sincronización SIESA'
        ordering = ['-inicio']

    def __str__(self):
        return f'{self.endpoint} — {self.inicio:%Y-%m-%d %H:%M} — {self.estado}'
