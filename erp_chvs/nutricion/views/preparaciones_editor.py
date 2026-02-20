from decimal import Decimal, InvalidOperation
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max, Min
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from principal.models import TablaGradosEscolaresUapa

from ..models import (
    AdecuacionTotalPorcentaje,
    MinutaPatronMeta,
    RecomendacionDiariaGradoMod,
    TablaAlimentos2018Icbf,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaMenus,
    TablaPreparacionIngredientes,
    TablaPreparaciones,
    TablaRequerimientosNutricionales,
)
from ..services.calculo_service import CalculoService


def _resolver_grupo_y_rango(menu, preparacion, ingrediente_icbf):
    """
    Resuelve grupo de alimentos y rango [min, max] para un ingrediente dentro de una preparación.
    Usa MinutaPatronMeta por modalidad + componente + grupo.

    NOTA: Esta función agrega MIN/MAX de TODOS los niveles escolares.
    Para rangos específicos por nivel, usar _resolver_grupo_y_rango_por_nivel()
    """
    grupo = None
    componente_ingrediente = getattr(ingrediente_icbf, 'id_componente', None)
    if componente_ingrediente and componente_ingrediente.id_grupo_alimentos:
        grupo = componente_ingrediente.id_grupo_alimentos
    elif preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos:
        grupo = preparacion.id_componente.id_grupo_alimentos

    if not grupo:
        return {
            'grupo_id': None,
            'grupo_nombre': 'SIN GRUPO',
            'minimo': None,
            'maximo': None
        }

    metas = MinutaPatronMeta.objects.filter(
        id_modalidad=menu.id_modalidad,
        id_grupo_alimentos=grupo
    )
    if preparacion.id_componente:
        metas = metas.filter(id_componente=preparacion.id_componente)

    agregados = metas.aggregate(
        minimo=Min('peso_neto_minimo'),
        maximo=Max('peso_neto_maximo')
    )

    return {
        'grupo_id': grupo.id_grupo_alimentos,
        'grupo_nombre': grupo.grupo_alimentos,
        'minimo': float(agregados['minimo']) if agregados['minimo'] is not None else None,
        'maximo': float(agregados['maximo']) if agregados['maximo'] is not None else None
    }


def _resolver_grupo_y_rango_por_nivel(menu, preparacion, ingrediente_icbf, nivel_escolar):
    """
    Resuelve grupo de alimentos y rango [min, max] para un ingrediente
    FILTRADO POR NIVEL ESCOLAR ESPECÍFICO.
    """
    grupo = None
    componente_ingrediente = getattr(ingrediente_icbf, 'id_componente', None)
    if componente_ingrediente and componente_ingrediente.id_grupo_alimentos:
        grupo = componente_ingrediente.id_grupo_alimentos
    elif preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos:
        grupo = preparacion.id_componente.id_grupo_alimentos

    if not grupo:
        return {
            'grupo_id': None,
            'grupo_nombre': 'SIN GRUPO',
            'minimo': None,
            'maximo': None,
            'rango_abierto': False
        }

    metas = MinutaPatronMeta.objects.filter(
        id_modalidad=menu.id_modalidad,
        id_grado_escolar_uapa=nivel_escolar,
        id_grupo_alimentos=grupo
    )

    # Primero intentamos buscar una meta específica para el componente
    meta = None
    if preparacion.id_componente:
        meta = metas.filter(id_componente=preparacion.id_componente).first()

    # Si no hay meta específica o no hay componente, buscamos la primera disponible para el grupo
    if not meta:
        meta = metas.first()

    if meta:
        minimo = float(meta.peso_neto_minimo) if meta.peso_neto_minimo is not None else None
        maximo = float(meta.peso_neto_maximo) if meta.peso_neto_maximo is not None else None

        if maximo == 0:
            maximo = None

        return {
            'grupo_id': grupo.id_grupo_alimentos,
            'grupo_nombre': grupo.grupo_alimentos,
            'minimo': minimo,
            'maximo': maximo,
            'rango_abierto': minimo is not None and maximo is None
        }
    return {
        'grupo_id': grupo.id_grupo_alimentos,
        'grupo_nombre': grupo.grupo_alimentos,
        'minimo': None,
        'maximo': None,
        'rango_abierto': False
    }


