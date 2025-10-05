"""
Servicios del módulo de nutrición.

Este paquete contiene la lógica de negocio separada de las vistas,
siguiendo el principio de Single Responsibility.
"""

from .calculo_service import CalculoService
from .analisis_service import AnalisisNutricionalService
from .menu_service import MenuService
from .preparacion_service import PreparacionService
from .ingrediente_service import IngredienteService
from .programa_service import ProgramaService

__all__ = [
    'CalculoService',
    'AnalisisNutricionalService',
    'MenuService',
    'PreparacionService',
    'IngredienteService',
    'ProgramaService',
]
