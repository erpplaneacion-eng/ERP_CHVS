"""
Vista única consolidada para el módulo de facturación.
Permite visualizar y guardar datos en una sola interfaz.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import SimpleUploadedFile
import base64
import pandas as pd
from io import StringIO

from .services import ProcesamientoService, ValidacionService, EstadisticasService
from .config import ProcesamientoConfig, FOCALIZACIONES_DISPONIBLES
from .logging_config import FacturacionLogger

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

                    # Debug: Verificar DataFrame reconstruido
                    print(f"DEBUG: DataFrame reconstruido - Shape: {df_procesado.shape}")
                    print(f"DEBUG: Columnas: {list(df_procesado.columns)}")
                    print(f"DEBUG: Primeras 3 filas:\n{df_procesado.head(3)}")

                    # Guardar directamente en BD usando el DataFrame procesado
                    from .persistence_service import PersistenceService
                    print(f"DEBUG: Llamando a PersistenceService.guardar_listados_focalizacion")
                    resultado_persistencia = PersistenceService.guardar_listados_focalizacion(df_procesado)

                    # Debug: Resultado de la persistencia
                    print(f"DEBUG: Resultado persistencia: {resultado_persistencia}")

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
