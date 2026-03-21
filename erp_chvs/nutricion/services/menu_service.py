"""
Servicio de Gestión de Menús.

Maneja toda la lógica relacionada con menús nutricionales.
"""

from typing import Dict, List
from django.db.models import QuerySet
from django.db import transaction

from ..models import TablaMenus
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo


class MenuService:
    """
    Servicio para gestión de menús nutricionales.
    """

    # =================== OBTENCIÓN DE DATOS ===================

    @staticmethod
    def obtener_menu(id_menu: int) -> TablaMenus:
        """
        Obtiene un menú por ID.
        """
        return TablaMenus.objects.select_related(
            'id_modalidad',
            'id_contrato'
        ).get(id_menu=id_menu)

    @staticmethod
    def obtener_menus_por_programa(id_programa: int) -> QuerySet:
        """
        Obtiene todos los menús de un programa.
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
        """
        return TablaMenus.objects.filter(
            id_contrato_id=id_programa,
            id_modalidad_id=id_modalidad
        ).order_by('menu')

    @staticmethod
    def contar_menus_modalidad(id_programa: int, id_modalidad: str) -> int:
        """
        Cuenta menús existentes de una modalidad.
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
        """
        # Validar que no existan menús previos
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=id_modalidad)
        programa = Programa.objects.get(id=id_programa)

        # Calcular el siguiente número disponible según los menús ya existentes
        # con nombre numérico puro (los regulares del ciclo semanal)
        numeros_usados = set(
            TablaMenus.objects
            .filter(id_contrato_id=id_programa, id_modalidad_id=id_modalidad)
            .values_list('menu', flat=True)
        )
        numeros_usados = {int(n) for n in numeros_usados if n.isdigit()}
        siguiente = max(numeros_usados, default=0) + 1

        menus_creados = []

        with transaction.atomic():
            for i in range(siguiente, siguiente + cantidad):
                menu = TablaMenus.objects.create(
                    menu=str(i),
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
        """
        return [MenuService.serializar_menu(menu) for menu in menus]
