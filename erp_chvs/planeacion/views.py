# planeacion/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.db import transaction
from collections import defaultdict

from .models import Programa, PlanificacionRaciones, SedesEducativas
from .forms import ProgramaForm
from principal.models import PrincipalMunicipio, NivelGradoEscolar
from facturacion.models import ListadosFocalizacion
from facturacion.config import FOCALIZACIONES_DISPONIBLES
from facturacion.utils import _extraer_grado_base, _mapear_grado_a_nivel_manual


@login_required
def planeacion_index(request):
    """
    Vista que muestra el dashboard principal del módulo de Planeación
    con tarjetas de acceso a las diferentes funcionalidades.
    """
    return render(request, 'planeacion/index.html')


@login_required
def lista_programas(request):
    if request.method == 'POST':
        form = ProgramaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('planeacion:lista_programas')
    else:
        form = ProgramaForm()

    programas = Programa.objects.all().order_by('-fecha_inicial')

    context = {
        'programas': programas,
        'form': form,
    }
    return render(request, 'planeacion/lista_programas.html', context)


@login_required
def editar_programa(request, pk):
    programa_a_editar = get_object_or_404(Programa, pk=pk)

    if request.method == 'POST':
        form = ProgramaForm(request.POST, request.FILES, instance=programa_a_editar)
        if form.is_valid():
            form.save()
            return redirect('planeacion:lista_programas')
        else:
            # Si el formulario es inválido, mostramos la lista de nuevo con los errores
            programas = Programa.objects.all().order_by('-fecha_inicial')
            context = {
                'programas': programas,
                'form': form,
                'editing_id': pk  # Para saber que estamos editando
            }
            return render(request, 'planeacion/lista_programas.html', context)

    return redirect('planeacion:lista_programas')


@login_required
@require_http_methods(["POST"])
def eliminar_programa(request, pk):
    """
    Vista para eliminar un programa y su imagen asociada en Cloudinary.
    """
    programa = get_object_or_404(Programa, pk=pk)
    
    # Intentar eliminar la imagen de Cloudinary si existe
    if programa.imagen:
        try:
            # El name del campo suele ser el public_id en Cloudinary
            from .services import CloudinaryService
            CloudinaryService.eliminar_imagen(programa.imagen.name)
        except Exception as e:
            print(f"Error al eliminar imagen de Cloudinary: {e}")

    programa.delete()
    return redirect('planeacion:lista_programas')


