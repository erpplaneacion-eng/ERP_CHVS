import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    TablaAlimentos2018Icbf,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaIngredientesSiesa,
    TablaMenus,
    TablaPreparaciones,
)
from ..services import AnalisisNutricionalService
from ..services.calculo_service import CalculoService


@login_required
def api_analisis_nutricional_menu(request, id_menu):
    """
    API para obtener análisis nutricional completo de un menú por niveles escolares.
    """
    try:
        resultado = AnalisisNutricionalService.obtener_analisis_completo(id_menu)
        return JsonResponse(resultado)

    except TablaMenus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Menú no encontrado'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener análisis: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def guardar_analisis_nutricional(request):
    """
    API para guardar automáticamente el análisis nutricional editado por el usuario.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)

        print(f"[DEBUG] Datos recibidos: {data}")
        print(f"[DEBUG] Claves disponibles: {list(data.keys())}")

        resultado = AnalisisNutricionalService.guardar_analisis(
            id_menu=data['id_menu'],
            id_nivel_escolar=data['id_nivel_escolar'],
            totales=data['totales'],
            porcentajes=data['porcentajes'],
            ingredientes=data['ingredientes'],
            usuario=request.user.username if hasattr(request.user, 'username') else 'sistema'
        )

        return JsonResponse(resultado)

    except KeyError as e:
        return JsonResponse({
            'success': False,
            'error': f'Falta el campo: {str(e)}'
        }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)

    except TablaMenus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Menú no encontrado'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al guardar: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def api_sincronizar_pesos_preparaciones(request):
    """
    Sincroniza los pesos desde TablaPreparacionIngredientes.gramaje
    hacia TablaIngredientesPorNivel para un menú y nivel específico.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        id_menu = data.get('id_menu')
        id_nivel_escolar = data.get('id_nivel_escolar')
        sobrescribir_existentes = data.get('sobrescribir_existentes', False)

        if not id_menu or not id_nivel_escolar:
            return JsonResponse({
                'error': 'Faltan parámetros: id_menu e id_nivel_escolar son requeridos'
            }, status=400)

        resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=id_menu,
            id_nivel_escolar=id_nivel_escolar,
            sobrescribir_existentes=sobrescribir_existentes
        )

        return JsonResponse(resultado)

    except TablaMenus.DoesNotExist:
        return JsonResponse({'error': 'Menú no encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al sincronizar pesos: {str(e)}'
        }, status=500)


def _guardar_ingrediente_por_nivel(menu, analisis, ing_data):
    id_preparacion = ing_data.get('id_preparacion')
    id_ingrediente = ing_data.get('id_ingrediente')
    peso_neto = float(ing_data.get('peso_neto', 0))

    try:
        preparacion = TablaPreparaciones.objects.get(
            id_preparacion=id_preparacion,
            id_menu=menu
        )

        try:
            ingrediente_icbf = TablaAlimentos2018Icbf.objects.get(
                codigo=id_ingrediente
            )
        except TablaAlimentos2018Icbf.DoesNotExist:
            return False, f'Ingrediente ICBF {id_ingrediente} no encontrado'

        # Usar el código ICBF como clave en TablaIngredientesSiesa.
        # Crea el registro puente si no existe (integración Siesa pendiente de implementar).
        ingrediente_siesa, _ = TablaIngredientesSiesa.objects.get_or_create(
            id_ingrediente_siesa=id_ingrediente,
            defaults={'nombre_ingrediente': ingrediente_icbf.nombre_del_alimento}
        )

        valores = CalculoService.calcular_valores_nutricionales_alimento(
            ingrediente_icbf,
            peso_neto
        )

        parte_comestible = float(ingrediente_icbf.parte_comestible_field or 100)
        peso_bruto = CalculoService.calcular_peso_bruto(peso_neto, parte_comestible)

        TablaIngredientesPorNivel.objects.update_or_create(
            id_analisis=analisis,
            id_preparacion=preparacion,
            id_ingrediente_siesa=ingrediente_siesa,
            defaults={
                'peso_neto': peso_neto,
                'peso_bruto': peso_bruto,
                'calorias': valores.get('calorias', 0),
                'proteina': valores.get('proteina', 0),
                'grasa': valores.get('grasa', 0),
                'cho': valores.get('cho', 0),
                'calcio': valores.get('calcio', 0),
                'hierro': valores.get('hierro', 0),
                'sodio': valores.get('sodio', 0)
            }
        )
        return True, None

    except TablaPreparaciones.DoesNotExist:
        return False, f'Preparación {id_preparacion} no encontrada'
    except Exception as e:
        return False, f'Error procesando ingrediente {id_ingrediente}: {str(e)}'


def _procesar_guardado_nivel(menu, nivel_data):
    errores = []
    registros_actualizados = 0

    id_analisis = nivel_data.get('id_analisis')
    ingredientes = nivel_data.get('ingredientes', [])

    try:
        analisis = TablaAnalisisNutricionalMenu.objects.get(
            id_analisis=id_analisis,
            id_menu=menu
        )
    except TablaAnalisisNutricionalMenu.DoesNotExist:
        return 0, [f'Análisis {id_analisis} no encontrado']

    for ing_data in ingredientes:
        actualizado, error = _guardar_ingrediente_por_nivel(menu, analisis, ing_data)
        if actualizado:
            registros_actualizados += 1
        elif error:
            errores.append(error)

    AnalisisNutricionalService._recalcular_totales_analisis(analisis)
    return registros_actualizados, errores


@login_required
@csrf_exempt
def api_guardar_ingredientes_por_nivel(request, id_menu):
    """
    Guarda los cambios de pesos de ingredientes por nivel escolar desde el editor de preparaciones.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        niveles = data.get('niveles', [])

        if not niveles:
            return JsonResponse({'error': 'No se enviaron datos para guardar'}, status=400)

        menu = get_object_or_404(TablaMenus, id_menu=id_menu)
        registros_actualizados = 0
        errores = []

        with transaction.atomic():
            for nivel_data in niveles:
                actualizados_nivel, errores_nivel = _procesar_guardado_nivel(menu, nivel_data)
                registros_actualizados += actualizados_nivel
                errores.extend(errores_nivel)

        return JsonResponse({
            'success': True,
            'registros_actualizados': registros_actualizados,
            'mensaje': 'Cambios guardados exitosamente',
            'errores': errores if errores else []
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al guardar cambios: {str(e)}'
        }, status=500)
