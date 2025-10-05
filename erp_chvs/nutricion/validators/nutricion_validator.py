"""
Validadores del módulo de nutrición.

Centraliza todas las validaciones de negocio.
"""

from typing import Dict, List, Tuple, Optional
from django.core.exceptions import ValidationError

from ..models import (
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaRequerimientosNutricionales
)
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo, TablaGradosEscolaresUapa


class NutricionValidator:
    """
    Validador centralizado para el módulo de nutrición.

    Contiene todas las validaciones de negocio reutilizables.
    """

    # =================== VALIDACIONES DE EXISTENCIA ===================

    @staticmethod
    def validar_menu_existe(id_menu: int) -> Tuple[bool, str]:
        """
        Valida que un menú exista.

        Args:
            id_menu: ID del menú

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not TablaMenus.objects.filter(id_menu=id_menu).exists():
            return False, f'Menú con ID {id_menu} no encontrado'
        return True, ''

    @staticmethod
    def validar_preparacion_existe(id_preparacion: int) -> Tuple[bool, str]:
        """
        Valida que una preparación exista.

        Args:
            id_preparacion: ID de la preparación

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not TablaPreparaciones.objects.filter(id_preparacion=id_preparacion).exists():
            return False, f'Preparación con ID {id_preparacion} no encontrada'
        return True, ''

    @staticmethod
    def validar_ingrediente_existe(id_ingrediente: str) -> Tuple[bool, str]:
        """
        Valida que un ingrediente exista.

        Args:
            id_ingrediente: ID del ingrediente

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not TablaIngredientesSiesa.objects.filter(
            id_ingrediente_siesa=id_ingrediente
        ).exists():
            return False, f'Ingrediente con ID {id_ingrediente} no encontrado'
        return True, ''

    @staticmethod
    def validar_programa_existe(id_programa: int) -> Tuple[bool, str]:
        """
        Valida que un programa exista.

        Args:
            id_programa: ID del programa

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not Programa.objects.filter(id=id_programa).exists():
            return False, f'Programa con ID {id_programa} no encontrado'
        return True, ''

    @staticmethod
    def validar_modalidad_existe(id_modalidad: str) -> Tuple[bool, str]:
        """
        Valida que una modalidad exista.

        Args:
            id_modalidad: ID de la modalidad

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not ModalidadesDeConsumo.objects.filter(
            id_modalidades=id_modalidad
        ).exists():
            return False, f'Modalidad con ID {id_modalidad} no encontrada'
        return True, ''

    @staticmethod
    def validar_nivel_escolar_existe(id_nivel: str) -> Tuple[bool, str]:
        """
        Valida que un nivel escolar exista.

        Args:
            id_nivel: ID del nivel escolar

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not TablaGradosEscolaresUapa.objects.filter(
            id_grado_escolar_uapa=id_nivel
        ).exists():
            return False, f'Nivel escolar con ID {id_nivel} no encontrado'
        return True, ''

    # =================== VALIDACIONES DE DATOS ===================

    @staticmethod
    def validar_nombre_no_vacio(nombre: str, campo: str = 'Nombre') -> Tuple[bool, str]:
        """
        Valida que un nombre no esté vacío.

        Args:
            nombre: Nombre a validar
            campo: Nombre del campo (para mensaje de error)

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not nombre or nombre.strip() == '':
            return False, f'{campo} no puede estar vacío'
        return True, ''

    @staticmethod
    def validar_peso_positivo(peso: float, campo: str = 'Peso') -> Tuple[bool, str]:
        """
        Valida que un peso sea positivo.

        Args:
            peso: Peso a validar
            campo: Nombre del campo

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if peso <= 0:
            return False, f'{campo} debe ser mayor que 0'
        return True, ''

    @staticmethod
    def validar_porcentaje_rango(
        porcentaje: float,
        campo: str = 'Porcentaje'
    ) -> Tuple[bool, str]:
        """
        Valida que un porcentaje esté en rango 0-100.

        Args:
            porcentaje: Porcentaje a validar
            campo: Nombre del campo

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if porcentaje < 0 or porcentaje > 100:
            return False, f'{campo} debe estar entre 0 y 100'
        return True, ''

    # =================== VALIDACIONES DE ANÁLISIS ===================

    @staticmethod
    def validar_datos_analisis(data: Dict) -> Tuple[bool, List[str]]:
        """
        Valida los datos de un análisis nutricional.

        Args:
            data: Diccionario con datos del análisis

        Returns:
            Tuple[bool, List[str]]: (es_valido, lista_de_errores)
        """
        errores = []

        # Validar campos requeridos
        campos_requeridos = ['id_menu', 'id_nivel_escolar', 'totales', 'porcentajes', 'ingredientes']
        for campo in campos_requeridos:
            if campo not in data:
                errores.append(f'Falta el campo requerido: {campo}')

        if errores:
            return False, errores

        # Validar que el menú exista
        es_valido, mensaje = NutricionValidator.validar_menu_existe(data['id_menu'])
        if not es_valido:
            errores.append(mensaje)

        # Validar que el nivel escolar exista
        es_valido, mensaje = NutricionValidator.validar_nivel_escolar_existe(
            data['id_nivel_escolar']
        )
        if not es_valido:
            errores.append(mensaje)

        # Validar totales
        totales_requeridos = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio']
        for nutriente in totales_requeridos:
            if nutriente not in data['totales']:
                errores.append(f'Falta total de {nutriente}')

        # Validar porcentajes
        for nutriente in totales_requeridos:
            if nutriente in data['porcentajes']:
                es_valido, mensaje = NutricionValidator.validar_porcentaje_rango(
                    data['porcentajes'][nutriente],
                    f'Porcentaje de {nutriente}'
                )
                if not es_valido:
                    errores.append(mensaje)

        # Validar ingredientes
        if not isinstance(data['ingredientes'], list):
            errores.append('Ingredientes debe ser una lista')
        elif len(data['ingredientes']) == 0:
            errores.append('Debe haber al menos un ingrediente')

        return len(errores) == 0, errores

    # =================== VALIDACIONES DE NEGOCIO ===================

    @staticmethod
    def validar_puede_generar_menus(
        id_programa: int,
        id_modalidad: str
    ) -> Tuple[bool, str]:
        """
        Valida si se pueden generar menús para una modalidad.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            Tuple[bool, str]: (puede_generar, mensaje_error)
        """
        # Validar programa existe
        es_valido, mensaje = NutricionValidator.validar_programa_existe(id_programa)
        if not es_valido:
            return False, mensaje

        # Validar modalidad existe
        es_valido, mensaje = NutricionValidator.validar_modalidad_existe(id_modalidad)
        if not es_valido:
            return False, mensaje

        # Validar que no haya menús existentes
        if TablaMenus.objects.filter(
            id_contrato_id=id_programa,
            id_modalidad_id=id_modalidad
        ).exists():
            return False, 'Ya existen menús para esta modalidad. Elimínelos primero.'

        return True, ''

    @staticmethod
    def validar_puede_eliminar_menu(id_menu: int) -> Tuple[bool, str]:
        """
        Valida si un menú puede ser eliminado.

        Args:
            id_menu: ID del menú

        Returns:
            Tuple[bool, str]: (puede_eliminar, mensaje_advertencia)
        """
        # Verificar que existe
        es_valido, mensaje = NutricionValidator.validar_menu_existe(id_menu)
        if not es_valido:
            return False, mensaje

        # Contar preparaciones asociadas
        count_preparaciones = TablaPreparaciones.objects.filter(
            id_menu_id=id_menu
        ).count()

        if count_preparaciones > 0:
            return True, (
                f'ADVERTENCIA: Este menú tiene {count_preparaciones} preparaciones '
                'que también serán eliminadas'
            )

        return True, ''

    # =================== VALIDACIONES COMBINADAS ===================

    @staticmethod
    def validar_crear_menu(
        nombre: str,
        id_programa: int,
        id_modalidad: str
    ) -> Tuple[bool, List[str]]:
        """
        Valida todos los datos para crear un menú.

        Args:
            nombre: Nombre del menú
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            Tuple[bool, List[str]]: (es_valido, lista_de_errores)
        """
        errores = []

        # Validar nombre
        es_valido, mensaje = NutricionValidator.validar_nombre_no_vacio(
            nombre, 'Nombre del menú'
        )
        if not es_valido:
            errores.append(mensaje)

        # Validar programa
        es_valido, mensaje = NutricionValidator.validar_programa_existe(id_programa)
        if not es_valido:
            errores.append(mensaje)

        # Validar modalidad
        es_valido, mensaje = NutricionValidator.validar_modalidad_existe(id_modalidad)
        if not es_valido:
            errores.append(mensaje)

        return len(errores) == 0, errores

    @staticmethod
    def validar_crear_preparacion(
        nombre: str,
        id_menu: int
    ) -> Tuple[bool, List[str]]:
        """
        Valida todos los datos para crear una preparación.

        Args:
            nombre: Nombre de la preparación
            id_menu: ID del menú

        Returns:
            Tuple[bool, List[str]]: (es_valido, lista_de_errores)
        """
        errores = []

        # Validar nombre
        es_valido, mensaje = NutricionValidator.validar_nombre_no_vacio(
            nombre, 'Nombre de la preparación'
        )
        if not es_valido:
            errores.append(mensaje)

        # Validar menú existe
        es_valido, mensaje = NutricionValidator.validar_menu_existe(id_menu)
        if not es_valido:
            errores.append(mensaje)

        return len(errores) == 0, errores

    # =================== HELPER PARA LANZAR EXCEPCIONES ===================

    @staticmethod
    def validar_o_error(validacion: Tuple[bool, str]) -> None:
        """
        Helper para lanzar ValidationError si la validación falla.

        Args:
            validacion: Tupla (es_valido, mensaje_error)

        Raises:
            ValidationError: Si la validación falla
        """
        es_valido, mensaje = validacion
        if not es_valido:
            raise ValidationError(mensaje)

    @staticmethod
    def validar_multiple_o_error(validacion: Tuple[bool, List[str]]) -> None:
        """
        Helper para lanzar ValidationError con múltiples errores.

        Args:
            validacion: Tupla (es_valido, lista_errores)

        Raises:
            ValidationError: Si hay errores
        """
        es_valido, errores = validacion
        if not es_valido:
            raise ValidationError(errores)
