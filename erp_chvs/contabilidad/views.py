import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from principal.models import RegistroActividad
from .models import Factura, RegistroContable, VerificacionChecklist
from .services import ContabilidadService


# --------------------------------------------------------------------------- #
# Helper de rol                                                                #
# --------------------------------------------------------------------------- #

def _tiene_rol(user, *roles):
    """Devuelve True si el usuario es superusuario, pertenece a ADMINISTRACION
    o a alguno de los roles indicados."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=list(roles) + ['ADMINISTRACION']).exists()


# --------------------------------------------------------------------------- #
# Vistas de página                                                             #
# --------------------------------------------------------------------------- #

@login_required
def contabilidad_principal(request):
    """Dashboard de acceso al módulo según el rol del usuario."""
    return render(request, 'contabilidad/index.html')


@login_required
def mis_registros(request):
    """Lista de registros del líder autenticado."""
    return render(request, 'contabilidad/mis_registros.html')


@login_required
def detalle_registro(request, pk):
    """Detalle de un registro contable."""
    registro = get_object_or_404(RegistroContable, pk=pk)
    return render(request, 'contabilidad/detalle_registro.html', {'registro': registro})


@login_required
def bandeja_compras(request):
    """Bandeja de Compras: registros pendientes de revisión."""
    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return render(request, 'contabilidad/sin_permiso.html', status=403)
    return render(request, 'contabilidad/bandeja_compras.html')


@login_required
def revision_compras(request, pk):
    """Página de revisión de un registro por parte de Compras."""
    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return render(request, 'contabilidad/sin_permiso.html', status=403)
    registro = get_object_or_404(RegistroContable, pk=pk)
    return render(request, 'contabilidad/revision_compras.html', {'registro': registro})


@login_required
def bandeja_contabilidad(request):
    """Bandeja de Contabilidad: registros aprobados por Compras."""
    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return render(request, 'contabilidad/sin_permiso.html', status=403)
    return render(request, 'contabilidad/bandeja_contabilidad.html')


@login_required
def revision_contabilidad(request, pk):
    """Página de revisión de un registro por parte de Contabilidad."""
    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return render(request, 'contabilidad/sin_permiso.html', status=403)
    registro = get_object_or_404(RegistroContable, pk=pk)
    return render(request, 'contabilidad/revision_contabilidad.html', {'registro': registro})


@login_required
def dashboard_gerencia(request):
    """Vista unificada: historial de líderes + KPIs. Accesible para Compras, Contabilidad y Gerencia."""
    if not _tiene_rol(request.user, 'GERENCIA', 'CONTABILIDAD', 'COMPRAS_CONTABLE'):
        return render(request, 'contabilidad/sin_permiso.html', status=403)
    return render(request, 'contabilidad/dashboard_gerencia.html')


@login_required
def seguimiento_lideres(request):
    """Redirige a la vista unificada dashboard_gerencia."""
    from django.shortcuts import redirect
    return redirect('contabilidad:dashboard_gerencia')


# --------------------------------------------------------------------------- #
# APIs JSON                                                                    #
# --------------------------------------------------------------------------- #

@login_required
@csrf_exempt
def api_crear_registro(request):
    """POST — Crea un nuevo RegistroContable en estado BORRADOR."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'LIDER_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    try:
        data = json.loads(request.body)
        tipo = data.get('tipo', '').strip()
        periodo_mes = int(data.get('periodo_mes', 0))
        periodo_ano = int(data.get('periodo_ano', 0))
        descripcion = data.get('descripcion', '').strip()

        if tipo not in ('SERVICIOS', 'MATERIAS_PRIMAS'):
            return JsonResponse({'success': False, 'error': 'Tipo inválido. Use SERVICIOS o MATERIAS_PRIMAS.'})
        if not (1 <= periodo_mes <= 12):
            return JsonResponse({'success': False, 'error': 'Mes inválido (1-12).'})
        if periodo_ano < 2000:
            return JsonResponse({'success': False, 'error': 'Año inválido.'})

        registro = ContabilidadService.crear_registro(
            lider=request.user,
            tipo=tipo,
            periodo_mes=periodo_mes,
            periodo_ano=periodo_ano,
            descripcion=descripcion,
        )
        RegistroActividad.registrar(
            request, 'contabilidad', 'crear_registro',
            f"ID: {registro.pk} | Tipo: {tipo} | Período: {periodo_mes}/{periodo_ano}"
        )
        return JsonResponse({'success': True, 'id': registro.pk})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_listar_registros(request):
    """GET — Lista registros según rol del usuario."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    user = request.user

    solo_activos = request.GET.get('todos') != '1'

    if _tiene_rol(user, 'GERENCIA'):
        qs = RegistroContable.objects.select_related('lider').all()
    elif _tiene_rol(user, 'COMPRAS_CONTABLE'):
        qs = ContabilidadService.get_bandeja_compras(solo_activos=solo_activos)
    elif _tiene_rol(user, 'CONTABILIDAD'):
        qs = ContabilidadService.get_bandeja_contabilidad(solo_activos=solo_activos)
    else:
        # Líder: solo sus propios registros
        qs = RegistroContable.objects.filter(lider=user).select_related('lider')

    registros = []
    for r in qs.order_by('-fecha_creacion'):
        registros.append({
            'id': r.pk,
            'tipo': r.tipo,
            'tipo_display': r.get_tipo_display(),
            'periodo_mes': r.periodo_mes,
            'periodo_ano': r.periodo_ano,
            'descripcion': r.descripcion,
            'estado': r.estado,
            'estado_display': r.get_estado_display(),
            'lider': r.lider.get_full_name() or r.lider.username,
            'lider_id': r.lider_id,
            'fecha_creacion': r.fecha_creacion.isoformat() if r.fecha_creacion else None,
            'fecha_envio': r.fecha_envio.isoformat() if r.fecha_envio else None,
            'valor_total': float(r.valor_total),
            'total_documentos': r.total_documentos,
            'registro_origen_id': r.registro_origen_id,
            'es_derivado': r.registro_origen_id is not None,
        })

    return JsonResponse({'success': True, 'data': registros})


@login_required
def api_detalle_registro(request, pk):
    """GET — Detalle completo de un registro."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    registro = get_object_or_404(RegistroContable, pk=pk)

    facturas = []
    for f in registro.facturas.all():
        facturas.append({
            'id': f.pk,
            'numero_factura': f.numero_factura,
            'proveedor': f.proveedor,
            'concepto': f.concepto,
            'valor': float(f.valor),
            'fecha_factura': f.fecha_factura.isoformat() if f.fecha_factura else None,
            'fecha_recepcion_lider': f.fecha_recepcion_lider.isoformat() if f.fecha_recepcion_lider else None,
            'fecha_carga': f.fecha_carga.isoformat() if f.fecha_carga else None,
            'estado_compras': f.estado_compras,
            'comentario_devolucion': f.comentario_devolucion,
            'estado_contabilidad': f.estado_contabilidad,
            'comentario_devolucion_contabilidad': f.comentario_devolucion_contabilidad,
            'observacion_retraso': f.observacion_retraso,
        })

    data = {
        'id': registro.pk,
        'tipo': registro.tipo,
        'tipo_display': registro.get_tipo_display(),
        'periodo_mes': registro.periodo_mes,
        'periodo_ano': registro.periodo_ano,
        'descripcion': registro.descripcion,
        'estado': registro.estado,
        'estado_display': registro.get_estado_display(),
        'lider': registro.lider.get_full_name() or registro.lider.username,
        'lider_id': registro.lider_id,
        'fecha_creacion': registro.fecha_creacion.isoformat() if registro.fecha_creacion else None,
        'fecha_envio': registro.fecha_envio.isoformat() if registro.fecha_envio else None,
        'fecha_cierre': registro.fecha_cierre.isoformat() if registro.fecha_cierre else None,
        'valor_total': float(registro.valor_total),
        'total_documentos': registro.total_documentos,
        'registro_origen_id': registro.registro_origen_id,
        'registros_derivados': list(
            registro.registros_derivados.values_list('id', flat=True)
        ),
        'fecha_entrega_fisica': registro.fecha_entrega_fisica.isoformat() if registro.fecha_entrega_fisica else None,
        'fecha_reentrega_fisica': registro.fecha_reentrega_fisica.isoformat() if registro.fecha_reentrega_fisica else None,
        'fecha_aprobacion_compras': registro.fecha_aprobacion_compras.isoformat() if registro.fecha_aprobacion_compras else None,
        'justificacion_demora_lider': registro.justificacion_demora_lider,
        'justificacion_demora_compras': registro.justificacion_demora_compras,
        'justificacion_demora_contabilidad': registro.justificacion_demora_contabilidad,
        'facturas': facturas,
    }
    return JsonResponse({'success': True, 'data': data})


