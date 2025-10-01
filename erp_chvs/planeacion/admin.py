from django.contrib import admin
from .models import InstitucionesEducativas, SedesEducativas, Programa, PlanificacionRaciones


@admin.register(InstitucionesEducativas)
class InstitucionesEducativasAdmin(admin.ModelAdmin):
    list_display = ('codigo_ie', 'nombre_institucion', 'id_municipios')
    list_filter = ('id_municipios',)
    search_fields = ('codigo_ie', 'nombre_institucion', 'id_municipios__nombre_municipio')
    list_per_page = 25
    ordering = ('nombre_institucion',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_ie', 'nombre_institucion', 'id_municipios')
        }),
    )


@admin.register(SedesEducativas)
class SedesEducativasAdmin(admin.ModelAdmin):
    list_display = ('cod_interprise', 'nombre_sede_educativa', 'nombre_generico_sede', 'codigo_ie', 'zona')
    list_filter = ('zona', 'codigo_ie')
    search_fields = ('cod_interprise', 'cod_dane', 'nombre_sede_educativa', 'nombre_generico_sede', 'codigo_ie__nombre_institucion')
    list_per_page = 25
    ordering = ('codigo_ie__nombre_institucion', 'nombre_sede_educativa')

    fieldsets = (
        ('Información Básica', {
            'fields': ('cod_interprise', 'cod_dane', 'nombre_sede_educativa', 'nombre_generico_sede', 'codigo_ie')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'zona')
        }),
        ('Información de Alimentación', {
            'fields': ('preparado', 'industrializado')
        }),
    )


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('programa', 'fecha_inicial', 'fecha_final', 'estado', 'municipio', 'contrato')
    list_filter = ('estado', 'municipio')
    search_fields = ('programa', 'contrato', 'municipio__nombre_municipio')
    list_per_page = 25
    ordering = ('programa',)

    fieldsets = (
        ('Información Básica', {
            'fields': ('programa', 'municipio', 'contrato')
        }),
        ('Fechas', {
            'fields': ('fecha_inicial', 'fecha_final')
        }),
        ('Estado y Multimedia', {
            'fields': ('estado', 'imagen')
        }),
    )


@admin.register(PlanificacionRaciones)
class PlanificacionRacionesAdmin(admin.ModelAdmin):
    list_display = ('sede_educativa', 'etc', 'focalizacion', 'nivel_escolar', 'ano', 'cap_am', 'cap_pm', 'almuerzo_ju', 'refuerzo', 'total_raciones')
    list_filter = ('etc', 'focalizacion', 'ano', 'nivel_escolar')
    search_fields = ('sede_educativa__nombre_sede_educativa', 'etc__nombre_municipio', 'focalizacion')
    list_per_page = 25
    ordering = ('etc__nombre_municipio', 'focalizacion', 'sede_educativa__nombre_sede_educativa')

    fieldsets = (
        ('Ubicación y Focalización', {
            'fields': ('etc', 'focalizacion', 'sede_educativa', 'nivel_escolar', 'ano')
        }),
        ('Cantidades de Raciones', {
            'fields': ('cap_am', 'cap_pm', 'almuerzo_ju', 'refuerzo')
        }),
    )

    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    def total_raciones(self, obj):
        """Muestra el total de raciones en el admin."""
        return obj.total_raciones()
    total_raciones.short_description = 'Total Raciones'