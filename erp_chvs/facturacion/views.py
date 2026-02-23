"""
Vista única consolidada para el módulo de facturación.
Permite visualizar y guardar datos en una sola interfaz.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
import base64
import pandas as pd
from io import StringIO
import json

from .models import ListadosFocalizacion
from principal.models import PrincipalDepartamento, PrincipalMunicipio, RegistroActividad
from .services import ProcesamientoService, ValidacionService, EstadisticasService
from .config import ProcesamientoConfig, FOCALIZACIONES_DISPONIBLES, MESES_ATENCION
from .logging_config import FacturacionLogger
from planeacion.models import SedesEducativas, Programa
from .utils import _mapear_grado_a_nivel_manual, _extraer_grado_base, _recrear_archivo_desde_sesion, _determinar_nivel_educativo
from .persistence_service import PersistenceService
from .pdf_generator import crear_formato_asistencia
from .pdf_service import PDFAsistenciaService
import random
from io import BytesIO
import zipfile

# Inicializar servicios
procesamiento_service = ProcesamientoService()
validacion_service = ValidacionService()
estadisticas_service = EstadisticasService()

@login_required
def facturacion_index(request):
    """
    Vista principal del dashboard de facturación.
    
    Args:
        request: HttpRequest object
    
    Returns:
        HttpResponse: Página principal de facturación
    """
    try:
        FacturacionLogger.log_procesamiento_inicio(
            "dashboard", "acceso_pagina_principal"
        )
        
        return render(request, 'facturacion/index.html')
        
    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "facturacion_index", str(e)
        )
        return render(request, 'facturacion/index.html', {
            'error': f"Error al cargar la página: {str(e)}"
        })

@login_required
def procesar_listados_view(request):
    """
    Vista ÚNICA consolidada de procesamiento con DOS ETAPAS:

    ETAPA 1 - VISUALIZACIÓN:
    - Usuario sube archivo Excel (formato original o nuevo)
    - Sistema procesa y muestra datos para validación
    - Usuario puede revisar sedes inválidas y estadísticas

    ETAPA 2 - ALMACENAMIENTO:
    - Si datos son correctos, usuario puede guardar en BD
    - Sistema muestra estadísticas de guardado
    - Opción de procesar nuevo archivo

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página de procesamiento por etapas
    """
    # Inicializar contexto para las dos etapas
    programas = Programa.objects.select_related('municipio').all()
    contexto = {
        # Configuración general
        'focalizaciones': FOCALIZACIONES_DISPONIBLES,
        'programas': programas,

        # ETAPA 1: Visualización
        'etapa_actual': 1,
        'dataframe_html': None,
        'verified_message': None,
        'invalid_sedes': [],
        'coincidencias_parciales': [],
        'coincidencias_genericas': [],
        'agrupacion_sedes': [],
        'datos_procesados': None,  # Para pasar a etapa 2

        # ETAPA 2: Almacenamiento
        'registros_guardados_bd': 0,
        'advertencia_bd': None,
        'persistencia_detalle': None,

        # Control de flujo
        'archivo_procesado_exitosamente': False,
        'listo_para_guardar': False
    }

    try:
        if request.method == 'POST':
            # Detectar qué etapa estamos procesando
            etapa = request.POST.get('etapa', '1')

            if etapa == '1' and request.FILES.get('archivo_excel'):
                # ================================
                # ETAPA 1: CARGUE Y VISUALIZACIÓN
                # ================================
                archivo = request.FILES['archivo_excel']
                focalizacion = request.POST.get('focalizacion', '')
                programa_id = request.POST.get('programa', '')

                # Validar programa
                if not programa_id:
                    contexto['error'] = "Debe seleccionar un programa."
                    return render(request, 'facturacion/procesar_listados.html', contexto)

                try:
                    programa = Programa.objects.select_related('municipio').get(id=programa_id)
                    municipio = programa.municipio.nombre_municipio
                    # Determinar tipo_procesamiento a partir del municipio
                    if "YUMBO" in municipio.upper():
                        tipo_procesamiento = "yumbo"
                    elif "BUGA" in municipio.upper():
                        tipo_procesamiento = "buga"
                    else:
                        tipo_procesamiento = "nuevo" # Cali o cualquier otro
                except Programa.DoesNotExist:
                    contexto['error'] = "El programa seleccionado no es válido."
                    return render(request, 'facturacion/procesar_listados.html', contexto)


                # Validar focalización
                if not focalizacion or focalizacion not in FOCALIZACIONES_DISPONIBLES:
                    contexto['error'] = "Focalización inválida. Seleccione una focalización válida."
                    return render(request, 'facturacion/procesar_listados.html', contexto)

                FacturacionLogger.log_procesamiento_inicio(archivo.name, f"etapa_1_{tipo_procesamiento}", focalizacion)

                # Leer el contenido del archivo primero
                archivo.seek(0)  # Asegurar que estamos al inicio
                archivo_contenido = archivo.read()
                archivo.seek(0)  # Resetear para el procesamiento

                # Procesar archivo según formato elegido
                if tipo_procesamiento == ProcesamientoConfig.TIPO_PROCESAMIENTO_NUEVO:
                    resultado = procesamiento_service.procesar_excel_nuevo_formato(archivo, focalizacion)
                elif tipo_procesamiento in [ProcesamientoConfig.TIPO_PROCESAMIENTO_YUMBO, ProcesamientoConfig.TIPO_PROCESAMIENTO_BUGA, ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL]:
                    # Todos estos usan el formato original
                    resultado = procesamiento_service.procesar_excel_original(archivo, focalizacion)
                else:
                    # Fallback al formato original
                    resultado = procesamiento_service.procesar_excel_original(archivo, focalizacion)

                # Actualizar contexto con los resultados de la visualización
                if resultado['success']:
                    RegistroActividad.registrar(
                        request, 'facturacion', 'cargue_excel',
                        f"Archivo: {archivo.name} | Municipio: {municipio} | "
                        f"Focalización: {focalizacion} | Registros: {resultado.get('total_registros', 0)}"
                    )
                    # Guardar datos en sesión para la etapa 2 (incluir DataFrame procesado)
                    # Convertir DataFrame a JSON para almacenar en sesión
                    df_procesado = resultado.get('dataframe')
                    if df_procesado is not None:
                        df_json = df_procesado.to_json(orient='records', date_format='iso')
                    else:
                        df_json = None

                    request.session['datos_etapa_1'] = {
                        'archivo_name': archivo.name,
                        'focalizacion': focalizacion,
                        'programa_id': programa_id,
                        'tipo_procesamiento': tipo_procesamiento,
                        'total_registros': resultado.get('total_registros', 0),
                        'dataframe_procesado_json': df_json,  # DataFrame ya procesado
                        'archivo_contenido_b64': base64.b64encode(archivo_contenido).decode('utf-8'),  # Solo backup
                        'archivo_content_type': archivo.content_type
                    }

                    contexto.update({
                        'etapa_actual': 2,  # Pasar a etapa 2
                        'dataframe_html': resultado['dataframe_html'],
                        'verified_message': resultado['verified_message'],
                        'invalid_sedes': resultado['invalid_sedes'],
                        'coincidencias_parciales': resultado['coincidencias_parciales'],
                        'coincidencias_genericas': resultado['coincidencias_genericas'],
                        'agrupacion_sedes': resultado['agrupacion_sedes'],
                        'archivo_procesado_exitosamente': True,
                        'listo_para_guardar': len(resultado['invalid_sedes']) == 0,  # Solo si no hay sedes inválidas
                        'datos_procesados': request.session['datos_etapa_1']
                    })

                    # Mensaje de éxito para etapa 1
                    if contexto['listo_para_guardar']:
                        contexto['success_message'] = "✅ Archivo procesado exitosamente. Todos los datos son válidos. Ahora puede guardar en la base de datos."
                    else:
                        contexto['warning_message'] = "⚠️ Archivo procesado con advertencias. Revise las sedes inválidas antes de guardar."
                else:
                    contexto['error'] = f"Error procesando archivo: {resultado.get('error', 'Error desconocido')}"

            elif etapa == '2':
                # ================================
                # ETAPA 2: ALMACENAMIENTO EN BD
                # ================================
                # Recuperar datos de la sesión de la etapa 1
                datos_etapa_1 = request.session.get('datos_etapa_1')

                if not datos_etapa_1:
                    contexto['error'] = "Error: No se encontraron datos de la etapa 1. Por favor, reinicie el proceso."
                    return render(request, 'facturacion/procesar_listados.html', contexto)

                archivo_name = datos_etapa_1['archivo_name']
                focalizacion = datos_etapa_1['focalizacion']
                tipo_procesamiento = datos_etapa_1['tipo_procesamiento']
                programa_id = datos_etapa_1.get('programa_id')

                FacturacionLogger.log_procesamiento_inicio(archivo_name, f"etapa_2_{tipo_procesamiento}", focalizacion)

                # Usar DataFrame ya procesado de la Etapa 1 (sin reprocesar)
                df_json = datos_etapa_1.get('dataframe_procesado_json')

                if df_json:
                    # Debug: Log del DataFrame recuperado
                    FacturacionLogger.log_procesamiento_inicio(
                        archivo_name, f"recuperando_dataframe_etapa_1", focalizacion
                    )

                    # Reconstruir DataFrame desde JSON (usando StringIO para evitar deprecación)
                    df_procesado = pd.read_json(StringIO(df_json), orient='records')

                    # Guardar directamente en BD usando el DataFrame procesado
                    
                    resultado_persistencia = PersistenceService.guardar_listados_focalizacion(df_procesado, programa_id=programa_id)

                    # Crear resultado compatible con el contexto
                    resultado = {
                        'success': resultado_persistencia['success'],
                        'registros_guardados_bd': resultado_persistencia.get('registros_guardados', 0),
                        'persistencia': resultado_persistencia,
                        'total_registros': datos_etapa_1['total_registros']
                    }

                    if not resultado_persistencia['success']:
                        resultado['error'] = resultado_persistencia.get('error', 'Error desconocido en persistencia')
                        resultado['advertencia_bd'] = resultado_persistencia.get('error')
                else:
                    # Fallback: reprocesar si no hay DataFrame (no debería pasar)
                    FacturacionLogger.log_procesamiento_error(archivo_name, "DataFrame no encontrado en sesión, reprocesando...")

                    try:
                        archivo_recreado = _recrear_archivo_desde_sesion(datos_etapa_1)
                    except ValueError as e:
                        contexto['error'] = str(e)
                        # Limpiar sesión para evitar bucles de error
                        if 'datos_etapa_1' in request.session:
                            del request.session['datos_etapa_1']
                        return render(request, 'facturacion/procesar_listados.html', contexto)

                    resultado = procesamiento_service.procesar_y_guardar_excel(
                        archivo_recreado,
                        focalizacion,
                        tipo_procesamiento,
                        guardar_en_bd=True,
                        programa_id=programa_id
                    )

                # Actualizar contexto con resultados del guardado
                contexto.update({
                    'etapa_actual': 3,  # Etapa completada
                    'registros_guardados_bd': resultado.get('registros_guardados_bd', 0),
                    'advertencia_bd': resultado.get('advertencia_bd'),
                    'persistencia_detalle': resultado.get('persistencia'),
                    'archivo_procesado_exitosamente': True
                })

                # Limpiar sesión después del guardado
                if 'datos_etapa_1' in request.session:
                    del request.session['datos_etapa_1']

                RegistroActividad.registrar(
                    request, 'facturacion', 'guardar_listados',
                    f"Archivo: {archivo_name} | Municipio: {datos_etapa_1.get('tipo_procesamiento', '')} | "
                    f"Focalización: {focalizacion} | Guardados en BD: {contexto['registros_guardados_bd']}",
                    exitoso=resultado.get('success', False)
                )

                # Mensaje de éxito para etapa 2
                if contexto['registros_guardados_bd'] > 0:
                    contexto['success_message'] = f"🎉 ¡Guardado exitoso! Se almacenaron {contexto['registros_guardados_bd']} registros en la base de datos."
                else:
                    contexto['warning_message'] = "⚠️ No se guardaron registros nuevos. Posiblemente ya existían en la base de datos."

        return render(request, 'facturacion/procesar_listados.html', contexto)

    except Exception as e:
        FacturacionLogger.log_procesamiento_error("procesar_listados_view", str(e))
        contexto['error'] = f"Error al procesar la solicitud: {str(e)}"
        return render(request, 'facturacion/procesar_listados.html', contexto)


@login_required
@require_http_methods(["POST"])
def validar_archivo_ajax(request):
    """
    Vista AJAX para validar archivo antes del procesamiento.
    
    Args:
        request: HttpRequest object
    
    Returns:
        JsonResponse: Resultado de la validación
    """
    try:
        if not request.FILES.get('archivo_excel'):
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó archivo'
            })
        
        archivo = request.FILES['archivo_excel']
        programa_id = request.POST.get('programa', '')

        if not programa_id:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar un programa'
            })

        try:
            programa = Programa.objects.get(id=programa_id)
            municipio = programa.municipio.nombre_municipio
            if "YUMBO" in municipio.upper():
                tipo_procesamiento = "yumbo"
            elif "BUGA" in municipio.upper():
                tipo_procesamiento = "buga"
            else:
                tipo_procesamiento = "nuevo"
        except Programa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'El programa seleccionado no es válido'
            })

        # Validar archivo básico
        if not procesamiento_service.excel_processor.validar_archivo_excel(archivo):
            return JsonResponse({
                'success': False,
                'error': 'Tipo de archivo inválido'
            })
        
        # Leer y validar estructura
        df = procesamiento_service.excel_processor.leer_excel(archivo)
        
        if tipo_procesamiento == ProcesamientoConfig.TIPO_PROCESAMIENTO_NUEVO:
            es_valido, errores = procesamiento_service.excel_processor.validar_estructura_nuevo_formato(df)
        else:
            es_valido, errores = procesamiento_service.excel_processor.validar_estructura_original_formato(df)
        
        if not es_valido:
            return JsonResponse({
                'success': False,
                'error': '; '.join(errores)
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Archivo válido',
            'total_filas': len(df),
            'total_columnas': len(df.columns)
        })
        
    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "validar_archivo_ajax", str(e)
        )
        return JsonResponse({
            'success': False,
            'error': f'Error durante la validación: {str(e)}'
        })

@login_required
def obtener_estadisticas_sedes(request):
    """
    Vista AJAX para obtener estadísticas de sedes.
    
    Args:
        request: HttpRequest object
    
    Returns:
        JsonResponse: Estadísticas de sedes
    """
    try:
        municipio = request.GET.get('municipio', 'CALI')
        
        # Obtener estadísticas básicas de sedes
        from .fuzzy_matching import FuzzyMatcher
        sedes_por_municipio = FuzzyMatcher.obtener_sedes_por_municipio([municipio])
        
        estadisticas = {
            'municipio': municipio,
            'total_sedes': len(sedes_por_municipio.get(municipio, {}).get('principales', [])),
            'sedes_genericas': len(sedes_por_municipio.get(municipio, {}).get('genericas', []))
        }
        
        return JsonResponse({
            'success': True,
            'estadisticas': estadisticas
        })
        
    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "obtener_estadisticas_sedes", str(e)
        )
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estadísticas: {str(e)}'
        })

@login_required
@require_http_methods(["GET"])
def api_focalizaciones_existentes(request):
    """
    API para obtener las focalizaciones que ya existen en la BD
    para un programa específico.
    """
    try:
        programa_id = request.GET.get('programa_id', '')
        if not programa_id:
            return JsonResponse({'focalizaciones': []})

        focalizaciones = ListadosFocalizacion.objects.filter(
            programa_id=programa_id
        ).values_list('focalizacion', flat=True).distinct()

        return JsonResponse({'focalizaciones': list(focalizaciones)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Funciones de utilidad para compatibilidad con el código existente
def validar_archivo_excel(archivo):
    """
    Función de compatibilidad para validar archivos Excel.
    Mantiene la interfaz original para no romper el código existente.
    """
    return procesamiento_service.excel_processor.validar_archivo_excel(archivo)

def leer_excel(archivo):
    """
    Función de compatibilidad para leer archivos Excel.
    Mantiene la interfaz original para no romper el código existente.
    """
    return procesamiento_service.excel_processor.leer_excel(archivo)

def verificar_columnas_requeridas(df, columnas_requeridas):
    """
    Función de compatibilidad para verificar columnas requeridas.
    Mantiene la interfaz original para no romper el código existente.
    """
    return procesamiento_service.excel_processor.verificar_columnas_requeridas(df, columnas_requeridas)

def aplicar_mapeos_datos(df):
    """
    Función de compatibilidad para aplicar mapeos de datos.
    Mantiene la interfaz original para no romper el código existente.
    """
    return procesamiento_service.data_transformer.aplicar_mapeos_datos(df)

def normalizar_texto(texto):
    """
    Función de compatibilidad para normalizar texto.
    Mantiene la interfaz original para no romper el código existente.
    """
    return procesamiento_service.fuzzy_matcher.normalizar_texto(texto)

def encontrar_coincidencia_difusa(sede_excel, sedes_bd, umbral=90):
    """
    Función de compatibilidad para encontrar coincidencias difusas.
    Mantiene la interfaz original para no romper el código existente.
    """
    return procesamiento_service.fuzzy_matcher.encontrar_coincidencia_difusa(sede_excel, sedes_bd, umbral)

# ===== VISTA PARA LISTADO DE LISTADOS FOCALIZACIÓN =====

@login_required
def lista_listados(request):
    """Vista para listar y gestionar listados de focalización con filtros"""

    # Obtener parámetros de filtro
    programa_filter_id = request.GET.get('programa', '').strip()
    sede_filter = request.GET.get('sede', '').strip()
    focalizacion_filter = request.GET.get('focalizacion', '').strip()

    # Query base con agregación
    from django.db.models import Count, Max, Func, CharField

    # Función personalizada para extraer el grado base usando regex de PostgreSQL
    # Ejemplo: "10-1001" -> "10", "-1-1" -> "-1"
    class ExtractGradoBase(Func):
        """Extrae el grado base (todo antes del último guión) usando regex de PostgreSQL"""
        function = 'REGEXP_REPLACE'
        template = "%(function)s(%(expressions)s, '-[^-]*$', '', 'g')"

        def __init__(self, expression, **extra):
            super().__init__(expression, output_field=CharField(), **extra)

    listados_grouped = ListadosFocalizacion.objects.annotate(
        grado_base=ExtractGradoBase('grado_grupos')
    ).values('sede', 'grado_base', 'programa__programa', 'focalizacion').annotate(
        total_raciones=Count('id_listados'),
        ultima_subida=Max('fecha_actualizacion'),
    ).order_by('sede', 'grado_base')

    # Aplicar filtros a la consulta agrupada
    if programa_filter_id:
        listados_grouped = listados_grouped.filter(programa_id=programa_filter_id)

    if sede_filter:
        listados_grouped = listados_grouped.filter(sede__icontains=sede_filter)

    if focalizacion_filter:
        listados_grouped = listados_grouped.filter(focalizacion=focalizacion_filter)

    # Calcular total de raciones (beneficiarios) con los filtros aplicados
    total_raciones_query = ListadosFocalizacion.objects.all()
    if programa_filter_id:
        total_raciones_query = total_raciones_query.filter(programa_id=programa_filter_id)
    if sede_filter:
        total_raciones_query = total_raciones_query.filter(sede__icontains=sede_filter)
    if focalizacion_filter:
        total_raciones_query = total_raciones_query.filter(focalizacion=focalizacion_filter)

    total_raciones = total_raciones_query.count()

    # Paginación
    paginator = Paginator(listados_grouped, 20)  # 20 grupos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener valores únicos para filtros
    programas = Programa.objects.all().order_by('municipio__nombre_municipio', 'programa')

    # Filtrar sedes y focalizaciones según el programa seleccionado
    if programa_filter_id:
        # Si hay programa seleccionado, mostrar solo sedes y focalizaciones de ese programa
        sede_values = ListadosFocalizacion.objects.filter(
            programa_id=programa_filter_id
        ).values_list('sede', flat=True).distinct().order_by('sede')

        focalizacion_values = ListadosFocalizacion.objects.filter(
            programa_id=programa_filter_id
        ).values_list('focalizacion', flat=True).distinct().order_by('focalizacion')
    else:
        # Si no hay programa seleccionado, mostrar todas
        sede_values = ListadosFocalizacion.objects.values_list('sede', flat=True).distinct().order_by('sede')
        focalizacion_values = ListadosFocalizacion.objects.values_list('focalizacion', flat=True).distinct().order_by('focalizacion')

    # Lógica para Sedes Faltantes
    sedes_faltantes = []
    total_sedes_faltantes = 0
    grados_disponibles = []
    filtros_aplicados = {
        'programa': programa_filter_id,
        'sede': sede_filter,
        'focalizacion': focalizacion_filter,
        'programa_nombre': ''
    }

    if programa_filter_id:
        try:
            programa_seleccionado = Programa.objects.get(id=programa_filter_id)
            filtros_aplicados['programa_nombre'] = programa_seleccionado.programa
            etc_filter = programa_seleccionado.municipio.nombre_municipio

            # El resto de la lógica de sedes faltantes funciona con etc_filter
            sedes_catalogo_etc = set(
                SedesEducativas.objects.filter(
                    codigo_ie__id_municipios__nombre_municipio__icontains=etc_filter
                ).values_list('nombre_sede_educativa', flat=True).distinct()
            )

            if focalizacion_filter:
                sedes_con_registros_etc = set(
                    ListadosFocalizacion.objects.filter(
                        programa_id=programa_filter_id,
                        focalizacion=focalizacion_filter
                    ).values_list('sede', flat=True).distinct()
                )
                sedes_sin_registros = list(sedes_catalogo_etc - sedes_con_registros_etc)
                for sede in sedes_sin_registros:
                    sedes_faltantes.append({
                        'sede': sede,
                        'focalizaciones_faltantes': [focalizacion_filter]
                    })
            else:
                focalizaciones_existentes_programa = set(
                    ListadosFocalizacion.objects.filter(
                        programa_id=programa_filter_id
                    ).values_list('focalizacion', flat=True).distinct()
                )
                for sede in sedes_catalogo_etc:
                    focalizaciones_sede = set(
                        ListadosFocalizacion.objects.filter(
                            programa_id=programa_filter_id,
                            sede=sede
                        ).values_list('focalizacion', flat=True).distinct()
                    )
                    focalizaciones_faltantes = focalizaciones_existentes_programa - focalizaciones_sede
                    if focalizaciones_faltantes:
                        sedes_faltantes.append({
                            'sede': sede,
                            'focalizaciones_faltantes': sorted(list(focalizaciones_faltantes))
                        })
            total_sedes_faltantes = len(sedes_faltantes)

        except Programa.DoesNotExist:
            pass # No hacer nada si el programa no existe

    context = {
        'listados': page_obj,
        'total_raciones': total_raciones,
        'programas': programas,
        'sede_values': sede_values,
        'focalizacion_values': focalizacion_values,
        'filtros_aplicados': filtros_aplicados,
        'sedes_faltantes': sedes_faltantes,
        'total_sedes_faltantes': total_sedes_faltantes,
        'grados_disponibles': grados_disponibles,
    }

    return render(request, 'facturacion/lista_listados.html', context)

# ===== APIs PARA GESTIÓN DE LISTADOS FOCALIZACIÓN =====
# NOTA: Las APIs de creación, edición, visualización y eliminación individual de registros
# han sido deshabilitadas. Los registros solo deben modificarse a través de la carga de
# archivos Excel para mantener la integridad de los datos.
#
# Si se necesita modificar registros, use las siguientes opciones:
# 1. Reemplazar focalización completa (reemplazar_focalizacion_sedes)
# 2. Transferir grados entre sedes (api_transferir_grados)
# 3. Cargar nuevamente el archivo Excel con los datos corregidos

@login_required
def api_obtener_sedes_con_grados(request):
    """
    API para obtener sedes disponibles con sus grados para transferencia.

    Retorna las sedes que tienen registros para un programa y focalización,
    agrupadas por grado con conteo de estudiantes.
    """
    try:
        programa_id = request.GET.get('programa_id')
        focalizacion = request.GET.get('focalizacion')

        if not programa_id or not focalizacion:
            return JsonResponse({
                'success': False,
                'error': 'Parámetros incompletos. Se requiere programa_id y focalizacion'
            })

        # Obtener todas las sedes del programa con esa focalización
        sedes_query = ListadosFocalizacion.objects.filter(
            programa_id=programa_id,
            focalizacion=focalizacion
        ).values('sede').distinct()

        sedes_con_grados = []

        for sede_data in sedes_query:
            sede_nombre = sede_data['sede']

            # Obtener grados únicos de esta sede
            grados_query = ListadosFocalizacion.objects.filter(
                programa_id=programa_id,
                focalizacion=focalizacion,
                sede=sede_nombre
            ).exclude(grado_grupos__isnull=True).exclude(grado_grupos='')

            # Agrupar por grado base
            grados_dict = {}
            for registro in grados_query:
                grado_base = _extraer_grado_base(registro.grado_grupos)
                if grado_base:
                    if grado_base not in grados_dict:
                        grados_dict[grado_base] = {
                            'grado': grado_base,
                            'count': 0,
                            'grupos': set()
                        }
                    grados_dict[grado_base]['count'] += 1
                    grados_dict[grado_base]['grupos'].add(registro.grado_grupos)

            # Organizar grados por nivel educativo
            niveles = {
                'Transición': [],
                'Primaria': [],
                'Secundaria': [],
                'Media': []
            }

            for grado_base, info in grados_dict.items():
                grado_obj = {
                    'grado': grado_base,
                    'descripcion': f"{info['count']} estudiante{'s' if info['count'] != 1 else ''} ({', '.join(sorted(info['grupos']))})"
                }

                # Clasificar por nivel
                if grado_base.startswith('-'):
                    niveles['Transición'].append(grado_obj)
                elif grado_base in ['0', '1', '2', '3', '4', '5']:
                    niveles['Primaria'].append(grado_obj)
                elif grado_base in ['6', '7', '8', '9']:
                    niveles['Secundaria'].append(grado_obj)
                elif grado_base in ['10', '11']:
                    niveles['Media'].append(grado_obj)
                else:
                    niveles['Primaria'].append(grado_obj)

            # Construir estructura de niveles con grados
            grados_por_nivel = []
            for nivel, grados in niveles.items():
                if grados:
                    # Ordenar grados dentro del nivel
                    grados_sorted = sorted(grados, key=lambda x: x['grado'])
                    grados_por_nivel.append({
                        'nivel': nivel,
                        'grados': grados_sorted
                    })

            if grados_por_nivel:
                sedes_con_grados.append({
                    'sede': sede_nombre,
                    'total_grados': len(grados_dict),
                    'total_estudiantes': sum(g['count'] for g in grados_dict.values()),
                    'grados': grados_por_nivel
                })

        return JsonResponse({
            'success': True,
            'sedes': sedes_con_grados
        })

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "api_obtener_sedes_con_grados", str(e)
        )
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener sedes: {str(e)}'
        })

@login_required
@csrf_exempt
def api_transferir_grados(request):
    """API para transferir grados de una sede a otra respetando la focalización"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sede_destino = data.get('sede_destino')
            sede_origen = data.get('sede_origen')
            grados_seleccionados = data.get('grados_seleccionados', [])
            focalizacion = data.get('focalizacion')  # Focalización activa

            if not sede_destino or not sede_origen or not grados_seleccionados:
                return JsonResponse({'success': False, 'error': 'Parámetros incompletos: sede_destino, sede_origen y grados_seleccionados son requeridos'})

            # Obtener registros fuente (de la sede origen específica con esos grados)
            # IMPORTANTE: Filtrar también por focalización para evitar mezclar focalizaciones
            query_fuente = ListadosFocalizacion.objects.filter(
                sede=sede_origen
            )

            # Si se especifica focalización, filtrar solo por esa focalización
            # RECOMENDADO: Siempre especificar focalización para evitar mezclar datos
            if focalizacion:
                query_fuente = query_fuente.filter(focalizacion=focalizacion)

            registros_fuente = query_fuente

            # Filtrar por grados seleccionados
            registros_a_copiar = []
            for registro in registros_fuente:
                if registro.grado_grupos:
                    grado_base = _extraer_grado_base(str(registro.grado_grupos))
                    if grado_base and grado_base in grados_seleccionados:
                        registros_a_copiar.append(registro)

            # MOVER registros a la sede destino (no copiar)
            registros_movidos = 0
            with transaction.atomic():
                for registro in registros_a_copiar:
                    try:
                        # Actualizar la sede del registro existente (MOVER, no copiar)
                        registro.sede = sede_destino
                        registro.save()
                        registros_movidos += 1
                    except Exception as e:
                        continue  # Continuar con el siguiente registro

            RegistroActividad.registrar(
                request, 'facturacion', 'transferir_grados',
                f"Origen: {sede_origen} → Destino: {sede_destino} | "
                f"Grados: {', '.join(grados_seleccionados)} | Focalización: {focalizacion} | "
                f"Registros movidos: {registros_movidos}"
            )
            return JsonResponse({
                'success': True,
                'registros_creados': registros_movidos,
                'mensaje': f'Se movieron {registros_movidos} registros a la sede {sede_destino}'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error en transferencia: {str(e)}'})

# Vista procesar_y_guardar_view eliminada - consolidada en procesar_listados_view

@login_required
def obtener_estadisticas_bd(request):
    """
    Vista AJAX para obtener estadísticas de la base de datos.

    Args:
        request: HttpRequest object

    Returns:
        JsonResponse: Estadísticas de la base de datos
    """
    try:
        

        estadisticas = PersistenceService.obtener_estadisticas_bd()

        return JsonResponse({
            'success': True,
            'estadisticas': estadisticas
        })

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "obtener_estadisticas_bd", str(e)
        )
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estadísticas de BD: {str(e)}'
        })

