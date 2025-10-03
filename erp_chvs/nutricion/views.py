from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json

from .models import (
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes
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
    """Vista para listar menús"""
    menus = TablaMenus.objects.select_related('id_modalidad', 'id_contrato').all().order_by('-fecha_creacion')
    paginator = Paginator(menus, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener datos para los selectores
    modalidades = ModalidadesDeConsumo.objects.all().order_by('modalidad')
    programas = Programa.objects.filter(estado='activo').order_by('-fecha_inicial')

    return render(request, 'nutricion/lista_menus.html', {
        'menus': page_obj,
        'total_menus': menus.count(),
        'modalidades': modalidades,
        'programas': programas
    })


@login_required
@csrf_exempt
def api_menus(request):
    """API para manejar menús via AJAX"""
    if request.method == 'GET':
        menus = TablaMenus.objects.select_related('id_modalidad', 'id_contrato').all().values(
            'id_menu', 'menu', 'id_modalidad__id_modalidades', 'id_modalidad__modalidad',
            'id_contrato__id', 'id_contrato__programa', 'fecha_creacion'
        )
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
            menu.menu = data['menu']
            menu.id_modalidad_id = data['id_modalidad']
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
        preparaciones = TablaPreparaciones.objects.select_related('id_menu').all().values(
            'id_preparacion', 'preparacion', 'id_menu__id_menu', 'id_menu__menu', 'fecha_creacion'
        )
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
            'id_ingrediente_siesa', 'nombre_ingrediente', 'unidades', 'presentacion', 'fecha_creacion'
        )
        return JsonResponse({'ingredientes': list(ingredientes)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            ingrediente = TablaIngredientesSiesa.objects.create(
                nombre_ingrediente=data['nombre_ingrediente'],
                unidades=data.get('unidades', ''),
                presentacion=data.get('presentacion', '')
            )

            return JsonResponse({
                'success': True,
                'ingrediente': {
                    'id_ingrediente_siesa': ingrediente.id_ingrediente_siesa,
                    'nombre_ingrediente': ingrediente.nombre_ingrediente,
                    'unidades': ingrediente.unidades,
                    'presentacion': ingrediente.presentacion
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
            'nombre_ingrediente': ingrediente.nombre_ingrediente,
            'unidades': ingrediente.unidades,
            'presentacion': ingrediente.presentacion
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            ingrediente.nombre_ingrediente = data['nombre_ingrediente']
            ingrediente.unidades = data.get('unidades', '')
            ingrediente.presentacion = data.get('presentacion', '')
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
            'id_ingrediente_siesa__nombre_ingrediente',
            'cantidad'
        )
        return JsonResponse({'ingredientes': list(ingredientes)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            ingrediente = TablaPreparacionIngredientes.objects.create(
                id_preparacion=preparacion,
                id_ingrediente_siesa_id=data['id_ingrediente_siesa'],
                cantidad=data['cantidad']
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