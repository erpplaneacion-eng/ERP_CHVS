"""
restriccion_subgrupo_service.py
-------------------------------
Lógica para sub-restricciones de alimentos dentro de un grupo por modalidad.

Una sub-restricción exige que, de todas las apariciones de un grupo en la semana,
al menos N de ellas usen un alimento de una lista blanca específica.

Ejemplo (modalidad 20503):
  G4 aparece 5 veces/semana, pero:
    - Al menos 1 debe ser "Huevo de gallina, entero, crudo"  (G4 Huevo)
    - Al menos 2 deben ser una leguminosa (Lenteja, Arveja...) (G4 Leguminosas)
"""

from ..models import RestriccionAlimentoSubgrupo


# ─────────────────────────────────────────────────────────────────────────────
# Carga de configuración
# ─────────────────────────────────────────────────────────────────────────────

def cargar_restricciones_subgrupo(modalidad_id):
    """
    Carga las sub-restricciones de la modalidad con sus listas blancas.

    Returns:
        list[dict] con:
            id               : int
            nombre           : str
            grupo_id         : str
            grupo_nombre     : str
            frecuencia       : int
            codigos_validos  : set[str]   — códigos de TablaAlimentos2018Icbf
            nombres_validos  : list[str]  — para mostrar en UI
    """
    restricciones = (
        RestriccionAlimentoSubgrupo.objects
        .filter(modalidad__id_modalidades=modalidad_id)
        .select_related('grupo')
        .prefetch_related('alimentos__alimento')
    )

    resultado = []
    for r in restricciones:
        codigos = set()
        nombres = []
        for ae in r.alimentos.all():
            codigos.add(ae.alimento.codigo)
            nombres.append(ae.alimento.nombre_del_alimento)
        resultado.append({
            'id': r.id,
            'nombre': r.nombre,
            'grupo_id': r.grupo.id_grupo_alimentos,
            'grupo_nombre': r.grupo.grupo_alimentos,
            'frecuencia': r.frecuencia,
            'codigos_validos': codigos,
            'nombres_validos': sorted(nombres),
        })
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# Validación
# ─────────────────────────────────────────────────────────────────────────────

def validar_restricciones_subgrupo(restricciones, ingredientes_detalle_por_grupo):
    """
    Evalúa cuántos menús de la semana usan un alimento válido para cada sub-restricción.

    Args:
        restricciones (list[dict]):
            Salida de cargar_restricciones_subgrupo().

        ingredientes_detalle_por_grupo (dict):
            {grupo_id: {menu_id: [{'codigo': str,
                                   'nombre_alimento': str,
                                   'preparacion': str,
                                   'menu_index': int}]}}
            Recopilado en semanal.py al recorrer las preparaciones.

    Returns:
        list[dict] con:
            id               : int
            nombre           : str
            grupo_id         : str
            frecuencia       : int
            actual           : int    — menús únicos que usaron un alimento válido
            cumple           : bool
            nombres_validos  : list[str]
            detalle          : list[dict]  — [{preparacion, menu_index, alimento_usado}]
    """
    if not restricciones:
        return []

    resultado = []
    for r in restricciones:
        grupo_id = r['grupo_id']
        codigos_validos = r['codigos_validos']
        menús_por_grupo = ingredientes_detalle_por_grupo.get(grupo_id, {})

        menus_que_cumplen = set()   # menu_ids únicos con al menos un alimento válido
        detalle = []

        for menu_id, ingredientes in menús_por_grupo.items():
            for ing in ingredientes:
                if ing['codigo'] in codigos_validos:
                    menus_que_cumplen.add(menu_id)
                    detalle.append({
                        'preparacion': ing['preparacion'],
                        'menu_index': ing['menu_index'],
                        'alimento_usado': ing['nombre_alimento'],
                    })
                    # Solo registrar el primer match por (preparacion, menu) para el tooltip
                    break

        actual = len(menus_que_cumplen)
        resultado.append({
            'id': r['id'],
            'nombre': r['nombre'],
            'grupo_id': grupo_id,
            'grupo_nombre': r['grupo_nombre'],
            'frecuencia': r['frecuencia'],
            'actual': actual,
            'cumple': actual >= r['frecuencia'],
            'nombres_validos': r['nombres_validos'],
            'detalle': sorted(detalle, key=lambda x: x['menu_index']),
        })

    return resultado
