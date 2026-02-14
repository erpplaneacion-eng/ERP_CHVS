from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError, transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import json

from .excel_generator import (
    generate_menu_excel,
    generate_menu_excel_real_data,
    generate_advanced_nutritional_excel,
    generate_excel_from_service
)
from .models import (
    TablaAlimentos2018Icbf,
    TablaMenus,
    TablaPreparaciones,
    TablaPreparacionIngredientes,
    TablaIngredientesSiesa,
    MinutaPatronMeta,
    TablaRequerimientosNutricionales,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    RequerimientoSemanal,
    ComponentesAlimentos
)
from .forms import AlimentoForm
from principal.models import ModalidadesDeConsumo, TablaGradosEscolaresUapa
from planeacion.models import Programa
from .services import AnalisisNutricionalService, MenuService
from .services.calculo_service import CalculoService


@login_required
@csrf_exempt
def api_generar_menu_ia(request):
    """
    API para generar un menÃº usando Inteligencia Artificial (Gemini).
    Genera automÃ¡ticamente el menÃº con pesos especÃ­ficos para TODOS los niveles educativos.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')

        if not all([programa_id, modalidad_id]):
            return JsonResponse({'error': 'Faltan parÃ¡metros (programa_id, modalidad_id)'}, status=400)

        # Delegar al servicio - None genera para TODOS los niveles educativos
        menu = MenuService.generar_menu_con_ia(
            id_programa=programa_id,
            id_modalidad=modalidad_id,
            niveles_educativos=None  # None = generar para todos los niveles (5 niveles)
        )

        if not menu:
            return JsonResponse({'error': 'La IA no pudo generar una propuesta vÃ¡lida. Intente nuevamente.'}, status=500)

        return JsonResponse({
            'success': True,
            'menu': {
                'id': menu.id_menu,
                'nombre': menu.menu,
                'modalidad': menu.id_modalidad.modalidad
            },
            'mensaje': 'MenÃº generado exitosamente con anÃ¡lisis nutricional para todos los niveles educativos'
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)


# =================== VISTAS GENERALES ===================

@login_required
def nutricion_index(request):
    """Vista principal del mÃ³dulo de nutriciÃ³n"""
    return render(request, 'nutricion/index.html')


# =================== ALIMENTOS ICBF ===================

@login_required
def lista_alimentos(request):
    """Vista para listar alimentos ICBF"""
    if request.method == 'POST':
        form = AlimentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nutricion:lista_alimentos')
    else:
        form = AlimentoForm()

    search_query = request.GET.get('q', '')
    alimentos_list = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')

    if search_query:
        alimentos_list = alimentos_list.filter(
            Q(nombre_del_alimento__icontains=search_query) |
            Q(codigo__icontains=search_query)
        )

    paginator = Paginator(alimentos_list, 20)
    page_number = request.GET.get('page')
    alimentos_page = paginator.get_page(page_number)

    context = {
        'alimentos_page': alimentos_page,
        'search_query': search_query,
        'form': form,
    }

    return render(request, 'nutricion/lista_alimentos.html', context)


@login_required
def editar_alimento(request, codigo):
    """Vista para editar un alimento"""
    from django.contrib import messages

    alimento_a_editar = get_object_or_404(TablaAlimentos2018Icbf, pk=codigo)

    if request.method == 'POST':
        form = AlimentoForm(request.POST, instance=alimento_a_editar)
        if form.is_valid():
            form.save()
            messages.success(request, f'Alimento "{alimento_a_editar.nombre_del_alimento}" actualizado correctamente.')
            return redirect('nutricion:lista_alimentos')
        else:
            # Si hay errores, mostrarlos en consola del servidor para debugging
            print("âŒ ERROR: Formulario no vÃ¡lido al editar alimento")
            print(f"CÃ³digo: {codigo}")
            print(f"Errores: {form.errors}")
            messages.error(request, f'Error al actualizar el alimento. Por favor, revise los datos ingresados.')
            return redirect('nutricion:lista_alimentos')

    return redirect('nutricion:lista_alimentos')


@login_required
@require_http_methods(["DELETE"])
def eliminar_alimento(request, codigo):
    """Vista para eliminar un alimento"""
    try:
        alimento = get_object_or_404(TablaAlimentos2018Icbf, pk=codigo)
        nombre = alimento.nombre_del_alimento
        alimento.delete()
        return JsonResponse({'success': True, 'message': f'Alimento "{nombre}" eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== MENÃšS ===================

@login_required
def lista_menus(request):
    """Vista para listar y gestionar menÃºs por municipio/programa/modalidad"""
    # Obtener SOLO municipios que tienen programas activos
    from principal.models import PrincipalMunicipio
    municipios = PrincipalMunicipio.objects.filter(
        programa__estado='activo'
    ).distinct().order_by('nombre_municipio')

    # Obtener filtros
    municipio_id = request.GET.get('municipio')
    programa_id = request.GET.get('programa')

    # Contexto inicial
    context = {
        'municipios': municipios,  # Cambio aquÃ­
        'municipio_seleccionado': municipio_id,
        'programa_seleccionado': programa_id,
    }

    # Si hay municipio seleccionado, obtener programas activos
    if municipio_id:
        programas_activos = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).order_by('-fecha_inicial')
        context['programas'] = programas_activos

        # Si hay programa seleccionado, obtener modalidades y menÃºs
        if programa_id:
            try:
                programa = Programa.objects.get(id=programa_id)
                context['programa_obj'] = programa

                # Obtener modalidades del municipio
                # Esto requiere saber quÃ© modalidades estÃ¡n configuradas para ese municipio
                # Por ahora, traemos todas las modalidades
                modalidades = ModalidadesDeConsumo.objects.all().order_by('modalidad')
                context['modalidades'] = modalidades

                # Obtener menÃºs existentes del programa
                menus_existentes = TablaMenus.objects.filter(
                    id_contrato=programa
                ).select_related('id_modalidad').order_by('id_modalidad', 'menu')

                # Agrupar menÃºs por modalidad
                from collections import defaultdict
                menus_por_modalidad = defaultdict(list)
                for menu in menus_existentes:
                    menus_por_modalidad[menu.id_modalidad.id_modalidades].append(menu)

                context['menus_por_modalidad'] = dict(menus_por_modalidad)

            except Programa.DoesNotExist:
                context['error'] = 'Programa no encontrado'

    return render(request, 'nutricion/lista_menus.html', context)


def _resolver_grupo_y_rango(menu, preparacion, ingrediente_icbf):
    """
    Resuelve grupo de alimentos y rango [min, max] para un ingrediente dentro de una preparación.
    Usa MinutaPatronMeta por modalidad + componente + grupo.

    NOTA: Esta función agrega MIN/MAX de TODOS los niveles escolares.
    Para rangos específicos por nivel, usar _resolver_grupo_y_rango_por_nivel()
    """
    grupo = None
    componente_ingrediente = getattr(ingrediente_icbf, 'id_componente', None)
    if componente_ingrediente and componente_ingrediente.id_grupo_alimentos:
        grupo = componente_ingrediente.id_grupo_alimentos
    elif preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos:
        grupo = preparacion.id_componente.id_grupo_alimentos

    if not grupo:
        return {
            'grupo_id': None,
            'grupo_nombre': 'SIN GRUPO',
            'minimo': None,
            'maximo': None
        }

    metas = MinutaPatronMeta.objects.filter(
        id_modalidad=menu.id_modalidad,
        id_grupo_alimentos=grupo
    )
    if preparacion.id_componente:
        metas = metas.filter(id_componente=preparacion.id_componente)

    agregados = metas.aggregate(
        minimo=Min('peso_neto_minimo'),
        maximo=Max('peso_neto_maximo')
    )

    return {
        'grupo_id': grupo.id_grupo_alimentos,
        'grupo_nombre': grupo.grupo_alimentos,
        'minimo': float(agregados['minimo']) if agregados['minimo'] is not None else None,
        'maximo': float(agregados['maximo']) if agregados['maximo'] is not None else None
    }


def _resolver_grupo_y_rango_por_nivel(menu, preparacion, ingrediente_icbf, nivel_escolar):
    """
    Resuelve grupo de alimentos y rango [min, max] para un ingrediente
    FILTRADO POR NIVEL ESCOLAR ESPECÍFICO.

    PASO 3: Esta función implementa el filtrado por nivel escolar que faltaba.

    Args:
        menu: Instancia del menú
        preparacion: Instancia de la preparación
        ingrediente_icbf: Instancia del alimento ICBF
        nivel_escolar: Instancia de TablaGradosEscolaresUapa

    Returns:
        Dict con grupo_id, grupo_nombre, minimo, maximo
    """
    grupo = None
    componente_ingrediente = getattr(ingrediente_icbf, 'id_componente', None)
    if componente_ingrediente and componente_ingrediente.id_grupo_alimentos:
        grupo = componente_ingrediente.id_grupo_alimentos
    elif preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos:
        grupo = preparacion.id_componente.id_grupo_alimentos

    if not grupo:
        return {
            'grupo_id': None,
            'grupo_nombre': 'SIN GRUPO',
            'minimo': None,
            'maximo': None
        }

    # ✨ MEJORA: Ahora filtra por nivel escolar específico
    metas = MinutaPatronMeta.objects.filter(
        id_modalidad=menu.id_modalidad,
        id_grado_escolar_uapa=nivel_escolar,  # ← FILTRO POR NIVEL
        id_grupo_alimentos=grupo
    )
    if preparacion.id_componente:
        metas = metas.filter(id_componente=preparacion.id_componente)

    # Como ya está filtrado por nivel, solo necesitamos tomar un registro
    meta = metas.first()

    if meta:
        return {
            'grupo_id': grupo.id_grupo_alimentos,
            'grupo_nombre': grupo.grupo_alimentos,
            'minimo': float(meta.peso_neto_minimo) if meta.peso_neto_minimo is not None else None,
            'maximo': float(meta.peso_neto_maximo) if meta.peso_neto_maximo is not None else None
        }
    else:
        # Si no hay meta para este nivel, retornar sin rangos
        return {
            'grupo_id': grupo.id_grupo_alimentos,
            'grupo_nombre': grupo.grupo_alimentos,
            'minimo': None,
            'maximo': None
        }


@login_required
def vista_preparaciones_editor(request, id_menu):
    """
    Vista integrada para gestionar preparaciones con análisis nutricional por nivel escolar.

    PASO 2: Ahora incluye tabs por nivel escolar con:
    - Pesos específicos por nivel
    - Rangos permitidos (min/max) según MinutaPatronMeta
    - Totales nutricionales en tiempo real
    - Semaforización (verde/amarillo/rojo)
    """
    from .services import AnalisisNutricionalService

    menu = get_object_or_404(
        TablaMenus.objects.select_related('id_modalidad', 'id_contrato'),
        id_menu=id_menu
    )

    # Obtener todos los niveles escolares
    niveles_escolares = TablaGradosEscolaresUapa.objects.all().order_by('id_grado_escolar_uapa')

    # Obtener requerimientos nutricionales para esta modalidad
    requerimientos_por_nivel = {}
    if menu.id_modalidad:
        requerimientos = TablaRequerimientosNutricionales.objects.filter(
            id_modalidad=menu.id_modalidad
        ).select_related('id_nivel_escolar_uapa')

        for req in requerimientos:
            requerimientos_por_nivel[req.id_nivel_escolar_uapa.id_grado_escolar_uapa] = {
                'calorias': float(req.calorias_kcal),
                'proteina': float(req.proteina_g),
                'grasa': float(req.grasa_g),
                'cho': float(req.cho_g),
                'calcio': float(req.calcio_mg),
                'hierro': float(req.hierro_mg),
                'sodio': float(req.sodio_mg)
            }

    # Obtener preparaciones e ingredientes base
    preparaciones = list(
        TablaPreparaciones.objects.filter(id_menu=menu)
        .select_related('id_componente')
        .order_by('preparacion')
    )

    # Construir datos por nivel escolar
    niveles_data = []

    for nivel in niveles_escolares:
        # Obtener o crear análisis para este nivel
        analisis, _ = TablaAnalisisNutricionalMenu.objects.get_or_create(
            id_menu=menu,
            id_nivel_escolar_uapa=nivel
        )

        # Cargar ingredientes configurados para este nivel
        ingredientes_configurados = {}
        ingredientes_nivel = TablaIngredientesPorNivel.objects.filter(
            id_analisis=analisis
        ).select_related('id_preparacion', 'id_ingrediente_siesa')

        for ing_nivel in ingredientes_nivel:
            key = f"{ing_nivel.id_preparacion_id}_{ing_nivel.id_ingrediente_siesa.id_ingrediente_siesa}"
            ingredientes_configurados[key] = {
                'peso_neto': float(ing_nivel.peso_neto),
                'peso_bruto': float(ing_nivel.peso_bruto),
                'calorias': float(ing_nivel.calorias),
                'proteina': float(ing_nivel.proteina),
                'grasa': float(ing_nivel.grasa),
                'cho': float(ing_nivel.cho),
                'calcio': float(ing_nivel.calcio),
                'hierro': float(ing_nivel.hierro),
                'sodio': float(ing_nivel.sodio)
            }

        # Construir filas de ingredientes para este nivel
        filas_nivel = []
        relaciones = TablaPreparacionIngredientes.objects.filter(
            id_preparacion__in=preparaciones
        ).select_related(
            'id_preparacion',
            'id_ingrediente_siesa',
            'id_ingrediente_siesa__id_componente',
            'id_ingrediente_siesa__id_componente__id_grupo_alimentos'
        )

        for rel in relaciones:
            # Resolver rango para este nivel específico
            rango = _resolver_grupo_y_rango_por_nivel(
                menu,
                rel.id_preparacion,
                rel.id_ingrediente_siesa,
                nivel
            )

            # Buscar peso configurado para este nivel
            key = f"{rel.id_preparacion_id}_{rel.id_ingrediente_siesa.codigo}"
            if key in ingredientes_configurados:
                peso_neto = ingredientes_configurados[key]['peso_neto']
                valores_nutricionales = ingredientes_configurados[key]
            else:
                # Usar gramaje base o 100g
                peso_neto = float(rel.gramaje) if rel.gramaje else 100.0
                # Calcular valores nutricionales para este peso
                valores_nutricionales = CalculoService.calcular_valores_nutricionales_alimento(
                    rel.id_ingrediente_siesa,
                    peso_neto
                ) if rel.id_ingrediente_siesa else {}

            filas_nivel.append({
                'id_preparacion': rel.id_preparacion.id_preparacion,
                'preparacion': rel.id_preparacion.preparacion,
                'id_ingrediente': rel.id_ingrediente_siesa.codigo,
                'ingrediente': rel.id_ingrediente_siesa.nombre_del_alimento,
                'codigo_icbf': rel.id_ingrediente_siesa.codigo,
                'grupo': rango['grupo_nombre'],
                'minimo': rango['minimo'],
                'maximo': rango['maximo'],
                'peso_neto': peso_neto,
                'parte_comestible': float(rel.id_ingrediente_siesa.parte_comestible_field or 100),
                **valores_nutricionales
            })

        # Calcular totales para este nivel
        totales = {
            'calorias': sum(f.get('calorias', 0) for f in filas_nivel),
            'proteina': sum(f.get('proteina', 0) for f in filas_nivel),
            'grasa': sum(f.get('grasa', 0) for f in filas_nivel),
            'cho': sum(f.get('cho', 0) for f in filas_nivel),
            'calcio': sum(f.get('calcio', 0) for f in filas_nivel),
            'hierro': sum(f.get('hierro', 0) for f in filas_nivel),
            'sodio': sum(f.get('sodio', 0) for f in filas_nivel),
            'peso_neto': sum(f.get('peso_neto', 0) for f in filas_nivel)
        }

        # Calcular porcentajes y estados
        requerimientos = requerimientos_por_nivel.get(nivel.id_grado_escolar_uapa, {})
        porcentajes = {}
        estados = {}

        for nutriente in ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio']:
            if requerimientos.get(nutriente, 0) > 0:
                porcentaje = (totales[nutriente] / requerimientos[nutriente]) * 100
                porcentajes[nutriente] = round(porcentaje, 1)

                # Clasificar estado (semáforo)
                if porcentaje <= 35:
                    estados[nutriente] = 'optimo'
                elif porcentaje <= 70:
                    estados[nutriente] = 'aceptable'
                else:
                    estados[nutriente] = 'alto'
            else:
                porcentajes[nutriente] = 0
                estados[nutriente] = 'optimo'

        niveles_data.append({
            'nivel': {
                'id': nivel.id_grado_escolar_uapa,
                'nombre': nivel.nivel_escolar_uapa
            },
            'filas': filas_nivel,
            'totales': totales,
            'requerimientos': requerimientos,
            'porcentajes': porcentajes,
            'estados': estados,
            'id_analisis': analisis.id_analisis
        })

    # Catálogo de ingredientes y preparaciones
    ingredientes_catalogo = list(
        TablaAlimentos2018Icbf.objects.values('codigo', 'nombre_del_alimento').order_by('nombre_del_alimento')
    )
    preparaciones_catalogo = [
        {'id_preparacion': p.id_preparacion, 'preparacion': p.preparacion}
        for p in preparaciones
    ]

    context = {
        'menu': menu,
        'niveles_data': niveles_data,
        'niveles_json': json.dumps(niveles_data, default=str),
        'ingredientes_json': json.dumps(ingredientes_catalogo),
        'preparaciones_json': json.dumps(preparaciones_catalogo),
    }
    return render(request, 'nutricion/preparaciones_editor.html', context)


@login_required
def api_rango_ingrediente_preparacion(request, id_menu):
    """Retorna grupo y rango permitido para una combinación preparación + ingrediente."""
    id_preparacion = request.GET.get('id_preparacion')
    id_ingrediente = request.GET.get('id_ingrediente')
    if not id_preparacion or not id_ingrediente:
        return JsonResponse({'success': False, 'error': 'Parámetros requeridos: id_preparacion, id_ingrediente'}, status=400)

    menu = get_object_or_404(TablaMenus, id_menu=id_menu)
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion, id_menu=menu)
    ingrediente = get_object_or_404(TablaAlimentos2018Icbf, codigo=id_ingrediente)

    rango = _resolver_grupo_y_rango(menu, preparacion, ingrediente)
    return JsonResponse({'success': True, **rango})


@login_required
@csrf_exempt
def api_guardar_preparaciones_editor(request, id_menu):
    """Guarda filas del editor de preparaciones validando gramajes por rango."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    menu = get_object_or_404(TablaMenus, id_menu=id_menu)
    try:
        payload = json.loads(request.body)
        filas = payload.get('filas', [])
    except Exception:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    errores = []
    guardadas = 0

    with transaction.atomic():
        for idx, fila in enumerate(filas):
            try:
                id_preparacion = fila.get('id_preparacion')
                id_ingrediente = str(fila.get('id_ingrediente', '')).strip()
                preparacion_nombre = str(fila.get('preparacion_nombre', '')).strip()
                gramaje_raw = fila.get('gramaje')
                if not id_ingrediente:
                    continue
                if id_preparacion:
                    preparacion = TablaPreparaciones.objects.get(id_preparacion=id_preparacion, id_menu=menu)
                else:
                    if not preparacion_nombre:
                        errores.append(f"Fila {idx + 1}: nombre de preparación requerido")
                        continue
                    preparacion, _ = TablaPreparaciones.objects.get_or_create(
                        id_menu=menu,
                        preparacion=preparacion_nombre,
                        defaults={'id_componente': None}
                    )
                ingrediente = TablaAlimentos2018Icbf.objects.get(codigo=id_ingrediente)

                gramaje = None
                if gramaje_raw not in (None, '', 'null'):
                    gramaje = Decimal(str(gramaje_raw))
                    if gramaje < 0:
                        raise InvalidOperation('Gramaje negativo')

                rango = _resolver_grupo_y_rango(menu, preparacion, ingrediente)
                minimo = Decimal(str(rango['minimo'])) if rango['minimo'] is not None else None
                maximo = Decimal(str(rango['maximo'])) if rango['maximo'] is not None else None

                if gramaje is not None and minimo is not None and gramaje < minimo:
                    errores.append(f"Fila {idx + 1}: gramaje {gramaje}g por debajo del mínimo {minimo}g")
                    continue
                if gramaje is not None and maximo is not None and gramaje > maximo:
                    errores.append(f"Fila {idx + 1}: gramaje {gramaje}g por encima del máximo {maximo}g")
                    continue

                rel, _ = TablaPreparacionIngredientes.objects.get_or_create(
                    id_preparacion=preparacion,
                    id_ingrediente_siesa=ingrediente
                )
                rel.gramaje = gramaje
                rel.save(update_fields=['gramaje'])
                guardadas += 1

            except (ValueError, InvalidOperation):
                errores.append(f"Fila {idx + 1}: gramaje inválido")
            except TablaPreparaciones.DoesNotExist:
                errores.append(f"Fila {idx + 1}: preparación no encontrada")
            except TablaAlimentos2018Icbf.DoesNotExist:
                errores.append(f"Fila {idx + 1}: ingrediente no encontrado")

    if errores:
        return JsonResponse({'success': False, 'guardadas': guardadas, 'errores': errores}, status=400)
    return JsonResponse({'success': True, 'guardadas': guardadas})


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

        # Importar el modelo de relaciÃ³n municipio-modalidades
        from principal.models import MunicipioModalidades

        # Obtener modalidades configuradas para el municipio del programa
        modalidades_configuradas = MunicipioModalidades.objects.filter(
            municipio=programa.municipio
        ).select_related('modalidad').values(
            'modalidad__id_modalidades',
            'modalidad__modalidad'
        ).order_by('modalidad__modalidad')

        # Si no hay configuraciÃ³n especÃ­fica, retornar todas las modalidades
        if not modalidades_configuradas.exists():
            modalidades = ModalidadesDeConsumo.objects.all().values(
                'id_modalidades', 'modalidad'
            ).order_by('modalidad')
            modalidades_list = list(modalidades)
        else:
            # Formatear modalidades configuradas
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
    """API para generar automÃ¡ticamente los 20 menÃºs de una modalidad"""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')

        if not programa_id or not modalidad_id:
            return JsonResponse({'error': 'Faltan parÃ¡metros'}, status=400)

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        # Verificar si ya existen menÃºs
        menus_existentes = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad
        ).count()

        if menus_existentes > 0:
            return JsonResponse({
                'error': f'Ya existen {menus_existentes} menÃºs para esta modalidad',
                'menus_existentes': menus_existentes
            }, status=400)

        # Crear los 20 menÃºs automÃ¡ticamente
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
    """API para crear un menÃº especial con nombre personalizado"""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        programa_id = data.get('programa_id')
        modalidad_id = data.get('modalidad_id')
        nombre_menu = data.get('nombre_menu', '').strip()

        if not programa_id or not modalidad_id or not nombre_menu:
            return JsonResponse({'error': 'Faltan parÃ¡metros'}, status=400)

        programa = Programa.objects.get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        # Verificar si ya existe un menÃº con ese nombre
        menu_existente = TablaMenus.objects.filter(
            id_contrato=programa,
            id_modalidad=modalidad,
            menu=nombre_menu
        ).exists()

        if menu_existente:
            return JsonResponse({
                'error': f'Ya existe un menÃº con el nombre "{nombre_menu}"'
            }, status=400)

        # Crear el menÃº especial
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
    """API para manejar menÃºs via AJAX"""
    if request.method == 'GET':
        # Filtrar por programa si se proporciona
        programa_id = request.GET.get('programa_id')

        menus_query = TablaMenus.objects.select_related('id_modalidad', 'id_contrato')

        if programa_id:
            menus_query = menus_query.filter(id_contrato_id=programa_id)

        menus = menus_query.values(
            'id_menu', 'menu', 'id_modalidad__id_modalidades', 'id_modalidad__modalidad',
            'id_contrato__id', 'id_contrato__programa', 'fecha_creacion'
        ).order_by('id_modalidad__id_modalidades', 'menu')

        return JsonResponse({'menus': list(menus)})

    elif request.method == 'POST':
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


