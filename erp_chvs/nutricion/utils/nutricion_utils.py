"""
Utilidades del módulo de nutrición.

Funciones helper reutilizables.
"""


def calcular_estado_adecuacion(porcentaje: float, nutriente: str, referencia: float = None) -> str:
    """
    Determina el estado de adecuación nutricional.

    Si se provee `referencia` (% esperado según AdecuacionTotalPorcentaje),
    el estado se calcula por proximidad a ese valor de referencia:
    - |diff| ≤ 3 puntos → ÓPTIMO  (verde)
    - |diff| ≤ 5 puntos → AZUL    (azul)
    - |diff| ≤ 7 puntos → ACEPTABLE (amarillo)
    - |diff| > 7 puntos → ALTO    (rojo)

    Sin referencia (fallback legacy):
    - 0-35%: ÓPTIMO (verde)
    - 35.1-70%: ACEPTABLE (amarillo)
    - >70%: ALTO (rojo)

    Args:
        porcentaje: Porcentaje calculado (total / recomendación × 100)
        nutriente: Nombre del nutriente
        referencia: Porcentaje esperado según tabla AdecuacionTotalPorcentaje (opcional)

    Returns:
        str: 'optimo', 'azul', 'aceptable' o 'alto'
    """
    if referencia is not None:
        diff = abs(porcentaje - float(referencia))
        if diff <= 3:
            return 'optimo'      # Verde: ≤3 puntos
        elif diff <= 5:
            return 'azul'        # Azul: 3-5 puntos
        elif diff <= 7:
            return 'aceptable'   # Amarillo: 5-7 puntos
        else:
            return 'alto'        # Rojo: >7 puntos

    # Fallback: lógica original sin referencia
    porcentaje = max(0, min(100, porcentaje))
    if porcentaje <= 35:
        return 'optimo'
    elif porcentaje <= 70:
        return 'aceptable'
    else:
        return 'alto'


def formatear_valor_nutricional(valor: float, nutriente: str) -> str:
    """
    Formatea un valor nutricional con su unidad correspondiente.

    Args:
        valor: Valor numérico del nutriente
        nutriente: Tipo de nutriente

    Returns:
        str: Valor formateado con unidad

    Examples:
        >>> formatear_valor_nutricional(250.5, 'calorias_kcal')
        '250.5 Kcal'
        >>> formatear_valor_nutricional(15.3, 'proteina_g')
        '15.3 g'
    """
    unidades = {
        'calorias_kcal': 'Kcal',
        'proteina_g': 'g',
        'grasa_g': 'g',
        'cho_g': 'g',
        'calcio_mg': 'mg',
        'hierro_mg': 'mg',
        'sodio_mg': 'mg',
        'peso_neto': 'g',
        'peso_bruto': 'g'
    }

    unidad = unidades.get(nutriente, '')
    return f"{valor:.1f} {unidad}".strip()


def validar_rango_porcentaje(porcentaje: float) -> float:
    """
    Valida que un porcentaje esté en el rango válido (0-100).

    Args:
        porcentaje: Valor del porcentaje

    Returns:
        float: Porcentaje validado (limitado a 0-100)

    Examples:
        >>> validar_rango_porcentaje(50)
        50.0
        >>> validar_rango_porcentaje(150)
        100.0
        >>> validar_rango_porcentaje(-10)
        0.0
    """
    return max(0.0, min(100.0, porcentaje))
