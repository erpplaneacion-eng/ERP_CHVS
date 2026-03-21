"""
pool_service.py
Mantiene el pool de borradores pre-generados de la IA.

Para cada modalidad activa, genera borradores (sin asignar a usuario ni menú)
hasta alcanzar el mínimo configurado. Los borradores quedan en
estado='disponible_pool' listos para ser tomados por los nutricionistas.
"""

import time
import logging

from agente.models import GeneracionIA

logger = logging.getLogger(__name__)


def _crear_registros_borrador(generacion, preparaciones_validadas):
    """Crea BorradorPreparacionIA + BorradorIngredienteIA para una generación."""
    from agente.models import BorradorPreparacionIA, BorradorIngredienteIA
    from nutricion.models import TablaAlimentos2018Icbf, ComponentesAlimentos

    for prep in preparaciones_validadas:
        componente_obj = None
        if prep['id_componente']:
            try:
                componente_obj = ComponentesAlimentos.objects.get(
                    id_componente=prep['id_componente']
                )
            except ComponentesAlimentos.DoesNotExist:
                pass

        prep_borrador = BorradorPreparacionIA.objects.create(
            generacion=generacion,
            nombre_preparacion=prep['nombre'],
            componente_sugerido=componente_obj,
            estado_validacion=prep['estado_validacion'],
            observaciones=prep['observaciones'],
            procedimiento=prep.get('procedimiento', ''),
        )

        for ing in prep['ingredientes']:
            alimento = None
            if ing['estado_validacion'] == 'valido':
                try:
                    alimento = TablaAlimentos2018Icbf.objects.get(codigo=ing['codigo_icbf'])
                except TablaAlimentos2018Icbf.DoesNotExist:
                    pass

            BorradorIngredienteIA.objects.create(
                borrador_preparacion=prep_borrador,
                codigo_icbf_sugerido=ing.get('codigo_icbf', ''),
                nombre_sugerido=ing.get('nombre', ''),
                alimento_icbf=alimento,
                estado_validacion=ing['estado_validacion'],
                observaciones=ing.get('observaciones', ''),
            )


# Modalidades que participan en el pool automático
MODALIDADES_POOL = ['020511', '020701', '20501', '20502', '20503', '20507', '20510']


def rellenar_pool(min_por_modalidad=20, pausa_entre_llamadas=1.5, ids_modalidad=None):
    """
    Revisa las modalidades del pool y genera borradores hasta alcanzar min_por_modalidad.
    Ejecutar desde un hilo de background o management command.

    Args:
        min_por_modalidad: Mínimo de borradores disponibles por modalidad (default 20).
        pausa_entre_llamadas: Segundos de pausa entre llamadas a Gemini (default 1.5s).
        ids_modalidad: Lista de id_modalidades a procesar. Si es None usa MODALIDADES_POOL.

    Returns:
        dict con resumen: {modalidades, generados, errores}
    """
    from principal.models import ModalidadesDeConsumo
    from agente.services.context_builder import obtener_contexto_modalidad
    from agente.services.llm_service import generar_borrador
    from agente.services.validador import validar_preparaciones

    ids = ids_modalidad if ids_modalidad is not None else MODALIDADES_POOL
    modalidades = list(
        ModalidadesDeConsumo.objects.filter(id_modalidades__in=ids).order_by('modalidad')
    )
    total_generados = 0
    total_errores = 0

    logger.info(f"[pool_service] Iniciando relleno de pool — {len(modalidades)} modalidades, mínimo {min_por_modalidad} c/u")

    for modalidad in modalidades:
        en_pool = GeneracionIA.objects.filter(
            estado=GeneracionIA.ESTADO_POOL,
            id_modalidad=modalidad,
        ).count()

        a_generar = min_por_modalidad - en_pool
        if a_generar <= 0:
            logger.info(f"[pool_service] {modalidad.modalidad}: {en_pool} en pool — suficiente, omitiendo")
            continue

        logger.info(f"[pool_service] {modalidad.modalidad}: {en_pool} en pool — generando {a_generar}")

        for i in range(a_generar):
            generacion = GeneracionIA.objects.create(
                id_modalidad=modalidad,
                estado=GeneracionIA.ESTADO_PROCESANDO,
                usuario_solicitante=None,
            )
            try:
                contexto = obtener_contexto_modalidad(modalidad.id_modalidades)
                resultado = generar_borrador(contexto, '')

                if not resultado['ok']:
                    generacion.estado = GeneracionIA.ESTADO_ERROR
                    generacion.errores_validacion = [resultado.get('error', 'Error LLM')]
                    generacion.save()
                    total_errores += 1
                    logger.warning(f"[pool_service] Error en {modalidad.modalidad} #{i+1}: {resultado.get('error')}")
                    continue

                preparaciones_validadas = validar_preparaciones(resultado['preparaciones'])
                generacion.prompt_final = resultado['prompt']
                generacion.respuesta_cruda = resultado['respuesta_cruda']
                generacion.estado = GeneracionIA.ESTADO_POOL
                generacion.save()

                _crear_registros_borrador(generacion, preparaciones_validadas)
                total_generados += 1
                logger.info(f"[pool_service] {modalidad.modalidad} #{i+1}/{a_generar} → pool (ID {generacion.id})")

            except Exception as e:
                logger.error(f"[pool_service] Excepción en {modalidad.modalidad} #{i+1}: {e}")
                total_errores += 1
                try:
                    generacion.estado = GeneracionIA.ESTADO_ERROR
                    generacion.errores_validacion = [str(e)]
                    generacion.save()
                except Exception:
                    pass

            if i < a_generar - 1:
                time.sleep(pausa_entre_llamadas)

    logger.info(f"[pool_service] Relleno completo — generados: {total_generados}, errores: {total_errores}")
    return {
        'modalidades': len(modalidades),
        'generados': total_generados,
        'errores': total_errores,
    }
