import logging

from django.db import transaction
from django.db.models import Count

from ..models import (
    TablaMenus,
    TablaPreparaciones,
    TablaPreparacionIngredientes,
    TablaAlimentos2018Icbf,
)

logger = logging.getLogger(__name__)


class CopiarMenuService:

    @staticmethod
    def get_programas_con_menus(excluir_programa_id=None):
        """
        Retorna todos los programas que tienen al menos 1 menu configurado,
        ordenados por municipio. Excluye el programa indicado.
        """
        qs = (
            TablaMenus.objects.values(
                'id_contrato_id',
                'id_contrato__programa',
                'id_contrato__contrato',
                'id_contrato__municipio__nombre_municipio',
            )
            .annotate(cantidad_menus=Count('id_menu'))
            .filter(cantidad_menus__gt=0)
            .order_by('id_contrato__municipio__nombre_municipio', '-id_contrato_id')
        )

        if excluir_programa_id:
            qs = qs.exclude(id_contrato_id=excluir_programa_id)

        return [
            {
                'id': p['id_contrato_id'],
                'programa': p['id_contrato__programa'],
                'contrato': p['id_contrato__contrato'] or '',
                'municipio': p['id_contrato__municipio__nombre_municipio'] or '',
                'cantidad_menus': p['cantidad_menus'],
            }
            for p in qs
        ]

    @staticmethod
    def get_menus_de_programa(programa_id):
        """
        Retorna los menus de un programa con conteo de preparaciones e ingredientes.
        """
        menus = (
            TablaMenus.objects.filter(id_contrato_id=programa_id)
            .prefetch_related('preparaciones__ingredientes')
            .order_by('semana', 'menu')
        )

        resultado = []
        for menu in menus:
            preparaciones = list(menu.preparaciones.all())
            total_ingredientes = sum(p.ingredientes.count() for p in preparaciones)
            resultado.append({
                'id_menu': menu.id_menu,
                'menu': menu.menu,
                'semana': menu.semana,
                'num_preparaciones': len(preparaciones),
                'num_ingredientes': total_ingredientes,
            })
        return resultado

    @staticmethod
    def get_detalle_menu(menu_id):
        """
        Retorna el detalle completo de un menu: preparaciones con sus ingredientes.
        Devuelve None si el menu no existe.
        """
        try:
            menu = TablaMenus.objects.prefetch_related(
                'preparaciones__ingredientes__id_ingrediente_siesa',
                'preparaciones__id_componente',
            ).get(id_menu=menu_id)
        except TablaMenus.DoesNotExist:
            return None

        preparaciones = []
        for prep in menu.preparaciones.all():
            ingredientes = [
                {
                    'codigo': ing.id_ingrediente_siesa.codigo,
                    'nombre': ing.id_ingrediente_siesa.nombre_del_alimento,
                    'gramaje': float(ing.gramaje) if ing.gramaje is not None else None,
                    'id_componente': ing.id_componente_id,
                }
                for ing in prep.ingredientes.all()
            ]
            preparaciones.append({
                'id_preparacion': prep.id_preparacion,
                'nombre': prep.preparacion,
                'id_componente': prep.id_componente_id,
                'ingredientes': ingredientes,
            })

        return {
            'id_menu': menu.id_menu,
            'menu': menu.menu,
            'preparaciones': preparaciones,
        }

    @staticmethod
    def buscar_alimentos(query, limit=20):
        """
        Busca alimentos ICBF 2018 por nombre (icontains).
        """
        return list(
            TablaAlimentos2018Icbf.objects.filter(
                nombre_del_alimento__icontains=query
            ).values('codigo', 'nombre_del_alimento')[:limit]
        )

    @staticmethod
    @transaction.atomic
    def ejecutar_copia(menu_destino_id, preparaciones_seleccionadas):
        """
        Copia las preparaciones e ingredientes seleccionados al menu destino.
        Elimina el contenido previo del menu destino antes de copiar.

        Args:
            menu_destino_id: ID del menu que recibira el contenido.
            preparaciones_seleccionadas: lista de dicts con la forma:
                [
                    {
                        'nombre': str,
                        'id_componente': str|None,
                        'ingredientes': [
                            {'codigo': str, 'gramaje': float|None, 'id_componente': str|None}
                        ]
                    }
                ]

        Returns:
            dict con 'preparaciones' y 'ingredientes' (contadores de lo copiado).
        """
        menu_destino = TablaMenus.objects.get(id_menu=menu_destino_id)

        # Eliminar preparaciones previas (CASCADE limpia ingredientes y analisis)
        menu_destino.preparaciones.all().delete()

        nuevas_preps = 0
        nuevos_ings = 0

        codigos_validos = set(
            TablaAlimentos2018Icbf.objects.filter(
                codigo__in=[
                    ing['codigo']
                    for prep in preparaciones_seleccionadas
                    for ing in prep.get('ingredientes', [])
                    if ing.get('codigo')
                ]
            ).values_list('codigo', flat=True)
        )

        for prep_data in preparaciones_seleccionadas:
            nueva_prep = TablaPreparaciones.objects.create(
                preparacion=prep_data['nombre'],
                id_menu=menu_destino,
                id_componente_id=prep_data.get('id_componente') or None,
            )
            nuevas_preps += 1

            ingredientes_a_crear = [
                TablaPreparacionIngredientes(
                    id_preparacion=nueva_prep,
                    id_ingrediente_siesa_id=ing['codigo'],
                    id_componente_id=ing.get('id_componente') or None,
                    gramaje=ing.get('gramaje'),
                )
                for ing in prep_data.get('ingredientes', [])
                if ing.get('codigo') and ing['codigo'] in codigos_validos
            ]

            if ingredientes_a_crear:
                TablaPreparacionIngredientes.objects.bulk_create(
                    ingredientes_a_crear,
                    ignore_conflicts=True,
                )
                nuevos_ings += len(ingredientes_a_crear)

        logger.info(
            'Copia de menu ejecutada: destino=%s preparaciones=%d ingredientes=%d',
            menu_destino_id, nuevas_preps, nuevos_ings,
        )
        return {'preparaciones': nuevas_preps, 'ingredientes': nuevos_ings}
