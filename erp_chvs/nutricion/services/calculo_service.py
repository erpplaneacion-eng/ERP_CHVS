"""
Servicio de Cálculos Nutricionales.

Contiene toda la lógica pura de cálculos nutricionales,
sin dependencias de Django (funciones puras, fáciles de testear).
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple


class CalculoService:
    """
    Servicio para cálculos nutricionales puros.

    Todas las funciones son estáticas y puras (sin efectos secundarios),
    lo que facilita el testing y la reutilización.
    """

    # =================== CÁLCULOS DE PESOS ===================

    @staticmethod
    def calcular_peso_bruto(peso_neto: float, parte_comestible: float) -> float:
        """
        Calcula el peso bruto a partir del peso neto y parte comestible.

        Fórmula: Peso Bruto = (Peso Neto × 100) / % Parte Comestible

        Args:
            peso_neto: Peso neto en gramos
            parte_comestible: Porcentaje de parte comestible (1-100)

        Returns:
            float: Peso bruto en gramos

        Examples:
            >>> CalculoService.calcular_peso_bruto(100, 85)
            117.65
        """
        # Validar que parte_comestible esté en rango válido
        parte_comestible = max(1.0, min(100.0, parte_comestible))

        return (peso_neto * 100) / parte_comestible

    @staticmethod
    def calcular_nutriente_por_peso(
        valor_por_100g: float,
        peso_neto: float
    ) -> float:
        """
        Calcula el valor de un nutriente para un peso específico.

        Fórmula: Nutriente = (Valor por 100g × Peso Neto) / 100

        Args:
            valor_por_100g: Valor del nutriente por 100g
            peso_neto: Peso neto en gramos

        Returns:
            float: Valor del nutriente para el peso dado

        Examples:
            >>> CalculoService.calcular_nutriente_por_peso(130, 150)
            195.0
        """
        return (valor_por_100g * peso_neto) / 100

    # =================== CÁLCULOS DESDE ALIMENTOS ICBF ===================

    @staticmethod
    def calcular_valores_nutricionales_alimento(alimento_icbf, peso_neto: float) -> Dict[str, float]:
        """
        Calcula todos los valores nutricionales de un alimento ICBF para un peso dado.

        Args:
            alimento_icbf: Objeto TablaAlimentos2018Icbf
            peso_neto: Peso neto en gramos

        Returns:
            Dict con todos los valores nutricionales calculados
        """
        factor = peso_neto / 100.0

        return {
            'calorias': float(alimento_icbf.energia_kcal) * factor,
            'proteina': float(alimento_icbf.proteina_g) * factor,
            'grasa': float(alimento_icbf.lipidos_g) * factor,
            'cho': float(alimento_icbf.carbohidratos_totales_g) * factor,
            'calcio': float(alimento_icbf.calcio_mg or 0) * factor,
            'hierro': float(alimento_icbf.hierro_mg or 0) * factor,
            'sodio': float(alimento_icbf.sodio_mg or 0) * factor,
        }

    # =================== CÁLCULOS DE TOTALES ===================

    @staticmethod
    def calcular_totales_ingredientes(
        ingredientes: List[Dict]
    ) -> Dict[str, float]:
        """
        Suma los valores nutricionales de todos los ingredientes.
        Prioritiza el uso de valores pre-calculados si existen.
        """
        totales = {
            'calorias': 0.0,
            'proteina': 0.0,
            'grasa': 0.0,
            'cho': 0.0,
            'calcio': 0.0,
            'hierro': 0.0,
            'sodio': 0.0,
            'peso_neto': 0.0,
            'peso_bruto': 0.0
        }

        for ing in ingredientes:
            if ing.get('alimento_encontrado', True):
                # Revisa si existen valores finales pre-calculados de un análisis guardado
                if 'valores_finales_guardados' in ing:
                    # Si existen, úsalos directamente
                    valores_finales = ing['valores_finales_guardados']
                    totales['calorias'] += valores_finales.get('calorias', 0)
                    totales['proteina'] += valores_finales.get('proteina', 0)
                    totales['grasa'] += valores_finales.get('grasa', 0)
                    totales['cho'] += valores_finales.get('cho', 0)
                    totales['calcio'] += valores_finales.get('calcio', 0)
                    totales['hierro'] += valores_finales.get('hierro', 0)
                    totales['sodio'] += valores_finales.get('sodio', 0)
                else:
                    # Si no, recalcula desde los datos base del ICBF
                    valores = ing.get('valores_por_100g', {})
                    peso_neto = ing.get('peso_neto_base', 0)
                    factor = peso_neto / 100

                    totales['calorias'] += valores.get('calorias_kcal', 0) * factor
                    totales['proteina'] += valores.get('proteina_g', 0) * factor
                    totales['grasa'] += valores.get('grasa_g', 0) * factor
                    totales['cho'] += valores.get('cho_g', 0) * factor
                    totales['calcio'] += valores.get('calcio_mg', 0) * factor
                    totales['hierro'] += valores.get('hierro_mg', 0) * factor
                    totales['sodio'] += valores.get('sodio_mg', 0) * factor
                
                # Sumar los pesos siempre, independientemente de la ruta de cálculo de nutrientes
                totales['peso_neto'] += ing.get('peso_neto_base', 0)
                totales['peso_bruto'] += ing.get('peso_bruto_base', 0)

        return totales

    # =================== CÁLCULOS DE PORCENTAJES ===================

    @staticmethod
    def calcular_porcentaje_adecuacion(
        total_actual: float,
        requerimiento: float,
        limitar_a_100: bool = True
    ) -> float:
        """
        Calcula el porcentaje de adecuación nutricional.

        Fórmula: % Adecuación = (Total Actual / Requerimiento) × 100

        Args:
            total_actual: Valor total actual del nutriente
            requerimiento: Valor requerido del nutriente
            limitar_a_100: Si True, limita el resultado a máximo 100%

        Returns:
            float: Porcentaje de adecuación (0-100 o sin límite)

        Examples:
            >>> CalculoService.calcular_porcentaje_adecuacion(400, 800)
            50.0
            >>> CalculoService.calcular_porcentaje_adecuacion(900, 800)
            100.0  # Limitado a 100
        """
        if requerimiento <= 0:
            return 0.0

        porcentaje = (total_actual / requerimiento) * 100

        if limitar_a_100:
            porcentaje = min(porcentaje, 100.0)

        return max(porcentaje, 0.0)

    @staticmethod
    def calcular_todos_porcentajes(
        totales: Dict[str, float],
        requerimientos: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula porcentajes de adecuación para todos los nutrientes.

        Args:
            totales: Dict con totales de nutrientes
            requerimientos: Dict con requerimientos nutricionales

        Returns:
            Dict con porcentaje y estado para cada nutriente
        """
        from ..utils import calcular_estado_adecuacion

        porcentajes = {}
        # Mapeo de claves de totales a claves de requerimientos si fuera necesario, 
        # pero aquí estandarizamos ambas a nombres simples.
        nutrientes = ['calorias', 'proteina', 'grasa', 'cho',
                     'calcio', 'hierro', 'sodio']

        for nutriente in nutrientes:
            total = totales.get(nutriente, 0)
            req = requerimientos.get(nutriente, 0)

            porcentaje = CalculoService.calcular_porcentaje_adecuacion(total, req)
            estado = calcular_estado_adecuacion(porcentaje, nutriente)

            porcentajes[nutriente] = {
                'porcentaje': round(porcentaje, 1),
                'estado': estado
            }

        return porcentajes

    # =================== AJUSTE BIDIRECCIONAL ===================

    @staticmethod
    def calcular_factor_escala(
        valor_objetivo: float,
        valor_actual: float
    ) -> float:
        """
        Calcula el factor de escala para ajustar pesos proporcionalmente.

        Args:
            valor_objetivo: Valor que se quiere alcanzar
            valor_actual: Valor actual

        Returns:
            float: Factor de escala (multiplicador)

        Examples:
            >>> CalculoService.calcular_factor_escala(400, 200)
            2.0
            >>> CalculoService.calcular_factor_escala(300, 600)
            0.5
        """
        if valor_actual <= 0:
            return 1.0

        return valor_objetivo / valor_actual

    @staticmethod
    def ajustar_pesos_proporcionalmente(
        ingredientes: List[Dict],
        factor_escala: float
    ) -> List[Dict]:
        """
        Ajusta todos los pesos de ingredientes manteniendo proporciones.

        Args:
            ingredientes: Lista de ingredientes con pesos
            factor_escala: Factor de escala a aplicar

        Returns:
            Lista de ingredientes con pesos ajustados
        """
        ingredientes_ajustados = []

        for ing in ingredientes:
            ing_copia = ing.copy()

            if ing_copia.get('alimento_encontrado', True):
                peso_neto_actual = ing_copia.get('peso_neto_base', 100)
                peso_neto_nuevo = peso_neto_actual * factor_escala

                parte_comestible = ing_copia.get('parte_comestible', 100)
                peso_bruto_nuevo = CalculoService.calcular_peso_bruto(
                    peso_neto_nuevo,
                    parte_comestible
                )

                ing_copia['peso_neto_base'] = round(peso_neto_nuevo, 2)
                ing_copia['peso_bruto_base'] = round(peso_bruto_nuevo, 2)

            ingredientes_ajustados.append(ing_copia)

        return ingredientes_ajustados

    @staticmethod
    def calcular_pesos_desde_porcentaje(
        ingredientes: List[Dict],
        nutriente: str,
        porcentaje_deseado: float,
        requerimiento: float
    ) -> Tuple[List[Dict], float]:
        """
        Calcula nuevos pesos para alcanzar un porcentaje de adecuación deseado.

        Args:
            ingredientes: Lista de ingredientes actuales
            nutriente: Nutriente a ajustar (ej: 'calorias_kcal')
            porcentaje_deseado: Porcentaje deseado (0-100)
            requerimiento: Requerimiento del nutriente

        Returns:
            Tuple de (ingredientes_ajustados, factor_escala_aplicado)
        """
        # 1. Calcular valor objetivo
        valor_objetivo = (porcentaje_deseado * requerimiento) / 100

        # 2. Calcular totales actuales
        totales = CalculoService.calcular_totales_ingredientes(ingredientes)
        valor_actual = totales.get(nutriente, 0)

        # 3. Calcular factor de escala
        factor_escala = CalculoService.calcular_factor_escala(valor_objetivo, valor_actual)

        # 4. Ajustar pesos proporcionalmente
        ingredientes_ajustados = CalculoService.ajustar_pesos_proporcionalmente(
            ingredientes,
            factor_escala
        )

        return ingredientes_ajustados, factor_escala
