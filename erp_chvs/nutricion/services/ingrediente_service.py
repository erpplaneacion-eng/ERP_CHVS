"""
Servicio de Gestión de Ingredientes.

Maneja toda la lógica relacionada con ingredientes SIESA.
"""

from typing import Dict, List, Optional
from django.db.models import QuerySet, Q

from ..models import TablaIngredientesSiesa


class IngredienteService:
    """
    Servicio para gestión de ingredientes SIESA.

    Responsabilidades:
    - CRUD de ingredientes
    - Búsqueda y filtrado
    - Validaciones
    """

    # =================== OBTENCIÓN DE DATOS ===================

    @staticmethod
    def obtener_ingrediente(id_ingrediente: str) -> TablaIngredientesSiesa:
        """
        Obtiene un ingrediente por ID.

        Args:
            id_ingrediente: ID del ingrediente

        Returns:
            TablaIngredientesSiesa: Instancia del ingrediente

        Raises:
            TablaIngredientesSiesa.DoesNotExist: Si no existe
        """
        return TablaIngredientesSiesa.objects.get(
            id_ingrediente_siesa=id_ingrediente
        )

    @staticmethod
    def obtener_todos_ingredientes() -> QuerySet:
        """
        Obtiene todos los ingredientes ordenados alfabéticamente.

        Returns:
            QuerySet de ingredientes
        """
        return TablaIngredientesSiesa.objects.all().order_by('nombre_ingrediente')

    @staticmethod
    def buscar_ingredientes(termino: str, limite: int = 50) -> QuerySet:
        """
        Busca ingredientes por nombre o código.

        Args:
            termino: Término de búsqueda
            limite: Máximo de resultados (default: 50)

        Returns:
            QuerySet de ingredientes que coinciden
        """
        if not termino or termino.strip() == '':
            return TablaIngredientesSiesa.objects.none()

        termino_limpio = termino.strip()

        return TablaIngredientesSiesa.objects.filter(
            Q(nombre_ingrediente__icontains=termino_limpio) |
            Q(id_ingrediente_siesa__icontains=termino_limpio)
        ).order_by('nombre_ingrediente')[:limite]

    @staticmethod
    def obtener_por_ids(ids_ingredientes: List[str]) -> QuerySet:
        """
        Obtiene múltiples ingredientes por sus IDs.

        Args:
            ids_ingredientes: Lista de IDs

        Returns:
            QuerySet de ingredientes
        """
        return TablaIngredientesSiesa.objects.filter(
            id_ingrediente_siesa__in=ids_ingredientes
        ).order_by('nombre_ingrediente')

    # =================== CREACIÓN ===================

    @staticmethod
    def crear_ingrediente(
        id_ingrediente: str,
        nombre: str
    ) -> TablaIngredientesSiesa:
        """
        Crea un nuevo ingrediente SIESA.

        Args:
            id_ingrediente: Código/ID del ingrediente
            nombre: Nombre del ingrediente

        Returns:
            TablaIngredientesSiesa: Ingrediente creado

        Raises:
            ValueError: Si los datos son inválidos
            IntegrityError: Si ya existe el ingrediente
        """
        if not id_ingrediente or id_ingrediente.strip() == '':
            raise ValueError('El ID del ingrediente no puede estar vacío')

        if not nombre or nombre.strip() == '':
            raise ValueError('El nombre del ingrediente no puede estar vacío')

        ingrediente = TablaIngredientesSiesa.objects.create(
            id_ingrediente_siesa=id_ingrediente.strip(),
            nombre_ingrediente=nombre.strip()
        )

        return ingrediente

    # =================== ACTUALIZACIÓN ===================

    @staticmethod
    def actualizar_ingrediente(
        id_ingrediente: str,
        datos: Dict
    ) -> TablaIngredientesSiesa:
        """
        Actualiza un ingrediente existente.

        Args:
            id_ingrediente: ID del ingrediente
            datos: Dict con campos a actualizar

        Returns:
            TablaIngredientesSiesa: Ingrediente actualizado
        """
        ingrediente = TablaIngredientesSiesa.objects.get(
            id_ingrediente_siesa=id_ingrediente
        )

        if 'nombre_ingrediente' in datos:
            if not datos['nombre_ingrediente'] or datos['nombre_ingrediente'].strip() == '':
                raise ValueError('El nombre no puede estar vacío')
            ingrediente.nombre_ingrediente = datos['nombre_ingrediente'].strip()

        ingrediente.save()
        return ingrediente

    # =================== ELIMINACIÓN ===================

    @staticmethod
    def eliminar_ingrediente(id_ingrediente: str) -> bool:
        """
        Elimina un ingrediente.

        ADVERTENCIA: Esto eliminará el ingrediente de todas las preparaciones.

        Args:
            id_ingrediente: ID del ingrediente

        Returns:
            bool: True si se eliminó correctamente
        """
        ingrediente = TablaIngredientesSiesa.objects.get(
            id_ingrediente_siesa=id_ingrediente
        )
        ingrediente.delete()
        return True

    # =================== VALIDACIONES ===================

    @staticmethod
    def existe_ingrediente(id_ingrediente: str) -> bool:
        """
        Verifica si existe un ingrediente.

        Args:
            id_ingrediente: ID del ingrediente

        Returns:
            bool: True si existe
        """
        return TablaIngredientesSiesa.objects.filter(
            id_ingrediente_siesa=id_ingrediente
        ).exists()

    @staticmethod
    def validar_nombre_unico(nombre: str, excluir_id: Optional[str] = None) -> bool:
        """
        Valida que el nombre del ingrediente sea único.

        Args:
            nombre: Nombre a validar
            excluir_id: ID a excluir de la búsqueda (para updates)

        Returns:
            bool: True si es único
        """
        query = TablaIngredientesSiesa.objects.filter(
            nombre_ingrediente__iexact=nombre.strip()
        )

        if excluir_id:
            query = query.exclude(id_ingrediente_siesa=excluir_id)

        return not query.exists()

    # =================== ESTADÍSTICAS ===================

    @staticmethod
    def contar_ingredientes() -> int:
        """
        Cuenta el total de ingredientes.

        Returns:
            int: Cantidad de ingredientes
        """
        return TablaIngredientesSiesa.objects.count()

    @staticmethod
    def obtener_ingredientes_mas_usados(limite: int = 10) -> List[Dict]:
        """
        Obtiene los ingredientes más utilizados en preparaciones.

        Args:
            limite: Cantidad máxima de resultados

        Returns:
            List[Dict]: Ingredientes con conteo de uso
        """
        from django.db.models import Count
        from ..models import TablaPreparacionIngredientes

        ingredientes = TablaIngredientesSiesa.objects.annotate(
            usos=Count('preparaciones')
        ).filter(
            usos__gt=0
        ).order_by('-usos')[:limite]

        return [
            {
                'id_ingrediente': ing.id_ingrediente_siesa,
                'nombre': ing.nombre_ingrediente,
                'cantidad_usos': ing.usos
            }
            for ing in ingredientes
        ]

    # =================== SERIALIZACIÓN ===================

    @staticmethod
    def serializar_ingrediente(ingrediente: TablaIngredientesSiesa) -> Dict:
        """
        Convierte un ingrediente a diccionario.

        Args:
            ingrediente: Instancia del ingrediente

        Returns:
            Dict con datos del ingrediente
        """
        return {
            'id_ingrediente_siesa': ingrediente.id_ingrediente_siesa,
            'nombre_ingrediente': ingrediente.nombre_ingrediente,
            'codigo': ingrediente.id_ingrediente_siesa  # Alias para frontend
        }

    @staticmethod
    def serializar_lista_ingredientes(ingredientes: QuerySet) -> List[Dict]:
        """
        Serializa una lista de ingredientes.

        Args:
            ingredientes: QuerySet de ingredientes

        Returns:
            List[Dict]: Lista de ingredientes serializados
        """
        return [
            IngredienteService.serializar_ingrediente(ing)
            for ing in ingredientes
        ]

    @staticmethod
    def serializar_para_select2(ingredientes: QuerySet) -> List[Dict]:
        """
        Serializa ingredientes para dropdown Select2.

        Args:
            ingredientes: QuerySet de ingredientes

        Returns:
            List[Dict]: Formato compatible con Select2
        """
        return [
            {
                'id': ing.id_ingrediente_siesa,
                'text': f"{ing.id_ingrediente_siesa} - {ing.nombre_ingrediente}"
            }
            for ing in ingredientes
        ]
