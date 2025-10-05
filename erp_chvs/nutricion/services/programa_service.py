"""
Servicio de Gestión de Programas y Modalidades.

Maneja consultas relacionadas con programas y modalidades de consumo.
"""

from typing import Dict, List
from django.db.models import QuerySet

from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo, MunicipioModalidades


class ProgramaService:
    """
    Servicio para consultas de programas y modalidades.

    Responsabilidades:
    - Obtener programas por municipio
    - Obtener modalidades por programa
    - Validaciones relacionadas
    """

    # =================== OBTENCIÓN DE PROGRAMAS ===================

    @staticmethod
    def obtener_programas_por_municipio(id_municipio: str) -> QuerySet:
        """
        Obtiene programas activos de un municipio.

        Args:
            id_municipio: ID del municipio

        Returns:
            QuerySet de programas activos
        """
        return Programa.objects.filter(
            municipio_id=id_municipio,
            estado='activo'
        ).order_by('programa')

    @staticmethod
    def obtener_programa(id_programa: int) -> Programa:
        """
        Obtiene un programa por ID.

        Args:
            id_programa: ID del programa

        Returns:
            Programa: Instancia del programa

        Raises:
            Programa.DoesNotExist: Si no existe
        """
        return Programa.objects.select_related('municipio').get(id=id_programa)

    # =================== OBTENCIÓN DE MODALIDADES ===================

    @staticmethod
    def obtener_modalidades_por_programa(id_programa: int) -> List[Dict]:
        """
        Obtiene modalidades configuradas para un programa.

        Si el municipio del programa tiene modalidades configuradas,
        retorna solo esas. Si no, retorna todas las modalidades.

        Args:
            id_programa: ID del programa

        Returns:
            List[Dict]: Lista de modalidades con id y nombre

        Raises:
            Programa.DoesNotExist: Si el programa no existe
        """
        programa = Programa.objects.select_related('municipio').get(id=id_programa)

        # Obtener modalidades configuradas para el municipio
        modalidades_configuradas = MunicipioModalidades.objects.filter(
            municipio=programa.municipio
        ).select_related('modalidad')

        if modalidades_configuradas.exists():
            # Usar modalidades configuradas
            modalidades_list = [
                {
                    'id_modalidades': mm.modalidad.id_modalidades,
                    'modalidad': mm.modalidad.modalidad
                }
                for mm in modalidades_configuradas.order_by('modalidad__modalidad')
            ]
        else:
            # Usar todas las modalidades
            modalidades = ModalidadesDeConsumo.objects.all().order_by('modalidad')
            modalidades_list = [
                {
                    'id_modalidades': m.id_modalidades,
                    'modalidad': m.modalidad
                }
                for m in modalidades
            ]

        return modalidades_list

    @staticmethod
    def obtener_todas_modalidades() -> QuerySet:
        """
        Obtiene todas las modalidades de consumo.

        Returns:
            QuerySet de modalidades
        """
        return ModalidadesDeConsumo.objects.all().order_by('modalidad')

    # =================== SERIALIZACIÓN ===================

    @staticmethod
    def serializar_programa(programa: Programa) -> Dict:
        """
        Convierte un programa a diccionario.

        Args:
            programa: Instancia del programa

        Returns:
            Dict con datos del programa
        """
        return {
            'id': programa.id,
            'programa': programa.programa,
            'contrato': programa.contrato,
            'fecha_inicial': programa.fecha_inicial.isoformat() if programa.fecha_inicial else None,
            'fecha_final': programa.fecha_final.isoformat() if programa.fecha_final else None,
            'estado': programa.estado,
            'municipio': {
                'id': programa.municipio.id_municipio if programa.municipio else None,
                'nombre': programa.municipio.municipio if programa.municipio else 'N/A'
            }
        }

    @staticmethod
    def serializar_lista_programas(programas: QuerySet) -> List[Dict]:
        """
        Serializa una lista de programas.

        Args:
            programas: QuerySet de programas

        Returns:
            List[Dict]: Lista de programas serializados
        """
        return [
            {
                'id': p.id,
                'programa': p.programa,
                'contrato': p.contrato,
                'fecha_inicial': p.fecha_inicial.isoformat() if p.fecha_inicial else None,
                'fecha_final': p.fecha_final.isoformat() if p.fecha_final else None
            }
            for p in programas
        ]

    @staticmethod
    def serializar_modalidad(modalidad: ModalidadesDeConsumo) -> Dict:
        """
        Convierte una modalidad a diccionario.

        Args:
            modalidad: Instancia de la modalidad

        Returns:
            Dict con datos de la modalidad
        """
        return {
            'id_modalidades': modalidad.id_modalidades,
            'modalidad': modalidad.modalidad
        }
