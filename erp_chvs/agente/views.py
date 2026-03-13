import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from nutricion.models import (
    TablaMenus, TablaAlimentos2018Icbf, ComponentesAlimentos
)
from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo

from .models import GeneracionIA, BorradorPreparacionIA, BorradorIngredienteIA
from .services.context_builder import obtener_contexto_modalidad
from .services.llm_service import generar_borrador
from .services.validador import validar_preparaciones
from .services.importador import importar_borrador


@login_required
def index(request):
    modalidades = ModalidadesDeConsumo.objects.order_by('modalidad')
    return render(request, 'agente/index.html', {'modalidades': modalidades})


@login_required
def borrador_view(request, generacion_id):
    generacion = get_object_or_404(
        GeneracionIA.objects.select_related(
            'id_modalidad', 'id_menu__id_modalidad', 'id_menu__id_contrato', 'usuario_solicitante'
        ),
        id=generacion_id
    )
    preparaciones = generacion.preparaciones.prefetch_related(
        'ingredientes__alimento_icbf',
        'componente_sugerido'
    ).all()

    programas = Programa.objects.filter(estado='activo').order_by('programa')

    return render(request, 'agente/borrador.html', {
        'generacion': generacion,
        'preparaciones': preparaciones,
        'programas': programas,
    })


@login_required
def api_programas(request):
    programas = Programa.objects.filter(estado='activo').order_by('programa').values('id', 'programa', 'contrato')
    return JsonResponse({'programas': list(programas)})


@login_required
def api_menus_por_programa_modalidad(request):
    programa_id = request.GET.get('programa_id')
    modalidad_id = request.GET.get('modalidad_id')
    if not programa_id or not modalidad_id:
        return JsonResponse({'menus': []})

    menus = TablaMenus.objects.filter(
        id_contrato_id=programa_id,
        id_modalidad_id=modalidad_id,
    ).filter(
        preparaciones__isnull=True,  # solo menús sin preparaciones
    ).order_by('menu').values('id_menu', 'menu')

    return JsonResponse({'menus': list(menus)})


@login_required
@require_POST
def api_generar(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    modalidad_id = data.get('modalidad_id')
    if not modalidad_id:
        return JsonResponse({'ok': False, 'error': 'Falta modalidad_id'}, status=400)

    ocasion_especial = data.get('ocasion_especial', '').strip()[:100]

    modalidad = get_object_or_404(ModalidadesDeConsumo, id_modalidades=modalidad_id)

    generacion = GeneracionIA.objects.create(
        id_modalidad=modalidad,
        ocasion_especial=ocasion_especial,
        usuario_solicitante=request.user,
        estado=GeneracionIA.ESTADO_PROCESANDO,
    )

    try:
        contexto = obtener_contexto_modalidad(modalidad_id)
        resultado_llm = generar_borrador(contexto, ocasion_especial)

        if not resultado_llm['ok']:
            generacion.estado = GeneracionIA.ESTADO_ERROR
            generacion.errores_validacion = [resultado_llm.get('error', 'Error desconocido')]
            generacion.save()
            return JsonResponse({'ok': False, 'error': resultado_llm.get('error')})

        preparaciones_validadas = validar_preparaciones(resultado_llm['preparaciones'])

        generacion.prompt_final = resultado_llm['prompt']
        generacion.respuesta_cruda = resultado_llm['respuesta_cruda']
        generacion.estado = GeneracionIA.ESTADO_PENDIENTE
        generacion.save()

        for prep in preparaciones_validadas:
            componente_obj = None
            if prep['id_componente']:
                try:
                    componente_obj = ComponentesAlimentos.objects.get(
                        id_componente=prep['id_componente']
                    )
                except ComponentesAlimentos.DoesNotExist:
                    pass

            prep_borrador = BorradorPreparacionIA.objects.create(
                generacion=generacion,
                nombre_preparacion=prep['nombre'],
                componente_sugerido=componente_obj,
                estado_validacion=prep['estado_validacion'],
                observaciones=prep['observaciones'],
                procedimiento=prep.get('procedimiento', ''),
            )

            for ing in prep['ingredientes']:
                alimento = None
                if ing['estado_validacion'] == 'valido':
                    try:
                        alimento = TablaAlimentos2018Icbf.objects.get(
                            codigo=ing['codigo_icbf']
                        )
                    except TablaAlimentos2018Icbf.DoesNotExist:
                        pass

                BorradorIngredienteIA.objects.create(
                    borrador_preparacion=prep_borrador,
                    codigo_icbf_sugerido=ing.get('codigo_icbf', ''),
                    nombre_sugerido=ing.get('nombre', ''),
                    alimento_icbf=alimento,
                    estado_validacion=ing['estado_validacion'],
                    observaciones=ing.get('observaciones', ''),
                )

        return JsonResponse({'ok': True, 'generacion_id': generacion.id})

    except Exception as e:
        generacion.estado = GeneracionIA.ESTADO_ERROR
        generacion.errores_validacion = [str(e)]
        generacion.save()
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def api_corregir_ingrediente(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    ingrediente_id = data.get('ingrediente_id')
    codigo_icbf_nuevo = data.get('codigo_icbf', '').strip()

    ing = get_object_or_404(BorradorIngredienteIA, id=ingrediente_id)

    try:
        alimento = TablaAlimentos2018Icbf.objects.get(codigo=codigo_icbf_nuevo)
        ing.alimento_icbf = alimento
        ing.estado_validacion = BorradorIngredienteIA.VALIDO
        ing.observaciones = ''
        ing.save()

        padre = ing.borrador_preparacion
        tiene_invalido = padre.ingredientes.filter(
            estado_validacion=BorradorIngredienteIA.NO_ENCONTRADO
        ).exists()
        if not tiene_invalido:
            padre.estado_validacion = BorradorPreparacionIA.VALIDA
            padre.observaciones = ''
            padre.save()

        return JsonResponse({'ok': True, 'nombre': alimento.nombre_del_alimento})
    except TablaAlimentos2018Icbf.DoesNotExist:
        return JsonResponse(
            {'ok': False, 'error': f"Código '{codigo_icbf_nuevo}' no existe en el catálogo ICBF."}
        )


@login_required
@require_POST
def api_aprobar(request, generacion_id):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    menu_id = data.get('menu_id')
    if not menu_id:
        return JsonResponse({'ok': False, 'error': 'Debes seleccionar un menú destino.'}, status=400)

    resultado = importar_borrador(generacion_id, menu_id, request)
    return JsonResponse(resultado)


@login_required
@require_POST
def api_eliminar_ingrediente(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    ingrediente_id = data.get('ingrediente_id')
    ing = get_object_or_404(BorradorIngredienteIA, id=ingrediente_id)

    # Verificar que el borrador aún esté pendiente de revisión
    generacion = ing.borrador_preparacion.generacion
    if generacion.estado != GeneracionIA.ESTADO_PENDIENTE:
        return JsonResponse({'ok': False, 'error': 'El borrador ya no está en estado pendiente.'}, status=400)

    ing.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_descartar(request, generacion_id):
    generacion = get_object_or_404(GeneracionIA, id=generacion_id)
    generacion.estado = GeneracionIA.ESTADO_DESCARTADO
    generacion.save(update_fields=['estado'])
    return JsonResponse({'ok': True})


@login_required
def api_buscar_alimento(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'resultados': []})

    alimentos = TablaAlimentos2018Icbf.objects.filter(
        nombre_del_alimento__icontains=q
    ).values('codigo', 'nombre_del_alimento')[:20]

    return JsonResponse({'resultados': list(alimentos)})
