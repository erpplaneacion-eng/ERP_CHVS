"""
Vistas refactorizadas para el módulo de facturación.
Utiliza la nueva arquitectura modular.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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
def generar_listados_view(request):
    """
    Vista para generar listados a partir de archivos Excel.
    Maneja tanto el formato original como el nuevo formato.
    
    Args:
        request: HttpRequest object
    
    Returns:
        HttpResponse: Página de generación de listados
    """
    # Inicializar variables del contexto
    contexto = {
        'dataframe_html': None,
        'verified_message': None,
        'invalid_sedes': [],
        'coincidencias_parciales': [],
        'coincidencias_genericas': [],
        'agrupacion_sedes': [],
        # Variables para el nuevo procesamiento
        'dataframe_nuevo_html': None,
        'verified_message_nuevo': None,
        'invalid_sedes_nuevo': [],
        'coincidencias_parciales_nuevo': [],
        'coincidencias_genericas_nuevo': [],
        'agrupacion_sedes_nuevo': [],
        'focalizaciones': FOCALIZACIONES_DISPONIBLES
    }
    
    try:
        if request.method == 'POST' and request.FILES.get('archivo_excel'):
            archivo = request.FILES['archivo_excel']
            focalizacion = request.POST.get('focalizacion', '')
            tipo_procesamiento = request.POST.get('tipo_procesamiento', ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL)
            
            # Validar focalización
            if not focalizacion or focalizacion not in FOCALIZACIONES_DISPONIBLES:
                contexto['error'] = "Focalización inválida. Seleccione una focalización válida."
                return render(request, 'facturacion/generar_listados.html', contexto)
            
            # Procesar archivo según el tipo
            if tipo_procesamiento == ProcesamientoConfig.TIPO_PROCESAMIENTO_NUEVO:
                resultado = procesamiento_service.procesar_excel_nuevo_formato(archivo, focalizacion)
                contexto = _actualizar_contexto_nuevo_formato(contexto, resultado)
            else:
                resultado = procesamiento_service.procesar_excel_original(archivo, focalizacion)
                contexto = _actualizar_contexto_original_formato(contexto, resultado)
        
        return render(request, 'facturacion/generar_listados.html', contexto)
        
    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "generar_listados_view", str(e)
        )
        contexto['error'] = f"Error al procesar la solicitud: {str(e)}"
        return render(request, 'facturacion/generar_listados.html', contexto)

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

def _actualizar_contexto_nuevo_formato(contexto: dict, resultado: dict) -> dict:
    """
    Actualiza el contexto con los resultados del nuevo formato.
    
    Args:
        contexto: Contexto actual
        resultado: Resultado del procesamiento
    
    Returns:
        dict: Contexto actualizado
    """
    if resultado['success']:
        contexto.update({
            'dataframe_nuevo_html': resultado['dataframe_html'],
            'verified_message_nuevo': resultado['verified_message'],
            'invalid_sedes_nuevo': resultado['invalid_sedes'],
            'coincidencias_parciales_nuevo': resultado['coincidencias_parciales'],
            'coincidencias_genericas_nuevo': resultado['coincidencias_genericas'],
            'agrupacion_sedes_nuevo': resultado['agrupacion_sedes']
        })
    else:
        contexto.update({
            'dataframe_nuevo_html': resultado['dataframe_html'],
            'verified_message_nuevo': None,
            'agrupacion_sedes_nuevo': []
        })
    
    return contexto

def _actualizar_contexto_original_formato(contexto: dict, resultado: dict) -> dict:
    """
    Actualiza el contexto con los resultados del formato original.
    
    Args:
        contexto: Contexto actual
        resultado: Resultado del procesamiento
    
    Returns:
        dict: Contexto actualizado
    """
    if resultado['success']:
        contexto.update({
            'dataframe_html': resultado['dataframe_html'],
            'verified_message': resultado['verified_message'],
            'invalid_sedes': resultado['invalid_sedes'],
            'coincidencias_parciales': resultado['coincidencias_parciales'],
            'coincidencias_genericas': resultado['coincidencias_genericas'],
            'agrupacion_sedes': resultado['agrupacion_sedes']
        })
    else:
        contexto.update({
            'dataframe_html': resultado['dataframe_html'],
            'verified_message': None,
            'agrupacion_sedes': []
        })
    
    return contexto

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

@login_required
def procesar_y_guardar_view(request):
    """
    Vista para procesar archivos Excel y guardarlos en la base de datos.
    Combina el procesamiento con la persistencia.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página de procesamiento con persistencia
    """
    # Inicializar variables del contexto
    contexto = {
        'dataframe_html': None,
        'verified_message': None,
        'invalid_sedes': [],
        'coincidencias_parciales': [],
        'coincidencias_genericas': [],
        'agrupacion_sedes': [],
        # Variables para el nuevo procesamiento
        'dataframe_nuevo_html': None,
        'verified_message_nuevo': None,
        'invalid_sedes_nuevo': [],
        'coincidencias_parciales_nuevo': [],
        'coincidencias_genericas_nuevo': [],
        'agrupacion_sedes_nuevo': [],
        'focalizaciones': FOCALIZACIONES_DISPONIBLES,
        # Variables de persistencia
        'registros_guardados_bd': 0,
        'advertencia_bd': None
    }

    try:
        if request.method == 'POST' and request.FILES.get('archivo_excel'):
            archivo = request.FILES['archivo_excel']
            focalizacion = request.POST.get('focalizacion', '')
            tipo_procesamiento = request.POST.get('tipo_procesamiento', ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL)
            guardar_en_bd = request.POST.get('guardar_en_bd', 'true').lower() == 'true'

            # Validar focalización
            if not focalizacion or focalizacion not in FOCALIZACIONES_DISPONIBLES:
                contexto['error'] = "Focalización inválida. Seleccione una focalización válida."
                return render(request, 'facturacion/procesar_y_guardar.html', contexto)

            # Procesar archivo con persistencia
            resultado = procesamiento_service.procesar_y_guardar_excel(
                archivo,
                focalizacion,
                tipo_procesamiento,
                guardar_en_bd
            )

            # Actualizar contexto según el tipo de procesamiento
            if tipo_procesamiento == ProcesamientoConfig.TIPO_PROCESAMIENTO_NUEVO:
                contexto = _actualizar_contexto_nuevo_formato(contexto, resultado)
            else:
                contexto = _actualizar_contexto_original_formato(contexto, resultado)

            # Agregar información de persistencia
            contexto['registros_guardados_bd'] = resultado.get('registros_guardados_bd', 0)
            contexto['advertencia_bd'] = resultado.get('advertencia_bd')

            if resultado.get('persistencia'):
                contexto['persistencia_detalle'] = resultado['persistencia']

        return render(request, 'facturacion/procesar_y_guardar.html', contexto)

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(
            "procesar_y_guardar_view", str(e)
        )
        contexto['error'] = f"Error al procesar la solicitud: {str(e)}"
        return render(request, 'facturacion/procesar_y_guardar.html', contexto)

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