NUTRIENTES_ANALISIS = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio']


def _obtener_requerimientos_por_nivel(modalidad):
    """
    Denominadores nutricionales por nivel.
    Prioriza RecomendacionDiariaGradoMod (ICBF oficial); hace fallback a
    TablaRequerimientosNutricionales para niveles sin entrada nueva.
    """
    requerimientos_por_nivel = {}
    if not modalidad:
        return requerimientos_por_nivel

    # 1. Intentar usar RecomendacionDiariaGradoMod
    try:
        for rec in RecomendacionDiariaGradoMod.objects.filter(
            id_modalidades=modalidad
        ).select_related('nivel_escolar_uapa'):
            nivel_id = rec.nivel_escolar_uapa.id_grado_escolar_uapa
            requerimientos_por_nivel[nivel_id] = {
                'calorias': float(rec.calorias_kcal),
                'proteina': float(rec.proteina_g),
                'grasa': float(rec.grasa_g),
                'cho': float(rec.cho_g),
                'calcio': float(rec.calcio_mg),
                'hierro': float(rec.hierro_mg),
                'sodio': float(rec.sodio_mg),
            }
    except Exception:
        pass

    # 2. Fallback: TablaRequerimientosNutricionales para niveles no cubiertos
    for req in TablaRequerimientosNutricionales.objects.filter(
        id_modalidad=modalidad
    ).select_related('id_nivel_escolar_uapa'):
        nivel_id = req.id_nivel_escolar_uapa.id_grado_escolar_uapa
        if nivel_id not in requerimientos_por_nivel:
            requerimientos_por_nivel[nivel_id] = {
                'calorias': float(req.calorias_kcal),
                'proteina': float(req.proteina_g),
                'grasa': float(req.grasa_g),
                'cho': float(req.cho_g),
                'calcio': float(req.calcio_mg),
                'hierro': float(req.hierro_mg),
                'sodio': float(req.sodio_mg),
            }

    return requerimientos_por_nivel


def _obtener_referencias_por_nivel(modalidad):
    """
    Porcentajes de adecuación de referencia (AdecuacionTotalPorcentaje).
    Se usan como 'vara de medición' para la semaforización por proximidad.
    """
    referencias_por_nivel = {}
    if not modalidad:
        return referencias_por_nivel

    try:
        for ref in AdecuacionTotalPorcentaje.objects.filter(
            id_modalidad=modalidad
        ).select_related('id_nivel_escolar_uapa'):
            nivel_id = ref.id_nivel_escolar_uapa.id_grado_escolar_uapa
            referencias_por_nivel[nivel_id] = {
                'calorias': float(ref.calorias_porc),
                'proteina': float(ref.proteina_porc),
                'grasa':    float(ref.grasa_porc),
                'cho':      float(ref.cho_porc),
                'calcio':   float(ref.calcio_porc),
                'hierro':   float(ref.hierro_porc),
                'sodio':    float(ref.sodio_porc),
            }
    except Exception:
        pass

    return referencias_por_nivel


def _obtener_ingredientes_configurados_por_analisis(analisis):
    ingredientes_configurados = {}
    ingredientes_nivel = TablaIngredientesPorNivel.objects.filter(
        id_analisis=analisis
    ).select_related('id_preparacion')

    for ing_nivel in ingredientes_nivel:
        key = f"{ing_nivel.id_preparacion_id}_{ing_nivel.codigo_icbf}"
        ingredientes_configurados[key] = {
            'peso_neto': float(ing_nivel.peso_neto),
            'peso_bruto': float(ing_nivel.peso_bruto),
            'calorias': float(ing_nivel.calorias),
            'proteina': float(ing_nivel.proteina),
            'grasa': float(ing_nivel.grasa),
            'cho': float(ing_nivel.cho),
            'calcio': float(ing_nivel.calcio),
            'hierro': float(ing_nivel.hierro),
            'sodio': float(ing_nivel.sodio)
        }

    return ingredientes_configurados


