from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from principal.models import RegistroActividad

from ..models import ProcedimientoPreparacion


@login_required
def lista_procedimientos(request):
    search_query = request.GET.get('q', '').strip()
    qs = ProcedimientoPreparacion.objects.order_by('nombre')

    if search_query:
        qs = qs.filter(
            Q(nombre__icontains=search_query) |
            Q(procedimiento__icontains=search_query)
        )

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    procedimientos_page = paginator.get_page(page_number)

    return render(request, 'nutricion/lista_procedimientos.html', {
        'procedimientos_page': procedimientos_page,
        'search_query': search_query,
    })


@login_required
def api_procedimientos(request):
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            nombre = (data.get('nombre') or '').strip()
            procedimiento = (data.get('procedimiento') or '').strip()
            activo = bool(data.get('activo', True))

            if not nombre:
                return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)
            if not procedimiento:
                return JsonResponse({'success': False, 'error': 'El procedimiento es obligatorio.'}, status=400)

            obj = ProcedimientoPreparacion.objects.create(
                nombre=nombre,
                procedimiento=procedimiento,
                activo=activo,
            )
            RegistroActividad.registrar(
                request, 'nutricion', 'crear_procedimiento_preparacion',
                f"ID: {obj.pk} | {obj.nombre}"
            )
            return JsonResponse({'success': True, 'id': obj.pk})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


@login_required
@require_http_methods(['PUT', 'DELETE'])
def api_procedimiento_detail(request, pk):
    import json
    obj = get_object_or_404(ProcedimientoPreparacion, pk=pk)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            nombre = (data.get('nombre') or '').strip()
            procedimiento = (data.get('procedimiento') or '').strip()

            if not nombre:
                return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)
            if not procedimiento:
                return JsonResponse({'success': False, 'error': 'El procedimiento es obligatorio.'}, status=400)

            obj.nombre = nombre
            obj.procedimiento = procedimiento
            obj.activo = bool(data.get('activo', obj.activo))
            obj.save()
            RegistroActividad.registrar(
                request, 'nutricion', 'editar_procedimiento_preparacion',
                f"ID: {obj.pk} | {obj.nombre}"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # DELETE
    try:
        nombre = obj.nombre
        obj.delete()
        RegistroActividad.registrar(
            request, 'nutricion', 'eliminar_procedimiento_preparacion',
            f"ID: {pk} | {nombre}"
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def api_procedimiento_get(request, pk):
    obj = get_object_or_404(ProcedimientoPreparacion, pk=pk)
    return JsonResponse({
        'id': obj.pk,
        'nombre': obj.nombre,
        'procedimiento': obj.procedimiento,
        'activo': obj.activo,
    })
