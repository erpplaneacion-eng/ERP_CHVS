"""
Vistas para el match ICBF → Compras.

Permite al nutricionista asociar cada alimento ICBF (usado en los menús
de un programa) con su producto equivalente en el catálogo de compras.

SIMULACRO: el catálogo de compras usa TablaIngredientesSiesa.
Cuando Api/ esté activo se reemplaza la fuente sin cambiar esta vista.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import json

from ..models import (
    TablaAlimentos2018Icbf,
    TablaIngredientesSiesa,
    EquivalenciaICBFCompras,
    TablaPreparacionIngredientes,
)
from principal.models import ModalidadesDeConsumo, PrincipalMunicipio, RegistroActividad
from planeacion.models import Programa


@login_required
def vista_match_icbf(request):
    """
    Página principal del match ICBF → Compras.
    Muestra los ingredientes ICBF usados en los menús del programa seleccionado
    y su estado de match (con/sin producto Siesa asignado).
    """
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
        context['programas'] = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).order_by('-fecha_inicial')

    if programa_id:
        try:
            programa = Programa.objects.get(id=programa_id)
            context['programa_obj'] = programa

            ingredientes_icbf = _obtener_ingredientes_programa(programa_id)
            matches_existentes = {
                eq.id_alimento_icbf_id: eq
                for eq in EquivalenciaICBFCompras.objects.filter(
                    id_programa_id=programa_id
                ).select_related('id_ingrediente_compras')
            }

            filas = []
            for alimento in ingredientes_icbf:
                match = matches_existentes.get(alimento.codigo)
                filas.append({
                    'alimento': alimento,
                    'match': match,
                    'tiene_match': match is not None and match.activo,
                })

            context['filas'] = filas
            context['total'] = len(filas)
            context['con_match'] = sum(1 for f in filas if f['tiene_match'])
            context['sin_match'] = sum(1 for f in filas if not f['tiene_match'])

        except Programa.DoesNotExist:
            context['error'] = 'Programa no encontrado.'
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Error en vista_match_icbf: %s', e, exc_info=True)
            # Probable causa: migraciones pendientes (0037/0038). Ejecutar: python manage.py migrate
            context['error'] = (
                f'Error al cargar los datos del programa: {e}. '
                'Si el error persiste, verifique que las migraciones estén aplicadas '
                '(python manage.py migrate).'
            )
            context.pop('programa_obj', None)

    return render(request, 'nutricion/match_icbf.html', context)


def _obtener_ingredientes_programa(programa_id):
    """
    Devuelve los alimentos ICBF distintos usados en los menús de un programa.
    """
    codigos = (
        TablaPreparacionIngredientes.objects
        .filter(id_preparacion__id_menu__id_contrato_id=programa_id)
        .values_list('id_ingrediente_siesa_id', flat=True)
        .distinct()
    )
    return (
        TablaAlimentos2018Icbf.objects
        .filter(codigo__in=codigos)
        .select_related('id_componente')
        .order_by('nombre_del_alimento')
    )


# =================== APIs ===================

@login_required
def api_productos_siesa(request):
    """
    Búsqueda de productos del catálogo Siesa para el selector del match.
    GET /nutricion/api/match/productos/?q=leche
    """
    q = request.GET.get('q', '').strip()
    qs = TablaIngredientesSiesa.objects.all()
    if q:
        qs = qs.filter(nombre_ingrediente__icontains=q)
    qs = qs[:30]
    return JsonResponse({
        'productos': [
            {
                'id': p.id_ingrediente_siesa,
                'texto': str(p),
                'nombre': p.nombre_ingrediente,
                'presentacion': p.presentacion or '',
                'unidad_medida': p.unidad_medida or '',
                'contenido_gramos': str(p.contenido_gramos) if p.contenido_gramos else '',
            }
            for p in qs
        ]
    })


@login_required
@require_http_methods(['POST'])
def api_guardar_match(request):
    """
    Guarda o actualiza un match ICBF → producto Siesa.
    POST /nutricion/api/match/guardar/
    Body: {programa_id, codigo_icbf, codigo_siesa}
    """
    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        codigo_icbf = data.get('codigo_icbf')
        codigo_siesa = data.get('codigo_siesa')

        if not all([programa_id, codigo_icbf, codigo_siesa]):
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        alimento = TablaAlimentos2018Icbf.objects.get(codigo=codigo_icbf)
        programa = Programa.objects.get(id=programa_id)
        producto = TablaIngredientesSiesa.objects.get(id_ingrediente_siesa=codigo_siesa)

        eq, created = EquivalenciaICBFCompras.objects.update_or_create(
            id_alimento_icbf=alimento,
            id_programa=programa,
            defaults={
                'id_ingrediente_compras': producto,
                'activo': True,
                'usuario': request.user.username,
            }
        )

        accion = 'crear_match_icbf' if created else 'editar_match_icbf'
        RegistroActividad.registrar(
            request, 'nutricion', accion,
            f"Programa: {programa_id} | ICBF: {alimento.nombre_del_alimento} → Siesa: {producto.nombre_ingrediente}"
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'match': {
                'codigo_icbf': codigo_icbf,
                'nombre_icbf': alimento.nombre_del_alimento,
                'codigo_siesa': producto.id_ingrediente_siesa,
                'nombre_siesa': producto.nombre_ingrediente,
                'presentacion': producto.presentacion or '',
            }
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
def api_eliminar_match(request, codigo_icbf):
    """
    Elimina el match de un alimento ICBF para un programa.
    DELETE /nutricion/api/match/<codigo_icbf>/?programa_id=5
    """
    try:
        programa_id = request.GET.get('programa_id')
        if not programa_id:
            return JsonResponse({'error': 'Falta programa_id'}, status=400)

        eq = EquivalenciaICBFCompras.objects.get(
            id_alimento_icbf_id=codigo_icbf,
            id_programa_id=programa_id
        )
        nombre_icbf = eq.id_alimento_icbf.nombre_del_alimento
        nombre_siesa = eq.id_ingrediente_compras.nombre_ingrediente
        eq.delete()

        RegistroActividad.registrar(
            request, 'nutricion', 'eliminar_match_icbf',
            f"Programa: {programa_id} | ICBF: {nombre_icbf} → Siesa: {nombre_siesa}"
        )
        return JsonResponse({'success': True})

    except EquivalenciaICBFCompras.DoesNotExist:
        return JsonResponse({'error': 'Match no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['GET', 'POST'])
def api_productos_siesa_crud(request):
    """
    GET  /nutricion/api/match/catalogo/        → lista productos
    POST /nutricion/api/match/catalogo/        → crear producto
    """
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        qs = TablaIngredientesSiesa.objects.all()
        if q:
            qs = qs.filter(nombre_ingrediente__icontains=q)
        return JsonResponse({
            'productos': [_serializar_producto(p) for p in qs[:50]]
        })

    data = json.loads(request.body)
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
        f"Código: {prod.id_ingrediente_siesa} | Nombre: {prod.nombre_ingrediente}"
    )
    return JsonResponse({'success': True, 'producto': _serializar_producto(prod)}, status=201)


@login_required
def api_producto_siesa_detail(request, codigo):
    """
    PUT    /nutricion/api/match/catalogo/<codigo>/  → editar
    DELETE /nutricion/api/match/catalogo/<codigo>/  → eliminar
    """
    try:
        prod = TablaIngredientesSiesa.objects.get(id_ingrediente_siesa=codigo)
    except TablaIngredientesSiesa.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    if request.method == 'PUT':
        data = json.loads(request.body)
        prod.nombre_ingrediente = data.get('nombre', prod.nombre_ingrediente)
        prod.presentacion = data.get('presentacion', '') or None
        prod.unidad_medida = data.get('unidad_medida', '') or None
        prod.contenido_gramos = data.get('contenido_gramos') or None
        prod.save()
        RegistroActividad.registrar(
            request, 'nutricion', 'editar_producto_siesa',
            f"Código: {codigo} | Nombre: {prod.nombre_ingrediente}"
        )
        return JsonResponse({'success': True, 'producto': _serializar_producto(prod)})

    if request.method == 'DELETE':
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
            f"Código: {codigo} | Nombre: {nombre}"
        )
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


def _serializar_producto(p):
    return {
        'id': p.id_ingrediente_siesa,
        'codigo': p.id_ingrediente_siesa,
        'nombre': p.nombre_ingrediente,
        'presentacion': p.presentacion or '',
        'unidad_medida': p.unidad_medida or '',
        'contenido_gramos': str(p.contenido_gramos) if p.contenido_gramos else '',
        'texto': str(p),
    }
