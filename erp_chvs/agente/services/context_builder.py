import random

from django.db.models import Count

from nutricion.models import (
    TablaMenus, TablaPreparacionIngredientes, ComponentesModalidades,
    TablaAlimentos2018Icbf,
)
from principal.models import ModalidadesDeConsumo


def obtener_contexto_modalidad(modalidad_id) -> dict:
    modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)
    componentes = _obtener_componentes_modalidad(modalidad_id)

    return {
        'modalidad': {
            'id': str(modalidad.id_modalidades),
            'nombre': modalidad.modalidad,
        },
        'menus_similares': _obtener_menus_similares(modalidad_id),
        'componentes_validos': componentes,
        'ingredientes_por_componente': _obtener_ingredientes_por_componente(modalidad_id, componentes),
        'catalogo_soporte': _obtener_catalogo_soporte(modalidad_id),
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
                'componente_id': p.id_componente.id_componente if p.id_componente else None,
                'componente': p.id_componente.componente if p.id_componente else None,
                'ingredientes': ingredientes,
            })
        if preps:
            resultado.append({'menu': m.menu, 'preparaciones': preps})
    return resultado


def _obtener_componentes_modalidad(modalidad_id) -> list:
    componentes = ComponentesModalidades.objects.filter(
        id_modalidad=modalidad_id
    ).select_related(
        'id_componente__id_grupo_alimentos'
    ).order_by('id_componente__componente')
    return [
        {
            'id': c.id_componente.id_componente,
            'nombre': c.id_componente.componente,
            'grupo': c.id_componente.id_grupo_alimentos.grupo_alimentos,
        }
        for c in componentes
    ]


def _obtener_ingredientes_por_componente(modalidad_id, componentes: list) -> dict:
    """
    Para cada componente, retorna los ingredientes PRINCIPALES más usados
    en preparaciones de ese componente (top 8 + 2 aleatorios para variedad).
    Estos definen el ingrediente estrella de cada preparación.
    """
    resultado = {}
    for comp in componentes:
        comp_id = comp['id']

        top_qs = TablaPreparacionIngredientes.objects.filter(
            id_preparacion__id_menu__id_modalidad=modalidad_id,
            id_preparacion__id_componente=comp_id,
        ).values(
            'id_ingrediente_siesa__codigo',
            'id_ingrediente_siesa__nombre_del_alimento',
        ).annotate(
            frecuencia=Count('id')
        ).order_by('-frecuencia')

        top_list = list(top_qs)
        top_8 = top_list[:8]
        codigos_top = {i['id_ingrediente_siesa__codigo'] for i in top_8}

        resto = [i for i in top_list[8:] if i['id_ingrediente_siesa__codigo'] not in codigos_top]
        extras = random.sample(resto, min(2, len(resto))) if resto else []

        resultado[comp_id] = [
            {
                'codigo': i['id_ingrediente_siesa__codigo'],
                'nombre': i['id_ingrediente_siesa__nombre_del_alimento'],
            }
            for i in top_8 + extras
        ]

    return resultado


def _obtener_catalogo_soporte(modalidad_id, limit=40) -> list:
    """
    Catálogo general de ingredientes usados en la modalidad.
    Incluye condimentos, aceites, especias, verduras de guiso y otros
    ingredientes de soporte que acompañan al ingrediente principal.
    Top 20 más frecuentes + muestra aleatoria por grupo para variedad.
    """
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

    # Muestra aleatoria por grupo para cubrir variedad de soporte
    grupos: dict = {}
    for item in top_list[20:]:
        grupo = item['id_ingrediente_siesa__id_componente__id_grupo_alimentos__grupo_alimentos'] or 'Sin grupo'
        grupos.setdefault(grupo, []).append(item)

    rotacion = []
    for items_grupo in grupos.values():
        rotacion.extend(random.sample(items_grupo, min(2, len(items_grupo))))

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
