from django.contrib import admin
from .models import TipoRuta, Ruta, RutaSedes


@admin.register(TipoRuta)
class TipoRutaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo')
    search_fields = ('tipo',)


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_ruta', 'id_tipo_ruta', 'id_programa', 'activa')
    list_filter = ('activa', 'id_tipo_ruta', 'id_programa')
    search_fields = ('nombre_ruta',)


@admin.register(RutaSedes)
class RutaSedesAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_ruta', 'sede_educativa', 'orden_visita')
    list_filter = ('id_ruta',)
    ordering = ('id_ruta', 'orden_visita')