@login_required
def ciclos_menus_view(request):
    """
    Vista principal para planificar ciclos de menús.
    Muestra filtros y tabla de planificación de raciones.
    """
    # Obtener programas activos ordenados por nombre
    programas = Programa.objects.filter(estado='activo').order_by('programa')

    context = {
        'programas': programas,
        'focalizaciones': FOCALIZACIONES_DISPONIBLES,
    }

    return render(request, 'planeacion/ciclos_menus.html', context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def inicializar_ciclos_menus(request):
    """
    API para inicializar la planificación de ciclos de menús.
    Procesa listados_focalizacion y crea/actualiza registros en PlanificacionRaciones.
    """
    try:
        import json
        data = json.loads(request.body)

        programa_id = data.get('programa_id')
        focalizacion = data.get('focalizacion')
        ano = data.get('ano', 2025)

        if not programa_id or not focalizacion:
            return JsonResponse({
                'success': False,
                'error': 'Parámetros Programa y Focalización son requeridos'
            }, status=400)

        # Obtener programa y municipio
        try:
            programa_obj = Programa.objects.get(id=programa_id)
            municipio_obj = programa_obj.municipio
            etc = municipio_obj.nombre_municipio
        except Programa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Programa con ID "{programa_id}" no encontrado'
            }, status=404)

        # Obtener todos los registros de listados_focalizacion para este ETC y focalización
        listados = ListadosFocalizacion.objects.filter(
            etc__icontains=etc,
            focalizacion=focalizacion
        )

        if not listados.exists():
            return JsonResponse({
                'success': False,
                'error': f'No se encontraron registros para ETC "{etc}" y Focalización "{focalizacion}"'
            }, status=404)

        # Obtener todos los niveles escolares y crear mapeo
        niveles_escolares = NivelGradoEscolar.objects.all()
        mapeo_grado_a_nivel_obj = {nivel.grados_sedes: nivel for nivel in niveles_escolares}

        # Agrupar datos por sede y nivel escolar
        # Usamos el objeto nivel completo como key para evitar problemas
        sedes_dict = defaultdict(lambda: defaultdict(lambda: {
            'cap_am': 0, 'cap_pm': 0, 'almuerzo_ju': 0, 'refuerzo': 0, 'grados': set()
        }))

        for listado in listados:
            sede_nombre = listado.sede
            grado_base = _extraer_grado_base(listado.grado_grupos)

            if not grado_base:
                continue

            # Buscar nivel escolar en el mapeo
            nivel_obj = mapeo_grado_a_nivel_obj.get(grado_base)

            if not nivel_obj:
                # Si no se encuentra en la tabla, intentar mapeo manual
                nivel_manual_nombre = _mapear_grado_a_nivel_manual(grado_base)
                if nivel_manual_nombre:
                    # Buscar nivel que contenga el nombre manual (ej: "Primaria" en "PRIMARIA 1 Y 2")
                    nivel_obj = next(
                        (n for n in niveles_escolares if nivel_manual_nombre.upper() in n.nivel_escolar_uapa.nivel_escolar_uapa.upper()),
                        None
                    )

            if not nivel_obj:
                continue  # Saltar si no se puede mapear el nivel

            # Usar el ID del nivel como clave
            nivel_key = nivel_obj.id_grado_escolar

            # Agregar grado al conjunto
            sedes_dict[sede_nombre][nivel_key]['grados'].add(grado_base)
            sedes_dict[sede_nombre][nivel_key]['nivel_obj'] = nivel_obj  # Guardar referencia al objeto

            # Contar por tipo de complemento
            if listado.complemento_alimentario_preparado_am:
                sedes_dict[sede_nombre][nivel_key]['cap_am'] += 1
            if listado.complemento_alimentario_preparado_pm:
                sedes_dict[sede_nombre][nivel_key]['cap_pm'] += 1
            if listado.almuerzo_jornada_unica:
                sedes_dict[sede_nombre][nivel_key]['almuerzo_ju'] += 1
            if listado.refuerzo_complemento_am_pm:
                sedes_dict[sede_nombre][nivel_key]['refuerzo'] += 1

        # Verificar si ya existen registros para esta combinación
        registros_existentes = PlanificacionRaciones.objects.filter(
            etc=municipio_obj,
            focalizacion=focalizacion,
            ano=ano
        ).exists()

        # Determinar modo de operación según parámetro
        modo_forzar = data.get('forzar_actualizacion', False)

        # Si existen registros y NO se forzó la actualización, retornar advertencia
        if registros_existentes and not modo_forzar:
            return JsonResponse({
                'success': False,
                'warning': 'Ya existen registros para esta combinación',
                'requiere_confirmacion': True,
                'total_registros_existentes': PlanificacionRaciones.objects.filter(
                    etc=municipio_obj,
                    focalizacion=focalizacion,
                    ano=ano
                ).count()
            }, status=200)

        # Determinar el nombre del programa basado en el municipio
        nombre_programa = _determinar_nombre_programa_por_municipio(municipio_obj.nombre_municipio)
        
        # Crear/actualizar registros en PlanificacionRaciones
        registros_creados = 0
        registros_actualizados = 0

        with transaction.atomic():
            for sede_nombre, niveles_data in sedes_dict.items():
                # Obtener objeto de sede
                try:
                    sede_obj = SedesEducativas.objects.get(nombre_sede_educativa=sede_nombre)
                except SedesEducativas.DoesNotExist:
                    continue  # Saltar sedes que no están en el catálogo

                for nivel_id, datos in niveles_data.items():
                    # Usar el nivel_obj guardado en los datos
                    nivel_obj = datos.get('nivel_obj')
                    if not nivel_obj:
                        continue

                    if modo_forzar:
                        # Modo FORZADO: Actualizar registros existentes (sobrescribir ediciones)
                        planificacion, created = PlanificacionRaciones.objects.update_or_create(
                            etc=municipio_obj,
                            focalizacion=focalizacion,
                            sede_educativa=sede_obj,
                            nivel_escolar=nivel_obj,
                            ano=ano,
                            defaults={
                                'nombre_programa': nombre_programa,
                                'cap_am': datos['cap_am'],
                                'cap_pm': datos['cap_pm'],
                                'almuerzo_ju': datos['almuerzo_ju'],
                                'refuerzo': datos['refuerzo'],
                            }
                        )
                    else:
                        # Modo SEGURO: Solo crear registros nuevos (preservar ediciones)
                        planificacion, created = PlanificacionRaciones.objects.get_or_create(
                            etc=municipio_obj,
                            focalizacion=focalizacion,
                            sede_educativa=sede_obj,
                            nivel_escolar=nivel_obj,
                            ano=ano,
                            defaults={
                                'nombre_programa': nombre_programa,
                                'cap_am': datos['cap_am'],
                                'cap_pm': datos['cap_pm'],
                                'almuerzo_ju': datos['almuerzo_ju'],
                                'refuerzo': datos['refuerzo'],
                            }
                        )

                    if created:
                        registros_creados += 1
                    else:
                        registros_actualizados += 1

        # Obtener datos para respuesta
        datos_respuesta = _obtener_datos_planificacion(municipio_obj, focalizacion, ano)

        return JsonResponse({
            'success': True,
            'message': f'Inicialización exitosa: {registros_creados} registros creados, {registros_actualizados} actualizados',
            'registros_creados': registros_creados,
            'registros_actualizados': registros_actualizados,
            'datos': datos_respuesta
        })

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error en inicializar_ciclos_menus: {error_detail}")  # Para debugging
        return JsonResponse({
            'success': False,
            'error': f'Error al inicializar: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def actualizar_racion(request):
    """
    API para actualizar una cantidad de ración específica.
    """
    try:
        import json
        data = json.loads(request.body)

        registro_id = data.get('id')
        campo = data.get('campo')  # cap_am, cap_pm, almuerzo_ju, refuerzo
        valor = data.get('valor')

        if not all([registro_id, campo, valor is not None]):
            return JsonResponse({
                'success': False,
                'error': 'Parámetros incompletos'
            }, status=400)

        # Validar campo
        campos_validos = ['cap_am', 'cap_pm', 'almuerzo_ju', 'refuerzo']
        if campo not in campos_validos:
            return JsonResponse({
                'success': False,
                'error': f'Campo inválido. Debe ser uno de: {", ".join(campos_validos)}'
            }, status=400)

        # Validar valor
        try:
            valor_int = int(valor)
            if valor_int < 0:
                raise ValueError("El valor no puede ser negativo")
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Valor inválido: {str(e)}'
            }, status=400)

        # Actualizar registro
        planificacion = get_object_or_404(PlanificacionRaciones, pk=registro_id)
        setattr(planificacion, campo, valor_int)
        planificacion.save()

        return JsonResponse({
            'success': True,
            'message': 'Registro actualizado exitosamente',
            'nuevo_total': planificacion.total_raciones()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def obtener_datos_ciclos(request):
    """
    API para obtener datos de planificación existentes.
    """
    try:
        programa_id = request.GET.get('programa_id')
        focalizacion = request.GET.get('focalizacion')
        ano = request.GET.get('ano', '2025')

        # Convertir año a entero
        try:
            ano = int(ano)
        except (ValueError, TypeError):
            ano = 2025

        if not programa_id or not focalizacion:
            return JsonResponse({
                'success': False,
                'error': 'Parámetros Programa y Focalización son requeridos'
            }, status=400)

        # Obtener programa y municipio
        try:
            programa_obj = Programa.objects.get(id=programa_id)
            municipio_obj = programa_obj.municipio
        except Programa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Programa con ID "{programa_id}" no encontrado'
            }, status=404)

        # Obtener datos
        datos = _obtener_datos_planificacion(municipio_obj, focalizacion, ano)

        return JsonResponse({
            'success': True,
            'datos': datos
        })

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error en obtener_datos_ciclos: {error_detail}")  # Para debugging
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener datos: {str(e)}'
        }, status=500)


