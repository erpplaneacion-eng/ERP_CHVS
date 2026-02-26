import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from principal.models import RegistroActividad

from ..models import (
    ComponentesAlimentos,
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparacionIngredientes,
    TablaPreparaciones,
)


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
        menu_id = request.GET.get('menu_id')

        preparaciones_query = TablaPreparaciones.objects.select_related('id_menu')

        if menu_id:
            preparaciones_query = preparaciones_query.filter(id_menu_id=menu_id)

        preparaciones = preparaciones_query.values(
            'id_preparacion', 'preparacion', 'id_menu__id_menu', 'id_menu__menu', 'fecha_creacion'
        ).order_by('preparacion')

        return JsonResponse({'preparaciones': list(preparaciones)})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            id_componente = data.get('id_componente')

            preparacion = TablaPreparaciones.objects.create(
                preparacion=data['preparacion'],
                id_menu_id=data['id_menu'],
                id_componente_id=id_componente if id_componente else None
            )
            RegistroActividad.registrar(
                request, 'nutricion', 'crear_preparacion',
                f"Preparación: {preparacion.preparacion} | Menú ID: {preparacion.id_menu.id_menu}"
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

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


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

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            preparacion.preparacion = data['preparacion']
            preparacion.id_menu_id = data['id_menu']
            preparacion.save()
            RegistroActividad.registrar(
                request, 'nutricion', 'editar_preparacion',
                f"Preparación ID: {id_preparacion} | Nombre: {preparacion.preparacion}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    if request.method == 'DELETE':
        try:
            nombre_prep = preparacion.preparacion
            preparacion.delete()
            RegistroActividad.registrar(
                request, 'nutricion', 'eliminar_preparacion',
                f"Preparación ID: {id_preparacion} | Nombre: {nombre_prep}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


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

        source_preparacion = get_object_or_404(TablaPreparaciones, pk=source_preparacion_id)
        target_menu = get_object_or_404(TablaMenus, pk=target_menu_id)

        new_preparacion = TablaPreparaciones.objects.create(
            preparacion=source_preparacion.preparacion,
            id_menu=target_menu,
            id_componente=source_preparacion.id_componente
        )

        source_ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=source_preparacion
        )

        nuevos_ingredientes = []
        for ing in source_ingredientes:
            nuevos_ingredientes.append(
                TablaPreparacionIngredientes(
                    id_preparacion=new_preparacion,
                    id_ingrediente_siesa=ing.id_ingrediente_siesa,
                    id_componente=ing.id_componente or new_preparacion.id_componente,
                )
            )

        if nuevos_ingredientes:
            TablaPreparacionIngredientes.objects.bulk_create(nuevos_ingredientes)

        RegistroActividad.registrar(
            request, 'nutricion', 'copiar_preparacion',
            f"Origen ID: {source_preparacion_id} → Menú destino ID: {target_menu_id} | Nueva: {new_preparacion.preparacion}"
        )
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
        menus_en_modalidad = TablaMenus.objects.filter(id_modalidad_id=modalidad_id)
        preparaciones = TablaPreparaciones.objects.filter(
            id_menu__in=menus_en_modalidad
        ).order_by('preparacion').distinct('preparacion')

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


@login_required
def lista_ingredientes(request):
    """Vista para listar ingredientes ICBF 2018"""
    ingredientes = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')
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
    """API para obtener ingredientes desde tabla ICBF 2018."""
    if request.method == 'GET':
        ingredientes = TablaAlimentos2018Icbf.objects.all().values(
            'codigo', 'nombre_del_alimento'
        ).order_by('nombre_del_alimento')

        data = [
            {
                'id_ingrediente_siesa': ing['codigo'],
                'nombre_ingrediente': ing['nombre_del_alimento'],
                'codigo': ing['codigo'],
                'nombre_del_alimento': ing['nombre_del_alimento'],
            }
            for ing in ingredientes
        ]
        return JsonResponse({'ingredientes': data})

    return JsonResponse({'error': 'Método no permitido para catálogo ICBF'}, status=405)


@login_required
@csrf_exempt
def api_ingrediente_detail(request, id_ingrediente):
    """API para manejar un ingrediente especifico del catalogo ICBF."""
    ingrediente = get_object_or_404(TablaAlimentos2018Icbf, codigo=id_ingrediente)

    if request.method == 'GET':
        return JsonResponse({
            'id_ingrediente_siesa': ingrediente.codigo,
            'nombre_ingrediente': ingrediente.nombre_del_alimento,
            'codigo': ingrediente.codigo,
            'nombre_del_alimento': ingrediente.nombre_del_alimento
        })

    return JsonResponse({'error': 'Metodo no permitido para catalogo ICBF'}, status=405)


@login_required
def api_componentes_alimentos(request):
    """API para obtener componentes de alimentos"""
    if request.method == 'GET':
        componentes = ComponentesAlimentos.objects.select_related('id_grupo_alimentos').all().values(
            'id_componente',
            'componente',
            'id_grupo_alimentos__id_grupo_alimentos',
            'id_grupo_alimentos__grupo_alimentos'
        ).order_by('componente')

        return JsonResponse({'componentes': list(componentes)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def detalle_preparacion(request, id_preparacion):
    """Vista para ver y gestionar ingredientes de una preparación"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)
    ingredientes_preparacion = TablaPreparacionIngredientes.objects.filter(
        id_preparacion=preparacion
    ).select_related('id_ingrediente_siesa')

    ingredientes_disponibles = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')

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
        relaciones = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=preparacion
        ).select_related('id_ingrediente_siesa')

        ingredientes = []
        for rel in relaciones:
            ingredientes.append({
                'id_ingrediente_siesa__id_ingrediente_siesa': rel.id_ingrediente_siesa.codigo,
                'id_ingrediente_siesa__nombre_ingrediente': rel.id_ingrediente_siesa.nombre_del_alimento,
                'codigo': rel.id_ingrediente_siesa.codigo,
                'nombre_del_alimento': rel.id_ingrediente_siesa.nombre_del_alimento,
                'gramaje': float(rel.gramaje) if rel.gramaje is not None else None,
            })
        return JsonResponse({'ingredientes': ingredientes})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if 'ingredientes' in data:
                ingredientes_creados = []
                for ing_data in data['ingredientes']:
                    ingrediente, created = TablaPreparacionIngredientes.objects.get_or_create(
                        id_preparacion=preparacion,
                        id_ingrediente_siesa_id=ing_data['id_ingrediente_siesa'],
                        defaults={'id_componente': preparacion.id_componente}
                    )
                    gramaje_raw = ing_data.get('gramaje')
                    if gramaje_raw not in (None, '', 'null'):
                        ingrediente.gramaje = Decimal(str(gramaje_raw))
                        ingrediente.save(update_fields=['gramaje'])
                    if created:
                        ingredientes_creados.append(ingrediente.id_ingrediente_siesa.nombre_del_alimento)

                RegistroActividad.registrar(
                    request, 'nutricion', 'agregar_ingredientes',
                    f"Preparación ID: {id_preparacion} | Ingredientes agregados: {len(ingredientes_creados)}"
                )
                return JsonResponse({
                    'success': True,
                    'mensaje': f'{len(ingredientes_creados)} ingrediente(s) agregado(s) exitosamente'
                })

            TablaPreparacionIngredientes.objects.create(
                id_preparacion=preparacion,
                id_ingrediente_siesa_id=data['id_ingrediente_siesa'],
                id_componente=preparacion.id_componente,
                gramaje=Decimal(str(data['gramaje'])) if data.get('gramaje') not in (None, '', 'null') else None
            )

            return JsonResponse({
                'success': True,
                'mensaje': 'Ingrediente agregado exitosamente'
            })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Este ingrediente ya está en la preparación'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


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
            RegistroActividad.registrar(
                request, 'nutricion', 'eliminar_ingrediente',
                f"Preparación ID: {id_preparacion} | Ingrediente: {id_ingrediente}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
