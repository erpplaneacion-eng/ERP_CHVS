from .core import (
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
from .copiar_menu_api import (
    api_copiar_menu_programas,
    api_copiar_menu_lista,
    api_copiar_menu_detalle,
    api_copiar_menu_ejecutar,
    api_buscar_alimentos_copiar_menu,
)
from .preparaciones_api import (
    lista_preparaciones,
    api_preparaciones,
    api_preparacion_detail,
    api_copiar_preparacion,
    api_preparaciones_por_modalidad,
    api_menus_misma_modalidad_para_copia,
    api_preparaciones_por_menu_para_copia,
    api_buscar_preparaciones_modalidad,
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
    download_guias_preparacion_excel,
    download_ciclo_menus_pdf,
)
from .semanal import (
    api_validar_semana,
    api_requerimientos_modalidad,
)
from .firmas import (
    firmas_contrato,
)
from .minuta_patron_rangos import (
    lista_minuta_patron_rangos,
    editar_minuta_patron_rango,
    eliminar_minuta_patron_rango,
)
from .match_icbf import (
    vista_match_icbf,
    api_productos_siesa,
    api_guardar_match,
    api_eliminar_match,
    api_productos_siesa_crud,
    api_producto_siesa_detail,
)
