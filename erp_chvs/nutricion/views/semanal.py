from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import RequerimientoSemanal, TablaPreparaciones
from ..services.exclusion_service import (
    cargar_sets_exclusion,
    ajustar_componentes_con_exclusion,
)
from ..services.restriccion_subgrupo_service import (
    cargar_restricciones_subgrupo,
    validar_restricciones_subgrupo,
)


@login_required
def api_validar_semana(request):
    """
    Valida si una semana cumple con las frecuencias requeridas por grupo de alimentos.
    Incorpora la lógica de grupos excluyentes: grupos que comparten una cuota semanal.
    """
    try:
        menu_ids_str = request.GET.get('menu_ids', '')
        modalidad_id = request.GET.get('modalidad_id')

        if not menu_ids_str or not modalidad_id:
            return JsonResponse({'error': 'Faltan parámetros: menu_ids y modalidad_id son requeridos'}, status=400)

        menu_ids = [int(id.strip()) for id in menu_ids_str.split(',') if id.strip()]

        if not menu_ids:
            return JsonResponse({'error': 'No se proporcionaron IDs de menús válidos'}, status=400)

        requerimientos = RequerimientoSemanal.objects.filter(
            modalidad__id_modalidades=modalidad_id
        ).select_related('grupo')

        if not requerimientos.exists():
            return JsonResponse({
                'cumple': True,
                'componentes': [],
                'mensaje': 'No hay requerimientos definidos para esta modalidad'
            })

        # menus_por_grupo: {grupo_id: set(menu_ids)} — para contar frecuencias
        menus_por_grupo = {}

        # preparaciones_detalle: {grupo_id: [{preparacion, menu_index}]}
        # Usado por exclusion_service para generar los tooltips
        preparaciones_detalle = {}

        # ingredientes_detalle_por_grupo: {grupo_id: {menu_id: [{'codigo', 'nombre_alimento', 'preparacion', 'menu_index'}]}}
        # Usado por restriccion_subgrupo_service para validar listas blancas
        ingredientes_detalle_por_grupo = {}

        for idx, menu_id in enumerate(menu_ids):
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu_id=menu_id
            ).select_related(
                'id_componente__id_grupo_alimentos'
            ).prefetch_related(
                'ingredientes__id_ingrediente_siesa__id_componente__id_grupo_alimentos'
            )

            grupos_del_menu = set()

            for prep in preparaciones:
                grupo_id = _resolver_grupo_preparacion(prep)

                if grupo_id is None:
                    continue

                # Para el conteo de frecuencias (una preparacion = un día para ese grupo)
                if grupo_id not in grupos_del_menu:
                    grupos_del_menu.add(grupo_id)

                # Para el tooltip de exclusión: acumular preparaciones por grupo
                if grupo_id not in preparaciones_detalle:
                    preparaciones_detalle[grupo_id] = []
                preparaciones_detalle[grupo_id].append({
                    'preparacion': prep.preparacion,
                    'menu_index': idx,  # 0=Lunes…4=Viernes dentro de la semana
                })

                # Para sub-restricciones: recolectar códigos ICBF de ingredientes
                for ing_rel in prep.ingredientes.all():
                    alimento = ing_rel.id_ingrediente_siesa
                    if alimento:
                        (
                            ingredientes_detalle_por_grupo
                            .setdefault(grupo_id, {})
                            .setdefault(menu_id, [])
                            .append({
                                'codigo': alimento.codigo,
                                'nombre_alimento': alimento.nombre_del_alimento,
                                'preparacion': prep.preparacion,
                                'menu_index': idx,
                            })
                        )

            for grupo_id in grupos_del_menu:
                if grupo_id not in menus_por_grupo:
                    menus_por_grupo[grupo_id] = set()
                menus_por_grupo[grupo_id].add(menu_id)

        conteo_grupos = {
            grupo_id: len(menus_set)
            for grupo_id, menus_set in menus_por_grupo.items()
        }

        # ── Resultado base (sin exclusiones) ────────────────────────────────
        grupos_resultado_base = []
        for req in requerimientos:
            grupo_id = req.grupo.id_grupo_alimentos
            requerido = req.frecuencia
            actual = conteo_grupos.get(grupo_id, 0)
            grupos_resultado_base.append({
                'id': grupo_id,
                'grupo': req.grupo.grupo_alimentos,
                'requerido': requerido,
                'actual': actual,
                'cumple': actual >= requerido,
            })

        # ── Ajuste por grupos excluyentes ────────────────────────────────────
        sets_exclusion = cargar_sets_exclusion(modalidad_id)
        grupos_resultado = ajustar_componentes_con_exclusion(
            grupos_resultado_base,
            sets_exclusion,
            preparaciones_detalle,
        )

        # ── Sub-restricciones de alimentos ───────────────────────────────────
        restricciones_subgrupo_cfg = cargar_restricciones_subgrupo(modalidad_id)
        restricciones_subgrupo_resultado = validar_restricciones_subgrupo(
            restricciones_subgrupo_cfg,
            ingredientes_detalle_por_grupo,
        )

        cumple_total = (
            all(comp['cumple'] for comp in grupos_resultado)
            and all(r['cumple'] for r in restricciones_subgrupo_resultado)
        )

        return JsonResponse({
            'cumple': cumple_total,
            'componentes': grupos_resultado,
            'restricciones_subgrupo': restricciones_subgrupo_resultado,
        })

    except ValueError as e:
        return JsonResponse({'error': f'Error en formato de parámetros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al validar semana: {str(e)}'}, status=500)


def _resolver_grupo_preparacion(prep):
    """
    Determina el grupo de alimentos de una preparación.
    Prioridad 1: id_componente asignado directamente a la preparación.
    Prioridad 2: componente del primer ingrediente que tenga grupo asignado.
    Devuelve el id_grupo_alimentos (str) o None.
    """
    if prep.id_componente and prep.id_componente.id_grupo_alimentos:
        return prep.id_componente.id_grupo_alimentos.id_grupo_alimentos

    for ingrediente_rel in prep.ingredientes.all():
        alimento = ingrediente_rel.id_ingrediente_siesa
        if alimento and alimento.id_componente and alimento.id_componente.id_grupo_alimentos:
            return alimento.id_componente.id_grupo_alimentos.id_grupo_alimentos

    return None


@login_required
def api_requerimientos_modalidad(request):
    """
    Obtiene los requerimientos semanales de una modalidad.
    """
    try:
        modalidad_id = request.GET.get('modalidad_id')

        if not modalidad_id:
            return JsonResponse({'error': 'Falta parámetro: modalidad_id es requerido'}, status=400)

        requerimientos = RequerimientoSemanal.objects.filter(
            modalidad__id_modalidades=modalidad_id
        ).select_related('grupo')

        resultado = []
        for req in requerimientos:
            resultado.append({
                'grupo_id': req.grupo.id_grupo_alimentos,
                'grupo_nombre': req.grupo.grupo_alimentos,
                'frecuencia': req.frecuencia
            })

        return JsonResponse({
            'modalidad_id': modalidad_id,
            'requerimientos': resultado
        })

    except Exception as e:
        return JsonResponse({'error': f'Error al obtener requerimientos: {str(e)}'}, status=500)
