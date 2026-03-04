from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from principal.models import RegistroActividad

from ..forms import MinutaPatronMetaForm
from ..models import MinutaPatronMeta


def _resumen_errores_form(form) -> str:
    errores = []
    for campo, mensajes in form.errors.items():
        if campo == '__all__':
            etiqueta = 'Validación general'
        else:
            etiqueta = form.fields.get(campo).label if campo in form.fields else campo
        for msg in mensajes:
            errores.append(f"{etiqueta}: {msg}")
    return " | ".join(errores)


def _errores_form_por_campo(form) -> dict:
    data = {}
    for campo, mensajes in form.errors.items():
        if campo == '__all__':
            data[campo] = [str(m) for m in mensajes]
            continue
        etiqueta = form.fields.get(campo).label if campo in form.fields else campo
        data[campo] = [f"{etiqueta}: {str(m)}" for m in mensajes]
    return data


@login_required
def lista_minuta_patron_rangos(request):
    if request.method == 'POST':
        form = MinutaPatronMetaForm(request.POST)
        if form.is_valid():
            rango = form.save()
            mensaje_ok = 'Registro de minuta patrón creado correctamente.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': mensaje_ok})
            messages.success(request, mensaje_ok)
            RegistroActividad.registrar(
                request,
                'nutricion',
                'crear_minuta_patron_rango',
                f"ID: {rango.pk} | Modalidad: {rango.id_modalidad_id} | Grado: {rango.id_grado_escolar_uapa_id}"
            )
            return redirect('nutricion:lista_minuta_patron_rangos')

        detalle = _resumen_errores_form(form)
        base = 'No se pudo guardar el registro.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {
                    'success': False,
                    'message': f'{base} {detalle}' if detalle else base,
                    'errors': _errores_form_por_campo(form),
                },
                status=400
            )
        messages.error(request, f'{base} {detalle}' if detalle else base)
    else:
        form = MinutaPatronMetaForm()

    search_query = request.GET.get('q', '').strip()
    rangos_qs = MinutaPatronMeta.objects.select_related(
        'id_modalidad',
        'id_grado_escolar_uapa',
        'id_componente',
        'id_grupo_alimentos'
    ).order_by(
        'id_modalidad__modalidad',
        'id_grado_escolar_uapa__nivel_escolar_uapa',
        'id_componente__componente',
        'id_grupo_alimentos__grupo_alimentos',
    )

    if search_query:
        rangos_qs = rangos_qs.filter(
            Q(id_modalidad__modalidad__icontains=search_query) |
            Q(id_modalidad__id_modalidades__icontains=search_query) |
            Q(id_grado_escolar_uapa__nivel_escolar_uapa__icontains=search_query) |
            Q(id_grado_escolar_uapa__id_grado_escolar_uapa__icontains=search_query) |
            Q(id_componente__componente__icontains=search_query) |
            Q(id_componente__id_componente__icontains=search_query) |
            Q(id_grupo_alimentos__grupo_alimentos__icontains=search_query) |
            Q(id_grupo_alimentos__id_grupo_alimentos__icontains=search_query)
        )

    paginator = Paginator(rangos_qs, 20)
    page_number = request.GET.get('page')
    rangos_page = paginator.get_page(page_number)

    context = {
        'rangos_page': rangos_page,
        'search_query': search_query,
        'form': form,
    }
    return render(request, 'nutricion/lista_minuta_patron_rangos.html', context)


@login_required
def editar_minuta_patron_rango(request, pk):
    rango = get_object_or_404(MinutaPatronMeta, pk=pk)

    if request.method == 'POST':
        form = MinutaPatronMetaForm(request.POST, instance=rango)
        if form.is_valid():
            form.save()
            mensaje_ok = 'Registro de minuta patrón actualizado correctamente.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': mensaje_ok})
            messages.success(request, mensaje_ok)
            RegistroActividad.registrar(
                request,
                'nutricion',
                'editar_minuta_patron_rango',
                f"ID: {rango.pk} | Modalidad: {rango.id_modalidad_id} | Grado: {rango.id_grado_escolar_uapa_id}"
            )
            return redirect('nutricion:lista_minuta_patron_rangos')

        detalle = _resumen_errores_form(form)
        base = 'No se pudo actualizar el registro.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {
                    'success': False,
                    'message': f'{base} {detalle}' if detalle else base,
                    'errors': _errores_form_por_campo(form),
                },
                status=400
            )
        messages.error(request, f'{base} {detalle}' if detalle else base)

    return redirect('nutricion:lista_minuta_patron_rangos')


@login_required
@require_http_methods(["DELETE"])
def eliminar_minuta_patron_rango(request, pk):
    try:
        rango = get_object_or_404(MinutaPatronMeta, pk=pk)
        descripcion = (
            f"{rango.id_modalidad.modalidad} - "
            f"{rango.id_grado_escolar_uapa.nivel_escolar_uapa} - "
            f"{rango.id_componente.componente}"
        )
        rango.delete()
        RegistroActividad.registrar(
            request,
            'nutricion',
            'eliminar_minuta_patron_rango',
            f"ID: {pk} | {descripcion}"
        )
        return JsonResponse({'success': True, 'message': 'Registro eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})
