from django.contrib import admin
from .models import (
    PermisosNutricion,
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaRequerimientosNutricionales,
    GrupoExcluyenteSet,
    GrupoExcluyenteSetMiembro,
    RestriccionAlimentoSubgrupo,
    RestriccionAlimentoEspecifico,
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
    search_fields = ('id_preparacion__preparacion', 'id_ingrediente_siesa__nombre_del_alimento', 'id_ingrediente_siesa__codigo')
    autocomplete_fields = ['id_preparacion', 'id_ingrediente_siesa']
    list_per_page = 25


class GrupoExcluyenteSetMiembroInline(admin.TabularInline):
    model = GrupoExcluyenteSetMiembro
    extra = 1
    autocomplete_fields = []


@admin.register(GrupoExcluyenteSet)
class GrupoExcluyenteSetAdmin(admin.ModelAdmin):
    """
    Configuración de grupos excluyentes por modalidad.
    Permite definir cuáles grupos comparten cuota semanal.
    """
    list_display = ('nombre', 'modalidad', 'frecuencia_compartida', 'lista_grupos')
    list_filter = ('modalidad',)
    search_fields = ('nombre', 'modalidad__modalidad')
    inlines = [GrupoExcluyenteSetMiembroInline]

    def lista_grupos(self, obj):
        grupos = obj.miembros.select_related('grupo').all()
        return ' + '.join(m.grupo.grupo_alimentos for m in grupos)
    lista_grupos.short_description = 'Grupos del Set'


class RestriccionAlimentoEspecificoInline(admin.TabularInline):
    model = RestriccionAlimentoEspecifico
    autocomplete_fields = ['alimento']
    extra = 1


@admin.register(RestriccionAlimentoSubgrupo)
class RestriccionAlimentoSubgrupoAdmin(admin.ModelAdmin):
    """
    Configuración de sub-restricciones de alimentos por subgrupo y modalidad.
    Permite definir qué alimentos específicos deben usarse dentro de un grupo.
    """
    list_display = ('nombre', 'modalidad', 'grupo', 'frecuencia', 'num_alimentos')
    list_filter = ('modalidad', 'grupo')
    search_fields = ('nombre',)
    inlines = [RestriccionAlimentoEspecificoInline]

    def num_alimentos(self, obj):
        return obj.alimentos.count()
    num_alimentos.short_description = 'Alimentos válidos'


@admin.register(TablaRequerimientosNutricionales)
class TablaRequerimientosNutricionalesAdmin(admin.ModelAdmin):
    """Administración de requerimientos nutricionales por nivel escolar."""
    list_display = (
        'id_requerimiento_nutricional',
        'id_nivel_escolar_uapa',
        'calorias_kcal',
        'proteina_g',
        'grasa_g',
        'cho_g',
        'calcio_mg',
        'hierro_mg',
        'sodio_mg'
    )
    list_filter = ('id_nivel_escolar_uapa',)
    search_fields = ('id_nivel_escolar_uapa__nivel_escolar_uapa', 'id_nivel_escolar_uapa__id_grado_escolar_uapa')
    autocomplete_fields = ['id_nivel_escolar_uapa']
    list_per_page = 25

    fieldsets = (
        ('Nivel Escolar', {
            'fields': ('id_nivel_escolar_uapa',)
        }),
        ('Macronutrientes', {
            'fields': ('calorias_kcal', 'proteina_g', 'grasa_g', 'cho_g')
        }),
        ('Micronutrientes', {
            'fields': ('calcio_mg', 'hierro_mg', 'sodio_mg')
        }),
    )
