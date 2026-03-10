"""
Vistas para el match ICBF → Compras.

Granularidad: (ingrediente_icbf, programa, menú) → 1 producto de compras.

Flujos:
  - Asignación masiva: mismo producto para todos los menús del ingrediente.
  - Override individual: cambia el producto de un menú específico.

SIMULACRO: el catálogo de compras usa TablaIngredientesSiesa.
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from ..models import (
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaIngredientesSiesa,
    EquivalenciaICBFCompras,
    TablaPreparacionIngredientes,
)
from ..services.match_icbf_service import obtener_dashboard_match
from principal.models import PrincipalMunicipio, RegistroActividad
from planeacion.models import Programa

logger = logging.getLogger(__name__)


@login_required
def vista_match_icbf(request):
    """
    Página principal del match ICBF → Compras.
    Tarjetas por ingrediente; dentro de cada tarjeta, tabla de menús
    con el producto de compras asignado a cada uno.
    """
    municipios = PrincipalMunicipio.objects.filter(
        programa__estado='activo'
    ).distinct().order_by('nombre_municipio')

    municipio_id = request.GET.get('municipio')
    programa_id  = request.GET.get('programa')

    context = {
        'municipios': municipios,
        'municipio_seleccionado': municipio_id,
        'programa_seleccionado': programa_id,
    }

    if municipio_id:
        context['programas'] = Programa.objects.filter(
            municipio_id=municipio_id, estado='activo'
        ).order_by('-fecha_inicial')

    if programa_id:
        try:
            programa = Programa.objects.get(id=programa_id)
            context['programa_obj'] = programa
            context.update(obtener_dashboard_match(programa_id))
        except Programa.DoesNotExist:
            context['error'] = 'Programa no encontrado.'
        except Exception as e:
            logger.error('Error en vista_match_icbf: %s', e, exc_info=True)
            context['error'] = (
                f'Error al cargar los datos: {e}. '
                'Verifique que las migraciones estén aplicadas (python manage.py migrate).'
            )
            context.pop('programa_obj', None)

    return render(request, 'nutricion/match_icbf.html', context)


# =================== APIs ===================

@login_required
def api_productos_siesa(request):
    """
    GET /nutricion/api/match/productos/?q=leche
    Búsqueda de productos del catálogo Siesa para el selector.
    """
    q = request.GET.get('q', '').strip()
    qs = TablaIngredientesSiesa.objects.all()
    if q:
        qs = qs.filter(nombre_ingrediente__icontains=q)
    return JsonResponse({
        'productos': [
            {
                'id':               p.id_ingrediente_siesa,
                'texto':            str(p),
                'nombre':           p.nombre_ingrediente,
                'presentacion':     p.presentacion or '',
                'unidad_medida':    p.unidad_medida or '',
                'contenido_gramos': str(p.contenido_gramos) if p.contenido_gramos else '',
            }
            for p in qs[:30]
        ]
    })


@login_required
@require_http_methods(['POST'])
def api_guardar_match(request):
    """
    Guarda o actualiza el match de un ingrediente ICBF para un menú específico.
    POST /nutricion/api/match/guardar/
    Body: {programa_id, codigo_icbf, menu_id, codigo_siesa}
    """
    try:
        data        = json.loads(request.body)
        programa_id = data.get('programa_id')
        codigo_icbf = data.get('codigo_icbf')
        menu_id     = data.get('menu_id')
        codigo_siesa = data.get('codigo_siesa')

        if not all([programa_id, codigo_icbf, menu_id, codigo_siesa]):
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        alimento = TablaAlimentos2018Icbf.objects.get(codigo=codigo_icbf)
        programa = Programa.objects.get(id=programa_id)
        menu     = TablaMenus.objects.get(id_menu=menu_id)
        producto = TablaIngredientesSiesa.objects.get(id_ingrediente_siesa=codigo_siesa)

        eq, created = EquivalenciaICBFCompras.objects.update_or_create(
            id_alimento_icbf=alimento,
            id_programa=programa,
            id_menu=menu,
            defaults={
                'id_ingrediente_compras': producto,
                'activo': True,
                'usuario': request.user.username,
            }
        )

        accion = 'crear_match_icbf' if created else 'editar_match_icbf'
        RegistroActividad.registrar(
            request, 'nutricion', accion,
            f"Programa:{programa_id} | Menú:{menu.menu} | "
            f"ICBF:{alimento.nombre_del_alimento} → {producto.nombre_ingrediente}"
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'match': {
                'id':               eq.id,
                'menu_id':          menu_id,
                'menu_num':         menu.menu,
                'codigo_siesa':     producto.id_ingrediente_siesa,
                'nombre_siesa':     producto.nombre_ingrediente,
                'presentacion':     producto.presentacion or '',
                'contenido_gramos': str(producto.contenido_gramos) if producto.contenido_gramos else '',
            }
        })

    except TablaAlimentos2018Icbf.DoesNotExist:
        return JsonResponse({'error': 'Alimento ICBF no encontrado'}, status=404)
    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)
    except TablaMenus.DoesNotExist:
        return JsonResponse({'error': 'Menú no encontrado'}, status=404)
    except TablaIngredientesSiesa.DoesNotExist:
        return JsonResponse({'error': 'Producto Siesa no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['POST'])
def api_guardar_match_bulk(request):
    """
    Asignación masiva: mismo producto para todos los menús donde aparece el ingrediente.
    POST /nutricion/api/match/guardar/bulk/
    Body: {programa_id, codigo_icbf, codigo_siesa, solo_sin_asignar: bool}
      solo_sin_asignar=true  → solo los menús sin match (no sobreescribe)
      solo_sin_asignar=false → todos (sobreescribe los que ya tenían)
    """
    try:
        data             = json.loads(request.body)
        programa_id      = data.get('programa_id')
        codigo_icbf      = data.get('codigo_icbf')
        codigo_siesa     = data.get('codigo_siesa')
        solo_sin_asignar = data.get('solo_sin_asignar', False)

        if not all([programa_id, codigo_icbf, codigo_siesa]):
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        alimento = TablaAlimentos2018Icbf.objects.get(codigo=codigo_icbf)
        programa = Programa.objects.get(id=programa_id)
        producto = TablaIngredientesSiesa.objects.get(id_ingrediente_siesa=codigo_siesa)

        menu_ids = list(
            TablaPreparacionIngredientes.objects
            .filter(
                id_preparacion__id_menu__id_contrato_id=programa_id,
                id_ingrediente_siesa=alimento,
            )
            .values_list('id_preparacion__id_menu_id', flat=True)
            .distinct()
        )

        if not menu_ids:
            return JsonResponse({'error': 'El ingrediente no aparece en ningún menú del programa'}, status=400)

        if solo_sin_asignar:
            ya_asignados = set(
                EquivalenciaICBFCompras.objects.filter(
                    id_alimento_icbf=alimento,
                    id_programa=programa,
                    id_menu_id__in=menu_ids,
                    activo=True,
                ).values_list('id_menu_id', flat=True)
            )
            menu_ids = [m for m in menu_ids if m not in ya_asignados]

        if not menu_ids:
            return JsonResponse({
                'success': True,
                'creados': 0,
                'actualizados': 0,
                'mensaje': 'Todos los menús ya tienen producto asignado.',
            })

        creados = actualizados = 0
        matches_resultado = []

        for menu_id in menu_ids:
            menu = TablaMenus.objects.get(id_menu=menu_id)
            eq, created = EquivalenciaICBFCompras.objects.update_or_create(
                id_alimento_icbf=alimento,
                id_programa=programa,
                id_menu=menu,
                defaults={
                    'id_ingrediente_compras': producto,
                    'activo': True,
                    'usuario': request.user.username,
                }
            )
            if created:
                creados += 1
            else:
                actualizados += 1
            matches_resultado.append({
                'id':               eq.id,
                'menu_id':          menu_id,
                'menu_num':         menu.menu,
                'codigo_siesa':     producto.id_ingrediente_siesa,
                'nombre_siesa':     producto.nombre_ingrediente,
                'presentacion':     producto.presentacion or '',
                'contenido_gramos': str(producto.contenido_gramos) if producto.contenido_gramos else '',
            })

        RegistroActividad.registrar(
            request, 'nutricion', 'crear_match_icbf_bulk',
            f"Programa:{programa_id} | ICBF:{alimento.nombre_del_alimento} → "
            f"{producto.nombre_ingrediente} | {creados} creados, {actualizados} actualizados"
        )

        return JsonResponse({
            'success':      True,
            'creados':      creados,
            'actualizados': actualizados,
            'matches':      matches_resultado,
        })

    except TablaAlimentos2018Icbf.DoesNotExist:
        return JsonResponse({'error': 'Alimento ICBF no encontrado'}, status=404)
    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)
    except TablaIngredientesSiesa.DoesNotExist:
        return JsonResponse({'error': 'Producto Siesa no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['DELETE'])
def api_eliminar_match(request, match_id):
    """
    Elimina un match específico por su PK.
    DELETE /nutricion/api/match/<match_id>/
    """
    try:
        eq = EquivalenciaICBFCompras.objects.select_related(
            'id_alimento_icbf', 'id_ingrediente_compras', 'id_menu'
        ).get(id=match_id)

        nombre_icbf  = eq.id_alimento_icbf.nombre_del_alimento
        nombre_siesa = eq.id_ingrediente_compras.nombre_ingrediente
        programa_id  = eq.id_programa_id
        menu_num     = eq.id_menu.menu

        eq.delete()

        RegistroActividad.registrar(
            request, 'nutricion', 'eliminar_match_icbf',
            f"Programa:{programa_id} | Menú:{menu_num} | ICBF:{nombre_icbf} → {nombre_siesa}"
        )
        return JsonResponse({'success': True})

    except EquivalenciaICBFCompras.DoesNotExist:
        return JsonResponse({'error': 'Match no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =================== Catálogo Siesa (simulacro) ===================

@login_required
@require_http_methods(['GET', 'POST'])
def api_productos_siesa_crud(request):
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        qs = TablaIngredientesSiesa.objects.all()
        if q:
            qs = qs.filter(nombre_ingrediente__icontains=q)
        return JsonResponse({'productos': [_serializar_producto(p) for p in qs[:50]]})

    data   = json.loads(request.body)
    codigo = data.get('codigo', '').strip()
    nombre = data.get('nombre', '').strip()
    if not codigo or not nombre:
        return JsonResponse({'error': 'Código y nombre son obligatorios'}, status=400)
    if TablaIngredientesSiesa.objects.filter(id_ingrediente_siesa=codigo).exists():
        return JsonResponse({'error': f'El código "{codigo}" ya existe'}, status=400)

    prod = TablaIngredientesSiesa.objects.create(
        id_ingrediente_siesa=codigo,
        nombre_ingrediente=nombre,
        presentacion=data.get('presentacion', '') or None,
        unidad_medida=data.get('unidad_medida', '') or None,
        contenido_gramos=data.get('contenido_gramos') or None,
    )
    RegistroActividad.registrar(
        request, 'nutricion', 'crear_producto_siesa',
        f"Código:{prod.id_ingrediente_siesa} | Nombre:{prod.nombre_ingrediente}"
    )
    return JsonResponse({'success': True, 'producto': _serializar_producto(prod)}, status=201)


@login_required
@require_http_methods(['GET', 'PUT', 'DELETE'])
def api_producto_siesa_detail(request, codigo):
    try:
        prod = TablaIngredientesSiesa.objects.get(id_ingrediente_siesa=codigo)
    except TablaIngredientesSiesa.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'producto': _serializar_producto(prod)})

    if request.method == 'PUT':
        data = json.loads(request.body)
        prod.nombre_ingrediente = data.get('nombre', prod.nombre_ingrediente)
        prod.presentacion       = data.get('presentacion', '') or None
        prod.unidad_medida      = data.get('unidad_medida', '') or None
        prod.contenido_gramos   = data.get('contenido_gramos') or None
        prod.save()
        RegistroActividad.registrar(
            request, 'nutricion', 'editar_producto_siesa',
            f"Código:{codigo} | Nombre:{prod.nombre_ingrediente}"
        )
        return JsonResponse({'success': True, 'producto': _serializar_producto(prod)})

    # DELETE
    nombre = prod.nombre_ingrediente
    try:
        prod.delete()
    except Exception:
        return JsonResponse(
            {'error': 'No se puede eliminar: tiene matches activos. Reasigne primero.'},
            status=400
        )
    RegistroActividad.registrar(
        request, 'nutricion', 'eliminar_producto_siesa',
        f"Código:{codigo} | Nombre:{nombre}"
    )
    return JsonResponse({'success': True})


def _serializar_producto(p):
    return {
        'id':               p.id_ingrediente_siesa,
        'codigo':           p.id_ingrediente_siesa,
        'nombre':           p.nombre_ingrediente,
        'presentacion':     p.presentacion or '',
        'unidad_medida':    p.unidad_medida or '',
        'contenido_gramos': str(p.contenido_gramos) if p.contenido_gramos else '',
        'texto':            str(p),
    }
