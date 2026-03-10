from django.db.models import Count

from nutricion.models import (
    TablaMenus, TablaPreparacionIngredientes, ComponentesModalidades
)
from principal.models import ModalidadesDeConsumo


def obtener_contexto_modalidad(modalidad_id) -> dict:
    modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

    return {
        'modalidad': {
            'id': str(modalidad.id_modalidades),
            'nombre': modalidad.modalidad,
        },
        'menus_similares': _obtener_menus_similares(modalidad_id),
        'componentes_validos': _obtener_componentes_modalidad(modalidad_id),
        'top_ingredientes': _obtener_top_ingredientes(modalidad_id),
    }


def _obtener_menus_similares(modalidad_id) -> list:
    menus = TablaMenus.objects.filter(
        id_modalidad=modalidad_id
    ).prefetch_related(
        'preparaciones__ingredientes__id_ingrediente_siesa',
        'preparaciones__id_componente'
    ).order_by('-fecha_creacion')[:5]

    resultado = []
    for m in menus:
        preps = []
        for p in m.preparaciones.all():
            ingredientes = [
                {
                    'codigo': ing.id_ingrediente_siesa.codigo,
                    'nombre': ing.id_ingrediente_siesa.nombre_del_alimento,
                }
                for ing in p.ingredientes.all()
            ]
            preps.append({
                'nombre': p.preparacion,
                'componente': p.id_componente.componente if p.id_componente else None,
                'ingredientes': ingredientes,
            })
        if preps:
            resultado.append({'menu': m.menu, 'preparaciones': preps})
    return resultado


def _obtener_componentes_modalidad(modalidad_id) -> list:
    componentes = ComponentesModalidades.objects.filter(
        id_modalidad=modalidad_id
    ).values(
        'id_componente__id_componente',
        'id_componente__componente',
        'id_componente__id_grupo_alimentos__grupo_alimentos',
    )
    return [
        {
            'id': c['id_componente__id_componente'],
            'nombre': c['id_componente__componente'],
            'grupo': c['id_componente__id_grupo_alimentos__grupo_alimentos'],
        }
        for c in componentes
    ]


def _obtener_top_ingredientes(modalidad_id, limit=50) -> list:
    ingredientes = TablaPreparacionIngredientes.objects.filter(
        id_preparacion__id_menu__id_modalidad=modalidad_id
    ).values(
        'id_ingrediente_siesa__codigo',
        'id_ingrediente_siesa__nombre_del_alimento',
    ).annotate(
        frecuencia=Count('id')
    ).order_by('-frecuencia')[:limit]

    return [
        {
            'codigo': i['id_ingrediente_siesa__codigo'],
            'nombre': i['id_ingrediente_siesa__nombre_del_alimento'],
        }
        for i in ingredientes
    ]
