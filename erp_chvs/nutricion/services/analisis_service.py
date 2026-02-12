"""
Servicio de Análisis Nutricional.

Orquesta la lógica completa del análisis nutricional de menús.
"""

import copy
from typing import Dict, List, Optional
from django.db.models import QuerySet

from ..models import (
    TablaMenus,
    TablaPreparaciones,
    TablaAlimentos2018Icbf,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaRequerimientosNutricionales,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaGradosEscolaresUapa
)
from .calculo_service import CalculoService


class AnalisisNutricionalService:
    """
    Servicio principal para análisis nutricional de menús.

    Coordina la obtención de datos, cálculos y preparación de resultados.
    """

    @staticmethod
    def obtener_analisis_completo(id_menu: int) -> Dict:
        """
        Obtiene el análisis nutricional completo de un menú.

        ACTUALIZACIÓN (Febrero 2025):
        - Ahora filtra requerimientos por NIVEL ESCOLAR + MODALIDAD
        - Los requerimientos son específicos para cada tipo de complemento alimentario
        - Semaforización ajustada según la Minuta Patrón ICBF

        Args:
            id_menu: ID del menú a analizar

        Returns:
            Dict con estructura completa del análisis

        Raises:
            TablaMenus.DoesNotExist: Si el menú no existe
        """
        # 1. Obtener menú y validar existencia
        menu = TablaMenus.objects.select_related('id_contrato', 'id_modalidad').get(id_menu=id_menu)

        # 2. Obtener datos base
        preparaciones_data = AnalisisNutricionalService._obtener_preparaciones_con_ingredientes(menu)

        # CAMBIO IMPORTANTE: Filtrar requerimientos por modalidad del menú
        # Cada modalidad (CAJM/JT, Almuerzo, etc.) tiene requerimientos específicos
        if menu.id_modalidad:
            requerimientos = TablaRequerimientosNutricionales.objects.filter(
                id_modalidad=menu.id_modalidad
            ).select_related('id_nivel_escolar_uapa', 'id_modalidad')
        else:
            # Fallback: Si el menú no tiene modalidad asignada, usar todos los requerimientos
            # (compatibilidad con datos antiguos)
            requerimientos = TablaRequerimientosNutricionales.objects.filter(
                id_modalidad__isnull=True
            ).select_related('id_nivel_escolar_uapa')

        nivel_escolar_programa = menu.id_contrato.get_nivel_escolar_uapa()

        # 3. Pre-cargar análisis guardados por nivel
        analisis_guardados = AnalisisNutricionalService._cargar_analisis_guardados(
            menu,
            requerimientos
        )

        # 4. Generar análisis por cada nivel escolar
        analisis_por_nivel = []

        for requerimiento in requerimientos:
            nivel_escolar = requerimiento.id_nivel_escolar_uapa
            es_programa_actual = (
                nivel_escolar_programa and
                nivel_escolar.id_grado_escolar_uapa == nivel_escolar_programa.id_grado_escolar_uapa
            )

            # Analizar este nivel
            analisis_nivel = AnalisisNutricionalService._analizar_nivel_escolar(
                preparaciones_data=preparaciones_data,
                requerimiento=requerimiento,
                nivel_escolar=nivel_escolar,
                analisis_guardado=analisis_guardados.get(nivel_escolar.id_grado_escolar_uapa),
                es_programa_actual=es_programa_actual
            )

            analisis_por_nivel.append(analisis_nivel)

        # 5. Preparar respuesta
        logo_path = None
        if menu.id_contrato and menu.id_contrato.imagen:
            try:
                logo_path = menu.id_contrato.imagen.path
            except (FileNotFoundError, ValueError):
                logo_path = None # Handle cases where file is missing or path is invalid

        return {
            'success': True,
            'menu': {
                'id': menu.id_menu,
                'nombre': menu.menu,
                'modalidad': menu.id_modalidad.modalidad if menu.id_modalidad else 'N/A',
                'programa': menu.id_contrato.programa if menu.id_contrato else 'N/A',
                'logo_path': logo_path
            },
            'analisis_por_nivel': analisis_por_nivel
        }

    @staticmethod
    def _obtener_preparaciones_con_ingredientes(menu: TablaMenus) -> List[Dict]:
        """
        Obtiene todas las preparaciones del menú con sus ingredientes.

        Args:
            menu: Instancia del menú

        Returns:
            Lista de preparaciones con ingredientes
        """
        preparaciones = TablaPreparaciones.objects.filter(
            id_menu=menu
        ).select_related(
            'id_componente',
            'id_componente__id_grupo_alimentos'
        ).prefetch_related('ingredientes__id_ingrediente_siesa')

        preparaciones_data = []

        for preparacion in preparaciones:
            ingredientes_prep = TablaPreparacionIngredientes.objects.filter(
                id_preparacion=preparacion
            ).select_related('id_ingrediente_siesa')

            ingredientes_data = []

            for ing_prep in ingredientes_prep:
                ingrediente = ing_prep.id_ingrediente_siesa

                # Buscar alimento en tabla ICBF
                alimento = TablaAlimentos2018Icbf.objects.filter(
                    codigo=ingrediente.id_ingrediente_siesa
                ).first()

                if not alimento:
                    alimento = TablaAlimentos2018Icbf.objects.filter(
                        nombre_del_alimento__icontains=ingrediente.nombre_ingrediente
                    ).first()

                if alimento:
                    # Calcular peso bruto
                    peso_neto_base = 100
                    parte_comestible = float(alimento.parte_comestible_field or 100)
                    parte_comestible = max(1.0, min(100.0, parte_comestible))

                    peso_bruto_base = CalculoService.calcular_peso_bruto(
                        peso_neto_base,
                        parte_comestible
                    )

                    # Valores por 100g
                    valores_por_100g = {
                        'calorias_kcal': float(alimento.energia_kcal or 0),
                        'proteina_g': float(alimento.proteina_g or 0),
                        'grasa_g': float(alimento.lipidos_g or 0),
                        'cho_g': float(alimento.carbohidratos_totales_g or 0),
                        'calcio_mg': float(alimento.calcio_mg or 0),
                        'hierro_mg': float(alimento.hierro_mg or 0),
                        'sodio_mg': float(alimento.sodio_mg or 0)
                    }

                    ingredientes_data.append({
                        'id_ingrediente': ingrediente.id_ingrediente_siesa,
                        'nombre': ingrediente.nombre_ingrediente,
                        'codigo_icbf': alimento.codigo,
                        'peso_neto_base': peso_neto_base,
                        'peso_bruto_base': round(peso_bruto_base, 1),
                        'parte_comestible': parte_comestible,
                        'valores_por_100g': valores_por_100g,
                        'alimento_encontrado': True
                    })
                else:
                    # Alimento no encontrado - usar defaults
                    ingredientes_data.append({
                        'id_ingrediente': ingrediente.id_ingrediente_siesa,
                        'nombre': ingrediente.nombre_ingrediente,
                        'peso_neto_base': 100,
                        'peso_bruto_base': 100,
                        'parte_comestible': 100,
                        'valores_por_100g': {
                            'calorias_kcal': 0, 'proteina_g': 0, 'grasa_g': 0,
                            'cho_g': 0, 'calcio_mg': 0, 'hierro_mg': 0, 'sodio_mg': 0
                        },
                        'alimento_encontrado': False
                    })

            # Obtener componente y grupo de alimentos
            componente = preparacion.id_componente.componente if preparacion.id_componente else 'SIN COMPONENTE'
            grupo_alimentos = (
                preparacion.id_componente.id_grupo_alimentos.grupo_alimentos
                if preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos
                else 'SIN GRUPO'
            )

            preparaciones_data.append({
                'id_preparacion': preparacion.id_preparacion,
                'nombre': preparacion.preparacion,
                'componente': componente,
                'grupo_alimentos': grupo_alimentos,
                'ingredientes': ingredientes_data
            })

        return preparaciones_data

    @staticmethod
    def _cargar_analisis_guardados(
        menu: TablaMenus,
        requerimientos: QuerySet
    ) -> Dict[str, TablaAnalisisNutricionalMenu]:
        """
        Pre-carga todos los análisis guardados del menú por nivel.

        Args:
            menu: Instancia del menú
            requerimientos: QuerySet de requerimientos

        Returns:
            Dict indexado por id_grado_escolar_uapa
        """
        analisis_guardados = {}

        for req in requerimientos:
            analisis = TablaAnalisisNutricionalMenu.objects.filter(
                id_menu=menu,
                id_nivel_escolar_uapa=req.id_nivel_escolar_uapa
            ).first()

            if analisis:
                analisis_guardados[req.id_nivel_escolar_uapa.id_grado_escolar_uapa] = analisis

        return analisis_guardados

    @staticmethod
    def _analizar_nivel_escolar(
        preparaciones_data: List[Dict],
        requerimiento: TablaRequerimientosNutricionales,
        nivel_escolar: 'TablaGradosEscolaresUapa',
        analisis_guardado: Optional[TablaAnalisisNutricionalMenu],
        es_programa_actual: bool
    ) -> Dict:
        """
        Analiza un nivel escolar específico.

        Args:
            preparaciones_data: Datos de preparaciones
            requerimiento: Requerimiento nutricional del nivel
            nivel_escolar: Nivel escolar
            analisis_guardado: Análisis guardado (si existe)
            es_programa_actual: Si es el nivel del programa actual

        Returns:
            Dict con análisis completo del nivel
        """
        # Crear copia profunda para este nivel
        preparaciones_nivel = copy.deepcopy(preparaciones_data)

        # Cargar análisis guardado si existe (pesos y valores)
        if analisis_guardado:
            AnalisisNutricionalService._aplicar_analisis_guardado(
                preparaciones_nivel,
                analisis_guardado
            )

        # Calcular totales
        totales = CalculoService.calcular_totales_ingredientes(
            [ing for prep in preparaciones_nivel for ing in prep['ingredientes']]
        )

        # Preparar requerimientos (estandarizado sin sufijos)
        requerimientos_dict = {
            'calorias': float(requerimiento.calorias_kcal),
            'proteina': float(requerimiento.proteina_g),
            'grasa': float(requerimiento.grasa_g),
            'cho': float(requerimiento.cho_g),
            'calcio': float(requerimiento.calcio_mg),
            'hierro': float(requerimiento.hierro_mg),
            'sodio': float(requerimiento.sodio_mg)
        }

        # Calcular porcentajes
        porcentajes = CalculoService.calcular_todos_porcentajes(totales, requerimientos_dict)

        return {
            'nivel_escolar': {
                'id': nivel_escolar.id_grado_escolar_uapa,
                'nombre': nivel_escolar.nivel_escolar_uapa,
                'rango_edades': getattr(nivel_escolar, 'rango_edades', '')
            },
            'es_programa_actual': es_programa_actual,
            'requerimientos': requerimientos_dict,
            'totales': totales,
            'porcentajes_adecuacion': porcentajes,
            'preparaciones': preparaciones_nivel
        }

    @staticmethod
    def _aplicar_analisis_guardado(
        preparaciones_nivel: List[Dict],
        analisis_guardado: TablaAnalisisNutricionalMenu
    ) -> None:
        """
        Aplica el análisis guardado (pesos y nutrientes) a los ingredientes.

        Modifica preparaciones_nivel in-place.

        Args:
            preparaciones_nivel: Lista de preparaciones (se modifica)
            analisis_guardado: Análisis con datos guardados
        """
        for prep in preparaciones_nivel:
            for ing in prep['ingredientes']:
                if ing.get('alimento_encontrado', True):
                    # Buscar ingrediente guardado
                    ingrediente_guardado = TablaIngredientesPorNivel.objects.filter(
                        id_analisis=analisis_guardado,
                        id_preparacion__id_preparacion=prep['id_preparacion'],
                        id_ingrediente_siesa__id_ingrediente_siesa=ing['id_ingrediente']
                    ).first()

                    if ingrediente_guardado:
                        # Aplicar pesos guardados
                        ing['peso_neto_base'] = float(ingrediente_guardado.peso_neto)
                        ing['peso_bruto_base'] = float(ingrediente_guardado.peso_bruto)

                        # Adjuntar los valores nutricionales finales que fueron guardados
                        ing['valores_finales_guardados'] = {
                            'calorias': float(ingrediente_guardado.calorias),
                            'proteina': float(ingrediente_guardado.proteina),
                            'grasa': float(ingrediente_guardado.grasa),
                            'cho': float(ingrediente_guardado.cho),
                            'calcio': float(ingrediente_guardado.calcio),
                            'hierro': float(ingrediente_guardado.hierro),
                            'sodio': float(ingrediente_guardado.sodio),
                        }

    @staticmethod
    def guardar_analisis(
        id_menu: int,
        id_nivel_escolar: str,
        totales: Dict,
        porcentajes: Dict,
        ingredientes: List[Dict],
        usuario: str = 'sistema'
    ) -> Dict:
        """
        Guarda el análisis nutricional en la base de datos.

        Args:
            id_menu: ID del menú
            id_nivel_escolar: ID del nivel escolar
            totales: Dict con totales nutricionales
            porcentajes: Dict con porcentajes de adecuación
            ingredientes: Lista de ingredientes con pesos
            usuario: Usuario que realiza el guardado

        Returns:
            Dict con resultado del guardado
        """
        from django.db import transaction
        from principal.models import TablaGradosEscolaresUapa

        # Validar menú existe
        menu = TablaMenus.objects.get(id_menu=id_menu)

        # Validar nivel escolar existe
        nivel_escolar = TablaGradosEscolaresUapa.objects.get(
            id_grado_escolar_uapa=id_nivel_escolar
        )

        with transaction.atomic():
            # Crear o actualizar análisis
            analisis, created = TablaAnalisisNutricionalMenu.objects.get_or_create(
                id_menu=menu,
                id_nivel_escolar_uapa=nivel_escolar,
                defaults={'usuario_modificacion': usuario}
            )

            print(f"[DEBUG] Guardando análisis - Menu ID: {id_menu}, Nivel: {id_nivel_escolar}, Created: {created}")
            print(f"[DEBUG] Totales recibidos: {totales}")
            print(f"[DEBUG] Porcentajes recibidos: {porcentajes}")
            print(f"[DEBUG] Total ingredientes: {len(ingredientes)}")

            # Actualizar totales
            analisis.total_calorias = totales.get('calorias', 0)
            analisis.total_proteina = totales.get('proteina', 0)
            analisis.total_grasa = totales.get('grasa', 0)
            analisis.total_cho = totales.get('cho', 0)
            analisis.total_calcio = totales.get('calcio', 0)
            analisis.total_hierro = totales.get('hierro', 0)
            analisis.total_sodio = totales.get('sodio', 0)
            analisis.total_peso_neto = totales.get('peso_neto', 0)
            analisis.total_peso_bruto = totales.get('peso_bruto', 0)

            # Actualizar porcentajes
            analisis.porcentaje_calorias = porcentajes.get('calorias', 0)
            analisis.porcentaje_proteina = porcentajes.get('proteina', 0)
            analisis.porcentaje_grasa = porcentajes.get('grasa', 0)
            analisis.porcentaje_cho = porcentajes.get('cho', 0)
            analisis.porcentaje_calcio = porcentajes.get('calcio', 0)
            analisis.porcentaje_hierro = porcentajes.get('hierro', 0)
            analisis.porcentaje_sodio = porcentajes.get('sodio', 0)

            analisis.usuario_modificacion = usuario
            analisis.save()

            # Eliminar ingredientes anteriores y crear nuevos
            TablaIngredientesPorNivel.objects.filter(id_analisis=analisis).delete()

            ingredientes_guardados = 0
            for ing_data in ingredientes:
                try:
                    preparacion = TablaPreparaciones.objects.get(
                        id_preparacion=ing_data['id_preparacion']
                    )
                    ingrediente = TablaIngredientesSiesa.objects.get(
                        id_ingrediente_siesa=ing_data['id_ingrediente_siesa']
                    )

                    TablaIngredientesPorNivel.objects.create(
                        id_analisis=analisis,
                        id_preparacion=preparacion,
                        id_ingrediente_siesa=ingrediente,
                        peso_neto=ing_data.get('peso_neto', 0),
                        peso_bruto=ing_data.get('peso_bruto', 0),
                        calorias=ing_data.get('calorias', 0),
                        proteina=ing_data.get('proteina', 0),
                        grasa=ing_data.get('grasa', 0),
                        cho=ing_data.get('cho', 0),
                        calcio=ing_data.get('calcio', 0),
                        hierro=ing_data.get('hierro', 0),
                        sodio=ing_data.get('sodio', 0)
                    )
                    ingredientes_guardados += 1

                except (TablaPreparaciones.DoesNotExist, TablaIngredientesSiesa.DoesNotExist):
                    continue

            return {
                'success': True,
                'message': 'Análisis nutricional guardado exitosamente',
                'analisis_id': analisis.id_analisis,
                'ingredientes_guardados': ingredientes_guardados,
                'created': created
            }

    @staticmethod
    def obtener_analisis_masivo_por_modalidad(programa_id: int, modalidad_id: int) -> Dict:
        """
        Obtiene y consolida el análisis nutricional de todos los menús de una modalidad.

        Args:
            programa_id: ID del programa/contrato.
            modalidad_id: ID de la modalidad de consumo.

        Returns:
            Dict con los análisis agrupados por nivel escolar.
        """
        from planeacion.models import Programa
        from principal.models import ModalidadesDeConsumo

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        menus = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad
        ).order_by('menu')

        analisis_final_por_nivel = {}

        for menu in menus:
            try:
                resultado_menu = AnalisisNutricionalService.obtener_analisis_completo(menu.id_menu)
                if not resultado_menu.get('success'):
                    continue

                for analisis_nivel in resultado_menu.get('analisis_por_nivel', []):
                    nombre_nivel = analisis_nivel.get('nivel_escolar', {}).get('nombre', 'Desconocido')
                    
                    if nombre_nivel not in analisis_final_por_nivel:
                        analisis_final_por_nivel[nombre_nivel] = []

                    menu_data_for_level = {
                        'menu_info': resultado_menu['menu'],
                        'analisis': analisis_nivel
                    }
                    analisis_final_por_nivel[nombre_nivel].append(menu_data_for_level)

            except Exception as e:
                # Log o manejo del error para un menú individual si es necesario
                print(f"Error procesando menú {menu.id_menu}: {e}")
                continue
        
        # Ordenar los menús dentro de cada nivel de forma robusta
        def sort_key(menu_analysis):
            menu_name = str(menu_analysis['menu_info']['nombre'])
            if menu_name.isdigit():
                return (0, int(menu_name))  # Tupla para ordenar: los números van primero
            else:
                return (1, menu_name)  # Los strings van después, ordenados alfabéticamente

        for nivel in analisis_final_por_nivel:
            analisis_final_por_nivel[nivel].sort(key=sort_key)

        return {
            "success": True,
            "programa_nombre": programa.programa,
            "modalidad_nombre": modalidad.modalidad,
            "analisis_por_nivel": analisis_final_por_nivel
        }

