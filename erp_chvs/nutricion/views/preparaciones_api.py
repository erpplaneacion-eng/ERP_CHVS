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
    TablaAnalisisNutricionalMenu,
    TablaMenus,
    TablaPreparacionIngredientes,
    TablaPreparaciones,
)


def _limpiar_analisis_si_menu_sin_ingredientes(menu):
    """
    Elimina registros de anÃ¡lisis nutricional cuando el menÃº ya no tiene
    relaciones preparaciÃ³n-ingrediente.
    """
    tiene_relaciones = TablaPreparacionIngredientes.objects.filter(
        id_preparacion__id_menu=menu
    ).exists()
    if not tiene_relaciones:
        TablaAnalisisNutricionalMenu.objects.filter(id_menu=menu).delete()


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
                f"PreparaciÃ³n: {preparacion.preparacion} | MenÃº ID: {preparacion.id_menu.id_menu}"
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

    return JsonResponse({'success': False, 'error': 'MÃ©todo no permitido'}, status=405)


@login_required
@csrf_exempt
def api_preparacion_detail(request, id_preparacion):
    """API para manejar una preparaciÃ³n especÃ­fica"""
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
                f"PreparaciÃ³n ID: {id_preparacion} | Nombre: {preparacion.preparacion}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    if request.method == 'DELETE':
        try:
            nombre_prep = preparacion.preparacion
            menu = preparacion.id_menu
            preparacion.delete()
            _limpiar_analisis_si_menu_sin_ingredientes(menu)
            RegistroActividad.registrar(
                request, 'nutricion', 'eliminar_preparacion',
                f"PreparaciÃ³n ID: {id_preparacion} | Nombre: {nombre_prep}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'MÃ©todo no permitido'}, status=405)


@login_required
@csrf_exempt
@transaction.atomic
def api_copiar_preparacion(request):
    """API para copiar una preparaciÃ³n completa a un nuevo menÃº."""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        target_menu_id = data.get('target_menu_id')
        target_menu = get_object_or_404(TablaMenus, pk=target_menu_id)

        # Soporta formato nuevo: {target_menu_id, copias: [{source_preparacion_id, ingredient_ids}]}
        # y formato legado:       {target_menu_id, source_preparacion_id, ingredient_ids}
        copias_raw = data.get('copias')
        if copias_raw is None:
            copias_raw = [{
                'source_preparacion_id': data.get('source_preparacion_id'),
                'ingredient_ids': data.get('ingredient_ids') or [],
            }]

        if not target_menu_id or not copias_raw:
            return JsonResponse({'error': 'Faltan parámetros requeridos.'}, status=400)

        nuevas_preparaciones = []
        for copia in copias_raw:
            source_preparacion_id = copia.get('source_preparacion_id')
            ingredient_ids = copia.get('ingredient_ids') or []

            if not source_preparacion_id:
                continue

            source_preparacion = get_object_or_404(TablaPreparaciones, pk=source_preparacion_id)

            GRUPOS_EQUIVALENTES = [
                {"20507", "20501"},
                {"20510", "20503", "20501", "20507"},
            ]
            src_mod = str(source_preparacion.id_menu.id_modalidad_id)
            tgt_mod = str(target_menu.id_modalidad_id)
            misma_modalidad = src_mod == tgt_mod
            equivalentes = any(
                src_mod in grupo and tgt_mod in grupo
                for grupo in GRUPOS_EQUIVALENTES
            )
            if not misma_modalidad and not equivalentes:
                return JsonResponse(
                    {'success': False, 'error': 'Solo se puede copiar desde menús de la misma modalidad.'},
                    status=400
                )

            source_ingredientes = TablaPreparacionIngredientes.objects.filter(
                id_preparacion=source_preparacion
            )
            if ingredient_ids:
                ids_norm = {str(i).strip() for i in ingredient_ids if str(i).strip()}
                source_ingredientes = source_ingredientes.filter(
                    id_ingrediente_siesa_id__in=ids_norm
                )

            if not source_ingredientes.exists():
                continue

            new_prep = TablaPreparaciones.objects.create(
                preparacion=source_preparacion.preparacion,
                id_menu=target_menu,
                id_componente=source_preparacion.id_componente,
            )
            nuevos_ingredientes = [
                TablaPreparacionIngredientes(
                    id_preparacion=new_prep,
                    id_ingrediente_siesa=ing.id_ingrediente_siesa,
                    id_componente=ing.id_componente or new_prep.id_componente,
                    id_grupo_alimentos=ing.id_grupo_alimentos,
                    gramaje=ing.gramaje,
                )
                for ing in source_ingredientes
            ]
            if nuevos_ingredientes:
                TablaPreparacionIngredientes.objects.bulk_create(nuevos_ingredientes)
            nuevas_preparaciones.append(new_prep.preparacion)

            RegistroActividad.registrar(
                request, 'nutricion', 'copiar_preparacion',
                f"Origen ID: {source_preparacion_id} -> Menú destino ID: {target_menu_id} | "
                f"Nueva: {new_prep.preparacion} | Ingredientes copiados: {len(nuevos_ingredientes)}"
            )

        if not nuevas_preparaciones:
            return JsonResponse(
                {'success': False, 'error': 'No se copió ninguna preparación. Verifica que tengan ingredientes.'},
                status=400
            )

        total = len(nuevas_preparaciones)
        msg = (
            f'Preparación "{nuevas_preparaciones[0]}" copiada exitosamente.'
            if total == 1
            else f'{total} preparaciones copiadas exitosamente.'
        )
        return JsonResponse({'success': True, 'message': msg})

    except (TablaPreparaciones.DoesNotExist, TablaMenus.DoesNotExist):
        return JsonResponse({'error': 'La preparación o el menú de destino no existen.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)


@login_required
def api_buscar_preparaciones_modalidad(request, id_menu):
    """Busca preparaciones en todos los menús de la misma modalidad (excepto el actual).
    Las modalidades 20507 y 20501 se consideran equivalentes entre sí para efectos de copia."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    menu_actual = get_object_or_404(
        TablaMenus.objects.select_related('id_modalidad', 'id_contrato'),
        id_menu=id_menu
    )
    q = request.GET.get('q', '').strip()

    GRUPOS_EQUIVALENTES = [
        {"20507", "20501"},
        {"20510", "20503", "20501", "20507"},
    ]
    modalidad_actual_id = str(menu_actual.id_modalidad_id)
    grupo_encontrado = next(
        (g for g in GRUPOS_EQUIVALENTES if modalidad_actual_id in g), None
    )
    if grupo_encontrado:
        modalidades_buscar = list(grupo_encontrado)
    else:
        modalidades_buscar = [modalidad_actual_id]

    qs = (
        TablaPreparaciones.objects
        .filter(id_menu__id_modalidad__in=modalidades_buscar)
        .exclude(id_menu=menu_actual)
        .select_related('id_menu__id_contrato')
        .prefetch_related('ingredientes__id_ingrediente_siesa')
        .order_by('preparacion', 'id_preparacion')
    )
    if q:
        qs = qs.filter(preparacion__icontains=q)

    data = []
    for prep in qs:
        ingredientes = [
            {'codigo': str(rel.id_ingrediente_siesa.codigo), 'nombre': rel.id_ingrediente_siesa.nombre_del_alimento}
            for rel in prep.ingredientes.all()
        ]
        if not ingredientes:
            continue
        data.append({
            'id_preparacion': prep.id_preparacion,
            'preparacion': prep.preparacion,
            'menu': prep.id_menu.menu,
            'programa': str(prep.id_menu.id_contrato),
            'ingredientes': ingredientes,
        })

    return JsonResponse({'success': True, 'preparaciones': data})


@login_required
def api_preparaciones_por_modalidad(request, modalidad_id):
    """API para listar todas las preparaciones Ãºnicas dentro de una modalidad."""
    if request.method != 'GET':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

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
        return JsonResponse({'error': f'OcurriÃ³ un error inesperado: {str(e)}'}, status=500)


@login_required
def api_menus_misma_modalidad_para_copia(request, id_menu):
    """Lista menÃºs de la misma modalidad para usar como origen de copia."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'MÃ©todo no permitido'}, status=405)

    menu_actual = get_object_or_404(
        TablaMenus.objects.select_related('id_modalidad', 'id_contrato'),
        id_menu=id_menu
    )
    menus = (
        TablaMenus.objects
        .filter(id_modalidad=menu_actual.id_modalidad)
        .select_related('id_contrato')
        .order_by('menu', 'id_menu')
    )

    data = [
        {
            'id_menu': m.id_menu,
            'menu': m.menu,
            'programa': str(m.id_contrato),
            'es_actual': m.id_menu == menu_actual.id_menu,
        }
        for m in menus
    ]
    return JsonResponse({'success': True, 'menus': data})


@login_required
def api_preparaciones_por_menu_para_copia(request, id_menu_origen):
    """Lista preparaciones de un menÃº origen para flujo de copia."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'MÃ©todo no permitido'}, status=405)

    menu_origen = get_object_or_404(TablaMenus, id_menu=id_menu_origen)
    preparaciones = (
        TablaPreparaciones.objects
        .filter(id_menu=menu_origen)
        .order_by('preparacion', 'id_preparacion')
    )

    data = []
    for prep in preparaciones:
        total_ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=prep
        ).count()
        data.append({
            'id_preparacion': prep.id_preparacion,
            'preparacion': prep.preparacion,
            'total_ingredientes': total_ingredientes,
        })

    return JsonResponse({'success': True, 'preparaciones': data})


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

    return JsonResponse({'error': 'MÃ©todo no permitido para catÃ¡logo ICBF'}, status=405)


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

    return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)


@login_required
def detalle_preparacion(request, id_preparacion):
    """Vista para ver y gestionar ingredientes de una preparaciÃ³n"""
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
    """API para manejar ingredientes de una preparaciÃ³n"""
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
                    f"PreparaciÃ³n ID: {id_preparacion} | Ingredientes agregados: {len(ingredientes_creados)}"
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
            return JsonResponse({'success': False, 'error': 'Este ingrediente ya estÃ¡ en la preparaciÃ³n'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'MÃ©todo no permitido'}, status=405)


@login_required
@csrf_exempt
def api_preparacion_ingrediente_delete(request, id_preparacion, id_ingrediente):
    """API para eliminar un ingrediente de una preparaciÃ³n"""
    if request.method == 'DELETE':
        try:
            ingrediente = get_object_or_404(
                TablaPreparacionIngredientes,
                id_preparacion_id=id_preparacion,
                id_ingrediente_siesa_id=id_ingrediente
            )
            menu = ingrediente.id_preparacion.id_menu
            ingrediente.delete()
            _limpiar_analisis_si_menu_sin_ingredientes(menu)
            RegistroActividad.registrar(
                request, 'nutricion', 'eliminar_ingrediente',
                f"PreparaciÃ³n ID: {id_preparacion} | Ingrediente: {id_ingrediente}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'MÃ©todo no permitido'}, status=405)

