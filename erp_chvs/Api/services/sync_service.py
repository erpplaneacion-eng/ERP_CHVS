"""Servicio de sincronización full de catálogos SIESA.

Descarga cada catálogo completo y hace upsert en las tablas locales.
Sin lógica delta (full sync siempre) — los endpoints actuales de SIESA
no exponen filtro por fecha de modificación.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from Api.models import (
    SiesaCentroCosto,
    SiesaCentroOperacion,
    SiesaConcepto,
    SiesaInstalacion,
    SiesaItem,
    SiesaMotivo,
    SiesaProyecto,
    SiesaSolicitante,
    SiesaSyncLog,
    SiesaTipoDocumento,
    SiesaUbicacion,
    SiesaUnidadNegocio,
)
from Api.services import mappers as mp
from Api.services.siesa_client import ENDPOINTS, SiesaClient, SiesaClientError

logger = logging.getLogger('Api')


CATALOGO_CONFIG = [
    {
        'endpoint': 'CENTROS-OPERACIONES',
        'modelo': SiesaCentroOperacion,
        'mapper': mp.map_centro_operacion,
        'con_lookup': True,
    },
    {
        'endpoint': 'INSTALACIONES',
        'modelo': SiesaInstalacion,
        'mapper': mp.map_instalacion,
        'con_lookup': True,
    },
    {
        'endpoint': 'TIPOS-DOCUMENTOS',
        'modelo': SiesaTipoDocumento,
        'mapper': mp.map_tipo_documento,
        'con_lookup': True,
    },
    {
        'endpoint': 'SOLICITANTES',
        'modelo': SiesaSolicitante,
        'mapper': mp.map_solicitante,
        'con_lookup': False,
    },
    {
        'endpoint': 'ITEMS',
        'modelo': SiesaItem,
        'mapper': mp.map_item,
        'con_lookup': False,
    },
    {
        'endpoint': 'UNIDADES-NEGOCIOS',
        'modelo': SiesaUnidadNegocio,
        'mapper': mp.map_unidad_negocio,
        'con_lookup': True,
    },
    {
        'endpoint': 'CCOSTOS',
        'modelo': SiesaCentroCosto,
        'mapper': mp.map_centro_costo,
        'con_lookup': True,
    },
    {
        'endpoint': 'PROYECTOS',
        'modelo': SiesaProyecto,
        'mapper': mp.map_proyecto,
        'con_lookup': True,
    },
    {
        'endpoint': 'CONCEPTOS',
        'modelo': SiesaConcepto,
        'mapper': mp.map_concepto,
        'con_lookup': True,
    },
    {
        'endpoint': 'MOTIVOS',
        'modelo': SiesaMotivo,
        'mapper': mp.map_motivo,
        'con_lookup': True,
    },
    {
        'endpoint': 'UBICACIONES',
        'modelo': SiesaUbicacion,
        'mapper': mp.map_ubicacion,
        'con_lookup': True,
    },
]

ENDPOINT_A_CONFIG = {c['endpoint']: c for c in CATALOGO_CONFIG}


def _extraer_lista(payload: Any) -> list:
    """Extrae el array de registros del payload de SIESA (siempre en `data`)."""
    if isinstance(payload, dict):
        return payload.get('data') or []
    if isinstance(payload, list):
        return payload
    return []


def sincronizar_catalogo(
    client: SiesaClient,
    endpoint: str,
    modelo,
    mapper: Callable,
    con_lookup: bool,
    dry_run: bool = False,
) -> SiesaSyncLog:
    """Sincroniza un catálogo individual. Retorna el SiesaSyncLog resultante."""
    inicio = datetime.now(timezone.utc)
    log = SiesaSyncLog(endpoint=endpoint, inicio=inicio)
    insertados = actualizados = errores = 0

    try:
        payload = client.get(endpoint)
    except SiesaClientError as exc:
        log.fin = datetime.now(timezone.utc)
        log.estado = SiesaSyncLog.ESTADO_ERROR
        log.detalle_error = str(exc)
        if not dry_run:
            log.save()
        logger.error('Error al obtener %s: %s', endpoint, exc)
        return log

    registros = _extraer_lista(payload)
    logger.info('%s: %s registros recibidos', endpoint, len(registros))

    for item in registros:
        try:
            lookup, defaults = mapper(item)
            if dry_run:
                insertados += 1
                continue
            if con_lookup and lookup:
                _, created = modelo.objects.update_or_create(defaults=defaults, **lookup)
                if created:
                    insertados += 1
                else:
                    actualizados += 1
            else:
                modelo.objects.create(**defaults)
                insertados += 1
        except Exception as exc:
            errores += 1
            logger.warning('%s: error procesando registro %s: %s', endpoint, item, exc)

    log.fin = datetime.now(timezone.utc)
    log.registros_insertados = insertados
    log.registros_actualizados = actualizados
    log.errores = errores
    log.estado = SiesaSyncLog.ESTADO_ERROR if errores and not (insertados + actualizados) else SiesaSyncLog.ESTADO_OK

    if not dry_run:
        log.save()

    logger.info(
        '%s: insertados=%s, actualizados=%s, errores=%s',
        endpoint, insertados, actualizados, errores,
    )
    return log


def sincronizar_todo(endpoint_filtro: str | None = None, dry_run: bool = False) -> list[SiesaSyncLog]:
    """Sincroniza todos los catálogos (o uno específico si se indica).

    Retorna lista de SiesaSyncLog con resultados por catálogo.
    """
    if endpoint_filtro and endpoint_filtro not in ENDPOINT_A_CONFIG:
        raise ValueError(
            f"Endpoint '{endpoint_filtro}' no reconocido. Opciones: {', '.join(ENDPOINT_A_CONFIG)}"
        )

    configs = [ENDPOINT_A_CONFIG[endpoint_filtro]] if endpoint_filtro else CATALOGO_CONFIG

    try:
        client = SiesaClient()
    except SiesaClientError as exc:
        raise RuntimeError(str(exc)) from exc

    resultados = []
    with client:
        for cfg in configs:
            log = sincronizar_catalogo(
                client=client,
                endpoint=cfg['endpoint'],
                modelo=cfg['modelo'],
                mapper=cfg['mapper'],
                con_lookup=cfg['con_lookup'],
                dry_run=dry_run,
            )
            resultados.append(log)

    return resultados
