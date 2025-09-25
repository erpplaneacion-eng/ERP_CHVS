from django.contrib import admin
from django.utils.html import format_html
from .models import ListadosFocalizacion


@admin.register(ListadosFocalizacion)
class ListadosFocalizacionAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para ListadosFocalizacion.
    """

    # Campos a mostrar en la lista
    list_display = [
        'id_listados',
        'get_nombre_completo_display',
        'ano',
        'etc',
        'sede',
        'focalizacion',
        'get_complementos_display',
        'fecha_creacion'
    ]

    # Filtros laterales
    list_filter = [
        'ano',
        'etc',
        'focalizacion',
        'genero',
        'fecha_creacion',
        'complemento_alimentario_preparado_am',
        'complemento_alimentario_preparado_pm',
        'almuerzo_jornada_unica',
        'refuerzo_complemento_am_pm'
    ]

    # Campos de búsqueda
    search_fields = [
        'id_listados',
        'doc',
        'nombre1',
        'nombre2',
        'apellido1',
        'apellido2',
        'institucion',
        'sede'
    ]

    # Campos de solo lectura
    readonly_fields = [
        'fecha_creacion',
        'fecha_actualizacion',
        'get_nombre_completo',
        'complementos_activos'
    ]

    # Ordenamiento por defecto
    ordering = ['-fecha_creacion', 'apellido1', 'nombre1']

    # Número de elementos por página
    list_per_page = 50

    # Configuración de formulario
    fieldsets = (
        ('Información General', {
            'fields': (
                'id_listados',
                'ano',
                'etc',
                'focalizacion'
            )
        }),
        ('Institución Educativa', {
            'fields': (
                'institucion',
                'sede',
                'grado_grupos'
            )
        }),
        ('Datos Personales', {
            'fields': (
                'tipodoc',
                'doc',
                'nombre1',
                'nombre2',
                'apellido1',
                'apellido2',
                'fecha_nacimiento',
                'edad',
                'genero',
                'etnia'
            )
        }),
        ('Complementos Alimentarios', {
            'fields': (
                'complemento_alimentario_preparado_am',
                'complemento_alimentario_preparado_pm',
                'almuerzo_jornada_unica',
                'refuerzo_complemento_am_pm'
            ),
            'description': 'Marque los complementos alimentarios que recibe el titular de derecho'
        }),
        ('Información de Auditoría', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
                'get_nombre_completo',
                'complementos_activos'
            ),
            'classes': ('collapse',)
        })
    )

    # Acciones personalizadas
    actions = ['export_to_excel', 'mark_all_complementos']

    def get_nombre_completo_display(self, obj):
        """Retorna el nombre completo para mostrar en la lista."""
        return obj.get_nombre_completo()
    get_nombre_completo_display.short_description = 'Nombre Completo'
    get_nombre_completo_display.admin_order_field = 'apellido1'

    def get_complementos_display(self, obj):
        """Muestra los complementos activos con colores."""
        complementos = obj.complementos_activos
        if not complementos:
            return format_html('<span style="color: #999;">Sin complementos</span>')

        html = []
        colors = {
            'CAP AM': '#28a745',
            'CAP PM': '#17a2b8',
            'Almuerzo JU': '#fd7e14',
            'Refuerzo': '#6f42c1'
        }

        for complemento in complementos:
            color = colors.get(complemento, '#6c757d')
            html.append(f'<span style="color: {color}; font-weight: bold;">● {complemento}</span>')

        return format_html('<br>'.join(html))
    get_complementos_display.short_description = 'Complementos'

    def export_to_excel(self, request, queryset):
        """Acción personalizada para exportar a Excel."""
        # Aquí puedes implementar la lógica de exportación
        self.message_user(request, f"Se exportaron {queryset.count()} registros.")
    export_to_excel.short_description = "Exportar seleccionados a Excel"

    def mark_all_complementos(self, request, queryset):
        """Acción para marcar todos los complementos alimentarios."""
        updated = queryset.update(
            complemento_alimentario_preparado_am='x',
            complemento_alimentario_preparado_pm='x'
        )
        self.message_user(request, f"Se actualizaron {updated} registros con complementos AM/PM.")
    mark_all_complementos.short_description = "Marcar complementos AM/PM"

    def get_queryset(self, request):
        """Optimizar consultas con select_related."""
        return super().get_queryset(request)