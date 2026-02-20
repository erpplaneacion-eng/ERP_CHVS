"""
Servicio de Análisis Nutricional.

Orquesta la lógica completa del análisis nutricional de menús.
"""

import copy
from typing import Dict, List, Optional
from django.db.models import QuerySet

from ..models import (
    MinutaPatronMeta,
    TablaMenus,
    TablaPreparaciones,
    TablaAlimentos2018Icbf,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaRequerimientosNutricionales,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaGradosEscolaresUapa,
    RecomendacionDiariaGradoMod,
    AdecuacionTotalPorcentaje,
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

        # 2. Obtener datos base (pasamos el primer nivel para obtener valores mínimos por defecto)
        primer_nivel = requerimientos.first().id_nivel_escolar_uapa if requerimientos else None
        nivel_para_defecto = primer_nivel.id_grado_escolar_uapa if primer_nivel else None
        preparaciones_data = AnalisisNutricionalService._obtener_preparaciones_con_ingredientes(
            menu, nivel_para_defecto
        )

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
    def _obtener_preparaciones_con_ingredientes(menu: TablaMenus, nivel_escolar=None) -> List[Dict]:
        """
        Obtiene todas las preparaciones del menú con sus ingredientes.

        Args:
            menu: Instancia del menú
            nivel_escolar: Nivel escolar opcional para obtener rango mínimo como valor por defecto

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
                ingrediente_codigo = getattr(ingrediente, 'codigo', None) or getattr(ingrediente, 'id_ingrediente_siesa', None)
                ingrediente_nombre = getattr(ingrediente, 'nombre_del_alimento', None) or getattr(ingrediente, 'nombre_ingrediente', '')

                # Buscar alimento en tabla ICBF
                alimento = TablaAlimentos2018Icbf.objects.filter(codigo=ingrediente_codigo).first()

                if not alimento:
                    alimento = TablaAlimentos2018Icbf.objects.filter(
                        nombre_del_alimento__icontains=ingrediente_nombre
                    ).first()

                if alimento:
                    # ✨ MEJORA: Usar gramaje de preparaciones como peso inicial
                    # Si existe gramaje guardado en TablaPreparacionIngredientes, usarlo
                    # Si no, usar el valor mínimo del rango como valor por defecto
                    if ing_prep.gramaje and ing_prep.gramaje > 0:
                        peso_neto_base = float(ing_prep.gramaje)
                    elif nivel_escolar and menu.id_modalidad:
                        # Obtener el mínimo del rango para este nivel y componente
                        componente = getattr(preparacion, 'id_componente', None)
                        if componente:
                            meta = MinutaPatronMeta.objects.filter(
                                id_modalidad=menu.id_modalidad,
                                id_grado_escolar_uapa=nivel_escolar,
                                id_componente=componente
                            ).first()
                            if meta and meta.peso_neto_minimo:
                                peso_neto_base = float(meta.peso_neto_minimo)
                            else:
                                peso_neto_base = 100.0
                        else:
                            peso_neto_base = 100.0
                    else:
                        peso_neto_base = 100.0

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
                        'id_ingrediente': ingrediente_codigo,
                        'nombre': ingrediente_nombre,
                        'codigo_icbf': alimento.codigo,
                        'peso_neto_base': peso_neto_base,
                        'peso_bruto_base': round(peso_bruto_base, 1),
                        'parte_comestible': parte_comestible,
                        'valores_por_100g': valores_por_100g,
                        'alimento_encontrado': True
                    })
                else:
                    # Alimento no encontrado - usar defaults
                    # ✨ MEJORA: Usar gramaje de preparaciones como peso inicial
                    if ing_prep.gramaje and ing_prep.gramaje > 0:
                        peso_neto_default = float(ing_prep.gramaje)
                    elif nivel_escolar and menu.id_modalidad:
                        # Obtener el mínimo del rango para este nivel
                        componente = getattr(preparacion, 'id_componente', None)
                        if componente:
                            meta = MinutaPatronMeta.objects.filter(
                                id_modalidad=menu.id_modalidad,
                                id_grado_escolar_uapa=nivel_escolar,
                                id_componente=componente
                            ).first()
                            if meta and meta.peso_neto_minimo:
                                peso_neto_default = float(meta.peso_neto_minimo)
                            else:
                                peso_neto_default = 100.0
                        else:
                            peso_neto_default = 100.0
                    else:
                        peso_neto_default = 100.0

                    ingredientes_data.append({
                        'id_ingrediente': ingrediente_codigo,
                        'nombre': ingrediente_nombre,
                        'peso_neto_base': peso_neto_default,
                        'peso_bruto_base': peso_neto_default,
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

        # Denominador: usar RecomendacionDiariaGradoMod (ICBF oficial) si existe,
        # si no, hacer fallback a TablaRequerimientosNutricionales.
        try:
            rec_diaria = RecomendacionDiariaGradoMod.objects.get(
                nivel_escolar_uapa=nivel_escolar,
                id_modalidades=requerimiento.id_modalidad
            )
            requerimientos_dict = {
                'calorias': float(rec_diaria.calorias_kcal),
                'proteina': float(rec_diaria.proteina_g),
                'grasa': float(rec_diaria.grasa_g),
                'cho': float(rec_diaria.cho_g),
                'calcio': float(rec_diaria.calcio_mg),
                'hierro': float(rec_diaria.hierro_mg),
                'sodio': float(rec_diaria.sodio_mg),
            }
        except RecomendacionDiariaGradoMod.DoesNotExist:
            requerimientos_dict = {
                'calorias': float(requerimiento.calorias_kcal),
                'proteina': float(requerimiento.proteina_g),
                'grasa': float(requerimiento.grasa_g),
                'cho': float(requerimiento.cho_g),
                'calcio': float(requerimiento.calcio_mg),
                'hierro': float(requerimiento.hierro_mg),
                'sodio': float(requerimiento.sodio_mg),
            }

        # Referencias de adecuación (vara de medición ICBF para semaforización)
        try:
            adecuacion_ref = AdecuacionTotalPorcentaje.objects.get(
                id_nivel_escolar_uapa=nivel_escolar,
                id_modalidad=requerimiento.id_modalidad
            )
            referencias_dict = {
                'calorias': float(adecuacion_ref.calorias_porc),
                'proteina': float(adecuacion_ref.proteina_porc),
                'grasa':    float(adecuacion_ref.grasa_porc),
                'cho':      float(adecuacion_ref.cho_porc),
                'calcio':   float(adecuacion_ref.calcio_porc),
                'hierro':   float(adecuacion_ref.hierro_porc),
                'sodio':    float(adecuacion_ref.sodio_porc),
            }
        except AdecuacionTotalPorcentaje.DoesNotExist:
            referencias_dict = None

        # Calcular porcentajes con semaforización por proximidad
        porcentajes = CalculoService.calcular_todos_porcentajes(
            totales, requerimientos_dict, referencias_dict
        )

        return {
            'nivel_escolar': {
                'id': nivel_escolar.id_grado_escolar_uapa,
                'nombre': nivel_escolar.nivel_escolar_uapa,
                'rango_edades': getattr(nivel_escolar, 'rango_edades', '')
            },
            'es_programa_actual': es_programa_actual,
            'requerimientos': requerimientos_dict,
            'referencias_adecuacion': referencias_dict,
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
                    ingrediente_codigo = ing_data.get('id_ingrediente_siesa') or ing_data.get('id_ingrediente')
                    ingrediente = TablaIngredientesSiesa.objects.filter(
                        id_ingrediente_siesa=ingrediente_codigo
                    ).first()

                    # Compatibilidad: si no existe en SIESA, crearlo a partir de ICBF
                    if not ingrediente and ingrediente_codigo:
                        alimento_icbf = TablaAlimentos2018Icbf.objects.filter(codigo=ingrediente_codigo).first()
                        if alimento_icbf:
                            ingrediente, _ = TablaIngredientesSiesa.objects.get_or_create(
                                id_ingrediente_siesa=alimento_icbf.codigo,
                                defaults={'nombre_ingrediente': alimento_icbf.nombre_del_alimento}
                            )
                    if not ingrediente:
                        continue

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

    @staticmethod
    def _recalcular_totales_analisis(analisis: TablaAnalisisNutricionalMenu) -> None:
        """
        Recalcula los totales de un análisis basándose en TablaIngredientesPorNivel.

        Args:
            analisis: Instancia del análisis a recalcular
        """
        ingredientes = TablaIngredientesPorNivel.objects.filter(id_analisis=analisis)

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
            totales['calorias'] += float(ing.calorias)
            totales['proteina'] += float(ing.proteina)
            totales['grasa'] += float(ing.grasa)
            totales['cho'] += float(ing.cho)
            totales['calcio'] += float(ing.calcio)
            totales['hierro'] += float(ing.hierro)
            totales['sodio'] += float(ing.sodio)
            totales['peso_neto'] += float(ing.peso_neto)
            totales['peso_bruto'] += float(ing.peso_bruto)

        # Actualizar análisis
        analisis.total_calorias = totales['calorias']
        analisis.total_proteina = totales['proteina']
        analisis.total_grasa = totales['grasa']
        analisis.total_cho = totales['cho']
        analisis.total_calcio = totales['calcio']
        analisis.total_hierro = totales['hierro']
        analisis.total_sodio = totales['sodio']
        analisis.total_peso_neto = totales['peso_neto']
        analisis.total_peso_bruto = totales['peso_bruto']

        # Calcular porcentajes: usar RecomendacionDiariaGradoMod (ICBF oficial) si existe,
        # si no, hacer fallback a TablaRequerimientosNutricionales.
        def _obtener_denominadores(nivel_escolar_uapa, modalidad):
            try:
                rec = RecomendacionDiariaGradoMod.objects.get(
                    nivel_escolar_uapa=nivel_escolar_uapa,
                    id_modalidades=modalidad
                )
                return {
                    'calorias': float(rec.calorias_kcal),
                    'proteina': float(rec.proteina_g),
                    'grasa': float(rec.grasa_g),
                    'cho': float(rec.cho_g),
                    'calcio': float(rec.calcio_mg),
                    'hierro': float(rec.hierro_mg),
                    'sodio': float(rec.sodio_mg),
                }
            except RecomendacionDiariaGradoMod.DoesNotExist:
                pass
            try:
                req = TablaRequerimientosNutricionales.objects.get(
                    id_nivel_escolar_uapa=nivel_escolar_uapa,
                    id_modalidad=modalidad
                )
                return {
                    'calorias': float(req.calorias_kcal),
                    'proteina': float(req.proteina_g),
                    'grasa': float(req.grasa_g),
                    'cho': float(req.cho_g),
                    'calcio': float(req.calcio_mg),
                    'hierro': float(req.hierro_mg),
                    'sodio': float(req.sodio_mg),
                }
            except TablaRequerimientosNutricionales.DoesNotExist:
                return None

        denominadores = _obtener_denominadores(
            analisis.id_nivel_escolar_uapa,
            analisis.id_menu.id_modalidad
        )

        if denominadores:
            def _pct(total, den):
                # Mantener consistencia con el resto del sistema:
                # los porcentajes de adecuacion se limitan a 100.
                return CalculoService.calcular_porcentaje_adecuacion(
                    total_actual=total,
                    requerimiento=den,
                    limitar_a_100=True,
                )

            analisis.porcentaje_calorias = _pct(totales['calorias'], denominadores['calorias'])
            analisis.porcentaje_proteina = _pct(totales['proteina'], denominadores['proteina'])
            analisis.porcentaje_grasa    = _pct(totales['grasa'],    denominadores['grasa'])
            analisis.porcentaje_cho      = _pct(totales['cho'],      denominadores['cho'])
            analisis.porcentaje_calcio   = _pct(totales['calcio'],   denominadores['calcio'])
            analisis.porcentaje_hierro   = _pct(totales['hierro'],   denominadores['hierro'])
            analisis.porcentaje_sodio    = _pct(totales['sodio'],    denominadores['sodio'])

            # Buscar referencia ICBF para semaforización por proximidad
            try:
                adecuacion_ref = AdecuacionTotalPorcentaje.objects.get(
                    id_nivel_escolar_uapa=analisis.id_nivel_escolar_uapa,
                    id_modalidad=analisis.id_menu.id_modalidad
                )
                refs = {
                    'calorias': float(adecuacion_ref.calorias_porc),
                    'proteina': float(adecuacion_ref.proteina_porc),
                    'grasa':    float(adecuacion_ref.grasa_porc),
                    'cho':      float(adecuacion_ref.cho_porc),
                    'calcio':   float(adecuacion_ref.calcio_porc),
                    'hierro':   float(adecuacion_ref.hierro_porc),
                    'sodio':    float(adecuacion_ref.sodio_porc),
                }
            except AdecuacionTotalPorcentaje.DoesNotExist:
                refs = {}

            def clasificar_estado(porcentaje, nutriente):
                ref = refs.get(nutriente)
                if ref is not None:
                    diff = abs(porcentaje - ref)
                    if diff <= 3: return 'optimo'
                    elif diff <= 5: return 'azul'
                    elif diff <= 7: return 'aceptable'
                    else: return 'alto'
                if porcentaje <= 35: return 'optimo'
                elif porcentaje <= 70: return 'aceptable'
                else: return 'alto'

            analisis.estado_calorias = clasificar_estado(analisis.porcentaje_calorias, 'calorias')
            analisis.estado_proteina = clasificar_estado(analisis.porcentaje_proteina, 'proteina')
            analisis.estado_grasa    = clasificar_estado(analisis.porcentaje_grasa,    'grasa')
            analisis.estado_cho      = clasificar_estado(analisis.porcentaje_cho,      'cho')
            analisis.estado_calcio   = clasificar_estado(analisis.porcentaje_calcio,   'calcio')
            analisis.estado_hierro   = clasificar_estado(analisis.porcentaje_hierro,   'hierro')
            analisis.estado_sodio    = clasificar_estado(analisis.porcentaje_sodio,    'sodio')

        analisis.save()

