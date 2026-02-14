from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError, transaction
from django.utils import timezone
import json

from .excel_generator import (
    generate_menu_excel,
    generate_menu_excel_real_data,
    generate_advanced_nutritional_excel,
    generate_excel_from_service
)
from .models import (
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaRequerimientosNutricionales,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    RequerimientoSemanal,
    ComponentesAlimentos
)
from .forms import AlimentoForm
from principal.models import ModalidadesDeConsumo
from planeacion.models import Programa
from .services import AnalisisNutricionalService, MenuService


@login_required
@csrf_exempt
def api_generar_menu_ia(request):
    """
    API para generar un menú usando Inteligencia Artificial (Gemini).
    Genera automáticamente el menú con pesos específicos para TODOS los niveles educativos.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')

        if not all([programa_id, modalidad_id]):
            return JsonResponse({'error': 'Faltan parámetros (programa_id, modalidad_id)'}, status=400)

        # Delegar al servicio - None genera para TODOS los niveles educativos
        menu = MenuService.generar_menu_con_ia(
            id_programa=programa_id,
            id_modalidad=modalidad_id,
            niveles_educativos=None  # None = generar para todos los niveles (5 niveles)
        )

        if not menu:
            return JsonResponse({'error': 'La IA no pudo generar una propuesta válida. Intente nuevamente.'}, status=500)

        return JsonResponse({
            'success': True,
            'menu': {
                'id': menu.id_menu,
                'nombre': menu.menu,
                'modalidad': menu.id_modalidad.modalidad
            },
            'mensaje': 'Menú generado exitosamente con análisis nutricional para todos los niveles educativos'
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)


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
    from django.contrib import messages

    alimento_a_editar = get_object_or_404(TablaAlimentos2018Icbf, pk=codigo)

    if request.method == 'POST':
        form = AlimentoForm(request.POST, instance=alimento_a_editar)
        if form.is_valid():
            form.save()
            messages.success(request, f'Alimento "{alimento_a_editar.nombre_del_alimento}" actualizado correctamente.')
            return redirect('nutricion:lista_alimentos')
        else:
            # Si hay errores, mostrarlos en consola del servidor para debugging
            print("❌ ERROR: Formulario no válido al editar alimento")
            print(f"Código: {codigo}")
            print(f"Errores: {form.errors}")
            messages.error(request, f'Error al actualizar el alimento. Por favor, revise los datos ingresados.')
            return redirect('nutricion:lista_alimentos')

    return redirect('nutricion:lista_alimentos')


@login_required
@require_http_methods(["DELETE"])
def eliminar_alimento(request, codigo):
    """Vista para eliminar un alimento"""
    try:
        alimento = get_object_or_404(TablaAlimentos2018Icbf, pk=codigo)
        nombre = alimento.nombre_del_alimento
        alimento.delete()
        return JsonResponse({'success': True, 'message': f'Alimento "{nombre}" eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


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

            # Obtener el componente si se proporciona
            id_componente = data.get('id_componente')

            preparacion = TablaPreparaciones.objects.create(
                preparacion=data['preparacion'],
                id_menu_id=data['id_menu'],
                id_componente_id=id_componente if id_componente else None
            )

            return JsonResponse({
                'success': True,
                'preparacion': {
                    'id_preparacion': preparacion.id_preparacion,
                    'preparacion': preparacion.preparacion,
                    'menu': preparacion.id_menu.menu,
                    'componente': preparacion.id_componente.componente if preparacion.id_componente else None
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


@login_required
@csrf_exempt
@transaction.atomic
def api_copiar_preparacion(request):
    """API para copiar una preparación completa a un nuevo menú."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        source_preparacion_id = data.get('source_preparacion_id')
        target_menu_id = data.get('target_menu_id')

        if not source_preparacion_id or not target_menu_id:
            return JsonResponse({'error': 'Faltan parámetros requeridos.'}, status=400)

        # Obtener los objetos de la base de datos
        source_preparacion = get_object_or_404(TablaPreparaciones, pk=source_preparacion_id)
        target_menu = get_object_or_404(TablaMenus, pk=target_menu_id)

        # Crear la nueva preparación (la copia)
        new_preparacion = TablaPreparaciones.objects.create(
            preparacion=source_preparacion.preparacion, # Copia el nombre
            id_menu=target_menu, # Asigna al nuevo menú
            id_componente=source_preparacion.id_componente # Copia el componente
        )

        # Obtener los ingredientes de la preparación original
        source_ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=source_preparacion
        )

        # Crear las nuevas relaciones de ingredientes en lote
        nuevos_ingredientes = []
        for ing in source_ingredientes:
            nuevos_ingredientes.append(
                TablaPreparacionIngredientes(
                    id_preparacion=new_preparacion,
                    id_ingrediente_siesa=ing.id_ingrediente_siesa
                )
            )
        
        if nuevos_ingredientes:
            TablaPreparacionIngredientes.objects.bulk_create(nuevos_ingredientes)

        return JsonResponse({
            'success': True,
            'message': f'Preparación "{new_preparacion.preparacion}" copiada exitosamente.',
            'nueva_preparacion': {
                'id_preparacion': new_preparacion.id_preparacion,
                'preparacion': new_preparacion.preparacion,
                'menu': new_preparacion.id_menu.menu
            }
        })

    except (TablaPreparaciones.DoesNotExist, TablaMenus.DoesNotExist):
        return JsonResponse({'error': 'La preparación o el menú de destino no existen.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)


@login_required
def api_preparaciones_por_modalidad(request, modalidad_id):
    """API para listar todas las preparaciones únicas dentro de una modalidad."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        # Encontrar todos los menús de esa modalidad
        menus_en_modalidad = TablaMenus.objects.filter(id_modalidad_id=modalidad_id)

        # Encontrar todas las preparaciones en esos menús, obteniendo solo nombres únicos
        preparaciones = TablaPreparaciones.objects.filter(
            id_menu__in=menus_en_modalidad
        ).order_by('preparacion').distinct('preparacion')

        # Formatear la respuesta
        # Se devuelve el ID de la *primera* preparación encontrada con ese nombre.
        # Esto es suficiente para que la API de copiado encuentre el original.
        preparaciones_data = [
            {
                "id": prep.id_preparacion,
                "nombre": prep.preparacion
            }
            for prep in preparaciones
        ]

        return JsonResponse({'preparaciones': preparaciones_data})

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)


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


# =================== COMPONENTES DE ALIMENTOS ===================

@login_required
def api_componentes_alimentos(request):
    """API para obtener componentes de alimentos"""
    if request.method == 'GET':
        from .models import ComponentesAlimentos

        componentes = ComponentesAlimentos.objects.select_related('id_grupo_alimentos').all().values(
            'id_componente',
            'componente',
            'id_grupo_alimentos__id_grupo_alimentos',
            'id_grupo_alimentos__grupo_alimentos'
        ).order_by('componente')

        return JsonResponse({'componentes': list(componentes)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


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
    ✨ REFACTORIZADO: Usa AnalisisNutricionalService para lógica de negocio.
    """
    from .services import AnalisisNutricionalService

    try:
        # Delegar toda la lógica al servicio
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
    ✨ REFACTORIZADO: Usa AnalisisNutricionalService.guardar_analisis()
    """
    from .services import AnalisisNutricionalService

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        
        print(f"[DEBUG] Datos recibidos: {data}")
        print(f"[DEBUG] Claves disponibles: {list(data.keys())}")

        # Delegar al servicio
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
def download_menu_excel(request, menu_id):
    """
    View to download an Excel file for a specific menu with advanced data integration.
    """
    try:
        # Usar el generador avanzado que detecta automáticamente datos reales vs guardados
        excel_stream = generate_advanced_nutritional_excel(menu_id, use_saved_analysis=True)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_analisis_nutricional.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel: {str(e)}", status=500)


@login_required
def download_menu_excel_service(request, menu_id):
    """
    View to download an Excel file using the nutritional analysis service directly.
    """
    try:
        excel_stream = generate_excel_from_service(menu_id)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_servicio_analisis.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel desde servicio: {str(e)}", status=500)


from .excel_drawing_utils import ExcelReportDrawer
from .master_excel_generator import MasterNutritionalExcelGenerator

@login_required
def download_menu_excel_with_nivel(request, menu_id, nivel_escolar_id):
    """
    View to download an Excel file for a specific menu and school level with advanced data integration.
    """
    try:
        # Usar el generador avanzado con nivel específico
        excel_stream = generate_advanced_nutritional_excel(menu_id, nivel_escolar_id, use_saved_analysis=True)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_nivel_{nivel_escolar_id}_analisis.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel: {str(e)}", status=500)


@login_required
def download_modalidad_excel(request, programa_id, modalidad_id):
    """
    Descarga el reporte maestro de Excel para todos los menús de una modalidad.
    """
    try:
        # 1. Llamar al nuevo servicio para obtener los datos masivos
        masive_data = AnalisisNutricionalService.obtener_analisis_masivo_por_modalidad(
            programa_id=programa_id,
            modalidad_id=modalidad_id
        )

        if not masive_data.get('success'):
            raise ValueError("No se pudieron generar los datos para el reporte maestro.")

        # 2. Instanciar y usar el nuevo generador maestro
        generator = MasterNutritionalExcelGenerator()
        excel_stream = generator.generate(masive_data)

        # 3. Devolver la respuesta
        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"reporte_maestro_{masive_data['programa_nombre']}_{masive_data['modalidad_nombre']}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando el reporte maestro de Excel: {str(e)}", status=500)

@login_required
def api_validar_semana(request):
    """
    Valida si una semana cumple con las frecuencias requeridas.
    
    GET params:
    - menu_ids: IDs de los 5 menús separados por coma
    - modalidad_id: ID de la modalidad
    
    Returns:
    {
        "cumple": true/false,
        "componentes": [
            {
                "id": "com1",
                "nombre": "Bebida con leche",
                "requerido": 5,
                "actual": 5,
                "cumple": true
            },
            ...
        ]
    }
    """
    try:
        menu_ids_str = request.GET.get('menu_ids', '')
        modalidad_id = request.GET.get('modalidad_id')

        if not menu_ids_str or not modalidad_id:
            return JsonResponse({'error': 'Faltan parámetros: menu_ids y modalidad_id son requeridos'}, status=400)

        # Convertir string de IDs a lista
        menu_ids = [int(id.strip()) for id in menu_ids_str.split(',') if id.strip()]

        if not menu_ids:
            return JsonResponse({'error': 'No se proporcionaron IDs de menús válidos'}, status=400)

        # Obtener requerimientos de la modalidad
        requerimientos = RequerimientoSemanal.objects.filter(
            modalidad__id_modalidades=modalidad_id
        ).select_related('componente')

        if not requerimientos.exists():
            return JsonResponse({
                'cumple': True,
                'componentes': [],
                'mensaje': 'No hay requerimientos definidos para esta modalidad'
            })

        # Contar componentes en los menús de la semana
        # Usamos sets para contar DÍAS únicos, no preparaciones totales
        # Ejemplo: Si Menú 1 tiene 2 preparaciones con "Bebida", cuenta como 1 día
        menus_por_componente = {}

        for menu_id in menu_ids:
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu_id=menu_id
            ).select_related('id_componente')

            # Componentes presentes en este menú (día)
            componentes_del_menu = set()
            for prep in preparaciones:
                comp_id = prep.id_componente.id_componente
                componentes_del_menu.add(comp_id)

            # Registrar este menú (día) para cada componente encontrado
            for comp_id in componentes_del_menu:
                if comp_id not in menus_por_componente:
                    menus_por_componente[comp_id] = set()
                menus_por_componente[comp_id].add(menu_id)

        # Convertir sets a conteos (número de días únicos)
        conteo_componentes = {
            comp_id: len(menus_set)
            for comp_id, menus_set in menus_por_componente.items()
        }

        # Validar contra requerimientos
        componentes_resultado = []
        cumple_total = True

        for req in requerimientos:
            comp_id = req.componente.id_componente
            comp_nombre = req.componente.componente
            requerido = req.frecuencia
            actual = conteo_componentes.get(comp_id, 0)
            cumple = actual == requerido

            if not cumple:
                cumple_total = False

            componentes_resultado.append({
                'id': comp_id,
                'componente': comp_nombre,  # Cambiado de 'nombre' a 'componente' para consistencia con frontend
                'requerido': requerido,
                'actual': actual,
                'cumple': cumple
            })

        return JsonResponse({
            'cumple': cumple_total,
            'componentes': componentes_resultado
        })

    except ValueError as e:
        return JsonResponse({'error': f'Error en formato de parámetros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al validar semana: {str(e)}'}, status=500)


@login_required
def api_requerimientos_modalidad(request):
    """
    Obtiene los requerimientos semanales de una modalidad.
    
    GET params:
    - modalidad_id: ID de la modalidad
    
    Returns:
    {
        "modalidad_id": "mod1",
        "requerimientos": [
            {
                "componente_id": "com1",
                "componente_nombre": "Bebida con leche",
                "frecuencia": 5
            },
            ...
        ]
    }
    """
    try:
        modalidad_id = request.GET.get('modalidad_id')

        if not modalidad_id:
            return JsonResponse({'error': 'Falta parámetro: modalidad_id es requerido'}, status=400)

        requerimientos = RequerimientoSemanal.objects.filter(
            modalidad__id_modalidades=modalidad_id
        ).select_related('componente')

        resultado = []
        for req in requerimientos:
            resultado.append({
                'componente_id': req.componente.id_componente,
                'componente_nombre': req.componente.componente,
                'frecuencia': req.frecuencia
            })

        return JsonResponse({
            'modalidad_id': modalidad_id,
            'requerimientos': resultado
        })

    except Exception as e:
        return JsonResponse({'error': f'Error al obtener requerimientos: {str(e)}'}, status=500)