def _obtener_datos_planificacion(municipio_obj, focalizacion, ano):
    """
    Función auxiliar para obtener datos de planificación en formato estructurado.
    """
    try:
        planificaciones = PlanificacionRaciones.objects.filter(
            etc=municipio_obj,
            focalizacion=focalizacion,
            ano=ano
        ).select_related('sede_educativa', 'nivel_escolar').order_by(
            'sede_educativa__nombre_sede_educativa', 'nivel_escolar__id_grado_escolar'
        )
    except Exception as e:
        print(f"Error al consultar PlanificacionRaciones: {e}")
        import traceback
        traceback.print_exc()
        return []

    # Agrupar por sede
    sedes_dict = defaultdict(list)

    for plan in planificaciones:
        # Obtener todos los grados únicos para esta sede y focalización
        grados_listados = ListadosFocalizacion.objects.filter(
            sede=plan.sede_educativa.nombre_sede_educativa,
            focalizacion=focalizacion
        ).values_list('grado_grupos', flat=True).distinct()

        # Filtrar grados que pertenecen a este nivel
        # Comparar con grados_sedes del nivel actual
        grados_del_nivel = set()
        for grado_grupo in grados_listados:
            grado_base = _extraer_grado_base(grado_grupo)
            if grado_base:
                # Verificar si este grado pertenece al nivel actual
                if grado_base == plan.nivel_escolar.grados_sedes:
                    grados_del_nivel.add(grado_base)

        sedes_dict[plan.sede_educativa.nombre_sede_educativa].append({
            'id': plan.id,
            'nivel_escolar': plan.nivel_escolar.nivel_escolar_uapa.nivel_escolar_uapa,
            'grados': ', '.join(sorted(grados_del_nivel)) if grados_del_nivel else plan.nivel_escolar.grados_sedes,
            'cap_am': plan.cap_am,
            'cap_pm': plan.cap_pm,
            'almuerzo_ju': plan.almuerzo_ju,
            'refuerzo': plan.refuerzo,
            'total': plan.total_raciones()
        })

    # Convertir a lista de sedes
    sedes_lista = []
    for sede_nombre, niveles in sedes_dict.items():
        sedes_lista.append({
            'sede': sede_nombre,
            'niveles': niveles
        })

    return sedes_lista


def _determinar_nombre_programa_por_municipio(nombre_municipio):
    """
    Determina el nombre del programa basado en el municipio.
    
    Args:
        nombre_municipio (str): Nombre del municipio
        
    Returns:
        str: Nombre del programa correspondiente
    """
    municipio_upper = nombre_municipio.upper()
    
    if 'CALI' in municipio_upper:
        return 'PAE CALI'
    elif 'YUMBO' in municipio_upper:
        return 'PAE YUMBO'
    elif 'BUGA' in municipio_upper:
        return 'PAE GUADALAJARA DE BUGA'
    else:
        # Municipio no reconocido, usar nombre genérico
        return f'PAE {nombre_municipio.upper()}'
