from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import RequerimientoSemanal, TablaPreparaciones


@login_required
def api_validar_semana(request):
    """
    Valida si una semana cumple con las frecuencias requeridas por grupo de alimentos.
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

        menus_por_grupo = {}

        for menu_id in menu_ids:
            # Obtener preparaciones con sus ingredientes y el componente → grupo
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu_id=menu_id
            ).select_related(
                'id_componente__id_grupo_alimentos'
            ).prefetch_related(
                'ingredientes__id_ingrediente_siesa__id_componente__id_grupo_alimentos'
            )

            grupos_del_menu = set()

            for prep in preparaciones:
                # 1. Intentar usar el componente asignado a la preparación (prioridad manual)
                if prep.id_componente and prep.id_componente.id_grupo_alimentos:
                    grupos_del_menu.add(prep.id_componente.id_grupo_alimentos.id_grupo_alimentos)

                # 2. Si no tiene, buscar en sus ingredientes
                else:
                    for ingrediente_rel in prep.ingredientes.all():
                        alimento = ingrediente_rel.id_ingrediente_siesa
                        if alimento and alimento.id_componente and alimento.id_componente.id_grupo_alimentos:
                            grupos_del_menu.add(alimento.id_componente.id_grupo_alimentos.id_grupo_alimentos)

            for grupo_id in grupos_del_menu:
                if grupo_id not in menus_por_grupo:
                    menus_por_grupo[grupo_id] = set()
                menus_por_grupo[grupo_id].add(menu_id)

        conteo_grupos = {
            grupo_id: len(menus_set)
            for grupo_id, menus_set in menus_por_grupo.items()
        }

        grupos_resultado = []
        cumple_total = True

        for req in requerimientos:
            grupo_id = req.grupo.id_grupo_alimentos
            grupo_nombre = req.grupo.grupo_alimentos
            requerido = req.frecuencia
            actual = conteo_grupos.get(grupo_id, 0)
            cumple = actual >= requerido

            if not cumple:
                cumple_total = False

            grupos_resultado.append({
                'id': grupo_id,
                'grupo': grupo_nombre,
                'requerido': requerido,
                'actual': actual,
                'cumple': cumple
            })

        return JsonResponse({
            'cumple': cumple_total,
            'componentes': grupos_resultado
        })

    except ValueError as e:
        return JsonResponse({'error': f'Error en formato de parámetros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al validar semana: {str(e)}'}, status=500)


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
