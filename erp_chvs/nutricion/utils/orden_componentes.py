"""
Orden de componentes por modalidad para exportación Excel.

Define el orden en que deben aparecer las preparaciones en los Excel de
análisis nutricional y guías de preparación, agrupadas por componente.

Las modalidades no listadas usan orden alfabético (fallback).
"""

# Mapa: id_modalidades → lista ordenada de id_componente
# Preparaciones con componentes fuera de la lista van al final (alfabéticamente).
ORDEN_COMPONENTES_POR_MODALIDAD = {
    # COMPLEMENTO AM/PM PREPARADO  y  COMPLEMENTO PM PREPARADO
    '20501': ['com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com15'],
    '20507': ['com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com15'],

    # COMPLEMENTO AM/PM INDUSTRIALIZADO  y  REFUERZO COMPLEMENTO AM/PM INDUSTRIALIZADO
    '20502':  ['com11', 'com3', 'com12', 'com13'],
    '020511': ['com11', 'com3', 'com12', 'com13'],

    # COMPLEMENTO AM/PM JORNADA UNICA  y  REFUERZO COMPLEMENTO AM/PM PREPARADO
    '20503': ['com2', 'com7', 'com8', 'com14', 'com11', 'com5', 'com6', 'com15'],
    '20510': ['com2', 'com7', 'com8', 'com14', 'com11', 'com5', 'com6', 'com15'],
}


def _indice_componente(componente_id, modalidad_id):
    """Retorna la posición del componente en el orden definido para la modalidad.
    Componentes no listados retornan 999 (van al final).
    """
    orden = ORDEN_COMPONENTES_POR_MODALIDAD.get(str(modalidad_id or ''), [])
    try:
        return orden.index(str(componente_id or ''))
    except ValueError:
        return 999


def sort_preparaciones_objetos(preparaciones, modalidad_id):
    """Ordena una lista de objetos TablaPreparaciones por componente según la
    modalidad. Dentro del mismo componente, ordena alfabéticamente por nombre.
    """
    return sorted(
        preparaciones,
        key=lambda p: (
            _indice_componente(p.id_componente_id, modalidad_id),
            (p.preparacion or '').lower(),
        ),
    )


def sort_preparaciones_dicts(preparaciones, modalidad_id):
    """Ordena una lista de dicts de preparaciones por componente según la
    modalidad. Cada dict debe tener 'id_componente_id' y 'nombre'.
    """
    return sorted(
        preparaciones,
        key=lambda p: (
            _indice_componente(p.get('id_componente_id', ''), modalidad_id),
            (p.get('nombre') or '').lower(),
        ),
    )