@login_required
def reportes_asistencia_view(request):
    """
    Vista para la interfaz de generación de reportes de asistencia, centrada en Programas.
    """
    # Contexto base
    context = {
        'meses_atencion': MESES_ATENCION,
        'programas': Programa.objects.all().order_by('municipio__nombre_municipio', 'programa'),
        'sedes': [],
        'focalizaciones_disponibles': [],
        'filtros_aplicados': {}
    }

    # Obtener el programa seleccionado desde los parámetros GET
    programa_id = request.GET.get('programa', '').strip()

    if programa_id:
        try:
            # Filtrar por el programa seleccionado
            programa_seleccionado = get_object_or_404(Programa, id=programa_id)
            context['filtros_aplicados']['programa'] = programa_seleccionado

            # 1. Obtener las sedes que tienen registros en ListadosFocalizacion para este programa
            sedes_con_registros_nombres = ListadosFocalizacion.objects \
                .filter(programa=programa_seleccionado) \
                .values_list('sede', flat=True).distinct()

            # Obtener los objetos SedesEducativas completos
            sedes = SedesEducativas.objects.filter(
                nombre_sede_educativa__in=sedes_con_registros_nombres
            ).select_related('codigo_ie__id_municipios').order_by('nombre_sede_educativa')
            
            context['sedes'] = sedes

            # 2. Obtener las focalizaciones disponibles solo para el programa seleccionado
            focalizaciones = ListadosFocalizacion.objects \
                .filter(programa=programa_seleccionado) \
                .values_list('focalizacion', flat=True).distinct().order_by('focalizacion')
            context['focalizaciones_disponibles'] = focalizaciones

        except Programa.DoesNotExist:
            # Si el ID del programa no es válido, no hacer nada y mostrar la página vacía
            pass

    return render(request, 'facturacion/reportes_asistencia.html', context)

