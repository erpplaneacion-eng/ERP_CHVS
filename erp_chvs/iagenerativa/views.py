from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .agent import generar_menu_con_ingredientes
from nutricion.models import TablaMenus, ModalidadesDeConsumo
from planeacion.models import Programa

def index(request):
    """Vista para renderizar la página principal de la app iagenerativa."""
    modalidades = ModalidadesDeConsumo.objects.all()
    programas = Programa.objects.all()
    context = {
        'modalidades': modalidades,
        'programas': programas
    }
    return render(request, 'iagenerativa/index.html', context)

@csrf_exempt
def generar_menu(request):
    """API endpoint para generar un nuevo menú."""
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre_menu = data.get('nombre_menu')
        id_modalidad = data.get('id_modalidad')
        id_contrato = data.get('id_contrato')

        if not all([nombre_menu, id_modalidad, id_contrato]):
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        try:
            # Llamar al agente para generar el menú
            respuesta_generada = generar_menu_con_ingredientes(nombre_menu, id_modalidad, id_contrato)

            # Aquí se procesaría la respuesta para crear los objetos en la BD
            # Por ahora, solo retornamos la respuesta del modelo

            return JsonResponse({'success': True, 'respuesta': respuesta_generada})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)