"""
exclusion_service.py
--------------------
Lógica para grupos de alimentos excluyentes por modalidad.

Un "set excluyente" es un conjunto de grupos que comparten una cuota semanal:
  - G4 + G6 deben aparecer 2 veces/semana EN TOTAL (no 2 veces cada uno).
  - Si G4 aparece 1 vez, G6 solo puede/necesita aparecer 1 vez más.
  - Si G4 aparece 2 veces, G6 no necesita aparecer (cuota ya cubierta).

Este módulo:
  1. Carga los sets de exclusión para una modalidad.
  2. Ajusta el resultado del validador semanal (requerido_efectivo, cumple, tooltip).
"""

from ..models import GrupoExcluyenteSet

# ─────────────────────────────────────────────────────────────────────────────
# Carga de configuración
# ─────────────────────────────────────────────────────────────────────────────

def cargar_sets_exclusion(modalidad_id):
    """
    Devuelve la configuración de sets excluyentes para una modalidad.

    Returns:
        list[dict] — cada dict tiene:
            id                  : int
            nombre              : str
            frecuencia_compartida: int
            grupos              : list[dict] con {'id': str, 'nombre': str}
    """
    sets = (
        GrupoExcluyenteSet.objects
        .filter(modalidad__id_modalidades=modalidad_id)
        .prefetch_related('miembros__grupo')
    )

    resultado = []
    for s in sets:
        grupos_info = [
            {
                'id': m.grupo.id_grupo_alimentos,
                'nombre': m.grupo.grupo_alimentos,
            }
            for m in s.miembros.all()
        ]
        resultado.append({
            'id': s.id,
            'nombre': s.nombre,
            'frecuencia_compartida': s.frecuencia_compartida,
            'grupos': grupos_info,          # [{id, nombre}, ...]
            'grupos_ids': {g['id'] for g in grupos_info},
        })
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# Ajuste de resultados del validador
# ─────────────────────────────────────────────────────────────────────────────

def ajustar_componentes_con_exclusion(componentes, sets_exclusion, preparaciones_detalle):
    """
    Ajusta la lista de componentes del validador semanal para reflejar
    la lógica de grupos excluyentes.

    Args:
        componentes (list[dict]):
            Resultado base del validador. Cada dict tiene al menos:
            {'id', 'grupo', 'requerido', 'actual', 'cumple'}

        sets_exclusion (list[dict]):
            Salida de cargar_sets_exclusion().

        preparaciones_detalle (dict):
            {grupo_id: [{'preparacion': str, 'menu_index': int}, ...]}
            Detalle de qué preparaciones (y en qué día) cubrieron cada grupo.

    Returns:
        list[dict] — mismos campos que componentes, con campos adicionales
        por grupo excluyente:
            requerido_efectivo  : int  — cuánto debe aportar AÚN este grupo
            exclusion           : dict | None — datos para el tooltip
    """
    if not sets_exclusion:
        # Sin exclusiones: devolver con campo exclusion=None para uniformidad
        return [{**c, 'requerido_efectivo': c['requerido'], 'exclusion': None}
                for c in componentes]

    # Mapa rápido: grupo_id → set config
    grupo_a_set = {}
    for s in sets_exclusion:
        for g in s['grupos']:
            grupo_a_set[g['id']] = s

    # Mapa rápido: grupo_id → actual count
    conteo_actual = {comp['id']: comp['actual'] for comp in componentes}

    resultado = []
    for comp in componentes:
        grupo_id = comp['id']

        if grupo_id not in grupo_a_set:
            resultado.append({**comp, 'requerido_efectivo': comp['requerido'], 'exclusion': None})
            continue

        s = grupo_a_set[grupo_id]
        grupos_hermanos = [g for g in s['grupos'] if g['id'] != grupo_id]

        # Cuánto aportaron los grupos hermanos
        cuota_hermanos = sum(conteo_actual.get(g['id'], 0) for g in grupos_hermanos)
        cuota_propia = comp['actual']
        cuota_total_usada = cuota_propia + cuota_hermanos

        # Cuánto queda por aportar ESTE grupo (restando lo que ya pusieron los hermanos)
        requerido_efectivo = max(0, s['frecuencia_compartida'] - cuota_hermanos)

        # El set cumple cuando la suma combinada llega a la cuota compartida
        cumple_set = cuota_total_usada >= s['frecuencia_compartida']

        # Preparaciones de los grupos hermanos (para el tooltip)
        aporte_hermanos = _recopilar_aporte_hermanos(
            grupos_hermanos, preparaciones_detalle
        )

        resultado.append({
            **comp,
            'cumple': cumple_set,
            'requerido_efectivo': requerido_efectivo,
            'exclusion': {
                'set_id': s['id'],
                'set_nombre': s['nombre'],
                'cuota_compartida': s['frecuencia_compartida'],
                'cuota_total_usada': cuota_total_usada,
                'cuota_hermanos': cuota_hermanos,
                'grupos_hermanos': [
                    {'id': g['id'], 'nombre': g['nombre']}
                    for g in grupos_hermanos
                ],
                'aporte_hermanos': aporte_hermanos,
            },
        })

    return resultado


def _recopilar_aporte_hermanos(grupos_hermanos, preparaciones_detalle):
    """
    Recopila las preparaciones de los grupos hermanos para mostrar en tooltip.

    Returns:
        list[dict]: [{'grupo_id', 'grupo_nombre', 'preparacion', 'menu_index'}, ...]
    """
    aporte = []
    vistos = set()  # evitar duplicados (preparacion, grupo, dia)

    for g in grupos_hermanos:
        for item in preparaciones_detalle.get(g['id'], []):
            clave = (g['id'], item['preparacion'], item['menu_index'])
            if clave in vistos:
                continue
            vistos.add(clave)
            aporte.append({
                'grupo_id': g['id'],
                'grupo_nombre': g['nombre'],
                'preparacion': item['preparacion'],
                'menu_index': item['menu_index'],
            })

    # Ordenar por día (menu_index) para presentación coherente
    aporte.sort(key=lambda x: x['menu_index'])
    return aporte
