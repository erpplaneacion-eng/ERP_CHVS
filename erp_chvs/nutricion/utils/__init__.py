"""
Utilidades del módulo de nutrición.

Funciones helper y utilidades generales.
"""

from .nutricion_utils import (
    calcular_estado_adecuacion,
    formatear_valor_nutricional,
)

__all__ = [
    'calcular_estado_adecuacion',
    'formatear_valor_nutricional',
]