@login_required
@csrf_exempt
def api_menu_detail(request, id_menu):
    """API para manejar un menÃº especÃ­fico"""
    menu = get_object_or_404(TablaMenus, id_menu=id_menu)

    if request.method == 'GET':
        return JsonResponse({
            'id_menu': menu.id_menu,
            'menu': menu.menu,
            'id_modalidad': menu.id_modalidad.id_modalidades,
            'id_contrato': menu.id_contrato.id
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            # Actualizar solo los campos que se envÃ­an
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

    elif request.method == 'DELETE':
        try:
            menu.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


# =================== PREPARACIONES ===================

@login_required
def lista_preparaciones(request):
    """Vista para listar preparaciones"""
    preparaciones = TablaPreparaciones.objects.select_related('id_menu').all().order_by('-fecha_creacion')
    paginator = Paginator(preparaciones, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    menus = TablaMenus.objects.all().order_by('menu')

    return render(request, 'nutricion/lista_preparaciones.html', {
        'preparaciones': page_obj,
        'total_preparaciones': preparaciones.count(),
        'menus': menus
    })


@login_required
@csrf_exempt
def api_preparaciones(request):
    """API para manejar preparaciones via AJAX"""
    if request.method == 'GET':
        # Filtrar por menÃº si se proporciona
        menu_id = request.GET.get('menu_id')

        preparaciones_query = TablaPreparaciones.objects.select_related('id_menu')

        if menu_id:
            preparaciones_query = preparaciones_query.filter(id_menu_id=menu_id)

        preparaciones = preparaciones_query.values(
            'id_preparacion', 'preparacion', 'id_menu__id_menu', 'id_menu__menu', 'fecha_creacion'
        ).order_by('preparacion')

        return JsonResponse({'preparaciones': list(preparaciones)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Obtener el componente si se proporciona
            id_componente = data.get('id_componente')

            preparacion = TablaPreparaciones.objects.create(
                preparacion=data['preparacion'],
                id_menu_id=data['id_menu'],
                id_componente_id=id_componente if id_componente else None
            )

            return JsonResponse({
                'success': True,
                'preparacion': {
                    'id_preparacion': preparacion.id_preparacion,
                    'preparacion': preparacion.preparacion,
                    'menu': preparacion.id_menu.menu,
                    'componente': preparacion.id_componente.componente if preparacion.id_componente else None
                }
            })

        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': f'Error de integridad: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_preparacion_detail(request, id_preparacion):
    """API para manejar una preparaciÃ³n especÃ­fica"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)

    if request.method == 'GET':
        return JsonResponse({
            'id_preparacion': preparacion.id_preparacion,
            'preparacion': preparacion.preparacion,
            'id_menu': preparacion.id_menu.id_menu
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            preparacion.preparacion = data['preparacion']
            preparacion.id_menu_id = data['id_menu']
            preparacion.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            preparacion.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})


@login_required
@csrf_exempt
@transaction.atomic
def api_copiar_preparacion(request):
    """API para copiar una preparaciÃ³n completa a un nuevo menÃº."""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        source_preparacion_id = data.get('source_preparacion_id')
        target_menu_id = data.get('target_menu_id')

        if not source_preparacion_id or not target_menu_id:
            return JsonResponse({'error': 'Faltan parÃ¡metros requeridos.'}, status=400)

        # Obtener los objetos de la base de datos
        source_preparacion = get_object_or_404(TablaPreparaciones, pk=source_preparacion_id)
        target_menu = get_object_or_404(TablaMenus, pk=target_menu_id)

        # Crear la nueva preparaciÃ³n (la copia)
        new_preparacion = TablaPreparaciones.objects.create(
            preparacion=source_preparacion.preparacion, # Copia el nombre
            id_menu=target_menu, # Asigna al nuevo menÃº
            id_componente=source_preparacion.id_componente # Copia el componente
        )

        # Obtener los ingredientes de la preparaciÃ³n original
        source_ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=source_preparacion
        )

        # Crear las nuevas relaciones de ingredientes en lote
        nuevos_ingredientes = []
        for ing in source_ingredientes:
            nuevos_ingredientes.append(
                TablaPreparacionIngredientes(
                    id_preparacion=new_preparacion,
                    id_ingrediente_siesa=ing.id_ingrediente_siesa
                )
            )
        
        if nuevos_ingredientes:
            TablaPreparacionIngredientes.objects.bulk_create(nuevos_ingredientes)

        return JsonResponse({
            'success': True,
            'message': f'PreparaciÃ³n "{new_preparacion.preparacion}" copiada exitosamente.',
            'nueva_preparacion': {
                'id_preparacion': new_preparacion.id_preparacion,
                'preparacion': new_preparacion.preparacion,
                'menu': new_preparacion.id_menu.menu
            }
        })

    except (TablaPreparaciones.DoesNotExist, TablaMenus.DoesNotExist):
        return JsonResponse({'error': 'La preparaciÃ³n o el menÃº de destino no existen.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'OcurriÃ³ un error inesperado: {str(e)}'}, status=500)


@login_required
def api_preparaciones_por_modalidad(request, modalidad_id):
    """API para listar todas las preparaciones Ãºnicas dentro de una modalidad."""
    if request.method != 'GET':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        # Encontrar todos los menÃºs de esa modalidad
        menus_en_modalidad = TablaMenus.objects.filter(id_modalidad_id=modalidad_id)

        # Encontrar todas las preparaciones en esos menÃºs, obteniendo solo nombres Ãºnicos
        preparaciones = TablaPreparaciones.objects.filter(
            id_menu__in=menus_en_modalidad
        ).order_by('preparacion').distinct('preparacion')

        # Formatear la respuesta
        # Se devuelve el ID de la *primera* preparaciÃ³n encontrada con ese nombre.
        # Esto es suficiente para que la API de copiado encuentre el original.
        preparaciones_data = [
            {
                "id": prep.id_preparacion,
                "nombre": prep.preparacion
            }
            for prep in preparaciones
        ]

        return JsonResponse({'preparaciones': preparaciones_data})

    except Exception as e:
        return JsonResponse({'error': f'OcurriÃ³ un error inesperado: {str(e)}'}, status=500)


# =================== INGREDIENTES SIESA ===================

@login_required
def lista_ingredientes(request):
    """Vista para listar ingredientes ICBF 2018"""
    ingredientes = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')
    paginator = Paginator(ingredientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'nutricion/lista_ingredientes.html', {
        'ingredientes': page_obj,
        'total_ingredientes': ingredientes.count()
    })


@login_required
@csrf_exempt
def api_ingredientes(request):
    """API para obtener ingredientes desde tabla ICBF 2018."""
    if request.method == 'GET':
        ingredientes = TablaAlimentos2018Icbf.objects.all().values(
            'codigo', 'nombre_del_alimento'
        ).order_by('nombre_del_alimento')

        data = [
            {
                # claves legacy para compatibilidad con frontend actual
                'id_ingrediente_siesa': ing['codigo'],
                'nombre_ingrediente': ing['nombre_del_alimento'],
                # claves explÃ­citas ICBF
                'codigo': ing['codigo'],
                'nombre_del_alimento': ing['nombre_del_alimento'],
            }
            for ing in ingredientes
        ]
        return JsonResponse({'ingredientes': data})

    return JsonResponse({'error': 'MÃ©todo no permitido para catÃ¡logo ICBF'}, status=405)


@login_required
@csrf_exempt
def api_ingrediente_detail(request, id_ingrediente):
    """API para manejar un ingrediente especifico del catalogo ICBF."""
    ingrediente = get_object_or_404(TablaAlimentos2018Icbf, codigo=id_ingrediente)

    if request.method == 'GET':
        return JsonResponse({
            'id_ingrediente_siesa': ingrediente.codigo,
            'nombre_ingrediente': ingrediente.nombre_del_alimento,
            'codigo': ingrediente.codigo,
            'nombre_del_alimento': ingrediente.nombre_del_alimento
        })

    return JsonResponse({'error': 'Metodo no permitido para catalogo ICBF'}, status=405)

# =================== COMPONENTES DE ALIMENTOS ===================

@login_required
def api_componentes_alimentos(request):
    """API para obtener componentes de alimentos"""
    if request.method == 'GET':
        from .models import ComponentesAlimentos

        componentes = ComponentesAlimentos.objects.select_related('id_grupo_alimentos').all().values(
            'id_componente',
            'componente',
            'id_grupo_alimentos__id_grupo_alimentos',
            'id_grupo_alimentos__grupo_alimentos'
        ).order_by('componente')

        return JsonResponse({'componentes': list(componentes)})

    return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)


# =================== PREPARACIÃ“N - INGREDIENTES ===================

@login_required
def detalle_preparacion(request, id_preparacion):
    """Vista para ver y gestionar ingredientes de una preparaciÃ³n"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)
    ingredientes_preparacion = TablaPreparacionIngredientes.objects.filter(
        id_preparacion=preparacion
    ).select_related('id_ingrediente_siesa')

    ingredientes_disponibles = TablaAlimentos2018Icbf.objects.all().order_by('nombre_del_alimento')

    return render(request, 'nutricion/detalle_preparacion.html', {
        'preparacion': preparacion,
        'ingredientes_preparacion': ingredientes_preparacion,
        'ingredientes_disponibles': ingredientes_disponibles
    })


@login_required
@csrf_exempt
def api_preparacion_ingredientes(request, id_preparacion):
    """API para manejar ingredientes de una preparaciÃ³n"""
    preparacion = get_object_or_404(TablaPreparaciones, id_preparacion=id_preparacion)

    if request.method == 'GET':
        relaciones = TablaPreparacionIngredientes.objects.filter(
            id_preparacion=preparacion
        ).select_related('id_ingrediente_siesa')

        ingredientes = []
        for rel in relaciones:
            ingredientes.append({
                # claves legacy para el frontend actual
                'id_ingrediente_siesa__id_ingrediente_siesa': rel.id_ingrediente_siesa.codigo,
                'id_ingrediente_siesa__nombre_ingrediente': rel.id_ingrediente_siesa.nombre_del_alimento,
                # claves explícitas ICBF
                'codigo': rel.id_ingrediente_siesa.codigo,
                'nombre_del_alimento': rel.id_ingrediente_siesa.nombre_del_alimento,
                'gramaje': float(rel.gramaje) if rel.gramaje is not None else None,
            })
        return JsonResponse({'ingredientes': ingredientes})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Soporte para agregar mÃºltiples ingredientes
            if 'ingredientes' in data:
                ingredientes_creados = []
                for ing_data in data['ingredientes']:
                    ingrediente, created = TablaPreparacionIngredientes.objects.get_or_create(
                        id_preparacion=preparacion,
                        id_ingrediente_siesa_id=ing_data['id_ingrediente_siesa']
                    )
                    gramaje_raw = ing_data.get('gramaje')
                    if gramaje_raw not in (None, '', 'null'):
                        ingrediente.gramaje = Decimal(str(gramaje_raw))
                        ingrediente.save(update_fields=['gramaje'])
                    if created:
                        ingredientes_creados.append(ingrediente.id_ingrediente_siesa.nombre_del_alimento)

                return JsonResponse({
                    'success': True,
                    'mensaje': f'{len(ingredientes_creados)} ingrediente(s) agregado(s) exitosamente'
                })
            else:
                # Soporte para agregar un solo ingrediente
                ingrediente = TablaPreparacionIngredientes.objects.create(
                    id_preparacion=preparacion,
                    id_ingrediente_siesa_id=data['id_ingrediente_siesa'],
                    gramaje=Decimal(str(data['gramaje'])) if data.get('gramaje') not in (None, '', 'null') else None
                )

                return JsonResponse({
                    'success': True,
                    'mensaje': 'Ingrediente agregado exitosamente'
                })

        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Este ingrediente ya estÃ¡ en la preparaciÃ³n'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error inesperado: {str(e)}'})


@login_required
@csrf_exempt
def api_preparacion_ingrediente_delete(request, id_preparacion, id_ingrediente):
    """API para eliminar un ingrediente de una preparaciÃ³n"""
    if request.method == 'DELETE':
        try:
            ingrediente = get_object_or_404(
                TablaPreparacionIngredientes,
                id_preparacion_id=id_preparacion,
                id_ingrediente_siesa_id=id_ingrediente
            )
            ingrediente.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})




# =================== ANÃLISIS NUTRICIONAL ===================

@login_required
def api_analisis_nutricional_menu(request, id_menu):
    """
    API para obtener anÃ¡lisis nutricional completo de un menÃº por niveles escolares.
    âœ¨ REFACTORIZADO: Usa AnalisisNutricionalService para lÃ³gica de negocio.
    """
    from .services import AnalisisNutricionalService

    try:
        # Delegar toda la lÃ³gica al servicio
        resultado = AnalisisNutricionalService.obtener_analisis_completo(id_menu)
        return JsonResponse(resultado)

    except TablaMenus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'MenÃº no encontrado'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener anÃ¡lisis: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def guardar_analisis_nutricional(request):
    """
    API para guardar automÃ¡ticamente el anÃ¡lisis nutricional editado por el usuario.
    âœ¨ REFACTORIZADO: Usa AnalisisNutricionalService.guardar_analisis()
    """
    from .services import AnalisisNutricionalService

    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        
        print(f"[DEBUG] Datos recibidos: {data}")
        print(f"[DEBUG] Claves disponibles: {list(data.keys())}")

        # Delegar al servicio
        resultado = AnalisisNutricionalService.guardar_analisis(
            id_menu=data['id_menu'],
            id_nivel_escolar=data['id_nivel_escolar'],
            totales=data['totales'],
            porcentajes=data['porcentajes'],
            ingredientes=data['ingredientes'],
            usuario=request.user.username if hasattr(request.user, 'username') else 'sistema'
        )

        return JsonResponse(resultado)

    except KeyError as e:
        return JsonResponse({
            'success': False,
            'error': f'Falta el campo: {str(e)}'
        }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON invÃ¡lidos'
        }, status=400)

    except TablaMenus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'MenÃº no encontrado'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al guardar: {str(e)}'
        }, status=500)

