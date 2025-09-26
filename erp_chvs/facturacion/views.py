"""
Vista única consolidada para el módulo de facturación.
Permite visualizar y guardar datos en una sola interfaz.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.db import IntegrityError
import base64
import pandas as pd
from io import StringIO
import json

from .models import ListadosFocalizacion
from .services import ProcesamientoService, ValidacionService, EstadisticasService
from .config import ProcesamientoConfig, FOCALIZACIONES_DISPONIBLES
from .logging_config import FacturacionLogger
from planeacion.models import SedesEducativas

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
    contexto = {
        # Configuración general
        'focalizaciones': FOCALIZACIONES_DISPONIBLES,

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
                tipo_procesamiento = request.POST.get('tipo_procesamiento', ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL)

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
                else:
                    resultado = procesamiento_service.procesar_excel_original(archivo, focalizacion)

                # Actualizar contexto con los resultados de la visualización
                if resultado['success']:
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
                    from .persistence_service import PersistenceService
                    resultado_persistencia = PersistenceService.guardar_listados_focalizacion(df_procesado)

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
                    FacturacionLogger.log_procesamiento_error(
                        archivo_name, "DataFrame no encontrado en sesión, reprocesando..."
                    )

                    # Recrear archivo y reprocesar
                    archivo_contenido_b64 = datos_etapa_1['archivo_contenido_b64']
                    archivo_contenido = base64.b64decode(archivo_contenido_b64)
                    archivo_recreado = SimpleUploadedFile(
                        archivo_name,
                        archivo_contenido,
                        content_type=datos_etapa_1['archivo_content_type']
                    )

                    resultado = procesamiento_service.procesar_y_guardar_excel(
                        archivo_recreado,
                        focalizacion,
                        tipo_procesamiento,
                        guardar_en_bd=True
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
        tipo_procesamiento = request.POST.get('tipo_procesamiento', ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL)
        
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
    etc_filter = request.GET.get('etc', '').strip()
    sede_filter = request.GET.get('sede', '').strip()

    # Query base
    listados = ListadosFocalizacion.objects.all().order_by('-fecha_creacion')

    # Aplicar filtros
    if etc_filter:
        listados = listados.filter(etc__icontains=etc_filter)

    if sede_filter:
        listados = listados.filter(sede__icontains=sede_filter)

    # Paginación
    paginator = Paginator(listados, 15)  # 20 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener valores únicos para filtros
    etc_values = ListadosFocalizacion.objects.values_list('etc', flat=True).distinct().order_by('etc')
    sede_values = ListadosFocalizacion.objects.values_list('sede', flat=True).distinct().order_by('sede')

    # Obtener sedes faltantes (solo si hay filtro ETC aplicado)
    sedes_faltantes = []
    if etc_filter:
        # Todas las sedes del ETC seleccionado
        todas_sedes_etc = SedesEducativas.objects.filter(
            codigo_ie__id_municipios__nombre_municipio__icontains=etc_filter
        ).select_related('codigo_ie').values_list('nombre_sede_educativa', flat=True).distinct()

        # Sedes que ya tienen registros en listados_focalizacion
        sedes_con_registros = listados.values_list('sede', flat=True).distinct()

        # Sedes faltantes = todas las sedes del ETC - sedes que ya tienen registros
        sedes_faltantes = [sede for sede in todas_sedes_etc if sede not in sedes_con_registros]

    context = {
        'listados': page_obj,
        'total_listados': listados.count(),
        'etc_values': etc_values,
        'sede_values': sede_values,
        'filtros_aplicados': {
            'etc': etc_filter,
            'sede': sede_filter,
        },
        'sedes_faltantes': sedes_faltantes,
        'total_sedes_faltantes': len(sedes_faltantes),
    }

    return render(request, 'facturacion/lista_listados.html', context)

# ===== APIs PARA GESTIÓN DE LISTADOS FOCALIZACIÓN =====

@login_required
@csrf_exempt
def api_listados(request):
    """API para manejar listados de focalización via AJAX"""
    if request.method == 'GET':
        listados = ListadosFocalizacion.objects.all().order_by('-fecha_creacion').values(
            'id_listados', 'ano', 'etc', 'institucion', 'sede', 'tipodoc', 'doc',
            'nombre1', 'apellido1', 'fecha_nacimiento', 'edad', 'genero',
            'grado_grupos', 'focalizacion', 'fecha_creacion'
        )
        return JsonResponse({'listados': list(listados)})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Crear nuevo registro
            listado = ListadosFocalizacion.objects.create(
                id_listados=data['id_listados'],
                ano=data.get('ano', 2025),
                etc=data.get('etc', ''),
                institucion=data.get('institucion', ''),
                sede=data.get('sede', ''),
                tipodoc=data.get('tipodoc', ''),
                doc=data.get('doc', ''),
                apellido1=data.get('apellido1'),
                apellido2=data.get('apellido2'),
                nombre1=data.get('nombre1', ''),
                nombre2=data.get('nombre2'),
                fecha_nacimiento=data.get('fecha_nacimiento'),
                edad=data.get('edad', 0),
                etnia=data.get('etnia'),
                genero=data.get('genero', ''),
                grado_grupos=data.get('grado_grupos', ''),
                complemento_alimentario_preparado_am=data.get('complemento_alimentario_preparado_am'),
                complemento_alimentario_preparado_pm=data.get('complemento_alimentario_preparado_pm'),
                almuerzo_jornada_unica=data.get('almuerzo_jornada_unica'),
                refuerzo_complemento_am_pm=data.get('refuerzo_complemento_am_pm'),
                focalizacion=data.get('focalizacion', '')
            )

            return JsonResponse({
                'success': True,
                'id_listado': listado.id_listados,
                'message': 'Registro creado exitosamente'
            })

        except IntegrityError as e:
            return JsonResponse({'success': False, 'error': f'ID ya existe: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al crear registro: {str(e)}'})

@login_required
@csrf_exempt
def api_listado_detail(request, id_listado):
    """API para manejar un listado específico"""
    listado = get_object_or_404(ListadosFocalizacion, id_listados=id_listado)

    if request.method == 'GET':
        return JsonResponse({
            'id_listados': listado.id_listados,
            'ano': listado.ano,
            'etc': listado.etc,
            'institucion': listado.institucion,
            'sede': listado.sede,
            'tipodoc': listado.tipodoc,
            'doc': listado.doc,
            'apellido1': listado.apellido1,
            'apellido2': listado.apellido2,
            'nombre1': listado.nombre1,
            'nombre2': listado.nombre2,
            'fecha_nacimiento': listado.fecha_nacimiento,
            'edad': listado.edad,
            'etnia': listado.etnia,
            'genero': listado.genero,
            'grado_grupos': listado.grado_grupos,
            'complemento_alimentario_preparado_am': listado.complemento_alimentario_preparado_am,
            'complemento_alimentario_preparado_pm': listado.complemento_alimentario_preparado_pm,
            'almuerzo_jornada_unica': listado.almuerzo_jornada_unica,
            'refuerzo_complemento_am_pm': listado.refuerzo_complemento_am_pm,
            'focalizacion': listado.focalizacion,
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)

            # Actualizar campos permitidos
            campos_actualizables = [
                'etc', 'institucion', 'sede', 'tipodoc', 'apellido1', 'apellido2',
                'nombre1', 'nombre2', 'fecha_nacimiento', 'edad', 'etnia', 'genero',
                'grado_grupos', 'complemento_alimentario_preparado_am',
                'complemento_alimentario_preparado_pm', 'almuerzo_jornada_unica',
                'refuerzo_complemento_am_pm'
            ]

            for campo in campos_actualizables:
                if campo in data:
                    setattr(listado, campo, data[campo])

            listado.save()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al actualizar: {str(e)}'})

    elif request.method == 'DELETE':
        try:
            listado.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'})

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
        from .persistence_service import PersistenceService

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
