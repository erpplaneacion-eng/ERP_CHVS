from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
import json

from .models import TipoRuta, Ruta, RutaSedes
from planeacion.models import Programa, SedesEducativas
from principal.models import RegistroActividad


# ===================== VISTAS DE PÁGINA =====================

@login_required
def logistica_principal(request):
    """Vista principal del módulo de logística."""
    return render(request, 'logistica/index.html')


@login_required
def lista_tipos_ruta(request):
    """Vista para listar tipos de ruta."""
    tipos = TipoRuta.objects.all().order_by('tipo')
    paginator = Paginator(tipos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'logistica/tipos_ruta.html', {
        'tipos_ruta': page_obj,
        'total_tipos_ruta': tipos.count()
    })


@login_required
def lista_rutas(request):
    """Vista para listar rutas de entrega."""
    rutas = Ruta.objects.select_related('id_tipo_ruta', 'id_programa').all().order_by('nombre_ruta')
    paginator = Paginator(rutas, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'logistica/rutas.html', {
        'rutas': page_obj,
        'total_rutas': rutas.count()
    })


@login_required
def lista_ruta_sedes(request):
    """Vista para listar asignaciones de sedes a rutas."""
    ruta_sedes = RutaSedes.objects.select_related(
        'id_ruta', 'id_ruta__id_tipo_ruta', 'sede_educativa'
    ).all().order_by('id_ruta__nombre_ruta', 'orden_visita')
    paginator = Paginator(ruta_sedes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'logistica/ruta_sedes.html', {
        'ruta_sedes': page_obj,
        'total_ruta_sedes': ruta_sedes.count()
    })


# ===================== API AUXILIARES =====================

@login_required
def api_programas_list(request):
    """Lista de programas para selects."""
    programas = Programa.objects.all().order_by('programa').values('id', 'programa', 'contrato')
    return JsonResponse({'programas': list(programas)})


@login_required
def api_sedes_list(request):
    """Lista de sedes educativas para selects."""
    sedes = SedesEducativas.objects.all().order_by('nombre_sede_educativa').values(
        'cod_interprise', 'nombre_sede_educativa', 'codigo_ie__nombre_institucion'
    )
    return JsonResponse({'sedes': list(sedes)})


@login_required
def api_rutas_list(request):
    """Lista de rutas activas para selects."""
    rutas = Ruta.objects.filter(activa=True).select_related('id_tipo_ruta').order_by('nombre_ruta').values(
        'id', 'nombre_ruta', 'id_tipo_ruta__tipo', 'id_programa__programa'
    )
    return JsonResponse({'rutas': list(rutas)})


# ===================== API: TIPOS DE RUTA =====================

@login_required
@csrf_exempt
def api_tipos_ruta(request):
    """API para listar y crear tipos de ruta."""
    if request.method == 'GET':
        tipos = TipoRuta.objects.all().order_by('tipo').values('id', 'tipo')
        return JsonResponse({'tipos_ruta': list(tipos)})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tipo_nombre = data.get('tipo', '').strip()
            if not tipo_nombre:
                return JsonResponse({'success': False, 'error': 'El nombre del tipo es obligatorio'})

            if TipoRuta.objects.filter(tipo__iexact=tipo_nombre).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un tipo de ruta con ese nombre'})

            tipo = TipoRuta.objects.create(tipo=tipo_nombre)
            RegistroActividad.registrar(
                request, 'logistica', 'crear_tipo_ruta',
                f"ID: {tipo.id} | Tipo: {tipo.tipo}"
            )
            return JsonResponse({'success': True, 'tipo_ruta': {'id': tipo.id, 'tipo': tipo.tipo}})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_tipo_ruta_detail(request, pk):
    """API para obtener, editar o eliminar un tipo de ruta."""
    try:
        tipo = TipoRuta.objects.get(pk=pk)
    except TipoRuta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tipo de ruta no encontrado'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'id': tipo.id, 'tipo': tipo.tipo})

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            tipo_nombre = data.get('tipo', '').strip()
            if not tipo_nombre:
                return JsonResponse({'success': False, 'error': 'El nombre del tipo es obligatorio'})

            if TipoRuta.objects.filter(tipo__iexact=tipo_nombre).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe un tipo de ruta con ese nombre'})

            tipo.tipo = tipo_nombre
            tipo.save()
            RegistroActividad.registrar(
                request, 'logistica', 'editar_tipo_ruta',
                f"ID: {pk} | Tipo: {tipo.tipo}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    if request.method == 'DELETE':
        try:
            nombre = tipo.tipo
            tipo.delete()
            RegistroActividad.registrar(
                request, 'logistica', 'eliminar_tipo_ruta',
                f"ID: {pk} | Tipo: {nombre}"
            )
            return JsonResponse({'success': True})
        except ProtectedError:
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar: existen rutas que usan este tipo.'
            }, status=409)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ===================== API: RUTAS =====================