@login_required
def download_menu_excel(request, menu_id):
    """
    View to download an Excel file for a specific menu with advanced data integration.
    """
    try:
        # Usar el generador avanzado que detecta automÃ¡ticamente datos reales vs guardados
        excel_stream = generate_advanced_nutritional_excel(menu_id, use_saved_analysis=True)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_analisis_nutricional.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel: {str(e)}", status=500)


@login_required
def download_menu_excel_service(request, menu_id):
    """
    View to download an Excel file using the nutritional analysis service directly.
    """
    try:
        excel_stream = generate_excel_from_service(menu_id)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_servicio_analisis.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel desde servicio: {str(e)}", status=500)


from .excel_drawing_utils import ExcelReportDrawer
from .master_excel_generator import MasterNutritionalExcelGenerator

@login_required
def download_menu_excel_with_nivel(request, menu_id, nivel_escolar_id):
    """
    View to download an Excel file for a specific menu and school level with advanced data integration.
    """
    try:
        # Usar el generador avanzado con nivel especÃ­fico
        excel_stream = generate_advanced_nutritional_excel(menu_id, nivel_escolar_id, use_saved_analysis=True)

        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="menu_{menu_id}_nivel_{nivel_escolar_id}_analisis.xlsx"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando Excel: {str(e)}", status=500)


