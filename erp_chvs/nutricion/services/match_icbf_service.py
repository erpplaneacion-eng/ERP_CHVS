"""
Servicio para el match ICBF → Compras.

Granularidad: (ingrediente_icbf, programa, menú) → 1 producto de compras.
"""
from ..models import (
    TablaPreparacionIngredientes,
    EquivalenciaICBFCompras,
)


def obtener_dashboard_match(programa_id):
    """
    Devuelve el contexto necesario para renderizar el dashboard de match.

    Returns:
        {
            'filas': [...],     # Lista de ingredientes con sus menús y matches
            'total': int,       # Total de ingredientes únicos
            'con_match': int,   # Ingredientes con todos los menús asignados
            'sin_match': int,   # Ingredientes con al menos un menú sin asignar
        }
    """
    ingredientes_data = _obtener_ingredientes_programa(programa_id)

    # Índice de matches por (codigo_icbf, menu_id)
    matches_dict = {
        (eq.id_alimento_icbf_id, eq.id_menu_id): eq
        for eq in EquivalenciaICBFCompras.objects.filter(
            id_programa_id=programa_id, activo=True
        ).select_related('id_ingrediente_compras', 'id_menu')
    }

    filas = []
    total_ingredientes = 0
    total_asignados_completos = 0

    for datos in ingredientes_data:
        alimento = datos['alimento']
        menus_filas = []
        asignados = 0

        for menu_data in datos['menus']:
            match = matches_dict.get((alimento.codigo, menu_data['menu_id']))
            if match:
                asignados += 1
            menus_filas.append({
                'menu_id':       menu_data['menu_id'],
                'menu_num':      menu_data['menu_num'],
                'preparaciones': menu_data['preparaciones'],
                'match':         match,
            })

        total_menus = len(menus_filas)
        completo = (asignados == total_menus)

        total_ingredientes += 1
        if completo:
            total_asignados_completos += 1

        filas.append({
            'alimento':    alimento,
            'menus':       menus_filas,
            'total_menus': total_menus,
            'asignados':   asignados,
            'tiene_match': asignados > 0,
            'completo':    completo,
        })

    return {
        'filas':     filas,
        'total':     total_ingredientes,
        'con_match': total_asignados_completos,
        'sin_match': total_ingredientes - total_asignados_completos,
    }


def _obtener_ingredientes_programa(programa_id):
    """
    Devuelve los ingredientes ICBF usados en el programa, agrupados por alimento.
    Cada entrada incluye la lista de menús donde aparece (deduplicada).

    Returns:
        [{'alimento': TablaAlimentos2018Icbf,
          'menus': [{'menu_id', 'menu_num', 'preparaciones': [str]}, ...]}, ...]
    """
    usos_qs = (
        TablaPreparacionIngredientes.objects
        .filter(id_preparacion__id_menu__id_contrato_id=programa_id)
        .select_related(
            'id_ingrediente_siesa',
            'id_ingrediente_siesa__id_componente',
            'id_preparacion',
            'id_preparacion__id_menu',
        )
        .order_by(
            'id_ingrediente_siesa__nombre_del_alimento',
            'id_preparacion__id_menu__menu',
            'id_preparacion__preparacion',
        )
    )

    # grupos: {codigo: {'alimento': obj, 'menus': {menu_id: {'menu_num', 'preps': set()}}}}
    grupos = {}
    for uso in usos_qs:
        alimento = uso.id_ingrediente_siesa
        if not alimento:
            continue
        codigo = alimento.codigo
        if codigo not in grupos:
            grupos[codigo] = {'alimento': alimento, 'menus': {}}
        menu = uso.id_preparacion.id_menu
        if menu.id_menu not in grupos[codigo]['menus']:
            grupos[codigo]['menus'][menu.id_menu] = {
                'menu_id':  menu.id_menu,
                'menu_num': menu.menu,
                'preps':    set(),
            }
        grupos[codigo]['menus'][menu.id_menu]['preps'].add(uso.id_preparacion.preparacion)

    resultado = []
    for datos in sorted(grupos.values(), key=lambda x: x['alimento'].nombre_del_alimento):
        menus = sorted(
            [
                {
                    'menu_id':       m['menu_id'],
                    'menu_num':      m['menu_num'],
                    'preparaciones': sorted(m['preps']),
                }
                for m in datos['menus'].values()
            ],
            key=lambda m: m['menu_num']
        )
        resultado.append({'alimento': datos['alimento'], 'menus': menus})

    return resultado
