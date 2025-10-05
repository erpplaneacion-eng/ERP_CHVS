"""
Utilidades del módulo de nutrición.

Funciones helper reutilizables.
"""


def calcular_estado_adecuacion(porcentaje: float, nutriente: str) -> str:
    """
    Determina el estado de adecuación nutricional según el porcentaje alcanzado.

    RANGOS DE EVALUACIÓN (válidos para todos los nutrientes):
    - 0-35%: ÓPTIMO (verde) - Aporte bajo pero seguro
    - 35.1-70%: ACEPTABLE (amarillo) - Aporte moderado
    - >70%: ALTO (rojo) - Aporte elevado, cerca del límite máximo

    NOTA IMPORTANTE:
    - El 100% representa el MÁXIMO permitido según ICBF 2018
    - Para sodio, valores bajos son mejores (pero el rango de colores es el mismo)
    - Para otros nutrientes, alcanzar valores altos es aceptable pero no debe exceder 100%

    Args:
        porcentaje: Porcentaje de adecuación (0-100)
        nutriente: Nombre del nutriente evaluado

    Returns:
        str: Estado ('optimo', 'aceptable', 'alto')

    Examples:
        >>> calcular_estado_adecuacion(25, 'calorias_kcal')
        'optimo'
        >>> calcular_estado_adecuacion(50, 'proteina_g')
        'aceptable'
        >>> calcular_estado_adecuacion(85, 'sodio_mg')
        'alto'
    """
    # Validar entrada
    porcentaje = max(0, min(100, porcentaje))

    # Rangos uniformes para todos los nutrientes
    if porcentaje <= 35:
        return 'optimo'      # 0-35%: Verde
    elif porcentaje <= 70:
        return 'aceptable'   # 35.1-70%: Amarillo
    else:
        return 'alto'        # >70%: Rojo


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
