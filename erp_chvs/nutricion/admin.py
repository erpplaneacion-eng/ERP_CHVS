
from django.contrib import admin
from .models import PermisosNutricion, TablaAlimentos2018Icbf

# 2. Registra el modelo en el sitio de administración.
#    Ahora Django sabrá que debe mostrarlo en el panel.
admin.site.register(PermisosNutricion)

@admin.register(TablaAlimentos2018Icbf)
class TablaAlimentosAdmin(admin.ModelAdmin):
    
    list_display = ('nombre_del_alimento', 'energia_kcal', 'proteina_g', 'lipidos_g')
    search_fields = ('nombre_del_alimento',)    
    # NOTA: No tienes un campo "grupo", así que he comentado el filtro.
    # Si tuvieras una columna para el grupo de alimento, la podrías añadir aquí.
    # list_filter = ('nombre_del_grupo',)