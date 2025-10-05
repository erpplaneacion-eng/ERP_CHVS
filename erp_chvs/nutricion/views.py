from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, transaction
from django.utils import timezone
import json

from .models import (
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaRequerimientosNutricionales,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel
)
from .forms import AlimentoForm
from principal.models import ModalidadesDeConsumo
from planeacion.models import Programa


# =================== VISTAS GENERALES ===================

@login_required
def nutricion_index(request):
    """Vista principal del módulo de nutrición"""
    return render(request, 'nutricion/index.html')


# =================== ALIMENTOS ICBF ===================

@login_required
def lista_alimentos(request):
    """Vista para listar alimentos ICBF"""
    if request.method == 'POST':
        form = AlimentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nutricion:lista_alimentos')
    else:
        form = AlimentoForm()

    search_query = request.GET.get('q', '')
    alimentos_list = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')

    if search_query:
        alimentos_list = alimentos_list.filter(
            Q(nombre_del_alimento__icontains=search_query) |
            Q(codigo__icontains=search_query)
        )

    paginator = Paginator(alimentos_list, 20)
    page_number = request.GET.get('page')
    alimentos_page = paginator.get_page(page_number)

    context = {
        'alimentos_page': alimentos_page,
        'search_query': search_query,
        'form': form,
    }

    return render(request, 'nutricion/lista_alimentos.html', context)


@login_required
def editar_alimento(request, codigo):
    """Vista para editar un alimento"""
    alimento_a_editar = get_object_or_404(TablaAlimentos2018Icbf, pk=codigo)

    if request.method == 'POST':
        form = AlimentoForm(request.POST, instance=alimento_a_editar)
        if form.is_valid():
            form.save()
            return redirect('nutricion:lista_alimentos')

    return redirect('nutricion:lista_alimentos')


# =================== MENÚS ===================

@login_required
def lista_menus(request):
    """Vista para listar y gestionar menús por municipio/programa/modalidad"""
    # Obtener SOLO municipios que tienen programas activos
    from principal.models import PrincipalMunicipio
    municipios = PrincipalMunicipio.objects.filter(
        programa__estado='activo'
    ).distinct().order_by('nombre_municipio')

    # Obtener filtros
    municipio_id = request.GET.get('municipio')
    programa_id = request.GET.get('programa')

    # Contexto inicial
    context = {
        'municipios': municipios,  # Cambio aquí
        'municipio_seleccionado': municipio_id,
        'programa_seleccionado': programa_id,
    }

    # Si hay municipio seleccionado, obtener programas activos
    if municipio_id:
        programas_activos = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).order_by('-fecha_inicial')
        context['programas'] = programas_activos

        # Si hay programa seleccionado, obtener modalidades y menús
        if programa_id:
            try:
                programa = Programa.objects.get(id=programa_id)
                context['programa_obj'] = programa

                # Obtener modalidades del municipio
                # Esto requiere saber qué modalidades están configuradas para ese municipio
                # Por ahora, traemos todas las modalidades
                modalidades = ModalidadesDeConsumo.objects.all().order_by('modalidad')
                context['modalidades'] = modalidades

                # Obtener menús existentes del programa
                menus_existentes = TablaMenus.objects.filter(
                    id_contrato=programa
                ).select_related('id_modalidad').order_by('id_modalidad', 'menu')

                # Agrupar menús por modalidad
                from collections import defaultdict
                menus_por_modalidad = defaultdict(list)
                for menu in menus_existentes:
                    menus_por_modalidad[menu.id_modalidad.id_modalidades].append(menu)

                context['menus_por_modalidad'] = dict(menus_por_modalidad)

            except Programa.DoesNotExist:
                context['error'] = 'Programa no encontrado'

    return render(request, 'nutricion/lista_menus.html', context)


