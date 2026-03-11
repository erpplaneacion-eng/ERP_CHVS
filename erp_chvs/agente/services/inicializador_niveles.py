"""
Inicializador de niveles nutricionales para menús importados desde el agente IA.

Crea TablaAnalisisNutricionalMenu y TablaIngredientesPorNivel para los 5 niveles
educativos, usando MinutaPatronMeta como fuente de pesos y CalculoService para
los cálculos nutricionales.
"""

from decimal import Decimal

from principal.models import TablaGradosEscolaresUapa
from nutricion.models import (
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaRequerimientosNutricionales,
    MinutaPatronMeta,
)
from nutricion.services.calculo_service import CalculoService

_ORDEN_NIVELES = [
    'prescolar',
    'primaria_1_2_3',
    'primaria_4_5',
    'secundaria',
    'media_ciclo_complementario',
]


def _estado_semaforo(pct: float) -> str:
    if pct <= 35:
        return 'optimo'
    elif pct <= 70:
        return 'aceptable'
    return 'alto'


def _porcentaje_adecuacion(total: float, req_val) -> float:
    if req_val and float(req_val) > 0:
        return min(round((total / float(req_val)) * 100, 2), 100.0)
    return 0.0


def inicializar_niveles_para_menu(menu, modalidad, items: list) -> None:
    """
    Crea TablaAnalisisNutricionalMenu y TablaIngredientesPorNivel para los 5
    niveles educativos de un menú recién importado desde el agente IA.

    Debe llamarse dentro de una transaction.atomic() activa.

    Args:
        menu: instancia de TablaMenus
        modalidad: instancia de ModalidadesDeConsumo
        items: lista de tuplas (TablaPreparaciones, TablaPreparacionIngredientes,
               TablaAlimentos2018Icbf)  — una por cada ingrediente creado
    """
    if not items:
        return

    # Niveles en orden pedagógico
    niveles = sorted(
        TablaGradosEscolaresUapa.objects.all(),
        key=lambda n: (
            _ORDEN_NIVELES.index(n.id_grado_escolar_uapa)
            if n.id_grado_escolar_uapa in _ORDEN_NIVELES else 999
        ),
    )
    if not niveles:
        return

    # Pre-cargar MinutaPatronMeta para esta modalidad
    # Clave: (nivel_id, componente_id) → meta
    metas_dict = {
        (m.id_grado_escolar_uapa_id, m.id_componente_id): m
        for m in MinutaPatronMeta.objects.filter(
            id_modalidad=modalidad
        ).select_related('id_grado_escolar_uapa', 'id_componente')
    }

    # Pre-cargar requerimientos nutricionales para esta modalidad
    # Clave: nivel_id → requerimiento
    reqs_dict = {
        r.id_nivel_escolar_uapa_id: r
        for r in TablaRequerimientosNutricionales.objects.filter(id_modalidad=modalidad)
    }

    for nivel in niveles:
        analisis, _ = TablaAnalisisNutricionalMenu.objects.get_or_create(
            id_menu=menu,
            id_nivel_escolar_uapa=nivel,
            defaults={
                'total_calorias': 0, 'total_proteina': 0, 'total_grasa': 0,
                'total_cho': 0, 'total_calcio': 0, 'total_hierro': 0, 'total_sodio': 0,
                'total_peso_neto': 0, 'total_peso_bruto': 0,
            },
        )

        totales = {
            'calorias': 0.0, 'proteina': 0.0, 'grasa': 0.0, 'cho': 0.0,
            'calcio': 0.0, 'hierro': 0.0, 'sodio': 0.0,
            'peso_neto': 0.0, 'peso_bruto': 0.0,
        }
        registros_nivel = []

        for prep_real, ing_prep_real, alimento_icbf in items:
            # Evitar duplicados por unique_together (id_analisis, id_preparacion, codigo_icbf)
            if TablaIngredientesPorNivel.objects.filter(
                id_analisis=analisis,
                id_preparacion=prep_real,
                codigo_icbf=alimento_icbf.codigo,
            ).exists():
                continue

            # Resolver componente: ingrediente ICBF → preparación
            componente = ing_prep_real.id_componente or prep_real.id_componente
            componente_id = componente.id_componente if componente else None

            # Buscar peso_neto en MinutaPatronMeta (modalidad + nivel + componente)
            meta = metas_dict.get((nivel.id_grado_escolar_uapa, componente_id))
            peso_neto = float(meta.peso_neto_minimo) if (meta and meta.peso_neto_minimo) else 100.0

            # Parte comestible del catálogo ICBF (con defensa ante NULL)
            parte_comestible = float(alimento_icbf.parte_comestible_field or 100)
            parte_comestible = max(1.0, min(100.0, parte_comestible))

            # Cálculos
            peso_bruto = CalculoService.calcular_peso_bruto(peso_neto, parte_comestible)
            nutrientes = CalculoService.calcular_valores_nutricionales_alimento(alimento_icbf, peso_neto)

            registros_nivel.append(TablaIngredientesPorNivel(
                id_analisis=analisis,
                id_preparacion=prep_real,
                id_preparacion_ingrediente=ing_prep_real,
                peso_neto=Decimal(str(round(peso_neto, 2))),
                peso_bruto=Decimal(str(round(peso_bruto, 2))),
                parte_comestible=Decimal(str(round(parte_comestible, 2))),
                calorias=Decimal(str(round(nutrientes['calorias'], 2))),
                proteina=Decimal(str(round(nutrientes['proteina'], 2))),
                grasa=Decimal(str(round(nutrientes['grasa'], 2))),
                cho=Decimal(str(round(nutrientes['cho'], 2))),
                calcio=Decimal(str(round(nutrientes['calcio'], 2))),
                hierro=Decimal(str(round(nutrientes['hierro'], 2))),
                sodio=Decimal(str(round(nutrientes['sodio'], 2))),
                codigo_icbf=alimento_icbf.codigo,
            ))

            totales['calorias'] += nutrientes['calorias']
            totales['proteina'] += nutrientes['proteina']
            totales['grasa'] += nutrientes['grasa']
            totales['cho'] += nutrientes['cho']
            totales['calcio'] += nutrientes['calcio']
            totales['hierro'] += nutrientes['hierro']
            totales['sodio'] += nutrientes['sodio']
            totales['peso_neto'] += peso_neto
            totales['peso_bruto'] += peso_bruto

        if registros_nivel:
            TablaIngredientesPorNivel.objects.bulk_create(registros_nivel)

        # Actualizar totales en el análisis nutricional
        update_fields = [
            'total_calorias', 'total_proteina', 'total_grasa', 'total_cho',
            'total_calcio', 'total_hierro', 'total_sodio',
            'total_peso_neto', 'total_peso_bruto',
        ]
        analisis.total_calorias = Decimal(str(round(totales['calorias'], 2)))
        analisis.total_proteina = Decimal(str(round(totales['proteina'], 2)))
        analisis.total_grasa = Decimal(str(round(totales['grasa'], 2)))
        analisis.total_cho = Decimal(str(round(totales['cho'], 2)))
        analisis.total_calcio = Decimal(str(round(totales['calcio'], 2)))
        analisis.total_hierro = Decimal(str(round(totales['hierro'], 2)))
        analisis.total_sodio = Decimal(str(round(totales['sodio'], 2)))
        analisis.total_peso_neto = Decimal(str(round(totales['peso_neto'], 2)))
        analisis.total_peso_bruto = Decimal(str(round(totales['peso_bruto'], 2)))

        # Calcular % adecuación y semáforo si hay requerimientos configurados
        req = reqs_dict.get(nivel.id_grado_escolar_uapa)
        if req:
            pcts = {
                'calorias': _porcentaje_adecuacion(totales['calorias'], req.calorias_kcal),
                'proteina': _porcentaje_adecuacion(totales['proteina'], req.proteina_g),
                'grasa':    _porcentaje_adecuacion(totales['grasa'],    req.grasa_g),
                'cho':      _porcentaje_adecuacion(totales['cho'],      req.cho_g),
                'calcio':   _porcentaje_adecuacion(totales['calcio'],   req.calcio_mg),
                'hierro':   _porcentaje_adecuacion(totales['hierro'],   req.hierro_mg),
                'sodio':    _porcentaje_adecuacion(totales['sodio'],    req.sodio_mg),
            }
            analisis.porcentaje_calorias = Decimal(str(pcts['calorias']))
            analisis.porcentaje_proteina = Decimal(str(pcts['proteina']))
            analisis.porcentaje_grasa    = Decimal(str(pcts['grasa']))
            analisis.porcentaje_cho      = Decimal(str(pcts['cho']))
            analisis.porcentaje_calcio   = Decimal(str(pcts['calcio']))
            analisis.porcentaje_hierro   = Decimal(str(pcts['hierro']))
            analisis.porcentaje_sodio    = Decimal(str(pcts['sodio']))

            analisis.estado_calorias = _estado_semaforo(pcts['calorias'])
            analisis.estado_proteina = _estado_semaforo(pcts['proteina'])
            analisis.estado_grasa    = _estado_semaforo(pcts['grasa'])
            analisis.estado_cho      = _estado_semaforo(pcts['cho'])
            analisis.estado_calcio   = _estado_semaforo(pcts['calcio'])
            analisis.estado_hierro   = _estado_semaforo(pcts['hierro'])
            analisis.estado_sodio    = _estado_semaforo(pcts['sodio'])

            update_fields += [
                'porcentaje_calorias', 'porcentaje_proteina', 'porcentaje_grasa',
                'porcentaje_cho', 'porcentaje_calcio', 'porcentaje_hierro', 'porcentaje_sodio',
                'estado_calorias', 'estado_proteina', 'estado_grasa', 'estado_cho',
                'estado_calcio', 'estado_hierro', 'estado_sodio',
            ]

        analisis.save(update_fields=update_fields)