@login_required
def download_modalidad_excel(request, programa_id, modalidad_id):
    """
    Descarga el reporte maestro de Excel para todos los menÃºs de una modalidad.
    """
    try:
        # 1. Llamar al nuevo servicio para obtener los datos masivos
        masive_data = AnalisisNutricionalService.obtener_analisis_masivo_por_modalidad(
            programa_id=programa_id,
            modalidad_id=modalidad_id
        )

        if not masive_data.get('success'):
            raise ValueError("No se pudieron generar los datos para el reporte maestro.")

        # 2. Instanciar y usar el nuevo generador maestro
        generator = MasterNutritionalExcelGenerator()
        excel_stream = generator.generate(masive_data)

        # 3. Devolver la respuesta
        response = HttpResponse(
            excel_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"reporte_maestro_{masive_data['programa_nombre']}_{masive_data['modalidad_nombre']}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generando el reporte maestro de Excel: {str(e)}", status=500)

@login_required
def api_validar_semana(request):
    """
    Valida si una semana cumple con las frecuencias requeridas.
    
    GET params:
    - menu_ids: IDs de los 5 menÃºs separados por coma
    - modalidad_id: ID de la modalidad
    
    Returns:
    {
        "cumple": true/false,
        "componentes": [
            {
                "id": "com1",
                "nombre": "Bebida con leche",
                "requerido": 5,
                "actual": 5,
                "cumple": true
            },
            ...
        ]
    }
    """
    try:
        menu_ids_str = request.GET.get('menu_ids', '')
        modalidad_id = request.GET.get('modalidad_id')

        if not menu_ids_str or not modalidad_id:
            return JsonResponse({'error': 'Faltan parÃ¡metros: menu_ids y modalidad_id son requeridos'}, status=400)

        # Convertir string de IDs a lista
        menu_ids = [int(id.strip()) for id in menu_ids_str.split(',') if id.strip()]

        if not menu_ids:
            return JsonResponse({'error': 'No se proporcionaron IDs de menÃºs vÃ¡lidos'}, status=400)

        # Obtener requerimientos de la modalidad
        requerimientos = RequerimientoSemanal.objects.filter(
            modalidad__id_modalidades=modalidad_id
        ).select_related('componente')

        if not requerimientos.exists():
            return JsonResponse({
                'cumple': True,
                'componentes': [],
                'mensaje': 'No hay requerimientos definidos para esta modalidad'
            })

        # Contar componentes en los menÃºs de la semana
        # Usamos sets para contar DÃAS Ãºnicos, no preparaciones totales
        # Ejemplo: Si MenÃº 1 tiene 2 preparaciones con "Bebida", cuenta como 1 dÃ­a
        menus_por_componente = {}

        for menu_id in menu_ids:
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu_id=menu_id
            ).select_related('id_componente')

            # Componentes presentes en este menÃº (dÃ­a)
            componentes_del_menu = set()
            for prep in preparaciones:
                comp_id = prep.id_componente.id_componente
                componentes_del_menu.add(comp_id)

            # Registrar este menÃº (dÃ­a) para cada componente encontrado
            for comp_id in componentes_del_menu:
                if comp_id not in menus_por_componente:
                    menus_por_componente[comp_id] = set()
                menus_por_componente[comp_id].add(menu_id)

        # Convertir sets a conteos (nÃºmero de dÃ­as Ãºnicos)
        conteo_componentes = {
            comp_id: len(menus_set)
            for comp_id, menus_set in menus_por_componente.items()
        }

        # Validar contra requerimientos
        componentes_resultado = []
        cumple_total = True

        for req in requerimientos:
            comp_id = req.componente.id_componente
            comp_nombre = req.componente.componente
            requerido = req.frecuencia
            actual = conteo_componentes.get(comp_id, 0)
            cumple = actual == requerido

            if not cumple:
                cumple_total = False

            componentes_resultado.append({
                'id': comp_id,
                'componente': comp_nombre,  # Cambiado de 'nombre' a 'componente' para consistencia con frontend
                'requerido': requerido,
                'actual': actual,
                'cumple': cumple
            })

        return JsonResponse({
            'cumple': cumple_total,
            'componentes': componentes_resultado
        })

    except ValueError as e:
        return JsonResponse({'error': f'Error en formato de parÃ¡metros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al validar semana: {str(e)}'}, status=500)


