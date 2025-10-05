"""
Servicio de Gestión de Preparaciones.

Maneja toda la lógica relacionada con preparaciones e ingredientes.
"""

from typing import Dict, List, Optional
from django.db.models import QuerySet
from django.db import transaction, IntegrityError

from ..models import (
    TablaPreparaciones,
    TablaMenus,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes
)


class PreparacionService:
    """
    Servicio para gestión de preparaciones e ingredientes.

    Responsabilidades:
    - CRUD de preparaciones
    - Gestión de ingredientes por preparación
    - Validaciones de negocio
    """

    # =================== OBTENCIÓN DE DATOS ===================

    @staticmethod
    def obtener_preparacion(id_preparacion: int) -> TablaPreparaciones:
        """
        Obtiene una preparación por ID.

        Args:
            id_preparacion: ID de la preparación

        Returns:
            TablaPreparaciones: Instancia de la preparación

        Raises:
            TablaPreparaciones.DoesNotExist: Si no existe
        """
        return TablaPreparaciones.objects.select_related(
            'id_menu'
        ).prefetch_related(
            'ingredientes__id_ingrediente_siesa'
        ).get(id_preparacion=id_preparacion)

    @staticmethod
    def obtener_preparaciones_menu(id_menu: int) -> QuerySet:
        """
        Obtiene todas las preparaciones de un menú.

        Args:
            id_menu: ID del menú

        Returns:
            QuerySet de preparaciones
        """
        return TablaPreparaciones.objects.filter(
            id_menu_id=id_menu
        ).prefetch_related('ingredientes__id_ingrediente_siesa').order_by('preparacion')

    @staticmethod
    def obtener_ingredientes_preparacion(
        id_preparacion: int
    ) -> List[Dict]:
        """
        Obtiene todos los ingredientes de una preparación.

        Args:
            id_preparacion: ID de la preparación

        Returns:
            List[Dict]: Lista de ingredientes con detalles
        """
        ingredientes_prep = TablaPreparacionIngredientes.objects.filter(
            id_preparacion_id=id_preparacion
        ).select_related('id_ingrediente_siesa')

        ingredientes = []
        for ing_prep in ingredientes_prep:
            ingrediente = ing_prep.id_ingrediente_siesa
            ingredientes.append({
                'id_ingrediente': ingrediente.id_ingrediente_siesa,
                'nombre': ingrediente.nombre_ingrediente,
                'codigo': ingrediente.id_ingrediente_siesa
            })

        return ingredientes

    # =================== CREACIÓN ===================

    @staticmethod
    def crear_preparacion(
        nombre: str,
        id_menu: int
    ) -> TablaPreparaciones:
        """
        Crea una nueva preparación.

        Args:
            nombre: Nombre de la preparación
            id_menu: ID del menú al que pertenece

        Returns:
            TablaPreparaciones: Preparación creada

        Raises:
            TablaMenus.DoesNotExist: Si el menú no existe
            ValueError: Si el nombre está vacío
        """
        if not nombre or nombre.strip() == '':
            raise ValueError('El nombre de la preparación no puede estar vacío')

        menu = TablaMenus.objects.get(id_menu=id_menu)

        preparacion = TablaPreparaciones.objects.create(
            preparacion=nombre.strip(),
            id_menu=menu
        )

        return preparacion

    @staticmethod
    def agregar_ingrediente(
        id_preparacion: int,
        id_ingrediente: str
    ) -> Dict:
        """
        Agrega un ingrediente a una preparación.

        Args:
            id_preparacion: ID de la preparación
            id_ingrediente: ID del ingrediente

        Returns:
            Dict con resultado de la operación

        Raises:
            TablaPreparaciones.DoesNotExist: Si la preparación no existe
            TablaIngredientesSiesa.DoesNotExist: Si el ingrediente no existe
        """
        preparacion = TablaPreparaciones.objects.get(id_preparacion=id_preparacion)
        ingrediente = TablaIngredientesSiesa.objects.get(
            id_ingrediente_siesa=id_ingrediente
        )

        try:
            # Intentar crear la relación
            relacion, created = TablaPreparacionIngredientes.objects.get_or_create(
                id_preparacion=preparacion,
                id_ingrediente_siesa=ingrediente
            )

            if created:
                return {
                    'success': True,
                    'message': 'Ingrediente agregado exitosamente',
                    'ingrediente': {
                        'id': ingrediente.id_ingrediente_siesa,
                        'nombre': ingrediente.nombre_ingrediente
                    }
                }
            else:
                return {
                    'success': False,
                    'message': 'El ingrediente ya está en esta preparación',
                    'ingrediente': {
                        'id': ingrediente.id_ingrediente_siesa,
                        'nombre': ingrediente.nombre_ingrediente
                    }
                }

        except IntegrityError as e:
            return {
                'success': False,
                'message': f'Error al agregar ingrediente: {str(e)}'
            }

    # =================== ACTUALIZACIÓN ===================

    @staticmethod
    def actualizar_preparacion(
        id_preparacion: int,
        nombre: str
    ) -> TablaPreparaciones:
        """
        Actualiza el nombre de una preparación.

        Args:
            id_preparacion: ID de la preparación
            nombre: Nuevo nombre

        Returns:
            TablaPreparaciones: Preparación actualizada

        Raises:
            ValueError: Si el nombre está vacío
        """
        if not nombre or nombre.strip() == '':
            raise ValueError('El nombre no puede estar vacío')

        preparacion = TablaPreparaciones.objects.get(id_preparacion=id_preparacion)
        preparacion.preparacion = nombre.strip()
        preparacion.save()

        return preparacion

    # =================== ELIMINACIÓN ===================

    @staticmethod
    def eliminar_preparacion(id_preparacion: int) -> bool:
        """
        Elimina una preparación (y sus ingredientes en cascada).

        Args:
            id_preparacion: ID de la preparación

        Returns:
            bool: True si se eliminó correctamente
        """
        preparacion = TablaPreparaciones.objects.get(id_preparacion=id_preparacion)
        preparacion.delete()
        return True

    @staticmethod
    def eliminar_ingrediente_preparacion(
        id_preparacion: int,
        id_ingrediente: str
    ) -> bool:
        """
        Elimina un ingrediente de una preparación.

        Args:
            id_preparacion: ID de la preparación
            id_ingrediente: ID del ingrediente

        Returns:
            bool: True si se eliminó correctamente

        Raises:
            TablaPreparacionIngredientes.DoesNotExist: Si la relación no existe
        """
        relacion = TablaPreparacionIngredientes.objects.get(
            id_preparacion_id=id_preparacion,
            id_ingrediente_siesa_id=id_ingrediente
        )

        relacion.delete()
        return True

    # =================== VALIDACIONES ===================

    @staticmethod
    def validar_puede_agregar_ingrediente(
        id_preparacion: int,
        id_ingrediente: str
    ) -> tuple[bool, str]:
        """
        Valida si se puede agregar un ingrediente a una preparación.

        Args:
            id_preparacion: ID de la preparación
            id_ingrediente: ID del ingrediente

        Returns:
            tuple: (puede_agregar: bool, mensaje: str)
        """
        # Verificar que preparación existe
        if not TablaPreparaciones.objects.filter(id_preparacion=id_preparacion).exists():
            return False, 'La preparación no existe'

        # Verificar que ingrediente existe
        if not TablaIngredientesSiesa.objects.filter(
            id_ingrediente_siesa=id_ingrediente
        ).exists():
            return False, 'El ingrediente no existe'

        # Verificar si ya está agregado
        if TablaPreparacionIngredientes.objects.filter(
            id_preparacion_id=id_preparacion,
            id_ingrediente_siesa_id=id_ingrediente
        ).exists():
            return False, 'El ingrediente ya está en esta preparación'

        return True, 'OK'

    @staticmethod
    def contar_ingredientes(id_preparacion: int) -> int:
        """
        Cuenta los ingredientes de una preparación.

        Args:
            id_preparacion: ID de la preparación

        Returns:
            int: Cantidad de ingredientes
        """
        return TablaPreparacionIngredientes.objects.filter(
            id_preparacion_id=id_preparacion
        ).count()

    # =================== OPERACIONES MASIVAS ===================

    @staticmethod
    def agregar_ingredientes_bulk(
        id_preparacion: int,
        ids_ingredientes: List[str]
    ) -> Dict:
        """
        Agrega múltiples ingredientes a una preparación.

        Args:
            id_preparacion: ID de la preparación
            ids_ingredientes: Lista de IDs de ingredientes

        Returns:
            Dict con resultado de la operación
        """
        preparacion = TablaPreparaciones.objects.get(id_preparacion=id_preparacion)

        agregados = 0
        ya_existentes = 0
        errores = []

        with transaction.atomic():
            for id_ingrediente in ids_ingredientes:
                try:
                    ingrediente = TablaIngredientesSiesa.objects.get(
                        id_ingrediente_siesa=id_ingrediente
                    )

                    _, created = TablaPreparacionIngredientes.objects.get_or_create(
                        id_preparacion=preparacion,
                        id_ingrediente_siesa=ingrediente
                    )

                    if created:
                        agregados += 1
                    else:
                        ya_existentes += 1

                except TablaIngredientesSiesa.DoesNotExist:
                    errores.append(f'Ingrediente {id_ingrediente} no encontrado')

        return {
            'success': True,
            'agregados': agregados,
            'ya_existentes': ya_existentes,
            'errores': errores,
            'total_procesados': len(ids_ingredientes)
        }

    # =================== SERIALIZACIÓN ===================

    @staticmethod
    def serializar_preparacion(preparacion: TablaPreparaciones) -> Dict:
        """
        Convierte una preparación a diccionario.

        Args:
            preparacion: Instancia de la preparación

        Returns:
            Dict con datos de la preparación
        """
        return {
            'id_preparacion': preparacion.id_preparacion,
            'preparacion': preparacion.preparacion,
            'id_menu': preparacion.id_menu.id_menu if preparacion.id_menu else None,
            'menu_nombre': preparacion.id_menu.menu if preparacion.id_menu else 'N/A',
            'cantidad_ingredientes': PreparacionService.contar_ingredientes(
                preparacion.id_preparacion
            ),
            'fecha_creacion': preparacion.fecha_creacion.isoformat() if hasattr(
                preparacion, 'fecha_creacion'
            ) else None
        }

    @staticmethod
    def serializar_preparacion_con_ingredientes(
        preparacion: TablaPreparaciones
    ) -> Dict:
        """
        Serializa preparación incluyendo sus ingredientes.

        Args:
            preparacion: Instancia de la preparación

        Returns:
            Dict con preparación e ingredientes
        """
        data = PreparacionService.serializar_preparacion(preparacion)
        data['ingredientes'] = PreparacionService.obtener_ingredientes_preparacion(
            preparacion.id_preparacion
        )
        return data

    @staticmethod
    def serializar_lista_preparaciones(
        preparaciones: QuerySet,
        incluir_ingredientes: bool = False
    ) -> List[Dict]:
        """
        Serializa una lista de preparaciones.

        Args:
            preparaciones: QuerySet de preparaciones
            incluir_ingredientes: Si incluye ingredientes de cada preparación

        Returns:
            List[Dict]: Lista de preparaciones serializadas
        """
        if incluir_ingredientes:
            return [
                PreparacionService.serializar_preparacion_con_ingredientes(prep)
                for prep in preparaciones
            ]
        else:
            return [
                PreparacionService.serializar_preparacion(prep)
                for prep in preparaciones
            ]
