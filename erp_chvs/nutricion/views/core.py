from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from ..models import (
    TablaAlimentos2018Icbf,
    TablaMenus,
)
from ..forms import AlimentoForm
from principal.models import ModalidadesDeConsumo
from planeacion.models import Programa
from ..services import MenuService


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

        menu = MenuService.generar_menu_con_ia(
            id_programa=programa_id,
            id_modalidad=modalidad_id,
            niveles_educativos=None
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


@login_required
def nutricion_index(request):
    """Vista principal del módulo de nutrición"""
    return render(request, 'nutricion/index.html')


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
    alimentos_list = TablaAlimentos2018Icbf.objects.select_related('id_componente').order_by('nombre_del_alimento')

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
            print("ERROR: Formulario no válido al editar alimento")
            print(f"Código: {codigo}")
            print(f"Errores: {form.errors}")
            messages.error(request, 'Error al actualizar el alimento. Por favor, revise los datos ingresados.')
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


@login_required
def lista_menus(request):
    """Vista para listar y gestionar menús por municipio/programa/modalidad"""
    from principal.models import PrincipalMunicipio
    from collections import defaultdict

    municipios = PrincipalMunicipio.objects.filter(
        programa__estado='activo'
    ).distinct().order_by('nombre_municipio')

    municipio_id = request.GET.get('municipio')
    programa_id = request.GET.get('programa')

    context = {
        'municipios': municipios,
        'municipio_seleccionado': municipio_id,
        'programa_seleccionado': programa_id,
    }

    if municipio_id:
        programas_activos = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).order_by('-fecha_inicial')
        context['programas'] = programas_activos

        if programa_id:
            try:
                programa = Programa.objects.get(id=programa_id)
                context['programa_obj'] = programa

                modalidades = ModalidadesDeConsumo.objects.all().order_by('modalidad')
                context['modalidades'] = modalidades

                menus_existentes = TablaMenus.objects.filter(
                    id_contrato=programa
                ).select_related('id_modalidad').order_by('id_modalidad', 'menu')

                menus_por_modalidad = defaultdict(list)
                for menu in menus_existentes:
                    menus_por_modalidad[menu.id_modalidad.id_modalidades].append(menu)

                context['menus_por_modalidad'] = dict(menus_por_modalidad)

            except Programa.DoesNotExist:
                context['error'] = 'Programa no encontrado'

    return render(request, 'nutricion/lista_menus.html', context)