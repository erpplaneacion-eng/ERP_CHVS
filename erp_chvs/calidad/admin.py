from django.contrib import admin
from .models import CertificadoCalidad


@admin.register(CertificadoCalidad)
class CertificadoCalidadAdmin(admin.ModelAdmin):
    list_display = ('numero_certificado', 'nombre_completo', 'cedula', 'cargo', 'tipo_empleado', 'fecha_emision', 'creado_por')
    list_filter = ('tipo_empleado', 'fecha_emision')
    search_fields = ('cedula', 'nombre_completo', 'numero_certificado')
    readonly_fields = ('numero_certificado', 'fecha_emision')
