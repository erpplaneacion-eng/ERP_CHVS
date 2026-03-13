from django.contrib import admin

from .models import (
    RegistroContable, Factura, ItemChecklist,
    VerificacionChecklist, HistorialEstado
)


@admin.register(RegistroContable)
class RegistroContableAdmin(admin.ModelAdmin):
    list_display = ['id', 'tipo', 'periodo_mes', 'periodo_ano', 'lider', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'tipo', 'periodo_ano']
    search_fields = ['lider__username', 'lider__first_name', 'lider__last_name', 'descripcion']
    readonly_fields = [
        'fecha_creacion', 'fecha_envio', 'fecha_entrega_fisica',
        'fecha_inicio_revision_compras', 'fecha_devolucion_compras',
        'fecha_reenvio', 'fecha_reentrega_fisica', 'fecha_aprobacion_compras',
        'fecha_inicio_revision_contabilidad', 'fecha_observacion_contabilidad',
        'fecha_respuesta_compras', 'fecha_aprobacion_contabilidad', 'fecha_cierre',
    ]
    ordering = ['-fecha_creacion']


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['id', 'registro', 'numero_factura', 'proveedor', 'valor', 'fecha_factura']
    list_filter = ['registro__tipo', 'registro__estado']
    search_fields = ['numero_factura', 'proveedor', 'concepto']
    readonly_fields = ['fecha_carga']


@admin.register(ItemChecklist)
class ItemChecklistAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo_proceso', 'obligatorio', 'activo', 'orden']
    list_filter = ['tipo_proceso', 'obligatorio', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['orden', 'nombre']


@admin.register(VerificacionChecklist)
class VerificacionChecklistAdmin(admin.ModelAdmin):
    list_display = ['id', 'factura', 'item', 'estado', 'verificado_por', 'fecha_verificacion']
    list_filter = ['estado', 'item__obligatorio']
    search_fields = ['factura__numero_factura', 'item__nombre']
    readonly_fields = ['fecha_verificacion']


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ['id', 'registro', 'accion', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha']
    list_filter = ['accion']
    search_fields = ['registro__id', 'usuario__username', 'comentario']
    readonly_fields = ['fecha']
    ordering = ['-fecha']
