import json

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Case, Count, IntegerField, Value, When
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from principal.models import ModalidadesDeConsumo
from planeacion.models import Programa, ProgramaModalidades

from ..models import TablaMenus


@login_required
def api_programas_por_municipio(request):
    """API para obtener programas activos de un municipio"""
    municipio_id = request.GET.get('municipio_id')

    if not municipio_id:
        return JsonResponse({'programas': []})

    try:
        programas = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).values('id', 'programa', 'contrato', 'fecha_inicial', 'fecha_final')

        return JsonResponse({'programas': list(programas)})

    except Exception as e:
        return JsonResponse({'programas': [], 'error': str(e)})


@login_required
def api_modalidades_por_programa(request):
    """API para obtener modalidades configuradas por programa/municipio"""
    programa_id = request.GET.get('programa_id')

    if not programa_id:
        return JsonResponse({'modalidades': []})

    try:
        programa = Programa.objects.get(id=programa_id)

        modalidades_configuradas = ProgramaModalidades.objects.filter(
            programa=programa
        ).select_related('modalidad').values(
            'modalidad__id_modalidades',
            'modalidad__modalidad'
        ).order_by('modalidad__modalidad')

        if not modalidades_configuradas.exists():
            modalidades = ModalidadesDeConsumo.objects.all().values(
                'id_modalidades', 'modalidad'
            ).order_by('modalidad')
            modalidades_list = list(modalidades)
        else:
            modalidades_list = [
                {
                    'id_modalidades': m['modalidad__id_modalidades'],
                    'modalidad': m['modalidad__modalidad']
                }
                for m in modalidades_configuradas
            ]

        return JsonResponse({
            'modalidades': modalidades_list,
            'programa': {
                'id': programa.id,
                'nombre': programa.programa,
                'contrato': programa.contrato
            }
        })
    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)


