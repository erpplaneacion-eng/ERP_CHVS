import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import services

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


@login_required
@require_POST
def api_nia_chat(request):
    try:
        data = json.loads(request.body)
        mensaje = data.get('mensaje', '').strip()
        if not mensaje:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        resultado = services.procesar_mensaje_nia(request, mensaje)
        return JsonResponse(resultado)
    except Exception as e:
        logger.exception(f"NIA chat error: {e}")
        return JsonResponse({'mensaje': 'Error interno. Intenta de nuevo.', 'tipo': 'error'})


@login_required
@require_POST
def api_nia_reset(request):
    request.session.pop('nia_chat_estado', None)
    return JsonResponse({'ok': True})