@login_required
@csrf_exempt
def api_rutas(request):
    """API para listar y crear rutas."""
    if request.method == 'GET':
        rutas = Ruta.objects.select_related('id_tipo_ruta', 'id_programa').all().order_by('nombre_ruta')
        data = [
            {
                'id': r.id,
                'nombre_ruta': r.nombre_ruta,
                'id_tipo_ruta': r.id_tipo_ruta_id,
                'tipo_ruta_nombre': r.id_tipo_ruta.tipo,
                'id_programa': r.id_programa_id,
                'programa_nombre': r.id_programa.programa,
                'activa': r.activa,
            }
            for r in rutas
        ]
        return JsonResponse({'rutas': data})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre_ruta', '').strip()
            id_tipo = data.get('id_tipo_ruta')
            id_programa = data.get('id_programa')
            activa = data.get('activa', True)

            if not nombre or not id_tipo or not id_programa:
                return JsonResponse({'success': False, 'error': 'Nombre, tipo de ruta y programa son obligatorios'})

            tipo = TipoRuta.objects.get(pk=id_tipo)
            programa = Programa.objects.get(pk=id_programa)

            if Ruta.objects.filter(nombre_ruta=nombre, id_programa=programa, id_tipo_ruta=tipo).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe una ruta con ese nombre en este programa y tipo'})

            ruta = Ruta.objects.create(
                nombre_ruta=nombre,
                id_tipo_ruta=tipo,
                id_programa=programa,
                activa=activa
            )
            RegistroActividad.registrar(
                request, 'logistica', 'crear_ruta',
                f"ID: {ruta.id} | Ruta: {ruta.nombre_ruta} | Programa: {programa.programa}"
            )
            return JsonResponse({'success': True, 'ruta': {
                'id': ruta.id,
                'nombre_ruta': ruta.nombre_ruta,
                'tipo_ruta_nombre': tipo.tipo,
                'programa_nombre': programa.programa,
                'activa': ruta.activa,
            }})

        except TipoRuta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tipo de ruta no encontrado'})
        except Programa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Programa no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_ruta_detail(request, pk):
    """API para obtener, editar o eliminar una ruta."""
    try:
        ruta = Ruta.objects.select_related('id_tipo_ruta', 'id_programa').get(pk=pk)
    except Ruta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ruta no encontrada'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': ruta.id,
            'nombre_ruta': ruta.nombre_ruta,
            'id_tipo_ruta': ruta.id_tipo_ruta_id,
            'id_programa': ruta.id_programa_id,
            'activa': ruta.activa,
        })

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nombre = data.get('nombre_ruta', '').strip()
            id_tipo = data.get('id_tipo_ruta')
            id_programa = data.get('id_programa')
            activa = data.get('activa', True)

            if not nombre or not id_tipo or not id_programa:
                return JsonResponse({'success': False, 'error': 'Nombre, tipo de ruta y programa son obligatorios'})

            tipo = TipoRuta.objects.get(pk=id_tipo)
            programa = Programa.objects.get(pk=id_programa)

            if Ruta.objects.filter(
                nombre_ruta=nombre, id_programa=programa, id_tipo_ruta=tipo
            ).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Ya existe una ruta con ese nombre en este programa y tipo'})

            ruta.nombre_ruta = nombre
            ruta.id_tipo_ruta = tipo
            ruta.id_programa = programa
            ruta.activa = activa
            ruta.save()
            RegistroActividad.registrar(
                request, 'logistica', 'editar_ruta',
                f"ID: {pk} | Ruta: {ruta.nombre_ruta}"
            )
            return JsonResponse({'success': True})

        except TipoRuta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tipo de ruta no encontrado'})
        except Programa.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Programa no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    if request.method == 'DELETE':
        try:
            nombre = ruta.nombre_ruta
            ruta.delete()
            RegistroActividad.registrar(
                request, 'logistica', 'eliminar_ruta',
                f"ID: {pk} | Ruta: {nombre}"
            )
            return JsonResponse({'success': True})
        except ProtectedError:
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar: existen sedes asignadas a esta ruta.'
            }, status=409)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ===================== API: RUTA SEDES =====================

