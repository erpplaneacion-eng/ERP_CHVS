import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from principal.models import RegistroActividad

from ..services.copiar_menu_service import CopiarMenuService

logger = logging.getLogger(__name__)


@login_required
def api_copiar_menu_programas(request):
    """
    GET /nutricion/api/copiar-menu/programas/
    Parametro opcional: excluir_programa_id

    Retorna programas con al menos 1 menu configurado.
    """
    excluir = request.GET.get('excluir_programa_id')
    try:
        programas = CopiarMenuService.get_programas_con_menus(
            excluir_programa_id=int(excluir) if excluir else None
        )
        return JsonResponse({'programas': programas})
    except Exception as e:
        logger.exception('Error en api_copiar_menu_programas')
        return JsonResponse({'programas': [], 'error': str(e)})


@login_required
def api_copiar_menu_lista(request):
    """
    GET /nutricion/api/copiar-menu/menus/?programa_id=X

    Retorna los menus de un programa con conteo de preparaciones.
    """
    programa_id = request.GET.get('programa_id')
    if not programa_id:
        return JsonResponse({'menus': [], 'error': 'programa_id requerido'}, status=400)
    try:
        menus = CopiarMenuService.get_menus_de_programa(int(programa_id))
        return JsonResponse({'menus': menus})
    except Exception as e:
        logger.exception('Error en api_copiar_menu_lista')
        return JsonResponse({'menus': [], 'error': str(e)})


@login_required
def api_copiar_menu_detalle(request):
    """
    GET /nutricion/api/copiar-menu/detalle/?menu_id=X

    Retorna preparaciones e ingredientes del menu indicado.
    """
    menu_id = request.GET.get('menu_id')
    if not menu_id:
        return JsonResponse({'error': 'menu_id requerido'}, status=400)
    try:
        detalle = CopiarMenuService.get_detalle_menu(int(menu_id))
        if detalle is None:
            return JsonResponse({'error': 'Menu no encontrado'}, status=404)
        return JsonResponse(detalle)
    except Exception as e:
        logger.exception('Error en api_copiar_menu_detalle')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def api_copiar_menu_ejecutar(request):
    """
    POST /nutricion/api/copiar-menu/ejecutar/
    Body: {
        menu_destino_id: int,
        preparaciones: [
            {nombre, id_componente, ingredientes: [{codigo, gramaje, id_componente}]}
        ]
    }

    Copia las preparaciones seleccionadas al menu destino,
    reemplazando su contenido previo.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        menu_destino_id = data.get('menu_destino_id')
        preparaciones = data.get('preparaciones', [])

        if not menu_destino_id:
            return JsonResponse({'error': 'menu_destino_id requerido'}, status=400)
        if not preparaciones:
            return JsonResponse({'error': 'Debe incluir al menos una preparacion'}, status=400)

        resultado = CopiarMenuService.ejecutar_copia(
            menu_destino_id=int(menu_destino_id),
            preparaciones_seleccionadas=preparaciones,
        )

        RegistroActividad.registrar(
            request, 'nutricion', 'copiar_menu',
            f"Menu destino: {menu_destino_id} | "
            f"Preparaciones: {resultado['preparaciones']} | "
            f"Ingredientes: {resultado['ingredientes']}"
        )

        return JsonResponse({'success': True, **resultado})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.exception('Error en api_copiar_menu_ejecutar')
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)


@login_required
def api_buscar_alimentos_copiar_menu(request):
    """
    GET /nutricion/api/copiar-menu/buscar-alimento/?q=texto

    Buscador de alimentos ICBF para agregar ingredientes en el wizard.
    Minimo 2 caracteres.
    """
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'alimentos': []})

    alimentos = CopiarMenuService.buscar_alimentos(q)
    return JsonResponse({'alimentos': alimentos})