def _construir_filas_nivel(menu, nivel, preparaciones, ingredientes_configurados):
    filas_nivel = []
    relaciones = TablaPreparacionIngredientes.objects.filter(
        id_preparacion__in=preparaciones
    ).select_related(
        'id_preparacion',
        'id_ingrediente_siesa',
        'id_ingrediente_siesa__id_componente',
        'id_ingrediente_siesa__id_componente__id_grupo_alimentos'
    )

    for rel in relaciones:
        rango = _resolver_grupo_y_rango_por_nivel(
            menu,
            rel.id_preparacion,
            rel.id_ingrediente_siesa,
            nivel
        )

        key = f"{rel.id_preparacion_id}_{rel.id_ingrediente_siesa.codigo}"
        if key in ingredientes_configurados:
            peso_neto = ingredientes_configurados[key]['peso_neto']
            valores_nutricionales = ingredientes_configurados[key]
        else:
            # Si no hay configuración específica para el nivel, intentamos usar el gramaje de la preparación
            # Pero si el gramaje es 0 o no existe, usamos el mínimo del rango
            gramaje_base = float(rel.gramaje) if rel.gramaje else 0
            minimo_rango = float(rango['minimo']) if rango['minimo'] is not None else 0

            if gramaje_base > 0:
                peso_neto = gramaje_base
            elif minimo_rango > 0:
                peso_neto = minimo_rango
            else:
                peso_neto = 100.0

            valores_nutricionales = CalculoService.calcular_valores_nutricionales_alimento(
                rel.id_ingrediente_siesa,
                peso_neto
            ) if rel.id_ingrediente_siesa else {}

        filas_nivel.append({
            'id_preparacion': rel.id_preparacion.id_preparacion,
            'preparacion': rel.id_preparacion.preparacion,
            'id_ingrediente': rel.id_ingrediente_siesa.codigo,
            'ingrediente': rel.id_ingrediente_siesa.nombre_del_alimento,
            'codigo_icbf': rel.id_ingrediente_siesa.codigo,
            'grupo': rango['grupo_nombre'],
            'minimo': rango['minimo'],
            'maximo': rango['maximo'],
            'rango_abierto': rango.get('rango_abierto', False),
            'peso_neto': peso_neto,
            'parte_comestible': float(rel.id_ingrediente_siesa.parte_comestible_field or 100),
            **valores_nutricionales
        })

    return filas_nivel


def _calcular_totales_filas(filas_nivel):
    return {
        'calorias': sum(f.get('calorias', 0) for f in filas_nivel),
        'proteina': sum(f.get('proteina', 0) for f in filas_nivel),
        'grasa': sum(f.get('grasa', 0) for f in filas_nivel),
        'cho': sum(f.get('cho', 0) for f in filas_nivel),
        'calcio': sum(f.get('calcio', 0) for f in filas_nivel),
        'hierro': sum(f.get('hierro', 0) for f in filas_nivel),
        'sodio': sum(f.get('sodio', 0) for f in filas_nivel),
        'peso_neto': sum(f.get('peso_neto', 0) for f in filas_nivel)
    }


