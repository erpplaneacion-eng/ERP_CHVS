from django.contrib import admin
from .models import GeneracionIA, BorradorPreparacionIA, BorradorIngredienteIA


class BorradorIngredienteInline(admin.TabularInline):
    model = BorradorIngredienteIA
    extra = 0
    readonly_fields = ['codigo_icbf_sugerido', 'nombre_sugerido', 'alimento_icbf', 'estado_validacion', 'observaciones']


class BorradorPreparacionInline(admin.TabularInline):
    model = BorradorPreparacionIA
    extra = 0
    readonly_fields = ['nombre_preparacion', 'componente_sugerido', 'estado_validacion', 'observaciones']


@admin.register(GeneracionIA)
class GeneracionIAAdmin(admin.ModelAdmin):
    list_display = ['id', 'id_modalidad', 'id_menu', 'estado', 'modelo_llm', 'usuario_solicitante', 'fecha_creacion']
    list_filter = ['estado', 'modelo_llm']
    readonly_fields = ['prompt_final', 'respuesta_cruda', 'fecha_creacion', 'fecha_aprobacion']
    inlines = [BorradorPreparacionInline]


@admin.register(BorradorPreparacionIA)
class BorradorPreparacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_preparacion', 'estado_validacion', 'generacion']
    list_filter = ['estado_validacion']
    inlines = [BorradorIngredienteInline]
