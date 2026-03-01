import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from principal.models import RegistroActividad
from .models import CertificadoCalidad
from .pdf_generator import generar_certificado_calidad_pdf
from .services import buscar_empleado_por_cedula

logger = logging.getLogger(__name__)


@login_required
def calidad_principal(request):
    return render(request, 'calidad/index.html')


@login_required
def lista_certificados(request):
    return render(request, 'calidad/certificados.html')


# ── APIs ──────────────────────────────────────────────────────────────────────

@login_required
def api_buscar_empleado(request):
    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return JsonResponse({'error': 'Ingresa una cédula.'}, status=400)

    try:
        empleado = buscar_empleado_por_cedula(cedula)
    except Exception as e:
        logger.error(f"Error consultando BD empleados (cédula={cedula}): {e}")
        return JsonResponse(
            {'error': 'No se pudo conectar a la base de datos de empleados.'},
            status=500
        )

    if not empleado:
        return JsonResponse({'error': 'Empleado no encontrado.'}, status=404)

    return JsonResponse({'empleado': empleado})


@login_required
def api_certificados_list(request):
    qs = (
        CertificadoCalidad.objects
        .select_related('creado_por')
        .values(
            'id', 'numero_certificado', 'cedula', 'nombre_completo',
            'cargo', 'tipo_empleado', 'fecha_emision',
            'creado_por__username',
        )
        .order_by('-fecha_emision', '-id')[:100]
    )
    data = []
    for c in qs:
        data.append({
            'id': c['id'],
            'numero_certificado': c['numero_certificado'],
            'cedula': c['cedula'],
            'nombre_completo': c['nombre_completo'],
            'cargo': c['cargo'],
            'tipo_empleado': c['tipo_empleado'],
            'fecha_emision': c['fecha_emision'].strftime('%d/%m/%Y'),
            'creado_por': c['creado_por__username'] or '—',
        })
    return JsonResponse({'certificados': data})


@login_required
@csrf_exempt
def generar_certificado(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    cedula = data.get('cedula', '').strip()
    if not cedula:
        return JsonResponse({'error': 'Cédula requerida.'}, status=400)

    try:
        empleado = buscar_empleado_por_cedula(cedula)
    except Exception as e:
        logger.error(f"Error buscando empleado {cedula}: {e}")
        return JsonResponse(
            {'error': 'Error al consultar datos del empleado.'},
            status=500
        )

    if not empleado:
        return JsonResponse(
            {'error': 'Empleado no encontrado en la base de datos.'},
            status=404
        )

    cert = CertificadoCalidad.objects.create(
        cedula=empleado['cedula'],
        nombre_completo=empleado.get('nombre_completo') or '',
        cargo=empleado.get('cargo') or '',
        programa_empresa=empleado.get('programa_empresa') or '',
        eps=empleado.get('eps') or '',
        tipo_empleado=empleado['tipo_empleado'],
        observaciones=data.get('observaciones', '').strip(),
        creado_por=request.user,
    )

    RegistroActividad.registrar(
        request, 'calidad', 'generar_certificado',
        f"Certificado {cert.numero_certificado} — {cert.nombre_completo} (C.C. {cert.cedula})"
    )

    return JsonResponse({
        'success': True,
        'pk': cert.pk,
        'numero': cert.numero_certificado,
        'url_descargar': f'/calidad/certificados/{cert.pk}/descargar/',
    })


@login_required
def descargar_certificado(request, pk):
    try:
        cert = CertificadoCalidad.objects.get(pk=pk)
    except CertificadoCalidad.DoesNotExist:
        return HttpResponse('Certificado no encontrado.', status=404)

    pdf_buffer = generar_certificado_calidad_pdf(cert)
    nombre = f"Certificado_{cert.numero_certificado}_{cert.cedula}.pdf"
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response
