from django.contrib import admin
from .models import InformacionCodindem, Programa
# Register your models here.
# 1. Importa tu nuevo modelo
# Register your models here.
# 2. Registra el modelo para que aparezca en el admin, con algunas mejoras.
@admin.register(InformacionCodindem)
class InformacionDemuincodiAdmin(admin.ModelAdmin):
    # Columnas que se mostrarán en la lista principal
    list_display = ('municipio', 'departamento', 'sede', 'cod_interface', 'tipo_comedor')
    
    # Añade una barra de búsqueda que buscará en estas columnas
    search_fields = ('municipio', 'departamento', 'sede', 'dane', 'cod_interface')
    
    # Añade filtros en la barra lateral para navegar más fácil
    list_filter = ('departamento', 'tipo_comedor')
    
    # Para que no cargue todos los miles de registros a la vez
    list_per_page = 25
# Register your models here.

@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('programa', 'fecha_inicial', 'fecha_final', 'estado')
    list_filter = ('estado',)
    search_fields = ('programa',)