@login_required
def api_programas_por_municipio(request):
    """API para obtener programas activos de un municipio"""
    municipio_id = request.GET.get('municipio_id')

    if not municipio_id:
        return JsonResponse({'programas': []})

    try:
        programas = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).values('id', 'programa', 'contrato', 'fecha_inicial', 'fecha_final')

        return JsonResponse({'programas': list(programas)})

    except Exception as e:
        return JsonResponse({'programas': [], 'error': str(e)})


@login_required
def api_modalidades_por_programa(request):
    """API para obtener modalidades configuradas por programa/municipio"""
    programa_id = request.GET.get('programa_id')

    if not programa_id:
        return JsonResponse({'modalidades': []})

    try:
        programa = Programa.objects.get(id=programa_id)

        # Importar el modelo de relación municipio-modalidades
        from principal.models import MunicipioModalidades

        # Obtener modalidades configuradas para el municipio del programa
        modalidades_configuradas = MunicipioModalidades.objects.filter(
            municipio=programa.municipio
        ).select_related('modalidad').values(
            'modalidad__id_modalidades',
            'modalidad__modalidad'
        ).order_by('modalidad__modalidad')

        # Si no hay configuración específica, retornar todas las modalidades
        if not modalidades_configuradas.exists():
            modalidades = ModalidadesDeConsumo.objects.all().values(
                'id_modalidades', 'modalidad'
            ).order_by('modalidad')
            modalidades_list = list(modalidades)
        else:
            # Formatear modalidades configuradas
            modalidades_list = [
                {
                    'id_modalidades': m['modalidad__id_modalidades'],
                    'modalidad': m['modalidad__modalidad']
                }
                for m in modalidades_configuradas
            ]

        return JsonResponse({
            'modalidades': modalidades_list,
            'programa': {
                'id': programa.id,
                'nombre': programa.programa,
                'contrato': programa.contrato
            }
        })
    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)


