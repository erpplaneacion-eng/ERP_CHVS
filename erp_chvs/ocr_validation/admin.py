from django.contrib import admin
from .models import PDFValidation, ValidationError, OCRConfiguration, FieldValidationRule

@admin.register(PDFValidation)
class PDFValidationAdmin(admin.ModelAdmin):
    list_display = ('archivo_nombre', 'sede_educativa', 'mes_atencion', 'ano', 'estado', 'total_errores', 'fecha_procesamiento')
    list_filter = ('estado', 'mes_atencion', 'ano', 'tipo_complemento')
    search_fields = ('archivo_nombre', 'sede_educativa')
    readonly_fields = ('fecha_procesamiento', 'fecha_completado', 'tiempo_procesamiento')

    fieldsets = (
        ('Información del Archivo', {
            'fields': ('archivo_nombre', 'archivo_path', 'sede_educativa', 'mes_atencion', 'ano', 'tipo_complemento')
        }),
        ('Estado del Procesamiento', {
            'fields': ('estado', 'total_errores', 'errores_criticos', 'errores_advertencia', 'fecha_procesamiento', 'fecha_completado', 'tiempo_procesamiento')
        }),
        ('Información Adicional', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ValidationError)
class ValidationErrorAdmin(admin.ModelAdmin):
    list_display = ('validacion', 'tipo_error', 'descripcion', 'pagina', 'severidad', 'resuelto', 'fecha_creacion')
    list_filter = ('tipo_error', 'severidad', 'resuelto', 'fecha_creacion')
    search_fields = ('descripcion', 'tipo_error')
    readonly_fields = ('fecha_creacion',)

    fieldsets = (
        ('Información del Error', {
            'fields': ('validacion', 'tipo_error', 'descripcion', 'severidad')
        }),
        ('Ubicación', {
            'fields': ('pagina', 'fila_estudiante', 'columna_campo')
        }),
        ('Detalles Técnicos', {
            'fields': ('valor_esperado', 'valor_encontrado', 'coordenada_x', 'coordenada_y'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('resuelto', 'fecha_creacion')
        }),
    )

@admin.register(OCRConfiguration)
class OCRConfigurationAdmin(admin.ModelAdmin):
    list_display = ('modelo_landingai', 'confianza_minima', 'detectar_firmas', 'procesar_imagenes', 'fecha_actualizacion')
    readonly_fields = ('fecha_actualizacion',)

    fieldsets = (
        ('Configuración LandingAI', {
            'fields': ('modelo_landingai', 'confianza_minima')
        }),
        ('Configuración de Detección', {
            'fields': ('tolerancia_posicion_x', 'tolerancia_posicion_y', 'permitir_texto_parcial')
        }),
        ('Características de Procesamiento', {
            'fields': ('detectar_firmas', 'procesar_imagenes', 'guardar_imagenes_temporales')
        }),
    )

@admin.register(FieldValidationRule)
class FieldValidationRuleAdmin(admin.ModelAdmin):
    list_display = ('nombre_campo', 'tipo_campo', 'obligatorio', 'activo', 'fecha_creacion')
    list_filter = ('tipo_campo', 'obligatorio', 'activo')
    search_fields = ('nombre_campo', 'descripcion_campo')
    readonly_fields = ('fecha_creacion',)

    fieldsets = (
        ('Información del Campo', {
            'fields': ('nombre_campo', 'descripcion_campo', 'tipo_campo')
        }),
        ('Ubicación en PDF', {
            'fields': ('pagina_tipica', 'posicion_x_relativa', 'posicion_y_relativa')
        }),
        ('Reglas de Validación', {
            'fields': ('obligatorio', 'patron_validacion', 'valor_minimo', 'valor_maximo')
        }),
        ('Configuración Avanzada', {
            'fields': ('detectar_posicion_x', 'tolerancia_posicion', 'activo'),
            'classes': ('collapse',)
        }),
    )