def _calcular_porcentajes_y_estados(totales, requerimientos, referencias=None):
    """
    Calcula porcentajes de adecuación y estados de semaforización.

    Si se proporciona 'referencias' (porcentajes de adecuación de referencia ICBF),
    usa lógica de proximidad de 4 colores:
      ≤3 pts  → optimo   (verde)
      3-5 pts → azul     (azul)
      5-7 pts → aceptable (amarillo)
      >7 pts  → alto     (rojo)

    Si no hay referencia, usa los rangos absolutos originales (35 / 70 %).
    """
    porcentajes = {}
    estados = {}

    for nutriente in NUTRIENTES_ANALISIS:
        if requerimientos.get(nutriente, 0) > 0:
            porcentaje = (totales[nutriente] / requerimientos[nutriente]) * 100
            porcentajes[nutriente] = round(porcentaje, 1)

            ref = (referencias or {}).get(nutriente)
            if ref is not None:
                diff = abs(porcentaje - float(ref))
                if diff <= 3:
                    estados[nutriente] = 'optimo'
                elif diff <= 5:
                    estados[nutriente] = 'azul'
                elif diff <= 7:
                    estados[nutriente] = 'aceptable'
                else:
                    estados[nutriente] = 'alto'
            else:
                if porcentaje <= 35:
                    estados[nutriente] = 'optimo'
                elif porcentaje <= 70:
                    estados[nutriente] = 'aceptable'
                else:
                    estados[nutriente] = 'alto'
        else:
            porcentajes[nutriente] = 0
            estados[nutriente] = 'optimo'

    return porcentajes, estados


@login_required
def vista_preparaciones_editor(request, id_menu):
    menu = get_object_or_404(
        TablaMenus.objects.select_related('id_modalidad', 'id_contrato'),
        id_menu=id_menu
    )

    # Orden pedagógico deseado: prescolar → primaria 1-3 → primaria 4-5 → secundaria → media
    # Los IDs son CharField, por lo que el sort alfabético ("100","1011","12"…) no sirve.
    _ORDEN_NIVELES = ['100', '123', '45', '6789', '1011']
    _todos_niveles = {n.id_grado_escolar_uapa: n for n in TablaGradosEscolaresUapa.objects.all()}
    niveles_escolares = sorted(
        _todos_niveles.values(),
        key=lambda n: _ORDEN_NIVELES.index(str(n.id_grado_escolar_uapa))
                      if str(n.id_grado_escolar_uapa) in _ORDEN_NIVELES else 999
    )
    requerimientos_por_nivel = _obtener_requerimientos_por_nivel(menu.id_modalidad)
    referencias_por_nivel = _obtener_referencias_por_nivel(menu.id_modalidad)

    preparaciones = list(
        TablaPreparaciones.objects.filter(id_menu=menu)
        .select_related('id_componente')
        .order_by('preparacion')
    )

    niveles_data = []

    for nivel in niveles_escolares:
        analisis, _ = TablaAnalisisNutricionalMenu.objects.get_or_create(
            id_menu=menu,
            id_nivel_escolar_uapa=nivel
        )

        ingredientes_configurados = _obtener_ingredientes_configurados_por_analisis(analisis)
        filas_nivel = _construir_filas_nivel(menu, nivel, preparaciones, ingredientes_configurados)
        totales = _calcular_totales_filas(filas_nivel)
        requerimientos = requerimientos_por_nivel.get(nivel.id_grado_escolar_uapa, {})
        referencias = referencias_por_nivel.get(nivel.id_grado_escolar_uapa, {})
        porcentajes, estados = _calcular_porcentajes_y_estados(totales, requerimientos, referencias)

        niveles_data.append({
            'nivel': {
                'id': nivel.id_grado_escolar_uapa,
                'nombre': nivel.nivel_escolar_uapa
            },
            'filas': filas_nivel,
            'totales': totales,
            'requerimientos': requerimientos,
            'referencias': referencias,
            'porcentajes': porcentajes,
            'estados': estados,
            'id_analisis': analisis.id_analisis
        })

    ingredientes_catalogo = list(
        TablaAlimentos2018Icbf.objects.values('codigo', 'nombre_del_alimento').order_by('nombre_del_alimento')
    )
    preparaciones_catalogo = [
        {'id_preparacion': p.id_preparacion, 'preparacion': p.preparacion}
        for p in preparaciones
    ]

    context = {
        'menu': menu,
        'niveles_data': niveles_data,
        'niveles_json': json.dumps(niveles_data, default=str),
        'ingredientes_json': json.dumps(ingredientes_catalogo),
        'preparaciones_json': json.dumps(preparaciones_catalogo),
    }
    return render(request, 'nutricion/preparaciones_editor.html', context)


