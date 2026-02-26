from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from planeacion.models import Programa
from principal.models import RegistroActividad

from ..forms import FirmaNutricionalContratoForm
from ..models import FirmaNutricionalContrato


@login_required
def firmas_contrato(request):
    programas = Programa.objects.filter(estado='activo').order_by('programa')
    programa_id = request.GET.get('programa') or request.POST.get('programa_id')

    programa_obj = None
    firma_obj = None
    form = None

    if programa_id:
        programa_obj = get_object_or_404(Programa, id=programa_id)
        firma_obj, _ = FirmaNutricionalContrato.objects.get_or_create(
            programa=programa_obj,
            defaults={
                'elabora_nombre': '',
                'elabora_matricula': '',
                'aprueba_nombre': '',
                'aprueba_matricula': '',
            }
        )

        if request.method == 'POST':
            form = FirmaNutricionalContratoForm(request.POST, request.FILES, instance=firma_obj)
            if form.is_valid():
                firma = form.save(commit=False)
                firma.programa = programa_obj
                firma.usuario_modificacion = request.user.username if request.user.is_authenticated else None
                firma.save()
                RegistroActividad.registrar(
                    request, 'nutricion', 'guardar_firmas',
                    f"Programa: {programa_obj.programa} (ID: {programa_obj.id})"
                )
                messages.success(request, "Firmas nutricionales actualizadas correctamente.")
                return redirect(f"{request.path}?programa={programa_obj.id}")
            messages.error(request, "No fue posible guardar. Revisa los campos obligatorios.")
        else:
            form = FirmaNutricionalContratoForm(instance=firma_obj)

    context = {
        'programas': programas,
        'programa_obj': programa_obj,
        'firma_obj': firma_obj,
        'form': form,
    }
    return render(request, 'nutricion/firmas_contrato.html', context)