@login_required
@csrf_exempt
def api_generar_menus_automaticos(request):
    """API para generar automáticamente los 20 menús de una modalidad"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')

        if not programa_id or not modalidad_id:
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        # Verificar si ya existen menús
        menus_existentes = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad
        ).count()

        if menus_existentes > 0:
            return JsonResponse({
                'error': f'Ya existen {menus_existentes} menús para esta modalidad',
                'menus_existentes': menus_existentes
            }, status=400)

        # Crear los 20 menús automáticamente
        menus_creados = []

        with transaction.atomic():
            for i in range(1, 21):
                menu = TablaMenus.objects.create(
                    menu=str(i),
                    id_modalidad=modalidad,
                    id_contrato=programa
                )
                menus_creados.append({
                    'id': menu.id_menu,
                    'nombre': menu.menu,
                    'modalidad': modalidad.modalidad
                })

        return JsonResponse({
            'success': True,
            'menus_creados': len(menus_creados),
            'menus': menus_creados
        })

    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)
    except ModalidadesDeConsumo.DoesNotExist:
        return JsonResponse({'error': 'Modalidad no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def api_crear_menu_especial(request):
    """API para crear un menú especial con nombre personalizado"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')
        nombre_menu = data.get('nombre_menu', '').strip()

        if not programa_id or not modalidad_id or not nombre_menu:
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        # Verificar si ya existe un menú con ese nombre
        menu_existente = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad,
            menu=nombre_menu
        ).exists()

        if menu_existente:
            return JsonResponse({
                'error': f'Ya existe un menú con el nombre "{nombre_menu}"'
            }, status=400)

        # Crear el menú especial
        menu = TablaMenus.objects.create(
            menu=nombre_menu,
            id_modalidad=modalidad,
            id_contrato=programa
        )

        return JsonResponse({
            'success': True,
            'menu': {
                'id': menu.id_menu,
                'nombre': menu.menu,
                'modalidad': modalidad.modalidad
            }
        })

    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)
    except ModalidadesDeConsumo.DoesNotExist:
        return JsonResponse({'error': 'Modalidad no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def api_menus(request):
    """API para manejar menús via AJAX"""
    if request.method == 'GET':
        # Filtrar por programa si se proporciona
        programa_id = request.GET.get('programa_id')

        menus_query = TablaMenus.objects.select_related('id_modalidad', 'id_contrato')

        if programa_id:
            menus_query = menus_query.filter(id_contrato_id=programa_id)

        menus = menus_query.values(
            'id_menu', 'menu', 'id_modalidad__id_modalidades', 'id_modalidad__modalidad',
            'id_contrato__id', 'id_contrato__programa', 'fecha_creacion'
        ).order_by('id_modalidad__id_modalidades', 'menu')

        return JsonResponse({'menus': list(menus)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            menu = TablaMenus.objects.create(
                menu=data['menu'],
                id_modalidad_id=data['id_modalidad'],
                id_contrato_id=data['id_contrato']
            )

            return JsonResponse({
                'success': True,
                'menu': {
                    'id_menu': menu.id_menu,
                    'menu': menu.menu,
                    'modalidad': menu.id_modalidad.modalidad,
                    'programa': menu.id_contrato.programa
                }
            })

        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': f'Error de integridad: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_menu_detail(request, id_menu):
    """API para manejar un menú específico"""
    menu = get_object_or_404(TablaMenus, id_menu=id_menu)

    if request.method == 'GET':
        return JsonResponse({
            'id_menu': menu.id_menu,
            'menu': menu.menu,
            'id_modalidad': menu.id_modalidad.id_modalidades,
            'id_contrato': menu.id_contrato.id
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            # Actualizar solo los campos que se envían
            if 'menu' in data:
                menu.menu = data['menu']
            if 'id_modalidad' in data:
                menu.id_modalidad_id = data['id_modalidad']
            if 'id_contrato' in data:
                menu.id_contrato_id = data['id_contrato']
            menu.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            menu.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== PREPARACIONES ===================

@login_required
def lista_preparaciones(request):
    """Vista para listar preparaciones"""
    preparaciones = TablaPreparaciones.objects.select_related('id_menu').all().order_by('-fecha_creacion')
    paginator = Paginator(preparaciones, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    menus = TablaMenus.objects.all().order_by('menu')

    return render(request, 'nutricion/lista_preparaciones.html', {
        'preparaciones': page_obj,
        'total_preparaciones': preparaciones.count(),
        'menus': menus
    })


@login_required
@csrf_exempt
def api_preparaciones(request):
    """API para manejar preparaciones via AJAX"""
    if request.method == 'GET':
        # Filtrar por menú si se proporciona
        menu_id = request.GET.get('menu_id')

        preparaciones_query = TablaPreparaciones.objects.select_related('id_menu')

        if menu_id:
            preparaciones_query = preparaciones_query.filter(id_menu_id=menu_id)

        preparaciones = preparaciones_query.values(
            'id_preparacion', 'preparacion', 'id_menu__id_menu', 'id_menu__menu', 'fecha_creacion'
        ).order_by('preparacion')

        return JsonResponse({'preparaciones': list(preparaciones)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            preparacion = TablaPreparaciones.objects.create(
                preparacion=data['preparacion'],
                id_menu_id=data['id_menu']
            )

            return JsonResponse({
                'success': True,
                'preparacion': {
                    'id_preparacion': preparacion.id_preparacion,
                    'preparacion': preparacion.preparacion,
                    'menu': preparacion.id_menu.menu
                }
            })

        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': f'Error de integridad: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_preparacion_detail(request, id_preparacion):
    """API para manejar una preparación específica"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)

    if request.method == 'GET':
        return JsonResponse({
            'id_preparacion': preparacion.id_preparacion,
            'preparacion': preparacion.preparacion,
            'id_menu': preparacion.id_menu.id_menu
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            preparacion.preparacion = data['preparacion']
            preparacion.id_menu_id = data['id_menu']
            preparacion.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            preparacion.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== INGREDIENTES SIESA ===================

@login_required
def lista_ingredientes(request):
    """Vista para listar ingredientes de inventario"""
    ingredientes = TablaIngredientesSiesa.objects.all().order_by('nombre_ingrediente')
    paginator = Paginator(ingredientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nutricion/lista_ingredientes.html', {
        'ingredientes': page_obj,
        'total_ingredientes': ingredientes.count()
    })


@login_required
@csrf_exempt
def api_ingredientes(request):
    """API para manejar ingredientes via AJAX"""
    if request.method == 'GET':
        ingredientes = TablaIngredientesSiesa.objects.all().values(
            'id_ingrediente_siesa', 'nombre_ingrediente'
        )
        return JsonResponse({'ingredientes': list(ingredientes)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            ingrediente = TablaIngredientesSiesa.objects.create(
                id_ingrediente_siesa=data['id_ingrediente_siesa'],
                nombre_ingrediente=data['nombre_ingrediente']
            )

            return JsonResponse({
                'success': True,
                'ingrediente': {
                    'id_ingrediente_siesa': ingrediente.id_ingrediente_siesa,
                    'nombre_ingrediente': ingrediente.nombre_ingrediente
                }
            })

        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': f'Error de integridad: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_ingrediente_detail(request, id_ingrediente):
    """API para manejar un ingrediente específico"""
    ingrediente = get_object_or_404(TablaIngredientesSiesa, id_ingrediente_siesa=id_ingrediente)

    if request.method == 'GET':
        return JsonResponse({
            'id_ingrediente_siesa': ingrediente.id_ingrediente_siesa,
            'nombre_ingrediente': ingrediente.nombre_ingrediente
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            ingrediente.nombre_ingrediente = data['nombre_ingrediente']
            ingrediente.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            ingrediente.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== PREPARACIÓN - INGREDIENTES ===================

@login_required
def detalle_preparacion(request, id_preparacion):
    """Vista para ver y gestionar ingredientes de una preparación"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)
    ingredientes_preparacion = TablaPreparacionIngredientes.objects.filter(
        id_preparacion=preparacion
    ).select_related('id_ingrediente_siesa')

    ingredientes_disponibles = TablaIngredientesSiesa.objects.all().order_by('nombre_ingrediente')

    return render(request, 'nutricion/detalle_preparacion.html', {
        'preparacion': preparacion,
        'ingredientes_preparacion': ingredientes_preparacion,
        'ingredientes_disponibles': ingredientes_disponibles
    })


@login_required
@csrf_exempt
def api_preparacion_ingredientes(request, id_preparacion):
    """API para manejar ingredientes de una preparación"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)

    if request.method == 'GET':
        ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=preparacion
        ).select_related('id_ingrediente_siesa').values(
            'id_ingrediente_siesa__id_ingrediente_siesa',
            'id_ingrediente_siesa__nombre_ingrediente'
        )
        return JsonResponse({'ingredientes': list(ingredientes)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Soporte para agregar múltiples ingredientes
            if 'ingredientes' in data:
                ingredientes_creados = []
                for ing_data in data['ingredientes']:
                    ingrediente, created = TablaPreparacionIngredientes.objects.get_or_create(
                        id_preparacion=preparacion,
                        id_ingrediente_siesa_id=ing_data['id_ingrediente_siesa']
                    )
                    if created:
                        ingredientes_creados.append(ingrediente.id_ingrediente_siesa.nombre_ingrediente)

                return JsonResponse({
                    'success': True,
                    'mensaje': f'{len(ingredientes_creados)} ingrediente(s) agregado(s) exitosamente'
                })
            else:
                # Soporte para agregar un solo ingrediente
                ingrediente = TablaPreparacionIngredientes.objects.create(
                    id_preparacion=preparacion,
                    id_ingrediente_siesa_id=data['id_ingrediente_siesa']
                )

                return JsonResponse({
                    'success': True,
                    'mensaje': 'Ingrediente agregado exitosamente'
                })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Este ingrediente ya está en la preparación'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_preparacion_ingrediente_delete(request, id_preparacion, id_ingrediente):
    """API para eliminar un ingrediente de una preparación"""
    if request.method == 'DELETE':
        try:
            ingrediente = get_object_or_404(
                TablaPreparacionIngredientes,
                id_preparacion_id=id_preparacion,
                id_ingrediente_siesa_id=id_ingrediente
            )
            ingrediente.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== ANÁLISIS NUTRICIONAL ===================

@login_required
def api_analisis_nutricional_menu(request, id_menu):
    """
    API para obtener análisis nutricional completo de un menú por niveles escolares.

    Retorna información detallada de:
    - Preparaciones e ingredientes del menú
    - Valores nutricionales por 100g de cada ingrediente
    - Pesos neto y bruto calculados
    - Totales nutricionales por nivel escolar
    - Porcentajes de adecuación nutricional (limitados a 100%)
    - Estados de adecuación (óptimo/aceptable/alto)

    CÁLCULOS PRINCIPALES:
    1. Peso Bruto = (Peso Neto × 100) / Parte Comestible
    2. Nutriente = (Valor por 100g × Peso Neto) / 100
    3. % Adecuación = min((Total / Requerimiento) × 100, 100)

    Args:
        request: HttpRequest object
        id_menu: ID del menú a analizar

    Returns:
        JsonResponse con estructura:
        {
            'success': True,
            'menu': {...},
            'analisis_por_nivel': [
                {
                    'nivel_escolar': {...},
                    'es_programa_actual': bool,
                    'requerimientos': {...},
                    'totales': {...},
                    'porcentajes_adecuacion': {...},
                    'preparaciones': [...]
                }
            ]
        }
    """
    
    def get_estado_adecuacion(porcentaje, nutriente):
        """
        Determina el estado de adecuación nutricional según el porcentaje alcanzado.

        RANGOS DE EVALUACIÓN (válidos para todos los nutrientes):
        - 0-35%: ÓPTIMO (verde) - Aporte bajo pero seguro
        - 35.1-70%: ACEPTABLE (amarillo) - Aporte moderado
        - >70%: ALTO (rojo) - Aporte elevado, cerca del límite máximo

        NOTA IMPORTANTE:
        - El 100% representa el MÁXIMO permitido según ICBF 2018
        - Para sodio, valores bajos son mejores (pero el rango de colores es el mismo)
        - Para otros nutrientes, alcanzar valores altos es aceptable pero no debe exceder 100%

        Args:
            porcentaje (float): Porcentaje de adecuación (0-100)
            nutriente (str): Nombre del nutriente evaluado

        Returns:
            str: Estado ('optimo', 'aceptable', 'alto')
        """
        # Validar entrada
        porcentaje = max(0, min(100, porcentaje))  # Limitar entre 0-100

        # Rangos uniformes para todos los nutrientes
        # (La interpretación nutricional varía, pero los rangos son consistentes)
        if porcentaje <= 35:
            return 'optimo'      # 0-35%: Verde
        elif porcentaje <= 70:
            return 'aceptable'   # 35.1-70%: Amarillo
        else:
            return 'alto'        # >70%: Rojo
    
    try:
        from decimal import Decimal
        
        # Obtener el menú
        menu = get_object_or_404(TablaMenus, id_menu=id_menu)
        
        # Obtener el programa y su nivel escolar asociado
        programa = menu.id_contrato

        # Obtener todas las preparaciones del menú con sus ingredientes
        preparaciones = TablaPreparaciones.objects.filter(id_menu=menu).prefetch_related(
            'ingredientes__id_ingrediente_siesa'
        )

        # Estructurar datos de preparaciones e ingredientes
        preparaciones_data = []
        
        for preparacion in preparaciones:
            ingredientes_prep = TablaPreparacionIngredientes.objects.filter(
                id_preparacion=preparacion
            ).select_related('id_ingrediente_siesa')
            
            ingredientes_data = []
            
            for ing_prep in ingredientes_prep:
                ingrediente = ing_prep.id_ingrediente_siesa
                
                # Buscar el ingrediente en la tabla de alimentos ICBF
                alimento = TablaAlimentos2018Icbf.objects.filter(
                    codigo=ingrediente.id_ingrediente_siesa
                ).first()
                
                if not alimento:
                    alimento = TablaAlimentos2018Icbf.objects.filter(
                        nombre_del_alimento__icontains=ingrediente.nombre_ingrediente
                    ).first()
                
                if alimento:
                    # Peso neto base por defecto (100g)
                    peso_neto_base = 100

                    # Calcular peso bruto usando parte_comestible_field
                    # Fórmula: Peso Bruto = (Peso Neto × 100) / % Parte Comestible
                    # Ejemplo: 100g neto con 85% comestible = (100 × 100) / 85 = 117.6g bruto
                    parte_comestible = float(alimento.parte_comestible_field) if alimento.parte_comestible_field else 100.0

                    # Validar que parte_comestible esté en rango válido (1-100%)
                    parte_comestible = max(1.0, min(100.0, parte_comestible))

                    # Calcular peso bruto
                    peso_bruto_base = (peso_neto_base * 100) / parte_comestible
                    
                    # Valores nutricionales por 100g
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
                        'parte_comestible': float(parte_comestible),
                        'valores_por_100g': valores_por_100g,
                        'alimento_encontrado': True
                    })
                else:
                    ingredientes_data.append({
                        'id_ingrediente': ingrediente.id_ingrediente_siesa,
                        'nombre': ingrediente.nombre_ingrediente,
                        'peso_neto_base': 100,
                        'peso_bruto_base': 100,
                        'parte_comestible': 100,
                        'valores_por_100g': {
                            'calorias_kcal': 0, 'proteina_g': 0, 'grasa_g': 0, 'cho_g': 0,
                            'calcio_mg': 0, 'hierro_mg': 0, 'sodio_mg': 0
                        },
                        'alimento_encontrado': False,
                        'mensaje': 'No se encontró en TABLA_ALIMENTOS_2018_ICBF'
                    })
            
            preparaciones_data.append({
                'id_preparacion': preparacion.id_preparacion,
                'nombre': preparacion.preparacion,
                'ingredientes': ingredientes_data
            })

        # Obtener TODOS los requerimientos nutricionales disponibles
        todos_requerimientos = TablaRequerimientosNutricionales.objects.select_related(
            'id_nivel_escolar_uapa'
        ).all()

        # Obtener el nivel escolar del programa actual
        nivel_escolar_programa = programa.get_nivel_escolar_uapa()

        # Generar análisis por cada nivel escolar
        analisis_por_nivel = []

        for requerimiento in todos_requerimientos:
            nivel_escolar = requerimiento.id_nivel_escolar_uapa
            es_programa_actual = (nivel_escolar_programa and 
                                nivel_escolar.id_grado_escolar_uapa == nivel_escolar_programa.id_grado_escolar_uapa)
            
            # Requerimientos nutricionales para este nivel
            requerimientos_nivel = {
                'calorias_kcal': float(requerimiento.calorias_kcal),
                'proteina_g': float(requerimiento.proteina_g),
                'grasa_g': float(requerimiento.grasa_g),
                'cho_g': float(requerimiento.cho_g),
                'calcio_mg': float(requerimiento.calcio_mg),
                'hierro_mg': float(requerimiento.hierro_mg),
                'sodio_mg': float(requerimiento.sodio_mg)
            }
            
            # Calcular totales del nivel sumando todos los ingredientes
            totales_nivel = {
                'calorias_kcal': 0,
                'proteina_g': 0,
                'grasa_g': 0,
                'cho_g': 0,
                'calcio_mg': 0,
                'hierro_mg': 0,
                'sodio_mg': 0,
                'peso_neto_total': 0,
                'peso_bruto_total': 0
            }
            
            # Sumar valores de todos los ingredientes de todas las preparaciones
            for prep in preparaciones_data:
                for ing in prep['ingredientes']:
                    if ing['alimento_encontrado']:
                        valores = ing['valores_por_100g']
                        factor = ing['peso_neto_base'] / 100
                        
                        totales_nivel['calorias_kcal'] += valores['calorias_kcal'] * factor
                        totales_nivel['proteina_g'] += valores['proteina_g'] * factor
                        totales_nivel['grasa_g'] += valores['grasa_g'] * factor
                        totales_nivel['cho_g'] += valores['cho_g'] * factor
                        totales_nivel['calcio_mg'] += valores['calcio_mg'] * factor
                        totales_nivel['hierro_mg'] += valores['hierro_mg'] * factor
                        totales_nivel['sodio_mg'] += valores['sodio_mg'] * factor
                        totales_nivel['peso_neto_total'] += ing['peso_neto_base']
                        totales_nivel['peso_bruto_total'] += ing['peso_bruto_base']
            
            # Calcular porcentajes de adecuación
            porcentajes_adecuacion = {}
            for nutriente in ['calorias_kcal', 'proteina_g', 'grasa_g', 'cho_g', 'calcio_mg', 'hierro_mg', 'sodio_mg']:
                total_actual = totales_nivel[nutriente]
                requerido = requerimientos_nivel[nutriente]
                
                if requerido > 0:
                    # Calcular porcentaje y limitarlo entre 0-100%
                    porcentaje = min((total_actual / requerido) * 100, 100.0)
                    porcentaje = max(porcentaje, 0.0)
                    
                    porcentajes_adecuacion[nutriente] = {
                        'porcentaje': round(porcentaje, 1),
                        'estado': get_estado_adecuacion(porcentaje, nutriente)
                    }
                else:
                    porcentajes_adecuacion[nutriente] = {
                        'porcentaje': 0.0,
                        'estado': 'sin_datos'
                    }
            
            analisis_por_nivel.append({
                'nivel_escolar': {
                    'id': nivel_escolar.id_grado_escolar_uapa,
                    'nombre': nivel_escolar.nivel_escolar_uapa,
                    'rango_edades': getattr(nivel_escolar, 'rango_edades', '')
                },
                'es_programa_actual': es_programa_actual,
                'requerimientos': requerimientos_nivel,
                'totales': totales_nivel,
                'porcentajes_adecuacion': porcentajes_adecuacion,
                'preparaciones': preparaciones_data  # Cada nivel tendrá las mismas preparaciones
            })

        # Preparar respuesta
        response_data = {
            'success': True,
            'menu': {
                'id': menu.id_menu,
                'nombre': menu.menu,
                'modalidad': menu.id_modalidad.modalidad,
                'programa': programa.programa
            },
            'analisis_por_nivel': analisis_por_nivel
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al calcular análisis nutricional: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def guardar_analisis_nutricional(request):
    """
    API para guardar automáticamente el análisis nutricional editado por el usuario.
    
    Guarda en las tablas:
    - TablaAnalisisNutricionalMenu: Totales y porcentajes por nivel
    - TablaIngredientesPorNivel: Pesos configurados de cada ingrediente
    
    Datos esperados en POST:
    {
        'id_menu': int,
        'id_nivel_escolar': int,
        'totales': {
            'calorias': float, 'proteina': float, ...
        },
        'porcentajes': {
            'calorias': float, 'proteina': float, ...
        },
        'ingredientes': [
            {
                'id_preparacion': int,
                'id_ingrediente_siesa': int,
                'peso_neto': float,
                'peso_bruto': float,
                'calorias': float,
                'proteina': float,
                'grasa': float,
                'cho': float,
                'calcio': float,
                'hierro': float,
                'sodio': float
            }
        ]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Validar datos requeridos
        required_fields = ['id_menu', 'id_nivel_escolar', 'totales', 'porcentajes', 'ingredientes']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Falta el campo: {field}'}, status=400)
        
        id_menu = data['id_menu']
        id_nivel_escolar = data['id_nivel_escolar']
        totales = data['totales']
        porcentajes = data['porcentajes']
        ingredientes = data['ingredientes']
        
        # Verificar que el menú existe
        try:
            menu = TablaMenus.objects.get(id_menu=id_menu)
        except TablaMenus.DoesNotExist:
            return JsonResponse({'error': 'Menú no encontrado'}, status=404)
        
        # Verificar que el nivel escolar existe
        from principal.models import TablaGradosEscolaresUapa
        try:
            nivel_escolar = TablaGradosEscolaresUapa.objects.get(id_grado_escolar_uapa=id_nivel_escolar)
        except TablaGradosEscolaresUapa.DoesNotExist:
            return JsonResponse({'error': 'Nivel escolar no encontrado'}, status=404)
        
        with transaction.atomic():
            # Buscar o crear el registro de análisis
            analisis, created = TablaAnalisisNutricionalMenu.objects.get_or_create(
                id_menu=menu,
                id_nivel_escolar_uapa=nivel_escolar,
                defaults={
                    'usuario_modificacion': request.user.username if hasattr(request.user, 'username') else 'sistema'
                }
            )

            # Actualizar totales nutricionales
            analisis.total_calorias = totales.get('calorias', 0)
            analisis.total_proteina = totales.get('proteina', 0)
            analisis.total_grasa = totales.get('grasa', 0)
            analisis.total_cho = totales.get('cho', 0)
            analisis.total_calcio = totales.get('calcio', 0)
            analisis.total_hierro = totales.get('hierro', 0)
            analisis.total_sodio = totales.get('sodio', 0)
            analisis.total_peso_neto = totales.get('peso_neto', 0)
            analisis.total_peso_bruto = totales.get('peso_bruto', 0)

            # Actualizar porcentajes de adecuación
            analisis.porcentaje_calorias = porcentajes.get('calorias', 0)
            analisis.porcentaje_proteina = porcentajes.get('proteina', 0)
            analisis.porcentaje_grasa = porcentajes.get('grasa', 0)
            analisis.porcentaje_cho = porcentajes.get('cho', 0)
            analisis.porcentaje_calcio = porcentajes.get('calcio', 0)
            analisis.porcentaje_hierro = porcentajes.get('hierro', 0)
            analisis.porcentaje_sodio = porcentajes.get('sodio', 0)

            # Actualizar usuario y fecha de modificación (fecha_actualizacion se actualiza automáticamente con auto_now=True)
            analisis.usuario_modificacion = request.user.username if hasattr(request.user, 'username') else 'sistema'
            analisis.save()
            
            # Eliminar ingredientes previos para este análisis
            TablaIngredientesPorNivel.objects.filter(id_analisis=analisis).delete()
            
            # Guardar configuración de ingredientes
            ingredientes_guardados = 0
            for ing_data in ingredientes:
                # Verificar que la preparación existe
                try:
                    preparacion = TablaPreparaciones.objects.get(id_preparacion=ing_data['id_preparacion'])
                except TablaPreparaciones.DoesNotExist:
                    continue
                    
                # Verificar que el ingrediente existe
                try:
                    ingrediente = TablaIngredientesSiesa.objects.get(id_ingrediente_siesa=ing_data['id_ingrediente_siesa'])
                except TablaIngredientesSiesa.DoesNotExist:
                    continue
                
                # Crear registro de ingrediente por nivel
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
        
        return JsonResponse({
            'success': True,
            'message': 'Análisis nutricional guardado exitosamente',
            'analisis_id': analisis.id_analisis,
            'ingredientes_guardados': ingredientes_guardados,
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al guardar análisis nutricional: {str(e)}'
        }, status=500)