from django.contrib import admin

from .models import (
    SiesaCentroOperacion,
    SiesaCentroCosto,
    SiesaConcepto,
    SiesaInstalacion,
    SiesaItem,
    SiesaMotivo,
    SiesaProyecto,
    SiesaSolicitante,
    SiesaSyncLog,
    SiesaTipoDocumento,
    SiesaUbicacion,
    SiesaUnidadNegocio,
)


@admin.register(SiesaCentroOperacion)
class SiesaCentroOperacionAdmin(admin.ModelAdmin):
    list_display = ('f285_id', 'f285_descripcion', 'fecha_sincronizacion')
    search_fields = ('f285_id', 'f285_descripcion')


@admin.register(SiesaInstalacion)
class SiesaInstalacionAdmin(admin.ModelAdmin):
    list_display = ('f157_id', 'f157_descripcion', 'f157_id_co', 'fecha_sincronizacion')
    search_fields = ('f157_id', 'f157_descripcion')


@admin.register(SiesaTipoDocumento)
class SiesaTipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('f021_id', 'f021_descripcion', 'fecha_sincronizacion')
    search_fields = ('f021_id', 'f021_descripcion')


@admin.register(SiesaSolicitante)
class SiesaSolicitanteAdmin(admin.ModelAdmin):
    list_display = ('id', 'payload', 'fecha_sincronizacion')


@admin.register(SiesaItem)
class SiesaItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'payload', 'fecha_sincronizacion')


@admin.register(SiesaUnidadNegocio)
class SiesaUnidadNegocioAdmin(admin.ModelAdmin):
    list_display = ('f281_id', 'f281_descripcion', 'fecha_sincronizacion')
    search_fields = ('f281_id', 'f281_descripcion')


@admin.register(SiesaCentroCosto)
class SiesaCentroCostoAdmin(admin.ModelAdmin):
    list_display = ('f284_id', 'f284_descripcion', 'f284_id_co', 'f284_id_un', 'fecha_sincronizacion')
    search_fields = ('f284_id', 'f284_descripcion')


@admin.register(SiesaProyecto)
class SiesaProyectoAdmin(admin.ModelAdmin):
    list_display = ('f107_id', 'f107_descripcion', 'f107_id_referencia', 'fecha_sincronizacion')
    search_fields = ('f107_id', 'f107_descripcion')


@admin.register(SiesaConcepto)
class SiesaConceptoAdmin(admin.ModelAdmin):
    list_display = ('f145_id', 'f145_descripcion', 'f145_ind_naturaleza', 'fecha_sincronizacion')
    search_fields = ('f145_id', 'f145_descripcion')


@admin.register(SiesaMotivo)
class SiesaMotivoAdmin(admin.ModelAdmin):
    list_display = ('f146_id', 'f146_id_concepto', 'f146_ind_naturaleza', 'fecha_sincronizacion')
    search_fields = ('f146_id', 'f146_id_concepto')


@admin.register(SiesaUbicacion)
class SiesaUbicacionAdmin(admin.ModelAdmin):
    list_display = ('f155_id', 'f155_descripcion', 'f150_id', 'fecha_sincronizacion')
    search_fields = ('f155_id', 'f155_descripcion')


@admin.register(SiesaSyncLog)
class SiesaSyncLogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'inicio', 'fin', 'registros_insertados', 'registros_actualizados', 'errores', 'estado')
    list_filter = ('endpoint', 'estado')
    readonly_fields = ('endpoint', 'inicio', 'fin', 'registros_insertados', 'registros_actualizados', 'errores', 'estado', 'detalle_error')
