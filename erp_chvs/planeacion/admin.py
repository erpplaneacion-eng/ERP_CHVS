from django.contrib import admin
from .models import InstitucionesEducativas, SedesEducativas, Programa


@admin.register(InstitucionesEducativas)
class InstitucionesEducativasAdmin(admin.ModelAdmin):
    list_display = ('codigo_dane', 'nombre_institucion', 'departamento', 'municipio', 'sector', 'estado')
    list_filter = ('sector', 'estado', 'departamento')
    search_fields = ('codigo_dane', 'nombre_institucion', 'municipio__nombre_municipio')
    list_per_page = 25
    ordering = ('nombre_institucion',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_dane', 'nombre_institucion', 'sector', 'estado')
        }),
        ('Ubicación', {
            'fields': ('departamento', 'municipio', 'direccion')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'rector')
        }),
    )


@admin.register(SedesEducativas)
class SedesEducativasAdmin(admin.ModelAdmin):
    list_display = ('codigo_sede', 'nombre_sede', 'institucion', 'zona', 'tiene_comedor', 'estado')
    list_filter = ('zona', 'tiene_comedor', 'estado', 'tipo_atencion')
    search_fields = ('codigo_sede', 'nombre_sede', 'institucion__nombre_institucion')
    list_per_page = 25
    ordering = ('institucion__nombre_institucion', 'nombre_sede')

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_sede', 'nombre_sede', 'institucion', 'estado')
        }),
        ('Ubicación y Contacto', {
            'fields': ('direccion', 'zona', 'telefono', 'coordinador')
        }),
        ('Información del Comedor', {
            'fields': ('tiene_comedor', 'tipo_atencion', 'capacidad_beneficiarios')
        }),
        ('Jornadas Disponibles', {
            'fields': ('jornada_manana', 'jornada_tarde', 'jornada_nocturna', 'jornada_unica')
        }),
    )


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('programa', 'fecha_inicial', 'fecha_final', 'estado')
    list_filter = ('estado',)
    search_fields = ('programa',)