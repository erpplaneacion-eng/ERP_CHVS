from django.contrib import admin
from .models import (
    PermisosNutricion,
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes
)


# Registro básico para permisos
admin.site.register(PermisosNutricion)


@admin.register(TablaAlimentos2018Icbf)
class TablaAlimentosAdmin(admin.ModelAdmin):
    """Administración de la tabla de alimentos ICBF 2018."""
    list_display = ('codigo', 'nombre_del_alimento', 'energia_kcal', 'proteina_g', 'lipidos_g')
    search_fields = ('nombre_del_alimento', 'codigo')
    list_per_page = 25


@admin.register(TablaMenus)
class TablaMenusAdmin(admin.ModelAdmin):
    """Administración de menús."""
    list_display = ('menu', 'id_modalidad', 'id_contrato', 'fecha_creacion')
    list_filter = ('id_modalidad', 'id_contrato', 'fecha_creacion')
    search_fields = ('menu',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    list_per_page = 20

    fieldsets = (
        ('Información Básica', {
            'fields': ('menu', 'id_modalidad', 'id_contrato')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


class TablaPreparacionIngredientesInline(admin.TabularInline):
    """Inline para agregar ingredientes a una preparación."""
    model = TablaPreparacionIngredientes
    extra = 1
    fields = ('id_ingrediente_siesa',)
    autocomplete_fields = ['id_ingrediente_siesa']


@admin.register(TablaPreparaciones)
class TablaPreparacionesAdmin(admin.ModelAdmin):
    """Administración de preparaciones/recetas."""
    list_display = ('preparacion', 'id_menu', 'fecha_creacion')
    list_filter = ('id_menu__id_modalidad', 'fecha_creacion')
    search_fields = ('preparacion', 'id_menu__menu')
    readonly_fields = ('fecha_creacion',)
    inlines = [TablaPreparacionIngredientesInline]
    list_per_page = 20

    fieldsets = (
        ('Información de la Preparación', {
            'fields': ('preparacion', 'id_menu')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TablaIngredientesSiesa)
class TablaIngredientesSiesaAdmin(admin.ModelAdmin):
    """Administración de ingredientes de inventario."""
    list_display = ('id_ingrediente_siesa', 'nombre_ingrediente')
    search_fields = ('id_ingrediente_siesa', 'nombre_ingrediente')
    list_per_page = 25


@admin.register(TablaPreparacionIngredientes)
class TablaPreparacionIngredientesAdmin(admin.ModelAdmin):
    """Administración de la relación preparaciones-ingredientes."""
    list_display = ('id_preparacion', 'id_ingrediente_siesa')
    search_fields = ('id_preparacion__preparacion', 'id_ingrediente_siesa__nombre_ingrediente')
    autocomplete_fields = ['id_preparacion', 'id_ingrediente_siesa']
    list_per_page = 25