@login_required
@csrf_exempt
def api_ruta_sedes(request):
    """API para listar y crear asignaciones de sedes a rutas."""
    if request.method == 'GET':
        ruta_id = request.GET.get('ruta_id')
        qs = RutaSedes.objects.select_related(
            'id_ruta', 'id_ruta__id_tipo_ruta', 'sede_educativa'
        ).all().order_by('id_ruta__nombre_ruta', 'orden_visita')

        if ruta_id:
            qs = qs.filter(id_ruta_id=ruta_id)

        data = [
            {
                'id': rs.id,
                'id_ruta': rs.id_ruta_id,
                'ruta_nombre': rs.id_ruta.nombre_ruta,
                'tipo_ruta_nombre': rs.id_ruta.id_tipo_ruta.tipo,
                'sede_educativa': rs.sede_educativa_id,
                'sede_nombre': rs.sede_educativa.nombre_sede_educativa,
                'orden_visita': rs.orden_visita,
            }
            for rs in qs
        ]
        return JsonResponse({'ruta_sedes': data})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            id_ruta = data.get('id_ruta')
            sede_cod = data.get('sede_educativa')
            orden = data.get('orden_visita', 1)

            if not id_ruta or not sede_cod:
                return JsonResponse({'success': False, 'error': 'Ruta y sede son obligatorios'})

            ruta = Ruta.objects.get(pk=id_ruta)
            sede = SedesEducativas.objects.get(cod_interprise=sede_cod)

            if RutaSedes.objects.filter(id_ruta=ruta, sede_educativa=sede).exists():
                return JsonResponse({'success': False, 'error': 'Esta sede ya está asignada a esa ruta'})

            rs = RutaSedes.objects.create(id_ruta=ruta, sede_educativa=sede, orden_visita=orden)
            RegistroActividad.registrar(
                request, 'logistica', 'asignar_sede_ruta',
                f"Ruta: {ruta.nombre_ruta} | Sede: {sede.nombre_sede_educativa} | Orden: {orden}"
            )
            return JsonResponse({'success': True, 'ruta_sede': {
                'id': rs.id,
                'ruta_nombre': ruta.nombre_ruta,
                'sede_nombre': sede.nombre_sede_educativa,
                'orden_visita': rs.orden_visita,
            }})

        except Ruta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ruta no encontrada'})
        except SedesEducativas.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Sede no encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_ruta_sede_detail(request, pk):
    """API para obtener, editar o eliminar una asignación sede-ruta."""
    try:
        rs = RutaSedes.objects.select_related('id_ruta', 'sede_educativa').get(pk=pk)
    except RutaSedes.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Asignación no encontrada'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': rs.id,
            'id_ruta': rs.id_ruta_id,
            'sede_educativa': rs.sede_educativa_id,
            'orden_visita': rs.orden_visita,
        })

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            id_ruta = data.get('id_ruta')
            sede_cod = data.get('sede_educativa')
            orden = data.get('orden_visita', rs.orden_visita)

            if not id_ruta or not sede_cod:
                return JsonResponse({'success': False, 'error': 'Ruta y sede son obligatorios'})

            ruta = Ruta.objects.get(pk=id_ruta)
            sede = SedesEducativas.objects.get(cod_interprise=sede_cod)

            if RutaSedes.objects.filter(id_ruta=ruta, sede_educativa=sede).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'Esta sede ya está asignada a esa ruta'})

            rs.id_ruta = ruta
            rs.sede_educativa = sede
            rs.orden_visita = orden
            rs.save()
            RegistroActividad.registrar(
                request, 'logistica', 'editar_asignacion_ruta',
                f"ID: {pk} | Ruta: {ruta.nombre_ruta} | Sede: {sede.nombre_sede_educativa}"
            )
            return JsonResponse({'success': True})

        except Ruta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ruta no encontrada'})
        except SedesEducativas.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Sede no encontrada'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    if request.method == 'DELETE':
        try:
            desc = f"Ruta: {rs.id_ruta.nombre_ruta} | Sede: {rs.sede_educativa.nombre_sede_educativa}"
            rs.delete()
            RegistroActividad.registrar(
                request, 'logistica', 'eliminar_asignacion_ruta',
                f"ID: {pk} | {desc}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)