@login_required
def generar_pdf_asistencia(request, programa_id, sede_cod_interprise, mes, focalizacion):
    """
    Vista para generar PDFs de asistencia.
    Delega la lógica principal al PDFAsistenciaService.
    """
    dias_str = request.GET.get('dias')
    dias_personalizados = None
    if dias_str:
        try:
            dias_personalizados = [int(d.strip()) for d in dias_str.split(',') if d.strip().isdigit()]
        except (ValueError, TypeError):
            return HttpResponse("Formato de días inválido. Deben ser números separados por comas.", status=400)

    RegistroActividad.registrar(
        request, 'facturacion', 'generar_pdf',
        f"Programa: {programa_id} | Sede: {sede_cod_interprise} | Mes: {mes} | Focalización: {focalizacion}"
    )
    return PDFAsistenciaService.generar_pdf_asistencia(programa_id, sede_cod_interprise, mes, focalizacion, dias_personalizados=dias_personalizados)

@login_required
def generar_zip_masivo_programa(request, programa_id, mes, focalizacion):
    """
    Vista para generar un ZIP masivo con todos los PDFs de asistencia 
    para todas las sedes de un Programa específico.
    """
    dias_str = request.GET.get('dias')
    dias_personalizados = None
    if dias_str:
        try:
            dias_personalizados = [int(d.strip()) for d in dias_str.split(',') if d.strip().isdigit()]
        except (ValueError, TypeError):
            return HttpResponse("Formato de días inválido. Deben ser números separados por comas.", status=400)
            
    RegistroActividad.registrar(
        request, 'facturacion', 'generar_zip_masivo',
        f"Programa: {programa_id} | Mes: {mes} | Focalización: {focalizacion}"
    )
    return PDFAsistenciaService.generar_zip_masivo_por_programa(programa_id, mes, focalizacion, dias_personalizados=dias_personalizados)