@login_required
@csrf_exempt
def api_aprobar_factura(request, pk):
    """POST — Compras aprueba una factura individual."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    factura = get_object_or_404(Factura, pk=pk)
    try:
        ContabilidadService.aprobar_factura(factura, request.user)
        RegistroActividad.registrar(
            request, 'contabilidad', 'aprobar_factura',
            f"Factura: {factura.numero_factura} | Registro: {factura.registro_id}"
        )
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_devolver_factura(request, pk):
    """POST — Compras devuelve una factura individual al líder."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    factura = get_object_or_404(Factura, pk=pk)
    try:
        data = json.loads(request.body)
        comentario = data.get('comentario', '').strip()
        ContabilidadService.devolver_factura(factura, request.user, comentario)
        RegistroActividad.registrar(
            request, 'contabilidad', 'devolver_factura',
            f"Factura: {factura.numero_factura} | Registro: {factura.registro_id} | Motivo: {comentario[:80]}"
        )
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_finalizar_revision(request, pk):
    """POST — Finaliza la revisión de Compras (todas las facturas decididas)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)
    try:
        data = json.loads(request.body) if request.body else {}
        justificacion = data.get('justificacion_demora', '')
        registro, nuevo = ContabilidadService.finalizar_revision_compras(registro, request.user, justificacion=justificacion)
        RegistroActividad.registrar(
            request, 'contabilidad', 'finalizar_revision_compras',
            f"Registro: {pk} | Estado final: {registro.estado}"
            + (f" | Derivado RC-{nuevo.pk}" if nuevo else "")
        )
        resp = {'success': True, 'estado': registro.estado}
        if nuevo:
            resp['registro_derivado_id'] = nuevo.pk
            resp['mensaje'] = (
                f"Se separaron las facturas aprobadas en el registro RC-{nuevo.pk}, "
                "que ya fue enviado a Contabilidad."
            )
        return JsonResponse(resp)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_agregar_factura(request, pk):
    """POST — Agrega una factura al registro."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    registro = get_object_or_404(RegistroContable, pk=pk)

    # Solo el líder dueño puede agregar facturas
    if registro.lider != request.user and not _tiene_rol(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    try:
        data = json.loads(request.body)
        factura = ContabilidadService.agregar_factura(registro, data)
        RegistroActividad.registrar(
            request, 'contabilidad', 'agregar_factura',
            f"Registro: {pk} | Factura: {factura.numero_factura} | Valor: {factura.valor}"
        )
        return JsonResponse({'success': True, 'id': factura.pk})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_eliminar_factura(request, pk):
    """DELETE — Elimina una factura."""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    factura = get_object_or_404(Factura, pk=pk)

    if factura.registro.lider != request.user and not _tiene_rol(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    try:
        registro_id = factura.registro_id
        num_factura = factura.numero_factura
        ContabilidadService.eliminar_factura(factura, request.user)
        RegistroActividad.registrar(
            request, 'contabilidad', 'eliminar_factura',
            f"Registro: {registro_id} | Factura: {num_factura}"
        )
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_enviar(request, pk):
    """POST — Envía el registro a Compras."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    registro = get_object_or_404(RegistroContable, pk=pk)

    if registro.lider != request.user and not _tiene_rol(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        justificacion = data.get('justificacion_demora', '')
        ContabilidadService.enviar(registro, request.user, justificacion=justificacion)
        RegistroActividad.registrar(
            request, 'contabilidad', 'enviar_registro',
            f"Registro: {pk} | Estado: {registro.estado}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_confirmar_recepcion(request, pk):
    """POST — Compras confirma recepción de documentos físicos."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        ContabilidadService.confirmar_recepcion(registro, request.user)
        RegistroActividad.registrar(
            request, 'contabilidad', 'confirmar_recepcion',
            f"Registro: {pk}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_devolver_compras(request, pk):
    """POST — Compras devuelve el registro al líder con comentario."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        data = json.loads(request.body)
        comentario = data.get('comentario', '').strip()
        ContabilidadService.devolver_compras(registro, request.user, comentario)
        RegistroActividad.registrar(
            request, 'contabilidad', 'devolver_registro',
            f"Registro: {pk} | Motivo: {comentario[:80]}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_aprobar_compras(request, pk):
    """POST — Compras aprueba el registro."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        data = json.loads(request.body) if request.body else {}
        comentario = data.get('comentario', '').strip()
        ContabilidadService.aprobar_compras(registro, request.user, comentario)
        RegistroActividad.registrar(
            request, 'contabilidad', 'aprobar_compras',
            f"Registro: {pk}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
def api_checklist(request, pk):
    """GET — Retorna el checklist del registro agrupado por factura.
    Inicializa si alguna factura no tiene verificaciones todavía."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    registro = get_object_or_404(RegistroContable, pk=pk)

    # Inicializar si no hay verificaciones en ninguna factura
    facturas_con_verificaciones = set(
        VerificacionChecklist.objects.filter(
            factura__registro=registro
        ).values_list('factura_id', flat=True)
    )
    facturas_sin_verificaciones = registro.facturas.exclude(
        pk__in=facturas_con_verificaciones
    )
    if facturas_sin_verificaciones.exists():
        ContabilidadService.inicializar_checklist(registro)

    # Cargar todo agrupado por factura
    facturas = registro.facturas.prefetch_related(
        'verificaciones__item',
        'verificaciones__verificado_por',
    ).order_by('fecha_carga')

    data = []
    for factura in facturas:
        verificaciones = sorted(
            factura.verificaciones.all(),
            key=lambda v: v.item.orden
        )
        data.append({
            'factura_id': factura.pk,
            'numero_factura': factura.numero_factura,
            'proveedor': factura.proveedor,
            'concepto': factura.concepto,
            'estado_compras': factura.estado_compras,
            'comentario_devolucion': factura.comentario_devolucion,
            'verificaciones': [
                {
                    'id': v.pk,
                    'item_id': v.item_id,
                    'item_nombre': v.item.nombre,
                    'item_descripcion': v.item.descripcion,
                    'item_obligatorio': v.item.obligatorio,
                    'item_orden': v.item.orden,
                    'estado': v.estado,
                    'observacion': v.observacion,
                    'verificado_por': v.verificado_por.username if v.verificado_por else None,
                    'fecha_verificacion': v.fecha_verificacion.isoformat() if v.fecha_verificacion else None,
                }
                for v in verificaciones
            ],
        })

    return JsonResponse({'success': True, 'data': data})


@login_required
@csrf_exempt
def api_guardar_checklist(request, pk):
    """POST — Guarda el checklist verificado por Compras."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        ContabilidadService.guardar_checklist(registro, items_data, request.user)
        RegistroActividad.registrar(
            request, 'contabilidad', 'guardar_checklist',
            f"Registro: {pk} | Ítems: {len(items_data)}"
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_aprobar_factura_contabilidad(request, pk):
    """POST — Contabilidad aprueba una factura individual."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
    factura = get_object_or_404(Factura, pk=pk)
    try:
        ContabilidadService.aprobar_factura_contabilidad(factura, request.user)
        RegistroActividad.registrar(
            request, 'contabilidad', 'aprobar_factura_contabilidad',
            f"Factura: {factura.numero_factura} | Registro: {factura.registro_id}"
        )
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_devolver_factura_contabilidad(request, pk):
    """POST — Contabilidad devuelve una factura individual a Compras."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
    factura = get_object_or_404(Factura, pk=pk)
    try:
        data = json.loads(request.body)
        comentario = data.get('comentario', '').strip()
        ContabilidadService.devolver_factura_contabilidad(factura, request.user, comentario)
        RegistroActividad.registrar(
            request, 'contabilidad', 'devolver_factura_contabilidad',
            f"Factura: {factura.numero_factura} | Registro: {factura.registro_id} | Motivo: {comentario[:80]}"
        )
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_finalizar_revision_contabilidad(request, pk):
    """POST — Contabilidad finaliza la revisión (con posible split parcial)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
    registro = get_object_or_404(RegistroContable, pk=pk)
    try:
        data = json.loads(request.body) if request.body else {}
        justificacion = data.get('justificacion_demora', '')
        registro_original, registro_nuevo = ContabilidadService.finalizar_revision_contabilidad(
            registro, request.user, justificacion=justificacion
        )
        RegistroActividad.registrar(
            request, 'contabilidad', 'finalizar_revision_contabilidad',
            f"Registro: {pk}" + (f" | Nuevo RC: {registro_nuevo.pk}" if registro_nuevo else "")
        )
        return JsonResponse({
            'success': True,
            'estado': registro_original.estado,
            'nuevo_registro_id': registro_nuevo.pk if registro_nuevo else None,
        })
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_observar_contabilidad(request, pk):
    """POST — Contabilidad observa el registro y lo devuelve a Compras."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        data = json.loads(request.body)
        comentario = data.get('comentario', '').strip()
        justificacion = data.get('justificacion_demora', '')
        ContabilidadService.observar_contabilidad(registro, request.user, comentario, justificacion=justificacion)
        RegistroActividad.registrar(
            request, 'contabilidad', 'observar_contabilidad',
            f"Registro: {pk} | Observación: {comentario[:80]}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_aprobar_contabilidad(request, pk):
    """POST — Contabilidad aprueba y cierra el registro."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'CONTABILIDAD'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        data = json.loads(request.body) if request.body else {}
        comentario = data.get('comentario', '').strip()
        justificacion = data.get('justificacion_demora', '')
        ContabilidadService.aprobar_contabilidad(registro, request.user, comentario, justificacion=justificacion)
        RegistroActividad.registrar(
            request, 'contabilidad', 'aprobar_contabilidad',
            f"Registro: {pk}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_responder_observacion(request, pk):
    """POST — Compras responde la observación de Contabilidad."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    registro = get_object_or_404(RegistroContable, pk=pk)

    try:
        data = json.loads(request.body)
        comentario = data.get('comentario', '').strip()
        ContabilidadService.responder_observacion(registro, request.user, comentario)
        RegistroActividad.registrar(
            request, 'contabilidad', 'responder_observacion',
            f"Registro: {pk} | Respuesta: {comentario[:80]}"
        )
        return JsonResponse({'success': True, 'estado': registro.estado})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
def api_historial(request, pk):
    """GET — Historial de estados de un registro."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    registro = get_object_or_404(RegistroContable, pk=pk)

    historial = []
    for h in registro.historial.select_related('usuario').all():
        historial.append({
            'id': h.pk,
            'accion': h.accion,
            'accion_display': h.get_accion_display(),
            'estado_anterior': h.estado_anterior,
            'estado_nuevo': h.estado_nuevo,
            'comentario': h.comentario,
            'usuario': h.usuario.get_full_name() or h.usuario.username if h.usuario else 'Sistema',
            'fecha': h.fecha.isoformat() if h.fecha else None,
        })

    return JsonResponse({'success': True, 'data': historial})


@login_required
def api_seguimiento_lideres(request):
    """GET — Alias mantenido por compatibilidad; delega a api_dashboard_unificado."""
    return api_dashboard_unificado(request)


@login_required
def api_dashboard(request):
    """GET — Alias legacy; delega a api_dashboard_unificado."""
    return api_dashboard_unificado(request)


@login_required
def api_dashboard_unificado(request):
    """GET — Vista unificada: KPIs globales + historial de métricas por líder."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    if not _tiene_rol(request.user, 'GERENCIA', 'CONTABILIDAD', 'COMPRAS_CONTABLE'):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    filtros = {
        'lider_id': request.GET.get('lider_id'),
        'periodo_mes': request.GET.get('periodo_mes'),
        'periodo_ano': request.GET.get('periodo_ano'),
        'tipo': request.GET.get('tipo'),
    }
    filtros = {k: v for k, v in filtros.items() if v}

    try:
        data = ContabilidadService.get_dashboard_unificado(filtros)
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})
