"""
Servicio de Gestión de Menús.

Maneja toda la lógica relacionada con menús nutricionales.
"""

from typing import Dict, List, Optional
from django.db.models import QuerySet
from django.db import transaction

from ..models import (
    TablaMenus, TablaPreparaciones, TablaIngredientesSiesa,
    TablaIngredientesPorNivel, TablaAlimentos2018Icbf,
    ComponentesAlimentos, TablaPreparacionIngredientes,
    TablaAnalisisNutricionalMenu
)
import logging

logger = logging.getLogger(__name__)
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo, TablaGradosEscolaresUapa

from .gemini_service import GeminiService
from .minuta_service import MinutaService
from .calculo_service import CalculoService


class MenuService:
    """
    Servicio para gestión de menús nutricionales.
    """

    # =================== GENERACIÓN CON IA ===================

    @staticmethod
    def generar_menu_con_ia(
        id_programa: int,
        id_modalidad: str,
        niveles_educativos: List[str] = None
    ) -> Optional[TablaMenus]:
        """
        Orquestador para generar un menú usando Inteligencia Artificial (Gemini).
        Genera menú con pesos específicos para TODOS los niveles educativos.

        Args:
            id_programa: ID del programa
            id_modalidad: ID de la modalidad de consumo
            niveles_educativos: Lista de niveles educativos (opcional, usa todos si no se especifica)

        Returns:
            TablaMenus: Menú creado con análisis nutricional por nivel
        """
        from .calculo_service import CalculoService

        # 1. Validaciones y obtención de datos base
        try:
            programa = Programa.objects.get(id=id_programa)
        except Programa.DoesNotExist:
            raise ValueError(f"El programa con ID {id_programa} no existe.")

        try:
            modalidad_obj = ModalidadesDeConsumo.objects.get(id_modalidades=id_modalidad)
        except ModalidadesDeConsumo.DoesNotExist:
            raise ValueError(f"La modalidad con ID {id_modalidad} no existe.")

        # 2. Obtener todos los niveles educativos si no se especificaron
        if niveles_educativos is None:
            niveles_educativos = list(
                TablaGradosEscolaresUapa.objects.values_list('nivel_escolar_uapa', flat=True)
            )

        # 3. Obtener minutas patrón para cada nivel
        minutas_por_nivel = {}
        for nivel in niveles_educativos:
            minuta_ctx = MinutaService.obtener_por_modalidad_y_nivel(
                modalidad_obj.modalidad,
                nivel
            )
            if minuta_ctx:
                minutas_por_nivel[nivel] = minuta_ctx
            else:
                logger.warning(f"No se encontró Minuta Patrón para '{modalidad_obj.modalidad}' y nivel '{nivel}'")

        if not minutas_por_nivel:
            raise ValueError(f"No se encontraron Minutas Patrón para '{modalidad_obj.modalidad}'")

        # 4. Llamar a Gemini con todos los niveles
        gemini = GeminiService()
        propuesta = gemini.generar_menu(
            niveles_educativos=list(minutas_por_nivel.keys()),
            minuta_patron_contexts=minutas_por_nivel
        )

        if not propuesta:
            logger.error("Gemini no devolvió una propuesta válida")
            return None

        # 5. Persistir en Base de Datos (Transaccional)
        with transaction.atomic():
            # 5.1 Crear el Menú base
            menu = TablaMenus.objects.create(
                menu=propuesta.get('nombre_menu', f"Menú IA - {modalidad_obj.modalidad}"),
                id_contrato=programa,
                id_modalidad=modalidad_obj
            )

            logger.info(f"Menú creado: {menu.menu} (ID: {menu.id_menu})")

            # 5.2 Crear preparaciones (compartidas por todos los niveles)
            preparaciones_creadas = {}

            for prep_data in propuesta.get('preparaciones', []):
                prep_nombre = prep_data.get('nombre_preparacion')
                componente_nombre = prep_data.get('componente', '')

                # Buscar componente
                componente = ComponentesAlimentos.objects.filter(
                    componente__icontains=componente_nombre
                ).first()

                # Crear preparación
                preparacion = TablaPreparaciones.objects.create(
                    preparacion=prep_nombre,
                    id_menu=menu,
                    id_componente=componente
                )
                preparaciones_creadas[prep_nombre] = preparacion

                logger.info(f"  Preparación creada: {prep_nombre}")

                # 5.3 Vincular ingredientes base (sin peso, solo relación M2M)
                ingredientes_por_nivel = prep_data.get('ingredientes_por_nivel', {})

                # Obtener todos los códigos únicos de ingredientes
                codigos_unicos = set()
                for nivel_ings in ingredientes_por_nivel.values():
                    for ing in nivel_ings:
                        codigos_unicos.add(ing.get('codigo_icbf'))

                # Crear relaciones base en TablaPreparacionIngredientes
                for codigo_icbf in codigos_unicos:
                    alimento_icbf = TablaAlimentos2018Icbf.objects.filter(codigo=codigo_icbf).first()

                    if not alimento_icbf:
                        logger.warning(f"    Alimento ICBF {codigo_icbf} no encontrado, omitiendo...")
                        continue

                    # Crear/obtener ingrediente en Siesa
                    ingrediente_siesa, created = TablaIngredientesSiesa.objects.get_or_create(
                        id_ingrediente_siesa=codigo_icbf,
                        defaults={'nombre_ingrediente': alimento_icbf.nombre_del_alimento}
                    )

                    # Vincular a preparación (sin peso)
                    TablaPreparacionIngredientes.objects.get_or_create(
                        id_preparacion=preparacion,
                        id_ingrediente_siesa=ingrediente_siesa
                    )

            # 5.4 Crear análisis nutricional POR CADA NIVEL con pesos específicos
            for nivel, nivel_data in ingredientes_por_nivel.items():
                # Convertir nombre del JSON al nombre de la BD
                nivel_bd = MenuService._convertir_nivel_json_a_bd(nivel)

                # Obtener objeto de nivel escolar
                nivel_obj = TablaGradosEscolaresUapa.objects.filter(
                    nivel_escolar_uapa=nivel_bd
                ).first()

                if not nivel_obj:
                    logger.warning(f"  Nivel '{nivel}' (BD: '{nivel_bd}') no encontrado en BD, omitiendo...")
                    continue

                # Crear análisis nutricional para este nivel
                analisis = TablaAnalisisNutricionalMenu.objects.create(
                    id_menu=menu,
                    id_nivel_escolar_uapa=nivel_obj
                )

                logger.info(f"  Análisis nutricional creado para: {nivel}")

                # 5.5 Por cada preparación, guardar ingredientes CON PESOS
                for prep_nombre, preparacion in preparaciones_creadas.items():
                    # Buscar datos de esta preparación en la propuesta
                    prep_propuesta = next(
                        (p for p in propuesta['preparaciones'] if p['nombre_preparacion'] == prep_nombre),
                        None
                    )

                    if not prep_propuesta:
                        continue

                    # Obtener ingredientes para este nivel
                    ingredientes_nivel = prep_propuesta.get('ingredientes_por_nivel', {}).get(nivel, [])

                    for ing_data in ingredientes_nivel:
                        codigo_icbf = ing_data.get('codigo_icbf')
                        peso_neto = float(ing_data.get('peso_neto', 0))

                        if peso_neto <= 0:
                            continue

                        # Obtener alimento ICBF
                        alimento_icbf = TablaAlimentos2018Icbf.objects.filter(codigo=codigo_icbf).first()

                        if not alimento_icbf:
                            continue

                        # Obtener ingrediente Siesa
                        ingrediente_siesa = TablaIngredientesSiesa.objects.filter(
                            id_ingrediente_siesa=codigo_icbf
                        ).first()

                        if not ingrediente_siesa:
                            continue

                        preparacion_ingrediente, _ = TablaPreparacionIngredientes.objects.get_or_create(
                            id_preparacion=preparacion,
                            id_ingrediente_siesa=alimento_icbf
                        )

                        # Calcular valores nutricionales
                        valores_nutricionales = CalculoService.calcular_valores_nutricionales_alimento(
                            alimento_icbf,
                            peso_neto
                        )

                        # Calcular peso bruto
                        parte_comestible = float(alimento_icbf.parte_comestible_field or 100)
                        peso_bruto = CalculoService.calcular_peso_bruto(peso_neto, parte_comestible)

                        # ✅ GUARDAR EN TablaIngredientesPorNivel con pesos y valores calculados
                        TablaIngredientesPorNivel.objects.create(
                            id_analisis=analisis,
                            id_preparacion=preparacion,
                            id_preparacion_ingrediente=preparacion_ingrediente,
                            id_ingrediente_siesa=ingrediente_siesa,
                            peso_neto=peso_neto,
                            peso_bruto=peso_bruto,
                            parte_comestible=parte_comestible,
                            calorias=valores_nutricionales['calorias'],
                            proteina=valores_nutricionales['proteina'],
                            grasa=valores_nutricionales['grasa'],
                            cho=valores_nutricionales['cho'],
                            calcio=valores_nutricionales['calcio'],
                            hierro=valores_nutricionales['hierro'],
                            sodio=valores_nutricionales['sodio']
                        )

                        logger.info(f"    [{nivel}] {ingrediente_siesa.nombre_ingrediente}: {peso_neto}g")

                # 5.6 Calcular totales del análisis nutricional
                MenuService._actualizar_totales_analisis(analisis)

            logger.info(f"✅ Menú generado exitosamente con IA para {len(minutas_por_nivel)} niveles")
            return menu

    @staticmethod
    def _convertir_nivel_json_a_bd(nivel_json: str) -> str:
        """
        Convierte un nombre de nivel del JSON de minutas al nombre en la BD.

        Args:
            nivel_json: Nombre del nivel en el JSON (ej: "Preescolar")

        Returns:
            Nombre del nivel en la BD (ej: "prescolar")
        """
        # Mapeo inverso: de JSON a BD
        MAPEO_INVERSO = {
            'Preescolar': 'prescolar',
            'Primaria (primero, segundo y tercero)': 'primaria_1_2_3',
            'Primaria (1ro, 2do y 3ro)': 'primaria_1_2_3',
            'Primaria (cuarto y quinto)': 'primaria_4_5',
            'Primaria (4to y 5to)': 'primaria_4_5',
            'Secundaria': 'secundaria',
            'Nivel medio y ciclo complementario': 'media_ciclo_complementario',
            'Media y Ciclo Complementario': 'media_ciclo_complementario',
        }
        return MAPEO_INVERSO.get(nivel_json, nivel_json)

    @staticmethod
    def _actualizar_totales_analisis(analisis: TablaAnalisisNutricionalMenu):
        """
        Calcula y actualiza los totales nutricionales de un análisis.
        """
        ingredientes = analisis.ingredientes_configurados.all()

        total_calorias = sum(float(ing.calorias) for ing in ingredientes)
        total_proteina = sum(float(ing.proteina) for ing in ingredientes)
        total_grasa = sum(float(ing.grasa) for ing in ingredientes)
        total_cho = sum(float(ing.cho) for ing in ingredientes)
        total_calcio = sum(float(ing.calcio) for ing in ingredientes)
        total_hierro = sum(float(ing.hierro) for ing in ingredientes)
        total_sodio = sum(float(ing.sodio) for ing in ingredientes)

        # Actualizar análisis
        analisis.total_calorias = total_calorias
        analisis.total_proteina = total_proteina
        analisis.total_grasa = total_grasa
        analisis.total_cho = total_cho
        analisis.total_calcio = total_calcio
        analisis.total_hierro = total_hierro
        analisis.total_sodio = total_sodio
        analisis.save()

        logger.info(f"    Totales calculados: {total_calorias:.1f} kcal, {total_proteina:.1f}g prot")

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
    @transaction.atomic
    def copiar_modalidad_completa(programa_origen_id: int, programa_destino_id: int, modalidad_id: str) -> int:
        """
        Copia todos los menús de una modalidad desde programa_origen a programa_destino.

        Copia la jerarquía completa:
            TablaMenus → TablaPreparaciones → TablaPreparacionIngredientes
            → TablaAnalisisNutricionalMenu → TablaIngredientesPorNivel

        Args:
            programa_origen_id: ID del programa fuente
            programa_destino_id: ID del programa destino
            modalidad_id: ID de la modalidad a copiar

        Returns:
            Número de menús copiados al programa destino

        Raises:
            ValueError: Si el programa destino ya tiene menús para esta modalidad
        """
        # 1. Validar que destino no tenga menús existentes para esta modalidad
        if TablaMenus.objects.filter(
            id_contrato_id=programa_destino_id,
            id_modalidad_id=modalidad_id
        ).exists():
            raise ValueError("El programa destino ya tiene menús para esta modalidad.")

        # 2. Obtener menús origen con toda la jerarquía prefetcheada
        menus_origen = TablaMenus.objects.filter(
            id_contrato_id=programa_origen_id,
            id_modalidad_id=modalidad_id
        ).prefetch_related(
            'preparaciones__ingredientes',
            'analisis_nutricionales__ingredientes_configurados'
        )

        prep_map = {}     # {old_prep_id: new_prep_instance}
        analisis_map = {} # {old_analisis_id: new_analisis_instance}

        for menu_origen in menus_origen:
            # Crear nuevo menú (save() auto-calcula semana)
            nuevo_menu = TablaMenus.objects.create(
                menu=menu_origen.menu,
                id_modalidad_id=modalidad_id,
                id_contrato_id=programa_destino_id
            )

            # Copiar preparaciones + ingredientes base (TablaPreparacionIngredientes)
            for prep_origen in menu_origen.preparaciones.all():
                nueva_prep = TablaPreparaciones.objects.create(
                    preparacion=prep_origen.preparacion,
                    id_menu=nuevo_menu,
                    id_componente=prep_origen.id_componente
                )
                prep_map[prep_origen.id_preparacion] = nueva_prep

                nuevos_ingredientes = [
                    TablaPreparacionIngredientes(
                        id_preparacion=nueva_prep,
                        id_ingrediente_siesa=ing.id_ingrediente_siesa,
                        gramaje=ing.gramaje
                    )
                    for ing in prep_origen.ingredientes.all()
                ]
                if nuevos_ingredientes:
                    TablaPreparacionIngredientes.objects.bulk_create(nuevos_ingredientes)

            # Copiar análisis nutricional por nivel + pesos por nivel
            for analisis_origen in menu_origen.analisis_nutricionales.all():
                nuevo_analisis = TablaAnalisisNutricionalMenu.objects.create(
                    id_menu=nuevo_menu,
                    id_nivel_escolar_uapa=analisis_origen.id_nivel_escolar_uapa,
                    total_calorias=analisis_origen.total_calorias,
                    total_proteina=analisis_origen.total_proteina,
                    total_grasa=analisis_origen.total_grasa,
                    total_cho=analisis_origen.total_cho,
                    total_calcio=analisis_origen.total_calcio,
                    total_hierro=analisis_origen.total_hierro,
                    total_sodio=analisis_origen.total_sodio,
                    total_peso_neto=analisis_origen.total_peso_neto,
                    total_peso_bruto=analisis_origen.total_peso_bruto,
                    porcentaje_calorias=analisis_origen.porcentaje_calorias,
                    porcentaje_proteina=analisis_origen.porcentaje_proteina,
                    porcentaje_grasa=analisis_origen.porcentaje_grasa,
                    porcentaje_cho=analisis_origen.porcentaje_cho,
                    porcentaje_calcio=analisis_origen.porcentaje_calcio,
                    porcentaje_hierro=analisis_origen.porcentaje_hierro,
                    porcentaje_sodio=analisis_origen.porcentaje_sodio,
                    estado_calorias=analisis_origen.estado_calorias,
                    estado_proteina=analisis_origen.estado_proteina,
                    estado_grasa=analisis_origen.estado_grasa,
                    estado_cho=analisis_origen.estado_cho,
                    estado_calcio=analisis_origen.estado_calcio,
                    estado_hierro=analisis_origen.estado_hierro,
                    estado_sodio=analisis_origen.estado_sodio,
                )
                analisis_map[analisis_origen.id_analisis] = nuevo_analisis

                # Copiar TablaIngredientesPorNivel (pesos por nivel educativo)
                nuevos_niveles = []
                for ing_nivel in analisis_origen.ingredientes_configurados.all():
                    if ing_nivel.id_preparacion_id not in prep_map:
                        continue

                    codigo_icbf = ing_nivel.codigo_icbf
                    nueva_preparacion = prep_map[ing_nivel.id_preparacion_id]
                    if not codigo_icbf:
                        continue

                    preparacion_ingrediente = TablaPreparacionIngredientes.objects.filter(
                        id_preparacion=nueva_preparacion,
                        id_ingrediente_siesa_id=codigo_icbf
                    ).first()
                    if not preparacion_ingrediente:
                        continue

                    nuevos_niveles.append(
                        TablaIngredientesPorNivel(
                            id_analisis=nuevo_analisis,
                            id_preparacion=nueva_preparacion,
                            id_preparacion_ingrediente=preparacion_ingrediente,
                            id_ingrediente_siesa=ing_nivel.id_ingrediente_siesa,
                            codigo_icbf=codigo_icbf,
                            peso_neto=ing_nivel.peso_neto,
                            peso_bruto=ing_nivel.peso_bruto,
                            parte_comestible=ing_nivel.parte_comestible,
                            calorias=ing_nivel.calorias,
                            proteina=ing_nivel.proteina,
                            grasa=ing_nivel.grasa,
                            cho=ing_nivel.cho,
                            calcio=ing_nivel.calcio,
                            hierro=ing_nivel.hierro,
                            sodio=ing_nivel.sodio,
                        )
                    )
                if nuevos_niveles:
                    TablaIngredientesPorNivel.objects.bulk_create(nuevos_niveles)

        total_copiados = TablaMenus.objects.filter(
            id_contrato_id=programa_destino_id,
            id_modalidad_id=modalidad_id
        ).count()
        logger.info(
            f"✅ Copia de modalidad completada: {total_copiados} menús copiados "
            f"(programa {programa_origen_id} → {programa_destino_id}, modalidad {modalidad_id})"
        )
        return total_copiados

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