@login_required
@csrf_exempt
def api_generar_menus_automaticos(request):
    """API para generar automáticamente los 20 menús de una modalidad"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')

        if not programa_id or not modalidad_id:
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        menus_existentes = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad
        ).count()

        if menus_existentes > 0:
            return JsonResponse({
                'error': f'Ya existen {menus_existentes} menús para esta modalidad',
                'menus_existentes': menus_existentes
            }, status=400)

        menus_creados = []
        with transaction.atomic():
            for i in range(1, 21):
                menu = TablaMenus.objects.create(
                    menu=str(i),
                    id_modalidad=modalidad,
                    id_contrato=programa
                )
                menus_creados.append({
                    'id': menu.id_menu,
                    'nombre': menu.menu,
                    'modalidad': modalidad.modalidad
                })

        return JsonResponse({
            'success': True,
            'menus_creados': len(menus_creados),
            'menus': menus_creados
        })

    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)
    except ModalidadesDeConsumo.DoesNotExist:
        return JsonResponse({'error': 'Modalidad no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def api_crear_menu_especial(request):
    """API para crear un menú especial con nombre personalizado"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')
        nombre_menu = data.get('nombre_menu', '').strip()

        if not programa_id or not modalidad_id or not nombre_menu:
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        menu_existente = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad,
            menu=nombre_menu
        ).exists()

        if menu_existente:
            return JsonResponse({
                'error': f'Ya existe un menú con el nombre "{nombre_menu}"'
            }, status=400)

        menu = TablaMenus.objects.create(
            menu=nombre_menu,
            id_modalidad=modalidad,
            id_contrato=programa
        )

        return JsonResponse({
            'success': True,
            'menu': {
                'id': menu.id_menu,
                'nombre': menu.menu,
                'modalidad': modalidad.modalidad
            }
        })

    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)
    except ModalidadesDeConsumo.DoesNotExist:
        return JsonResponse({'error': 'Modalidad no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def api_menus(request):
    """API para manejar menús via AJAX"""
    if request.method == 'GET':
        programa_id = request.GET.get('programa_id')

        menus_query = TablaMenus.objects.select_related('id_modalidad', 'id_contrato')
        if programa_id:
            menus_query = menus_query.filter(id_contrato_id=programa_id)

        # Ordenar numéricamente: convertir campo 'menu' (texto) a entero
        # Para menús especiales (no numéricos), asignar un valor alto (9999)
        menus = menus_query.annotate(
            menu_numerico=Case(
                # Si el campo puede convertirse a entero, usar ese valor
                When(menu__regex=r'^\d+$', then=Cast('menu', IntegerField())),
                # Si no, asignar 9999 para que aparezcan al final
                default=Value(9999),
                output_field=IntegerField()
            )
        ).values(
            'id_menu', 'menu', 'id_modalidad__id_modalidades', 'id_modalidad__modalidad',
            'id_contrato__id', 'id_contrato__programa', 'fecha_creacion'
        ).order_by('id_modalidad__id_modalidades', 'menu_numerico')

        return JsonResponse({'menus': list(menus)})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu = TablaMenus.objects.create(
                menu=data['menu'],
                id_modalidad_id=data['id_modalidad'],
                id_contrato_id=data['id_contrato']
            )

            return JsonResponse({
                'success': True,
                'menu': {
                    'id_menu': menu.id_menu,
                    'menu': menu.menu,
                    'modalidad': menu.id_modalidad.modalidad,
                    'programa': menu.id_contrato.programa
                }
            })

        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': f'Error de integridad: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
@csrf_exempt
def api_menu_detail(request, id_menu):
    """API para manejar un menú específico"""
    menu = get_object_or_404(TablaMenus, id_menu=id_menu)

    if request.method == 'GET':
        return JsonResponse({
            'id_menu': menu.id_menu,
            'menu': menu.menu,
            'id_modalidad': menu.id_modalidad.id_modalidades,
            'id_contrato': menu.id_contrato.id
        })

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            if 'menu' in data:
                menu.menu = data['menu']
            if 'id_modalidad' in data:
                menu.id_modalidad_id = data['id_modalidad']
            if 'id_contrato' in data:
                menu.id_contrato_id = data['id_contrato']
            menu.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    if request.method == 'DELETE':
        try:
            menu.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def api_programas_con_modalidad(request):
    """
    GET /nutricion/api/programas-con-modalidad/?modalidad_id=X&programa_excluir=Y

    Devuelve todos los programas que tienen al menos 1 menú configurado para
    la modalidad indicada, ordenados por municipio → ID desc.
    El programa actual (programa_excluir) se omite del resultado.
    """
    modalidad_id = request.GET.get('modalidad_id')
    programa_excluir = request.GET.get('programa_excluir')

    if not modalidad_id:
        return JsonResponse({'programas': []})

    try:
        qs = TablaMenus.objects.filter(
            id_modalidad_id=modalidad_id
        ).values(
            'id_contrato_id',
            'id_contrato__programa',
            'id_contrato__contrato',
            'id_contrato__municipio__nombre_municipio',
        ).annotate(
            cantidad_menus=Count('id_menu')
        ).filter(
            cantidad_menus__gt=0
        ).order_by(
            'id_contrato__municipio__nombre_municipio',
            '-id_contrato_id'
        )

        if programa_excluir:
            qs = qs.exclude(id_contrato_id=programa_excluir)

        programas = [
            {
                'id': p['id_contrato_id'],
                'programa': p['id_contrato__programa'],
                'contrato': p['id_contrato__contrato'],
                'municipio_nombre': p['id_contrato__municipio__nombre_municipio'],
                'cantidad_menus': p['cantidad_menus'],
            }
            for p in qs
        ]

        return JsonResponse({'programas': programas})

    except Exception as e:
        return JsonResponse({'programas': [], 'error': str(e)})


@login_required
@csrf_exempt
def api_copiar_modalidad(request):
    """
    POST /nutricion/api/copiar-modalidad/
    Body: {programa_origen_id, programa_destino_id, modalidad_id}

    Copia la jerarquía completa de menús de una modalidad entre programas.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_origen_id = data.get('programa_origen_id')
        programa_destino_id = data.get('programa_destino_id')
        modalidad_id = data.get('modalidad_id')

        if not all([programa_origen_id, programa_destino_id, modalidad_id]):
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)

        from ..services.menu_service import MenuService
        menus_copiados = MenuService.copiar_modalidad_completa(
            programa_origen_id=int(programa_origen_id),
            programa_destino_id=int(programa_destino_id),
            modalidad_id=str(modalidad_id)
        )

        return JsonResponse({
            'success': True,
            'menus_copiados': menus_copiados
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)
