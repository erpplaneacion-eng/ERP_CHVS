"""
Servicio de Gestión de Menús.

Maneja toda la lógica relacionada con menús nutricionales.
"""

from typing import Dict, List, Optional
from django.db.models import QuerySet
from django.db import transaction

from ..models import TablaMenus, TablaPreparaciones
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo


class MenuService:
    """
    Servicio para gestión de menús nutricionales.

    Responsabilidades:
    - CRUD de menús
    - Generación automática de menús
    - Validaciones de negocio
    """

    # =================== OBTENCIÓN DE DATOS ===================

    @staticmethod
    def obtener_menu(id_menu: int) -> TablaMenus:
        """
        Obtiene un menú por ID.

        Args:
            id_menu: ID del menú

        Returns:
            TablaMenus: Instancia del menú

        Raises:
            TablaMenus.DoesNotExist: Si no existe el menú
        """
        return TablaMenus.objects.select_related(
            'id_modalidad',
            'id_contrato'
        ).get(id_menu=id_menu)

    @staticmethod
    def obtener_menus_por_programa(id_programa: int) -> QuerySet:
        """
        Obtiene todos los menús de un programa.

        Args:
            id_programa: ID del programa

        Returns:
            QuerySet de menús del programa
        """
        return TablaMenus.objects.filter(
            id_contrato_id=id_programa
        ).select_related('id_modalidad').order_by('menu')

    @staticmethod
    def obtener_menus_por_modalidad(
        id_programa: int,
        id_modalidad: str
    ) -> QuerySet:
        """
        Obtiene menús de un programa filtrados por modalidad.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            QuerySet de menús filtrados
        """
        return TablaMenus.objects.filter(
            id_contrato_id=id_programa,
            id_modalidad_id=id_modalidad
        ).order_by('menu')

    @staticmethod
    def contar_menus_modalidad(id_programa: int, id_modalidad: str) -> int:
        """
        Cuenta menús existentes de una modalidad.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            int: Cantidad de menús
        """
        return TablaMenus.objects.filter(
            id_contrato_id=id_programa,
            id_modalidad_id=id_modalidad
        ).count()

    # =================== CREACIÓN DE MENÚS ===================

    @staticmethod
    def crear_menu(
        nombre: str,
        id_programa: int,
        id_modalidad: str
    ) -> TablaMenus:
        """
        Crea un nuevo menú.

        Args:
            nombre: Nombre del menú
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            TablaMenus: Menú creado

        Raises:
            Programa.DoesNotExist: Si no existe el programa
            ModalidadesDeConsumo.DoesNotExist: Si no existe la modalidad
        """
        programa = Programa.objects.get(id=id_programa)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=id_modalidad)

        menu = TablaMenus.objects.create(
            menu=nombre,
            id_contrato=programa,
            id_modalidad=modalidad
        )

        return menu

    @staticmethod
    def generar_menus_automaticos(
        id_programa: int,
        id_modalidad: str,
        cantidad: int = 5
    ) -> List[TablaMenus]:
        """
        Genera múltiples menús automáticamente.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad
            cantidad: Cantidad de menús a generar (default: 5)

        Returns:
            List[TablaMenus]: Lista de menús creados

        Raises:
            ValueError: Si ya existen menús para esta modalidad
        """
        # Validar que no existan menús previos
        menus_existentes = MenuService.contar_menus_modalidad(
            id_programa,
            id_modalidad
        )

        if menus_existentes > 0:
            raise ValueError(
                f'Ya existen {menus_existentes} menús para esta modalidad. '
                'Elimínelos primero antes de generar nuevos.'
            )

        # Obtener modalidad para el nombre
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=id_modalidad)
        programa = Programa.objects.get(id=id_programa)

        menus_creados = []

        with transaction.atomic():
            for i in range(1, cantidad + 1):
                nombre_menu = f"Menú {i} - {modalidad.modalidad}"

                menu = TablaMenus.objects.create(
                    menu=nombre_menu,
                    id_contrato=programa,
                    id_modalidad=modalidad
                )

                menus_creados.append(menu)

        return menus_creados

    @staticmethod
    def crear_menu_especial(
        nombre_personalizado: str,
        id_programa: int,
        id_modalidad: str
    ) -> TablaMenus:
        """
        Crea un menú con nombre personalizado.

        Args:
            nombre_personalizado: Nombre custom del menú
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            TablaMenus: Menú creado

        Raises:
            ValueError: Si el nombre está vacío
        """
        if not nombre_personalizado or nombre_personalizado.strip() == '':
            raise ValueError('El nombre del menú no puede estar vacío')

        return MenuService.crear_menu(
            nombre=nombre_personalizado.strip(),
            id_programa=id_programa,
            id_modalidad=id_modalidad
        )

    # =================== ACTUALIZACIÓN ===================

    @staticmethod
    def actualizar_menu(
        id_menu: int,
        datos: Dict
    ) -> TablaMenus:
        """
        Actualiza un menú existente.

        Args:
            id_menu: ID del menú
            datos: Dict con campos a actualizar

        Returns:
            TablaMenus: Menú actualizado
        """
        menu = TablaMenus.objects.get(id_menu=id_menu)

        # Actualizar campos permitidos
        if 'menu' in datos:
            menu.menu = datos['menu']
        if 'id_modalidad' in datos:
            menu.id_modalidad = ModalidadesDeConsumo.objects.get(
                id_modalidades=datos['id_modalidad']
            )

        menu.save()
        return menu

    # =================== ELIMINACIÓN ===================

    @staticmethod
    def eliminar_menu(id_menu: int) -> bool:
        """
        Elimina un menú (y sus preparaciones en cascada).

        Args:
            id_menu: ID del menú a eliminar

        Returns:
            bool: True si se eliminó correctamente
        """
        menu = TablaMenus.objects.get(id_menu=id_menu)
        menu.delete()
        return True

    @staticmethod
    def eliminar_menus_por_modalidad(
        id_programa: int,
        id_modalidad: str
    ) -> int:
        """
        Elimina todos los menús de una modalidad.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            int: Cantidad de menús eliminados
        """
        menus = TablaMenus.objects.filter(
            id_contrato_id=id_programa,
            id_modalidad_id=id_modalidad
        )

        cantidad = menus.count()
        menus.delete()

        return cantidad

    # =================== VALIDACIONES ===================

    @staticmethod
    def validar_puede_crear_menu(id_programa: int, id_modalidad: str) -> bool:
        """
        Valida si se puede crear un menú para esta modalidad.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad

        Returns:
            bool: True si se puede crear
        """
        # Verificar que programa existe
        if not Programa.objects.filter(id=id_programa).exists():
            return False

        # Verificar que modalidad existe
        if not ModalidadesDeConsumo.objects.filter(
            id_modalidades=id_modalidad
        ).exists():
            return False

        return True

    # =================== UTILIDADES ===================

    @staticmethod
    def serializar_menu(menu: TablaMenus) -> Dict:
        """
        Convierte un menú a diccionario.

        Args:
            menu: Instancia del menú

        Returns:
            Dict con datos del menú
        """
        return {
            'id_menu': menu.id_menu,
            'menu': menu.menu,
            'modalidad': {
                'id': menu.id_modalidad.id_modalidades if menu.id_modalidad else None,
                'nombre': menu.id_modalidad.modalidad if menu.id_modalidad else 'N/A'
            },
            'programa': {
                'id': menu.id_contrato.id if menu.id_contrato else None,
                'nombre': menu.id_contrato.programa if menu.id_contrato else 'N/A'
            },
            'fecha_creacion': menu.fecha_creacion.isoformat() if hasattr(menu, 'fecha_creacion') else None
        }

    @staticmethod
    def serializar_lista_menus(menus: QuerySet) -> List[Dict]:
        """
        Serializa una lista de menús.

        Args:
            menus: QuerySet de menús

        Returns:
            List[Dict]: Lista de menús serializados
        """
        return [MenuService.serializar_menu(menu) for menu in menus]
