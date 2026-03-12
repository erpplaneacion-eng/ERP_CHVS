import random

from django.db.models import Count

from nutricion.models import (
    TablaMenus, TablaPreparacionIngredientes, ComponentesModalidades,
    TablaAlimentos2018Icbf,
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
    # Muestra aleatoria de hasta 5 menús para no sesgar siempre hacia los más recientes
    ids = list(
        TablaMenus.objects.filter(id_modalidad=modalidad_id)
        .values_list('id_menu', flat=True)
    )
    ids_muestra = random.sample(ids, min(5, len(ids))) if ids else []
    menus = TablaMenus.objects.filter(id_menu__in=ids_muestra).prefetch_related(
        'preparaciones__ingredientes__id_ingrediente_siesa',
        'preparaciones__id_componente'
    )

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
    # Top 20 más usados (ancla de calidad) + muestra aleatoria por grupo para forzar variedad
    top_qs = TablaPreparacionIngredientes.objects.filter(
        id_preparacion__id_menu__id_modalidad=modalidad_id
    ).values(
        'id_ingrediente_siesa__codigo',
        'id_ingrediente_siesa__nombre_del_alimento',
        'id_ingrediente_siesa__id_componente__id_grupo_alimentos__grupo_alimentos',
    ).annotate(
        frecuencia=Count('id')
    ).order_by('-frecuencia')

    top_list = list(top_qs)
    top_20 = top_list[:20]
    codigos_top = {i['id_ingrediente_siesa__codigo'] for i in top_20}

    # Agrupar el resto por grupo de alimentos y tomar 1-2 aleatorios por grupo
    grupos: dict = {}
    for item in top_list[20:]:
        grupo = item['id_ingrediente_siesa__id_componente__id_grupo_alimentos__grupo_alimentos'] or 'Sin grupo'
        grupos.setdefault(grupo, []).append(item)

    rotacion = []
    for items_grupo in grupos.values():
        n = min(2, len(items_grupo))
        rotacion.extend(random.sample(items_grupo, n))

    # Mezclar rotación y completar hasta el límite
    random.shuffle(rotacion)
    extras = [i for i in rotacion if i['id_ingrediente_siesa__codigo'] not in codigos_top]
    combinado = top_20 + extras[:limit - len(top_20)]

    return [
        {
            'codigo': i['id_ingrediente_siesa__codigo'],
            'nombre': i['id_ingrediente_siesa__nombre_del_alimento'],
        }
        for i in combinado
    ]