@login_required
def get_municipio_for_programa(request):
    """
    Vista AJAX para obtener el municipio de un programa.
    """
    programa_id = request.GET.get('programa_id')
    if not programa_id:
        return JsonResponse({'error': 'No se proporcionó el ID del programa'}, status=400)

    try:
        programa = Programa.objects.select_related('municipio').get(id=programa_id)
        municipio = {
            'id': programa.municipio.pk,
            'nombre': programa.municipio.nombre_municipio
        }
        return JsonResponse({'municipio': municipio})
    except Programa.DoesNotExist:
        return JsonResponse({'error': 'Programa no encontrado'}, status=404)

@login_required
def get_focalizaciones_for_programa(request):
    """
    Vista AJAX para obtener las focalizaciones de un programa.
    """
    programa_id = request.GET.get('programa_id')
    if not programa_id:
        return JsonResponse({'error': 'No se proporcionó el ID del programa'}, status=400)

    try:
        focalizaciones = ListadosFocalizacion.objects.filter(
            programa_id=programa_id
        ).values_list('focalizacion', flat=True).order_by('focalizacion').distinct()
        return JsonResponse({'focalizaciones': list(focalizaciones)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_sedes_for_programa_focalizacion(request):
    """
    Vista AJAX para obtener las sedes de un programa y focalización.
    """
    programa_id = request.GET.get('programa_id')
    focalizacion = request.GET.get('focalizacion')

    if not programa_id or not focalizacion:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)

    try:
        sedes = ListadosFocalizacion.objects.filter(programa_id=programa_id, focalizacion=focalizacion).values_list('sede', flat=True).distinct()
        return JsonResponse({'sedes': list(sedes)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def reemplazar_focalizacion_sedes(request):
    """
    Vista para reemplazar la focalización de una o varias sedes de un programa.
    """
    try:
        programa_id = request.POST.get('programa')
        focalizacion_origen = request.POST.get('focalizacion_origen')
        sedes = request.POST.getlist('sedes')
        focalizacion_nueva = request.POST.get('focalizacion_nueva')
        archivo_excel = request.FILES.get('archivo_excel')

        if not all([programa_id, focalizacion_origen, sedes, focalizacion_nueva, archivo_excel]):
            return JsonResponse({'success': False, 'error': 'Parámetros incompletos'}, status=400)

        with transaction.atomic():
            # 1. Eliminar registros existentes
            ListadosFocalizacion.objects.filter(
                programa_id=programa_id,
                focalizacion=focalizacion_origen,
                sede__in=sedes
            ).delete()

            # 2. Procesar el nuevo archivo
            programa = Programa.objects.get(id=programa_id)
            municipio = programa.municipio.nombre_municipio
            if "YUMBO" in municipio.upper():
                tipo_procesamiento = "yumbo"
            elif "BUGA" in municipio.upper():
                tipo_procesamiento = "buga"
            else:
                tipo_procesamiento = "nuevo"

            if tipo_procesamiento == "nuevo":
                resultado_procesamiento = procesamiento_service.procesar_excel_nuevo_formato(archivo_excel, focalizacion_nueva)
            else:
                resultado_procesamiento = procesamiento_service.procesar_excel_original(archivo_excel, focalizacion_nueva)

            if not resultado_procesamiento['success']:
                raise Exception(resultado_procesamiento['error'])

            df_para_guardar = resultado_procesamiento.get('dataframe')

            # 3. Validar que el archivo solo contenga las sedes seleccionadas
            sedes_en_archivo = df_para_guardar['SEDE'].unique().tolist()
            if not all(sede in sedes for sede in sedes_en_archivo):
                raise Exception("El archivo contiene sedes que no fueron seleccionadas para el reemplazo.")

            # 4. Guardar nuevos registros
            resultado_persistencia = PersistenceService.guardar_listados_focalizacion(
                df_para_guardar,
                programa_id=programa_id
            )

            if not resultado_persistencia['success']:
                raise Exception(resultado_persistencia['error'])

        RegistroActividad.registrar(
            request, 'facturacion', 'reemplazar_focalizacion',
            f"Programa ID: {programa_id} | Sedes: {', '.join(sedes)} | "
            f"{focalizacion_origen} → {focalizacion_nueva}"
        )
        return JsonResponse({'success': True, 'message': 'Focalización reemplazada exitosamente'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ===== NUEVAS VISTAS PARA GENERACIÓN PREDILIGENCIADA =====

@login_required
@require_http_methods(["GET"])
def api_get_sedes_completas(request):
    """
    API para obtener las sedes completas con su cod_interprise y nombre
    para un programa específico.

    Returns:
        JsonResponse con array de sedes: [{ nombre, cod_interprise }, ...]
    """
    try:
        programa_id = request.GET.get('programa_id')

        if not programa_id:
            return JsonResponse({
                'success': False,
                'error': 'Falta el parámetro programa_id'
            }, status=400)

        # Obtener programa
        try:
            programa_obj = Programa.objects.get(id=programa_id)
        except Programa.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Programa no encontrado'
            }, status=404)

        # Obtener sedes que tienen registros en ListadosFocalizacion para este programa
        sedes_con_registros_nombres = ListadosFocalizacion.objects.filter(
            programa=programa_obj
        ).values_list('sede', flat=True).distinct()

        # Obtener los objetos SedesEducativas completos
        sedes = SedesEducativas.objects.filter(
            nombre_sede_educativa__in=sedes_con_registros_nombres
        ).select_related('codigo_ie__id_municipios').order_by('nombre_sede_educativa')

        # Construir respuesta
        sedes_data = []
        for sede in sedes:
            sedes_data.append({
                'nombre': sede.nombre_sede_educativa,
                'cod_interprise': sede.cod_interprise
            })

        return JsonResponse({
            'success': True,
            'sedes': sedes_data
        })

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "api_get_sedes_completas", str(e)
        )
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener sedes: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_conteo_estudiantes_por_nivel(request):
    """
    API para obtener el conteo de estudiantes agrupados por nivel educativo
    para una sede, programa, focalización y complemento específicos.

    Returns:
        JsonResponse con:
        - total: Total de estudiantes
        - por_nivel: Dict con conteos por nivel (transicion, primaria, secundaria, media)
        - por_complemento: Dict con conteos por tipo de complemento
    """
    try:
        programa_id = request.GET.get('programa_id')
        sede_nombre = request.GET.get('sede_nombre')
        focalizacion = request.GET.get('focalizacion')
        complemento = request.GET.get('complemento')  # "CAP AM", "CAP PM", "Almuerzo JU", "Refuerzo"

        if not all([programa_id, sede_nombre, focalizacion, complemento]):
            return JsonResponse({
                'success': False,
                'error': 'Parámetros incompletos'
            }, status=400)

        # Obtener estudiantes de la sede con el complemento específico
        estudiantes = ListadosFocalizacion.objects.filter(
            programa_id=programa_id,
            sede=sede_nombre,
            focalizacion=focalizacion
        )

        # Filtrar por complemento activo
        estudiantes_con_complemento = []
        for est in estudiantes:
            if complemento in est.complementos_activos:
                estudiantes_con_complemento.append(est)

        # Agrupar por nivel educativo (5 niveles)
        conteo_por_nivel = {
            'preescolar': 0,
            'primaria_1_3': 0,
            'primaria_4_5': 0,
            'secundaria': 0,
            'media': 0
        }

        for est in estudiantes_con_complemento:
            nivel = _determinar_nivel_educativo(est.grado_grupos)
            if nivel in conteo_por_nivel:
                conteo_por_nivel[nivel] += 1

        return JsonResponse({
            'success': True,
            'total': len(estudiantes_con_complemento),
            'por_nivel': conteo_por_nivel,
            'complemento': complemento
        })

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "api_conteo_estudiantes_por_nivel", str(e)
        )
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener conteo: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def generar_pdf_asistencia_prediligenciada(request):
    """
    Genera un PDF de asistencia con marcas (X) prediligenciadas según
    la configuración de días proporcionada.

    Recibe un JSON con:
    - programa_id
    - sede_cod_interprise
    - sede_nombre
    - mes
    - focalizacion
    - complemento
    - dias: [{ dia: 3, total: 400, transicion: 80, primaria: 120, secundaria: 120, media: 80 }, ...]
    """
    try:
        data = json.loads(request.body)

        programa_id = data.get('programa_id')
        sede_cod_interprise = data.get('sede_cod_interprise')
        sede_nombre = data.get('sede_nombre')
        mes = data.get('mes')
        focalizacion = data.get('focalizacion')
        complemento = data.get('complemento')
        configuracion_dias = data.get('dias', [])

        if not all([programa_id, sede_cod_interprise, sede_nombre, mes, focalizacion, complemento]):
            return JsonResponse({
                'success': False,
                'error': 'Parámetros incompletos'
            }, status=400)

        FacturacionLogger.log_procesamiento_inicio(
            f"PDF_Prediligenciado_{sede_nombre}_{mes}",
            "generar_pdf_prediligenciado",
            focalizacion
        )

        # Obtener programa y sede
        programa_obj = get_object_or_404(Programa, id=programa_id)
        sede_obj = get_object_or_404(
            SedesEducativas.objects.select_related('codigo_ie__id_municipios'),
            cod_interprise=sede_cod_interprise
        )

        # Obtener estudiantes de la sede con el complemento específico
        estudiantes_sede = ListadosFocalizacion.objects.filter(
            programa=programa_obj,
            sede=sede_nombre,
            focalizacion=focalizacion
        ).order_by('apellido1', 'apellido2', 'nombre1')

        # Filtrar solo estudiantes con el complemento activo
        estudiantes_con_complemento = []
        for est in estudiantes_sede:
            if complemento in est.complementos_activos:
                estudiantes_con_complemento.append(est)

        if not estudiantes_con_complemento:
            return HttpResponse(
                f"No se encontraron estudiantes con el complemento '{complemento}' en la sede {sede_nombre}",
                status=404
            )

        # Ordenar por grado
        def clave_ordenamiento_grado(estudiante):
            grado_base_str = _extraer_grado_base(estudiante.grado_grupos)
            try:
                return int(grado_base_str)
            except (ValueError, TypeError):
                return float('inf')

        estudiantes_ordenados = sorted(estudiantes_con_complemento, key=clave_ordenamiento_grado)

        # Agrupar estudiantes por nivel educativo (5 niveles)
        estudiantes_por_nivel = {
            'preescolar': [],
            'primaria_1_3': [],
            'primaria_4_5': [],
            'secundaria': [],
            'media': []
        }

        for est in estudiantes_ordenados:
            nivel = _determinar_nivel_educativo(est.grado_grupos)
            if nivel in estudiantes_por_nivel:
                estudiantes_por_nivel[nivel].append(est)

        # Generar marcas de asistencia aleatorias según configuración
        marcas_asistencia = {}  # {id_listados: [dias_marcados]}

        for config_dia in configuracion_dias:
            dia = config_dia['dia']

            # Validar que no se marquen más estudiantes de los disponibles por nivel
            for nivel in ['preescolar', 'primaria_1_3', 'primaria_4_5', 'secundaria', 'media']:
                cantidad_solicitada = config_dia.get(nivel, 0)
                cantidad_disponible = len(estudiantes_por_nivel[nivel])

                if cantidad_solicitada > cantidad_disponible:
                    nivel_display = nivel.replace('_', ' ').title()
                    return JsonResponse({
                        'success': False,
                        'error': f'El día {dia} solicita {cantidad_solicitada} estudiantes de {nivel_display}, pero solo hay {cantidad_disponible} disponibles.'
                    }, status=400)

            # Seleccionar aleatoriamente estudiantes por nivel para este día
            seleccionados_dia = []

            if config_dia.get('preescolar', 0) > 0:
                seleccionados_dia += random.sample(
                    estudiantes_por_nivel['preescolar'],
                    config_dia['preescolar']
                )

            if config_dia.get('primaria_1_3', 0) > 0:
                seleccionados_dia += random.sample(
                    estudiantes_por_nivel['primaria_1_3'],
                    config_dia['primaria_1_3']
                )

            if config_dia.get('primaria_4_5', 0) > 0:
                seleccionados_dia += random.sample(
                    estudiantes_por_nivel['primaria_4_5'],
                    config_dia['primaria_4_5']
                )

            if config_dia.get('secundaria', 0) > 0:
                seleccionados_dia += random.sample(
                    estudiantes_por_nivel['secundaria'],
                    config_dia['secundaria']
                )

            if config_dia.get('media', 0) > 0:
                seleccionados_dia += random.sample(
                    estudiantes_por_nivel['media'],
                    config_dia['media']
                )

            # Registrar marcas para este día
            for est in seleccionados_dia:
                if est.id_listados not in marcas_asistencia:
                    marcas_asistencia[est.id_listados] = []
                marcas_asistencia[est.id_listados].append(dia)

        # Preparar datos del encabezado
        nombre_municipio_etc = programa_obj.municipio.nombre_municipio
        dane_municipio = programa_obj.municipio.codigo_municipio

        try:
            departamento_obj = PrincipalDepartamento.objects.get(
                codigo_departamento=programa_obj.municipio.codigo_departamento
            )
            dane_departamento = departamento_obj.codigo_departamento
        except PrincipalDepartamento.DoesNotExist:
            departamento_obj = None
            dane_departamento = 'N/A'

        try:
            sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=sede_nombre)
            dane_ie = sede_info_dane.cod_dane
            es_industrializado = sede_info_dane.industrializado == 'VERDADERO'
        except SedesEducativas.DoesNotExist:
            dane_ie = 'DANE no encontrado'
            es_industrializado = False

        ano = estudiantes_ordenados[0].ano if estudiantes_ordenados else datetime.now().year

        # Mapear complemento a código
        if es_industrializado:
            mapeo_codigos = {
                "CAP AM": "CAJMRI",
                "CAP PM": "CAJTRI",
                "Almuerzo JU": "ALMUERZO",
                "Refuerzo": "RCRI"
            }
        else:
            mapeo_codigos = {
                "CAP AM": "CAJMPS",
                "CAP PM": "CAJTPS",
                "Almuerzo JU": "ALMUERZO",
                "Refuerzo": "RCPS"
            }

        codigo_complemento = mapeo_codigos.get(complemento, complemento)

        ruta_logo_final = None
        if programa_obj and programa_obj.imagen:
            try:
                ruta_logo_final = programa_obj.imagen.path
            except Exception:
                ruta_logo_final = programa_obj.imagen.url

        institucion_con_focalizacion = f"{focalizacion} {sede_nombre}"

        # Extraer solo los días configurados
        dias_configurados = [config['dia'] for config in configuracion_dias]

        datos_encabezado = {
            'departamento': str(departamento_obj.nombre_departamento) if departamento_obj else 'N/A',
            'institucion': str(institucion_con_focalizacion),
            'municipio': str(nombre_municipio_etc),
            'dane_ie': str(dane_ie),
            'operador': str(programa_obj.programa),
            'contrato': str(programa_obj.contrato),
            'mes': str(mes).upper(),
            'ano': str(ano),
            'dane_departamento': str(dane_departamento),
            'dane_municipio': str(dane_municipio),
            'codigo_complemento': str(codigo_complemento),
            'ruta_logo': ruta_logo_final,
            'dias_personalizados': sorted(dias_configurados),
            'marcas_asistencia': marcas_asistencia  # Nueva clave para las marcas
        }

        # Generar PDF
        pdf_buffer = BytesIO()
        crear_formato_asistencia(pdf_buffer, datos_encabezado, estudiantes_ordenados)
        pdf_buffer.seek(0)

        # Retornar PDF como respuesta
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        nombre_archivo = f"Asistencia_Prediligenciada_{sede_nombre.replace(' ', '_')}_{codigo_complemento}_{mes}_{ano}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

        RegistroActividad.registrar(
            request, 'facturacion', 'pdf_prediligenciado',
            f"Sede: {sede_nombre} | Mes: {mes} | Focalización: {focalizacion} | "
            f"Complemento: {complemento} | Días configurados: {len(configuracion_dias)}"
        )
        return response

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "generar_pdf_asistencia_prediligenciada", str(e)
        )
        return HttpResponse(f"Error al generar el PDF prediligenciado: {str(e)}", status=500)


