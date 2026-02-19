from .core import (
    api_generar_menu_ia,
    nutricion_index,
    lista_alimentos,
    editar_alimento,
    eliminar_alimento,
    lista_menus,
)
from .preparaciones_editor import (
    vista_preparaciones_editor,
    api_rango_ingrediente_preparacion,
    api_guardar_preparaciones_editor,
)
from .menus_api import (
    api_programas_por_municipio,
    api_modalidades_por_programa,
    api_generar_menus_automaticos,
    api_crear_menu_especial,
    api_menus,
    api_menu_detail,
)
from .preparaciones_api import (
    lista_preparaciones,
    api_preparaciones,
    api_preparacion_detail,
    api_copiar_preparacion,
    api_preparaciones_por_modalidad,
    lista_ingredientes,
    api_ingredientes,
    api_ingrediente_detail,
    api_componentes_alimentos,
    detalle_preparacion,
    api_preparacion_ingredientes,
    api_preparacion_ingrediente_delete,
)
from .analisis_api import (
    api_analisis_nutricional_menu,
    guardar_analisis_nutricional,
    api_guardar_ingredientes_por_nivel,
)
from .exportes import (
    download_menu_excel,
    download_menu_excel_service,
    download_menu_excel_with_nivel,
    download_modalidad_excel,
)
from .semanal import (
    api_validar_semana,
    api_requerimientos_modalidad,
)
