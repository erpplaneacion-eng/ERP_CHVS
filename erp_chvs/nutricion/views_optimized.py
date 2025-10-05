"""
VISTAS OPTIMIZADAS PARA ANÁLISIS NUTRICIONAL
Lógica bidireccional movida al backend para mejor performance
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from decimal import Decimal
import json

from .models import (
    TablaMenus,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaRequerimientosNutricionales,
    TablaAlimentos2018Icbf,
    TablaPreparacionIngredientes,
    TablaPreparaciones
)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_obtener_o_crear_analisis(request):
    """
    API para obtener o crear análisis nutricional automáticamente.

    Este endpoint:
    1. Verifica si existe análisis en BD para menu + nivel
    2. Si existe: lo retorna
    3. Si NO existe: lo crea automáticamente con datos base

    POST /api/nutricion/obtener-crear-analisis/
    Body: {
        "id_menu": 123,
        "id_nivel_escolar": 456
    }

    Returns: {
        "success": true,
        "analisis": {...},
        "ingredientes": [...],
        "es_nuevo": true/false
    }
    """
    try:
        data = json.loads(request.body)
        id_menu = data.get('id_menu')
        id_nivel_escolar = data.get('id_nivel_escolar')

        # Obtener menú y nivel
        menu = TablaMenus.objects.get(id_menu=id_menu)

        # Buscar análisis existente
        analisis, creado = TablaAnalisisNutricionalMenu.objects.get_or_create(
            id_menu=menu,
            id_nivel_escolar_uapa_id=id_nivel_escolar,
            defaults={
                'usuario_modificacion': request.user.username
            }
        )

        # Si es nuevo, crear ingredientes base (peso 100g por defecto)
        if creado:
            # Obtener preparaciones del menú
            preparaciones = TablaPreparaciones.objects.filter(id_menu=menu)

            for preparacion in preparaciones:
                # Obtener ingredientes de la preparación
                ingredientes_prep = TablaPreparacionIngredientes.objects.filter(
                    id_preparacion=preparacion
                ).select_related('id_ingrediente_siesa')

                for ing_prep in ingredientes_prep:
                    # Buscar alimento ICBF
                    ingrediente = ing_prep.id_ingrediente_siesa
                    alimento = TablaAlimentos2018Icbf.objects.filter(
                        nombre_del_alimento__icontains=ingrediente.nombre_ingrediente
                    ).first()

                    if alimento:
                        # Crear ingrediente con peso base 100g
                        peso_neto = 100
                        parte_comestible = max(1.0, min(100.0, float(alimento.parte_comestible_field or 100)))
                        peso_bruto = (peso_neto * 100) / parte_comestible
                        factor = peso_neto / 100

                        TablaIngredientesPorNivel.objects.create(
                            id_analisis=analisis,
                            id_preparacion=preparacion,
                            id_ingrediente_siesa=ingrediente,
                            peso_neto=Decimal(str(peso_neto)),
                            peso_bruto=Decimal(str(round(peso_bruto, 2))),
                            parte_comestible=Decimal(str(parte_comestible)),
                            calorias=Decimal(str(round(float(alimento.energia_kcal or 0) * factor, 2))),
                            proteina=Decimal(str(round(float(alimento.proteina_g or 0) * factor, 2))),
                            grasa=Decimal(str(round(float(alimento.lipidos_g or 0) * factor, 2))),
                            cho=Decimal(str(round(float(alimento.carbohidratos_totales_g or 0) * factor, 2))),
                            calcio=Decimal(str(round(float(alimento.calcio_mg or 0) * factor, 2))),
                            hierro=Decimal(str(round(float(alimento.hierro_mg or 0) * factor, 2))),
                            sodio=Decimal(str(round(float(alimento.sodio_mg or 0) * factor, 2))),
                            codigo_icbf=alimento.codigo_icbf
                        )

            # Recalcular totales del análisis nuevo
            recalcular_analisis(analisis, request.user.username)

        # Obtener ingredientes
        ingredientes = TablaIngredientesPorNivel.objects.filter(
            id_analisis=analisis
        ).select_related('id_preparacion', 'id_ingrediente_siesa')

        ingredientes_data = [{
            'id': ing.id_ingrediente_nivel,
            'preparacion': ing.id_preparacion.nombre_preparacion,
            'ingrediente': ing.id_ingrediente_siesa.nombre_ingrediente,
            'peso_neto': float(ing.peso_neto),
            'peso_bruto': float(ing.peso_bruto),
            'parte_comestible': float(ing.parte_comestible),
            'calorias': float(ing.calorias),
            'proteina': float(ing.proteina),
            'grasa': float(ing.grasa),
            'cho': float(ing.cho),
            'calcio': float(ing.calcio),
            'hierro': float(ing.hierro),
            'sodio': float(ing.sodio)
        } for ing in ingredientes]

        return JsonResponse({
            'success': True,
            'es_nuevo': creado,
            'analisis': {
                'id': analisis.id_analisis,
                'total_calorias': float(analisis.total_calorias),
                'total_proteina': float(analisis.total_proteina),
                'total_grasa': float(analisis.total_grasa),
                'total_cho': float(analisis.total_cho),
                'total_calcio': float(analisis.total_calcio),
                'total_hierro': float(analisis.total_hierro),
                'total_sodio': float(analisis.total_sodio),
                'total_peso_neto': float(analisis.total_peso_neto),
                'total_peso_bruto': float(analisis.total_peso_bruto),
                'porcentaje_calorias': float(analisis.porcentaje_calorias),
                'porcentaje_proteina': float(analisis.porcentaje_proteina),
                'porcentaje_grasa': float(analisis.porcentaje_grasa),
                'porcentaje_cho': float(analisis.porcentaje_cho),
                'porcentaje_calcio': float(analisis.porcentaje_calcio),
                'porcentaje_hierro': float(analisis.porcentaje_hierro),
                'porcentaje_sodio': float(analisis.porcentaje_sodio),
                'estado_calorias': analisis.estado_calorias,
                'estado_proteina': analisis.estado_proteina,
                'estado_grasa': analisis.estado_grasa,
                'estado_cho': analisis.estado_cho,
                'estado_calcio': analisis.estado_calcio,
                'estado_hierro': analisis.estado_hierro,
                'estado_sodio': analisis.estado_sodio
            },
            'ingredientes': ingredientes_data
        })

    except TablaMenus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Menú no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener/crear análisis: {str(e)}'
        }, status=500)


def calcular_estado_adecuacion(porcentaje):
    """
    Determina el estado de adecuación según el porcentaje.
    - 0-35%: óptimo
    - 35.1-70%: aceptable
    - >70%: alto
    """
    porcentaje = max(0, min(100, porcentaje))
    if porcentaje <= 35:
        return 'optimo'
    elif porcentaje <= 70:
        return 'aceptable'
    else:
        return 'alto'


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_ajustar_porcentaje_adecuacion(request):
    """
    API OPTIMIZADA: Ajusta pesos de ingredientes desde porcentaje de adecuación.

    LÓGICA BIDIRECCIONAL:
    1. Usuario edita % de adecuación de un nutriente
    2. Backend calcula factor de escala proporcional
    3. Ajusta TODOS los pesos de ingredientes
    4. Guarda en BD
    5. Retorna datos actualizados

    POST /api/nutricion/ajustar-porcentaje/
    Body: {
        "id_analisis": 123,
        "nutriente": "calorias_kcal",
        "porcentaje_deseado": 50.0
    }

    Returns: {
        "success": True,
        "analisis": {...},
        "ingredientes": [...]
    }
    """
    try:
        data = json.loads(request.body)
        id_analisis = data.get('id_analisis')
        nutriente = data.get('nutriente')
        porcentaje_deseado = float(data.get('porcentaje_deseado', 0))

        # Validar porcentaje (0-100%)
        porcentaje_deseado = max(0, min(100, porcentaje_deseado))

        # Obtener análisis
        analisis = TablaAnalisisNutricionalMenu.objects.select_related(
            'id_menu',
            'id_nivel_escolar_uapa'
        ).get(id_analisis=id_analisis)

        # Obtener requerimientos nutricionales
        requerimiento = TablaRequerimientosNutricionales.objects.get(
            id_nivel_escolar_uapa=analisis.id_nivel_escolar_uapa
        )

        # Obtener valor requerido del nutriente
        requerimiento_valor = getattr(requerimiento, nutriente, 0)

        if requerimiento_valor == 0:
            return JsonResponse({
                'success': False,
                'error': f'Requerimiento no encontrado para {nutriente}'
            }, status=400)

        # Calcular valor objetivo
        valor_objetivo = (porcentaje_deseado * float(requerimiento_valor)) / 100

        # Obtener todos los ingredientes configurados
        ingredientes = TablaIngredientesPorNivel.objects.filter(
            id_analisis=analisis
        ).select_related('id_ingrediente_siesa')

        # Calcular total actual del nutriente
        total_actual = sum([
            float(getattr(ing, nutriente.replace('_kcal', '').replace('_g', '').replace('_mg', ''), 0))
            for ing in ingredientes
        ])

        if total_actual == 0:
            return JsonResponse({
                'success': False,
                'error': 'No hay ingredientes que aporten este nutriente'
            }, status=400)

        # ========== CÁLCULO DEL FACTOR DE ESCALA PROPORCIONAL ==========
        # Este es el núcleo de la lógica bidireccional
        factor_escala = valor_objetivo / total_actual

        print(f"[AJUSTE] {nutriente}: {total_actual} → {valor_objetivo} (factor: {factor_escala:.3f})")

        # ========== AJUSTAR TODOS LOS PESOS PROPORCIONALMENTE ==========
        ingredientes_actualizados = []

        for ingrediente in ingredientes:
            # Obtener alimento ICBF para recalcular nutrientes
            alimento = TablaAlimentos2018Icbf.objects.filter(
                codigo_icbf=ingrediente.codigo_icbf
            ).first()

            if not alimento:
                continue

            # Nuevo peso neto (manteniendo proporciones)
            nuevo_peso_neto = float(ingrediente.peso_neto) * factor_escala

            # Validar peso >= 0
            nuevo_peso_neto = max(0, nuevo_peso_neto)

            # Recalcular peso bruto
            parte_comestible = max(1.0, min(100.0, float(alimento.parte_comestible_field or 100)))
            nuevo_peso_bruto = (nuevo_peso_neto * 100) / parte_comestible

            # Recalcular nutrientes
            factor_nutrientes = nuevo_peso_neto / 100

            ingrediente.peso_neto = Decimal(str(round(nuevo_peso_neto, 2)))
            ingrediente.peso_bruto = Decimal(str(round(nuevo_peso_bruto, 2)))
            ingrediente.calorias = Decimal(str(round(float(alimento.energia_kcal or 0) * factor_nutrientes, 2)))
            ingrediente.proteina = Decimal(str(round(float(alimento.proteina_g or 0) * factor_nutrientes, 2)))
            ingrediente.grasa = Decimal(str(round(float(alimento.lipidos_g or 0) * factor_nutrientes, 2)))
            ingrediente.cho = Decimal(str(round(float(alimento.carbohidratos_totales_g or 0) * factor_nutrientes, 2)))
            ingrediente.calcio = Decimal(str(round(float(alimento.calcio_mg or 0) * factor_nutrientes, 2)))
            ingrediente.hierro = Decimal(str(round(float(alimento.hierro_mg or 0) * factor_nutrientes, 2)))
            ingrediente.sodio = Decimal(str(round(float(alimento.sodio_mg or 0) * factor_nutrientes, 2)))

            ingrediente.save()

            ingredientes_actualizados.append({
                'id': ingrediente.id_ingrediente_nivel,
                'nombre': ingrediente.id_ingrediente_siesa.nombre_ingrediente,
                'peso_neto': float(ingrediente.peso_neto),
                'peso_bruto': float(ingrediente.peso_bruto),
                'calorias': float(ingrediente.calorias),
                'proteina': float(ingrediente.proteina),
                'grasa': float(ingrediente.grasa),
                'cho': float(ingrediente.cho),
                'calcio': float(ingrediente.calcio),
                'hierro': float(ingrediente.hierro),
                'sodio': float(ingrediente.sodio)
            })

        # ========== RECALCULAR TOTALES DEL ANÁLISIS ==========
        ingredientes_refresh = TablaIngredientesPorNivel.objects.filter(id_analisis=analisis)

        analisis.total_calorias = sum([float(ing.calorias) for ing in ingredientes_refresh])
        analisis.total_proteina = sum([float(ing.proteina) for ing in ingredientes_refresh])
        analisis.total_grasa = sum([float(ing.grasa) for ing in ingredientes_refresh])
        analisis.total_cho = sum([float(ing.cho) for ing in ingredientes_refresh])
        analisis.total_calcio = sum([float(ing.calcio) for ing in ingredientes_refresh])
        analisis.total_hierro = sum([float(ing.hierro) for ing in ingredientes_refresh])
        analisis.total_sodio = sum([float(ing.sodio) for ing in ingredientes_refresh])
        analisis.total_peso_neto = sum([float(ing.peso_neto) for ing in ingredientes_refresh])
        analisis.total_peso_bruto = sum([float(ing.peso_bruto) for ing in ingredientes_refresh])

        # ========== RECALCULAR PORCENTAJES DE ADECUACIÓN ==========
        nutrientes_map = {
            'calorias_kcal': ('total_calorias', requerimiento.calorias_kcal),
            'proteina_g': ('total_proteina', requerimiento.proteina_g),
            'grasa_g': ('total_grasa', requerimiento.grasa_g),
            'cho_g': ('total_cho', requerimiento.cho_g),
            'calcio_mg': ('total_calcio', requerimiento.calcio_mg),
            'hierro_mg': ('total_hierro', requerimiento.hierro_mg),
            'sodio_mg': ('total_sodio', requerimiento.sodio_mg)
        }

        for nut_key, (total_attr, req_val) in nutrientes_map.items():
            total_val = float(getattr(analisis, total_attr, 0))
            req_val_float = float(req_val) if req_val else 1

            porcentaje = min((total_val / req_val_float) * 100, 100) if req_val_float > 0 else 0
            porcentaje = max(0, porcentaje)

            setattr(analisis, f'porcentaje_{nut_key.replace("_kcal", "").replace("_g", "").replace("_mg", "")}',
                    Decimal(str(round(porcentaje, 2))))
            setattr(analisis, f'estado_{nut_key.replace("_kcal", "").replace("_g", "").replace("_mg", "")}',
                    calcular_estado_adecuacion(porcentaje))

        analisis.usuario_modificacion = request.user.username
        analisis.save()

        # ========== PREPARAR RESPUESTA ==========
        return JsonResponse({
            'success': True,
            'message': f'Análisis ajustado a {porcentaje_deseado}% de {nutriente}',
            'analisis': {
                'total_calorias': float(analisis.total_calorias),
                'total_proteina': float(analisis.total_proteina),
                'total_grasa': float(analisis.total_grasa),
                'total_cho': float(analisis.total_cho),
                'total_calcio': float(analisis.total_calcio),
                'total_hierro': float(analisis.total_hierro),
                'total_sodio': float(analisis.total_sodio),
                'total_peso_neto': float(analisis.total_peso_neto),
                'total_peso_bruto': float(analisis.total_peso_bruto),
                'porcentaje_calorias': float(analisis.porcentaje_calorias),
                'porcentaje_proteina': float(analisis.porcentaje_proteina),
                'porcentaje_grasa': float(analisis.porcentaje_grasa),
                'porcentaje_cho': float(analisis.porcentaje_cho),
                'porcentaje_calcio': float(analisis.porcentaje_calcio),
                'porcentaje_hierro': float(analisis.porcentaje_hierro),
                'porcentaje_sodio': float(analisis.porcentaje_sodio),
                'estado_calorias': analisis.estado_calorias,
                'estado_proteina': analisis.estado_proteina,
                'estado_grasa': analisis.estado_grasa,
                'estado_cho': analisis.estado_cho,
                'estado_calcio': analisis.estado_calcio,
                'estado_hierro': analisis.estado_hierro,
                'estado_sodio': analisis.estado_sodio
            },
            'ingredientes': ingredientes_actualizados,
            'factor_escala': round(factor_escala, 3)
        })

    except TablaAnalisisNutricionalMenu.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Análisis no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al ajustar porcentaje: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_ajustar_peso_ingrediente(request):
    """
    API OPTIMIZADA: Ajusta peso de un ingrediente y recalcula todo.

    POST /api/nutricion/ajustar-peso/
    Body: {
        "id_ingrediente_nivel": 456,
        "peso_neto": 150.0
    }

    Returns: {
        "success": True,
        "ingrediente": {...},
        "analisis": {...}
    }
    """
    try:
        data = json.loads(request.body)
        id_ingrediente_nivel = data.get('id_ingrediente_nivel')
        nuevo_peso_neto = float(data.get('peso_neto', 100))

        # Validar peso >= 0
        nuevo_peso_neto = max(0, nuevo_peso_neto)

        # Obtener ingrediente
        ingrediente = TablaIngredientesPorNivel.objects.select_related(
            'id_analisis',
            'id_ingrediente_siesa'
        ).get(id_ingrediente_nivel=id_ingrediente_nivel)

        # Obtener alimento ICBF
        alimento = TablaAlimentos2018Icbf.objects.filter(
            codigo_icbf=ingrediente.codigo_icbf
        ).first()

        if not alimento:
            return JsonResponse({
                'success': False,
                'error': 'Alimento ICBF no encontrado'
            }, status=404)

        # Recalcular peso bruto
        parte_comestible = max(1.0, min(100.0, float(alimento.parte_comestible_field or 100)))
        nuevo_peso_bruto = (nuevo_peso_neto * 100) / parte_comestible

        # Recalcular nutrientes
        factor = nuevo_peso_neto / 100

        ingrediente.peso_neto = Decimal(str(round(nuevo_peso_neto, 2)))
        ingrediente.peso_bruto = Decimal(str(round(nuevo_peso_bruto, 2)))
        ingrediente.calorias = Decimal(str(round(float(alimento.energia_kcal or 0) * factor, 2)))
        ingrediente.proteina = Decimal(str(round(float(alimento.proteina_g or 0) * factor, 2)))
        ingrediente.grasa = Decimal(str(round(float(alimento.lipidos_g or 0) * factor, 2)))
        ingrediente.cho = Decimal(str(round(float(alimento.carbohidratos_totales_g or 0) * factor, 2)))
        ingrediente.calcio = Decimal(str(round(float(alimento.calcio_mg or 0) * factor, 2)))
        ingrediente.hierro = Decimal(str(round(float(alimento.hierro_mg or 0) * factor, 2)))
        ingrediente.sodio = Decimal(str(round(float(alimento.sodio_mg or 0) * factor, 2)))

        ingrediente.save()

        # Recalcular totales del análisis (llamar a función auxiliar)
        recalcular_analisis(ingrediente.id_analisis, request.user.username)

        # Obtener análisis actualizado
        analisis = ingrediente.id_analisis

        return JsonResponse({
            'success': True,
            'message': 'Peso ajustado correctamente',
            'ingrediente': {
                'id': ingrediente.id_ingrediente_nivel,
                'peso_neto': float(ingrediente.peso_neto),
                'peso_bruto': float(ingrediente.peso_bruto),
                'calorias': float(ingrediente.calorias),
                'proteina': float(ingrediente.proteina),
                'grasa': float(ingrediente.grasa),
                'cho': float(ingrediente.cho),
                'calcio': float(ingrediente.calcio),
                'hierro': float(ingrediente.hierro),
                'sodio': float(ingrediente.sodio)
            },
            'analisis': {
                'total_calorias': float(analisis.total_calorias),
                'porcentaje_calorias': float(analisis.porcentaje_calorias),
                'estado_calorias': analisis.estado_calorias
                # ... (otros campos)
            }
        })

    except TablaIngredientesPorNivel.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Ingrediente no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al ajustar peso: {str(e)}'
        }, status=500)


def recalcular_analisis(analisis, usuario=None):
    """
    Función auxiliar para recalcular totales y porcentajes de un análisis.
    """
    # Obtener todos los ingredientes
    ingredientes = TablaIngredientesPorNivel.objects.filter(id_analisis=analisis)

    # Recalcular totales
    analisis.total_calorias = sum([float(ing.calorias) for ing in ingredientes])
    analisis.total_proteina = sum([float(ing.proteina) for ing in ingredientes])
    analisis.total_grasa = sum([float(ing.grasa) for ing in ingredientes])
    analisis.total_cho = sum([float(ing.cho) for ing in ingredientes])
    analisis.total_calcio = sum([float(ing.calcio) for ing in ingredientes])
    analisis.total_hierro = sum([float(ing.hierro) for ing in ingredientes])
    analisis.total_sodio = sum([float(ing.sodio) for ing in ingredientes])
    analisis.total_peso_neto = sum([float(ing.peso_neto) for ing in ingredientes])
    analisis.total_peso_bruto = sum([float(ing.peso_bruto) for ing in ingredientes])

    # Obtener requerimientos
    requerimiento = TablaRequerimientosNutricionales.objects.get(
        id_nivel_escolar_uapa=analisis.id_nivel_escolar_uapa
    )

    # Recalcular porcentajes
    nutrientes_map = {
        'calorias': (analisis.total_calorias, requerimiento.calorias_kcal),
        'proteina': (analisis.total_proteina, requerimiento.proteina_g),
        'grasa': (analisis.total_grasa, requerimiento.grasa_g),
        'cho': (analisis.total_cho, requerimiento.cho_g),
        'calcio': (analisis.total_calcio, requerimiento.calcio_mg),
        'hierro': (analisis.total_hierro, requerimiento.hierro_mg),
        'sodio': (analisis.total_sodio, requerimiento.sodio_mg)
    }

    for nut_name, (total_val, req_val) in nutrientes_map.items():
        req_val_float = float(req_val) if req_val else 1
        porcentaje = min((float(total_val) / req_val_float) * 100, 100) if req_val_float > 0 else 0
        porcentaje = max(0, porcentaje)

        setattr(analisis, f'porcentaje_{nut_name}', Decimal(str(round(porcentaje, 2))))
        setattr(analisis, f'estado_{nut_name}', calcular_estado_adecuacion(porcentaje))

    if usuario:
        analisis.usuario_modificacion = usuario

    analisis.save()
    return analisis