@login_required
def api_requerimientos_modalidad(request):
    """
    Obtiene los requerimientos semanales de una modalidad.
    
    GET params:
    - modalidad_id: ID de la modalidad
    
    Returns:
    {
        "modalidad_id": "mod1",
        "requerimientos": [
            {
                "componente_id": "com1",
                "componente_nombre": "Bebida con leche",
                "frecuencia": 5
            },
            ...
        ]
    }
    """
    try:
        modalidad_id = request.GET.get('modalidad_id')

        if not modalidad_id:
            return JsonResponse({'error': 'Falta parÃ¡metro: modalidad_id es requerido'}, status=400)

        requerimientos = RequerimientoSemanal.objects.filter(
            modalidad__id_modalidades=modalidad_id
        ).select_related('componente')

        resultado = []
        for req in requerimientos:
            resultado.append({
                'componente_id': req.componente.id_componente,
                'componente_nombre': req.componente.componente,
                'frecuencia': req.frecuencia
            })

        return JsonResponse({
            'modalidad_id': modalidad_id,
            'requerimientos': resultado
        })

    except Exception as e:
        return JsonResponse({'error': f'Error al obtener requerimientos: {str(e)}'}, status=500)


@login_required
@csrf_exempt
def api_sincronizar_pesos_preparaciones(request):
    """
    Sincroniza los pesos desde TablaPreparacionIngredientes.gramaje
    hacia TablaIngredientesPorNivel para un menú y nivel específico.

    POST params:
    - id_menu: ID del menú
    - id_nivel_escolar: ID del nivel escolar
    - sobrescribir_existentes: (opcional) Si True, sobrescribe pesos ya guardados

    Returns:
    {
        "success": true,
        "mensaje": "Sincronización completada",
        "sincronizados": 15,
        "omitidos": 3,
        "errores": []
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        id_menu = data.get('id_menu')
        id_nivel_escolar = data.get('id_nivel_escolar')
        sobrescribir_existentes = data.get('sobrescribir_existentes', False)

        if not id_menu or not id_nivel_escolar:
            return JsonResponse({
                'error': 'Faltan parámetros: id_menu e id_nivel_escolar son requeridos'
            }, status=400)

        # Delegar al servicio
        resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
            id_menu=id_menu,
            id_nivel_escolar=id_nivel_escolar,
            sobrescribir_existentes=sobrescribir_existentes
        )

        return JsonResponse(resultado)

    except TablaMenus.DoesNotExist:
        return JsonResponse({'error': 'Menú no encontrado'}, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al sincronizar pesos: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
def api_guardar_ingredientes_por_nivel(request, id_menu):
    """
    Guarda los cambios de pesos de ingredientes por nivel escolar
    desde el editor de preparaciones.

    POST params:
    - niveles: Lista de objetos con:
        - id_nivel_escolar: ID del nivel
        - id_analisis: ID del análisis nutricional
        - ingredientes: Lista de ingredientes con:
            - id_preparacion: ID de la preparación
            - id_ingrediente: Código del ingrediente ICBF
            - peso_neto: Nuevo peso neto

    Returns:
    {
        "success": true,
        "registros_actualizados": 15,
        "mensaje": "Cambios guardados exitosamente"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        niveles = data.get('niveles', [])

        if not niveles:
            return JsonResponse({'error': 'No se enviaron datos para guardar'}, status=400)

        menu = get_object_or_404(TablaMenus, id_menu=id_menu)
        registros_actualizados = 0
        errores = []

        with transaction.atomic():
            for nivel_data in niveles:
                id_nivel_escolar = nivel_data.get('id_nivel_escolar')
                id_analisis = nivel_data.get('id_analisis')
                ingredientes = nivel_data.get('ingredientes', [])

                # Obtener el análisis
                try:
                    analisis = TablaAnalisisNutricionalMenu.objects.get(
                        id_analisis=id_analisis,
                        id_menu=menu
                    )
                except TablaAnalisisNutricionalMenu.DoesNotExist:
                    errores.append(f'Análisis {id_analisis} no encontrado')
                    continue

                # Actualizar cada ingrediente
                for ing_data in ingredientes:
                    id_preparacion = ing_data.get('id_preparacion')
                    id_ingrediente = ing_data.get('id_ingrediente')
                    peso_neto = float(ing_data.get('peso_neto', 0))

                    try:
                        # Buscar el ingrediente por nivel
                        preparacion = TablaPreparaciones.objects.get(
                            id_preparacion=id_preparacion,
                            id_menu=menu
                        )

                        ingrediente_siesa = TablaIngredientesSiesa.objects.get(
                            id_ingrediente_siesa=id_ingrediente
                        )

                        # Buscar el alimento ICBF para calcular nutrientes
                        try:
                            ingrediente_icbf = TablaAlimentos2018Icbf.objects.get(
                                codigo=id_ingrediente
                            )
                        except TablaAlimentos2018Icbf.DoesNotExist:
                            errores.append(f'Ingrediente ICBF {id_ingrediente} no encontrado')
                            continue

                        # Calcular valores nutricionales
                        from .services.calculo_service import CalculoService
                        valores = CalculoService.calcular_valores_nutricionales_alimento(
                            ingrediente_icbf,
                            peso_neto
                        )

                        # Calcular peso bruto
                        parte_comestible = float(ingrediente_icbf.parte_comestible_field or 100)
                        peso_bruto = CalculoService.calcular_peso_bruto(peso_neto, parte_comestible)

                        # Actualizar o crear el registro
                        obj, created = TablaIngredientesPorNivel.objects.update_or_create(
                            id_analisis=analisis,
                            id_preparacion=preparacion,
                            id_ingrediente_siesa=ingrediente_siesa,
                            defaults={
                                'peso_neto': peso_neto,
                                'peso_bruto': peso_bruto,
                                'calorias': valores.get('calorias', 0),
                                'proteina': valores.get('proteina', 0),
                                'grasa': valores.get('grasa', 0),
                                'cho': valores.get('cho', 0),
                                'calcio': valores.get('calcio', 0),
                                'hierro': valores.get('hierro', 0),
                                'sodio': valores.get('sodio', 0)
                            }
                        )

                        registros_actualizados += 1

                    except TablaPreparaciones.DoesNotExist:
                        errores.append(f'Preparación {id_preparacion} no encontrada')
                    except TablaIngredientesSiesa.DoesNotExist:
                        errores.append(f'Ingrediente Siesa {id_ingrediente} no encontrado')
                    except Exception as e:
                        errores.append(f'Error procesando ingrediente {id_ingrediente}: {str(e)}')

                # Recalcular totales del análisis
                AnalisisNutricionalService._recalcular_totales_analisis(analisis)

        return JsonResponse({
            'success': True,
            'registros_actualizados': registros_actualizados,
            'mensaje': 'Cambios guardados exitosamente',
            'errores': errores if errores else []
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al guardar cambios: {str(e)}'
        }, status=500)