@login_required
def api_rango_ingrediente_preparacion(request, id_menu):
    """Retorna grupo y rango permitido para una combinación preparación + ingrediente."""
    id_preparacion = request.GET.get('id_preparacion')
    id_ingrediente = request.GET.get('id_ingrediente')
    if not id_preparacion or not id_ingrediente:
        return JsonResponse({'success': False, 'error': 'Parámetros requeridos: id_preparacion, id_ingrediente'}, status=400)

    menu = get_object_or_404(TablaMenus, id_menu=id_menu)
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion, id_menu=menu)
    ingrediente = get_object_or_404(TablaAlimentos2018Icbf, codigo=id_ingrediente)

    rango = _resolver_grupo_y_rango(menu, preparacion, ingrediente)
    return JsonResponse({'success': True, **rango})


@login_required
@csrf_exempt
def api_guardar_preparaciones_editor(request, id_menu):
    """Guarda filas del editor de preparaciones validando gramajes por rango."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    menu = get_object_or_404(TablaMenus, id_menu=id_menu)
    try:
        payload = json.loads(request.body)
        filas = payload.get('filas', [])
    except Exception:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    errores = []
    guardadas = 0

    with transaction.atomic():
        for idx, fila in enumerate(filas):
            try:
                id_preparacion = fila.get('id_preparacion')
                id_ingrediente = str(fila.get('id_ingrediente', '')).strip()
                preparacion_nombre = str(fila.get('preparacion_nombre', '')).strip()
                gramaje_raw = fila.get('gramaje')
                if not id_ingrediente:
                    continue
                if id_preparacion:
                    preparacion = TablaPreparaciones.objects.get(id_preparacion=id_preparacion, id_menu=menu)
                else:
                    if not preparacion_nombre:
                        errores.append(f"Fila {idx + 1}: nombre de preparación requerido")
                        continue
                    preparacion, _ = TablaPreparaciones.objects.get_or_create(
                        id_menu=menu,
                        preparacion=preparacion_nombre,
                        defaults={'id_componente': None}
                    )
                ingrediente = TablaAlimentos2018Icbf.objects.get(codigo=id_ingrediente)

                gramaje = None
                if gramaje_raw not in (None, '', 'null'):
                    gramaje = Decimal(str(gramaje_raw))
                    if gramaje < 0:
                        raise InvalidOperation('Gramaje negativo')

                rango = _resolver_grupo_y_rango(menu, preparacion, ingrediente)
                minimo = Decimal(str(rango['minimo'])) if rango['minimo'] is not None else None
                maximo = Decimal(str(rango['maximo'])) if rango['maximo'] is not None else None

                if gramaje is not None and minimo is not None and gramaje < minimo:
                    errores.append(f"Fila {idx + 1}: gramaje {gramaje}g por debajo del mínimo {minimo}g")
                    continue
                if gramaje is not None and maximo is not None and gramaje > maximo:
                    errores.append(f"Fila {idx + 1}: gramaje {gramaje}g por encima del máximo {maximo}g")
                    continue

                rel, _ = TablaPreparacionIngredientes.objects.get_or_create(
                    id_preparacion=preparacion,
                    id_ingrediente_siesa=ingrediente
                )
                rel.gramaje = gramaje
                rel.save(update_fields=['gramaje'])
                guardadas += 1

            except (ValueError, InvalidOperation):
                errores.append(f"Fila {idx + 1}: gramaje inválido")
            except TablaPreparaciones.DoesNotExist:
                errores.append(f"Fila {idx + 1}: preparación no encontrada")
            except TablaAlimentos2018Icbf.DoesNotExist:
                errores.append(f"Fila {idx + 1}: ingrediente no encontrado")

    if errores:
        return JsonResponse({'success': False, 'guardadas': guardadas, 'errores': errores}, status=400)
    return JsonResponse({'success': True, 'guardadas': guardadas})