@login_required
def api_obtener_sedes_con_grado_especifico(request):
    """
    API para obtener sedes que tienen un grado específico.

    Usado en el modal de transferencia específica (desde tabla).
    Retorna solo las sedes que tienen registros para un programa, grado y focalización específicos.
    """
    from django.db.models import Count, Func, CharField

    try:
        programa_id = request.GET.get('programa_id')
        grado = request.GET.get('grado')
        focalizacion = request.GET.get('focalizacion')

        if not all([programa_id, grado, focalizacion]):
            return JsonResponse({
                'success': False,
                'error': 'Parámetros incompletos. Se requiere programa_id, grado y focalizacion'
            })

        # Función personalizada para extraer el grado base usando regex de PostgreSQL
        class ExtractGradoBase(Func):
            """Extrae el grado base (todo antes del último guión) usando regex de PostgreSQL"""
            function = 'REGEXP_REPLACE'
            template = "%(function)s(%(expressions)s, '-[^-]*$', '', 'g')"

            def __init__(self, expression, **extra):
                super().__init__(expression, output_field=CharField(), **extra)

        # Obtener sedes que tienen este grado específico
        sedes_query = ListadosFocalizacion.objects.filter(
            programa_id=programa_id,
            focalizacion=focalizacion
        ).annotate(
            grado_base=ExtractGradoBase('grado_grupos')
        ).filter(
            grado_base=grado
        ).values('sede').annotate(
            total_estudiantes=Count('id_listados')
        ).order_by('sede')

        sedes_con_grado = []
        for sede_data in sedes_query:
            sedes_con_grado.append({
                'sede': sede_data['sede'],
                'total_estudiantes': sede_data['total_estudiantes']
            })

        return JsonResponse({
            'success': True,
            'sedes': sedes_con_grado,
            'total_sedes': len(sedes_con_grado)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener sedes: {str(e)}'
        })
