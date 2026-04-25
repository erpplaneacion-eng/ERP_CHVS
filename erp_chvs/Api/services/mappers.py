"""Mappers JSON → kwargs de modelo para cada catálogo SIESA.

Cada función recibe un dict (un registro del array `data`) y retorna
los kwargs que se pasan a `update_or_create`. Sin lógica de negocio.
"""

from __future__ import annotations

from typing import Any


def map_centro_operacion(item: dict[str, Any]) -> tuple[dict, dict]:
    """CENTROS-OPERACIONES → SiesaCentroOperacion."""
    lookup = {'f285_id': item['f285_id']}
    defaults = {'f285_descripcion': item.get('f285_descripcion', '')}
    return lookup, defaults


def map_instalacion(item: dict[str, Any]) -> tuple[dict, dict]:
    """INSTALACIONES → SiesaInstalacion."""
    lookup = {'f157_id': item['f157_id']}
    defaults = {
        'f157_descripcion': item.get('f157_descripcion', ''),
        'f157_id_co': item.get('f157_id_co', ''),
    }
    return lookup, defaults


def map_tipo_documento(item: dict[str, Any]) -> tuple[dict, dict]:
    """TIPOS-DOCUMENTOS → SiesaTipoDocumento."""
    lookup = {'f021_id': item['f021_id']}
    defaults = {'f021_descripcion': item.get('f021_descripcion', '')}
    return lookup, defaults


def map_solicitante(item: dict[str, Any]) -> tuple[dict, dict]:
    """SOLICITANTES → SiesaSolicitante (payload genérico hasta que SIESA llene el catálogo)."""
    return {}, {'payload': item}


def map_item(item: dict[str, Any]) -> tuple[dict, dict]:
    """ITEMS → SiesaItem (payload genérico hasta que SIESA llene el catálogo)."""
    return {}, {'payload': item}


def map_unidad_negocio(item: dict[str, Any]) -> tuple[dict, dict]:
    """UNIDADES-NEGOCIOS → SiesaUnidadNegocio."""
    lookup = {'f281_id': item['f281_id']}
    defaults = {'f281_descripcion': item.get('f281_descripcion', '')}
    return lookup, defaults


def map_centro_costo(item: dict[str, Any]) -> tuple[dict, dict]:
    """CCOSTOS → SiesaCentroCosto."""
    lookup = {'f284_id': item['f284_id']}
    defaults = {
        'f284_descripcion': item.get('f284_descripcion', ''),
        'f284_id_co': item.get('f284_id_co', ''),
        'f284_id_un': item.get('f284_id_un', ''),
    }
    return lookup, defaults


def map_proyecto(item: dict[str, Any]) -> tuple[dict, dict]:
    """PROYECTOS → SiesaProyecto."""
    lookup = {'f107_id': item['f107_id']}
    defaults = {
        'f107_descripcion': item.get('f107_descripcion', ''),
        'f107_id_referencia': item.get('f107_id_referencia', ''),
    }
    return lookup, defaults


def map_concepto(item: dict[str, Any]) -> tuple[dict, dict]:
    """CONCEPTOS → SiesaConcepto."""
    lookup = {'f145_id': item['f145_id']}
    defaults = {
        'f145_descripcion': item.get('f145_descripcion', ''),
        'f145_ind_naturaleza': item.get('f145_ind_naturaleza', ''),
        'f145_ind_liquidacion': item.get('f145_ind_liquidacion', ''),
    }
    return lookup, defaults


def map_motivo(item: dict[str, Any]) -> tuple[dict, dict]:
    """MOTIVOS → SiesaMotivo. PK compuesta: (f146_id_concepto, f146_id)."""
    lookup = {
        'f146_id': item['f146_id'],
        'f146_id_concepto': item['f146_id_concepto'],
    }
    defaults = {'f146_ind_naturaleza': item.get('f146_ind_naturaleza', '')}
    return lookup, defaults


def map_ubicacion(item: dict[str, Any]) -> tuple[dict, dict]:
    """UBICACIONES (BODEGAS) → SiesaUbicacion."""
    lookup = {'f155_id': item['f155_id']}
    defaults = {
        'f155_descripcion': item.get('f155_descripcion', ''),
        'f150_id': item.get('f150_id', ''),
    }
    return lookup, defaults
