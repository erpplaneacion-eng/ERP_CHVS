from django.contrib import admin
from .models import InstitucionesEducativas, SedesEducativas, Programa


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
    list_display = ('cod_interprise', 'nombre_sede_educativa', 'codigo_ie', 'zona')
    list_filter = ('zona', 'codigo_ie')
    search_fields = ('cod_interprise', 'cod_dane', 'nombre_sede_educativa', 'codigo_ie__nombre_institucion')
    list_per_page = 25
    ordering = ('codigo_ie__nombre_institucion', 'nombre_sede_educativa')

    fieldsets = (
        ('Información Básica', {
            'fields': ('cod_interprise', 'cod_dane', 'nombre_sede_educativa', 'codigo_ie')
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
    list_display = ('programa', 'fecha_inicial', 'fecha_final', 'estado')
    list_filter = ('estado',)
    search_fields = ('programa',)