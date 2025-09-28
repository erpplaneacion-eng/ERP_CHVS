"""
Vista única consolidada para el módulo de facturación.
Permite visualizar y guardar datos en una sola interfaz.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.db import IntegrityError
import base64
import pandas as pd
from io import StringIO, BytesIO
import json
import zipfile
import os
from django.conf import settings

from .models import ListadosFocalizacion
from .services import ProcesamientoService, ValidacionService, EstadisticasService
from .config import ProcesamientoConfig, FOCALIZACIONES_DISPONIBLES, MESES_ATENCION
from .logging_config import FacturacionLogger
from planeacion.models import SedesEducativas, Programa
from .persistence_service import PersistenceService
from .pdf_generator import crear_formato_asistencia

# Inicializar servicios
procesamiento_service = ProcesamientoService()
validacion_service = ValidacionService()
estadisticas_service = EstadisticasService()

def _mapear_grado_a_nivel_manual(grado):
    """
    Mapea manualmente grados que no están en la tabla NivelGradoEscolar
    a sus niveles escolares correspondientes.

    Args:
        grado: String del grado (ej: "-1", "-2", "0")

    Returns:
        str: Nombre del nivel escolar o None si no se puede mapear
    """
    try:
        grado_num = float(grado)  # Convertir a número para comparación

        # Reglas de mapeo conocidas
        if grado_num < 0:
            return "Preescolar"  # Grados negativos como -1, -2 son Preescolar
        elif grado_num == 0:
            return "Preescolar"  # Grado 0 también es Preescolar
        elif 1 <= grado_num <= 5:
            return "Primaria"
        elif 6 <= grado_num <= 9:
            return "Secundaria"
        elif 10 <= grado_num <= 11:
            return "Media"
        else:
            return None  # No se puede mapear

    except (ValueError, TypeError):
        # Si no se puede convertir a número, no se puede mapear
        return None

def _extraer_grado_base(grado_grupos):
    """
    Extrae el grado base de un valor grado_grupos considerando diferentes formatos.

    Args:
        grado_grupos: String con el valor del grado (ej: "3-A", "-1", "2-201", "-1--101", "5")

    Returns:
        str: Grado base extraído o None si no es válido

    Ejemplos:
        "3-A" → "3"
        "-1" → "-1"
        "2-201" → "2"
        "-1--101" → "-1"  (grado negativo con grupo especial)
        "-2--201" → "-2"  (grado negativo con grupo especial)
        "5" → "5"
        "" → None
        None → None
    """
    if not grado_grupos or grado_grupos == '':
        return None

    grado_str = str(grado_grupos).strip()

    # Caso especial: grados negativos con grupos (ej: "-1--101", "-2--201")
    if grado_str.startswith('-') and '--' in grado_str:
        # Extraer solo la parte del grado (antes del "--")
        grado_base = grado_str.split('--')[0]
        return grado_base

    # Caso especial: si comienza con '-', devolver el valor completo (ej: "-1", "-2")
    if grado_str.startswith('-'):
        return grado_str

    # Caso normal: dividir por '-' y tomar la primera parte
    if '-' in grado_str:
        parte_grado = grado_str.split('-')[0]
        # Validar que la parte del grado no esté vacía
        if parte_grado:
            return parte_grado

    # Si no tiene '-', devolver el valor completo
    return grado_str

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


    # Obtener sedes faltantes y grados disponibles (solo si hay filtro ETC aplicado)
    sedes_faltantes = []
    grados_disponibles = []
    if etc_filter:
        # Optimización: Obtener sedes válidas del catálogo primero (más eficiente)
        sedes_catalogo_etc = set(
            SedesEducativas.objects.filter(
                codigo_ie__id_municipios__nombre_municipio__icontains=etc_filter
            ).values_list('nombre_sede_educativa', flat=True).distinct()
        )

        # Sedes que tienen registros en listados_focalizacion para este ETC
        sedes_con_registros_etc = set(
            ListadosFocalizacion.objects.filter(
                etc__icontains=etc_filter
            ).values_list('sede', flat=True).distinct()
        )

        # Sedes faltantes = sedes del catálogo oficial que NO tienen registros
        # (sedes que deberían tener registros pero aún no han sido procesadas)
        sedes_faltantes = list(sedes_catalogo_etc - sedes_con_registros_etc)

        if sedes_con_registros_etc:
            from principal.models import NivelGradoEscolar

            # Obtener sedes disponibles con sus grados
            sedes_disponibles = []
            for sede in sedes_con_registros_etc:
                # Obtener grados únicos de esta sede
                registros_sede = ListadosFocalizacion.objects.filter(
                    etc__icontains=etc_filter,
                    sede=sede
                ).values('grado_grupos').distinct()

                grados_sede = set()
                for registro in registros_sede:
                    if registro['grado_grupos']:
                        grado_base = _extraer_grado_base(str(registro['grado_grupos']))
                        if grado_base:  # Solo agregar si no es vacío
                            grados_sede.add(grado_base)


                # Mapear grados a niveles escolares
                grados_mapeados = {}
                grados_sin_nivel = []  # Grados que no están en la tabla NivelGradoEscolar

                for grado in grados_sede:
                    try:
                        nivel = NivelGradoEscolar.objects.filter(grados_sedes=grado).first()
                        if nivel:
                            nivel_nombre = nivel.nivel_escolar_uapa
                            if nivel_nombre not in grados_mapeados:
                                grados_mapeados[nivel_nombre] = []
                            grados_mapeados[nivel_nombre].append({
                                'grado': grado,
                                'descripcion': f"{nivel.grados_sedes} - {nivel.nivel_escolar_uapa}"
                            })
                        else:
                            # Grado no encontrado en tabla - intentar mapeo manual por reglas conocidas
                            nivel_manual = _mapear_grado_a_nivel_manual(grado)
                            if nivel_manual:
                                if nivel_manual not in grados_mapeados:
                                    grados_mapeados[nivel_manual] = []
                                grados_mapeados[nivel_manual].append({
                                    'grado': grado,
                                    'descripcion': f"Grado {grado} - {nivel_manual} (mapeo manual)"
                                })
                            else:
                                # Último recurso: grados especiales
                                grados_sin_nivel.append({
                                    'grado': grado,
                                    'descripcion': f"Grado {grado} (sin nivel asignado)"
                                })
                    except Exception as e:
                        # En caso de error, agregar a lista especial
                        grados_sin_nivel.append({
                            'grado': grado,
                            'descripcion': f"Grado {grado} (error en mapeo: {str(e)})"
                        })

                # Convertir a lista ordenada por nivel
                grados_ordenados = []

                # Agregar grados con nivel asignado
                for nivel, grados in sorted(grados_mapeados.items()):
                    grados_ordenados.append({
                        'nivel': nivel,
                        'grados': sorted(grados, key=lambda x: x['grado'])
                    })

                # Agregar grados que no pudieron mapearse en una categoría especial (solo como último recurso)
                if grados_sin_nivel:
                    grados_ordenados.append({
                        'nivel': 'Grados Especiales',
                        'grados': sorted(grados_sin_nivel, key=lambda x: x['grado'])
                    })

                sedes_disponibles.append({
                    'sede': sede,
                    'grados': grados_ordenados,
                    'total_grados': len(grados_sede)
                })

            grados_disponibles = sedes_disponibles

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
        'grados_disponibles': grados_disponibles,
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

@login_required
@csrf_exempt
def api_transferir_grados(request):
    """API para transferir grados de una sede a otra"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sede_destino = data.get('sede_destino')
            sede_origen = data.get('sede_origen')
            grados_seleccionados = data.get('grados_seleccionados', [])
            etc = data.get('etc')

            if not sede_destino or not sede_origen or not grados_seleccionados or not etc:
                return JsonResponse({'success': False, 'error': 'Parámetros incompletos'})

            # Obtener registros fuente (de la sede origen específica con esos grados)
            registros_fuente = ListadosFocalizacion.objects.filter(
                etc__icontains=etc,
                sede=sede_origen
            )

            # Filtrar por grados seleccionados
            registros_a_copiar = []
            for registro in registros_fuente:
                if registro.grado_grupos:
                    grado_base = _extraer_grado_base(str(registro.grado_grupos))
                    if grado_base and grado_base in grados_seleccionados:
                        registros_a_copiar.append(registro)

            # Crear copias con la sede destino
            registros_creados = 0
            for registro in registros_a_copiar:
                try:
                    # Generar nuevo ID único para el registro copiado
                    id_nuevo = PersistenceService.generar_id_listado_unico(registro)

                    # Crear copia con sede destino
                    ListadosFocalizacion.objects.create(
                        id_listados=id_nuevo,
                        ano=registro.ano,
                        etc=registro.etc,
                        institucion=registro.institucion,
                        sede=sede_destino,  # ← Cambiar sede
                        tipodoc=registro.tipodoc,
                        doc=registro.doc,
                        apellido1=registro.apellido1,
                        apellido2=registro.apellido2,
                        nombre1=registro.nombre1,
                        nombre2=registro.nombre2,
                        fecha_nacimiento=registro.fecha_nacimiento,
                        edad=registro.edad,
                        etnia=registro.etnia,
                        genero=registro.genero,
                        grado_grupos=registro.grado_grupos,
                        complemento_alimentario_preparado_am=registro.complemento_alimentario_preparado_am,
                        complemento_alimentario_preparado_pm=registro.complemento_alimentario_preparado_pm,
                        almuerzo_jornada_unica=registro.almuerzo_jornada_unica,
                        refuerzo_complemento_am_pm=registro.refuerzo_complemento_am_pm,
                        focalizacion=registro.focalizacion
                    )
                    registros_creados += 1
                except Exception as e:
                    continue  # Continuar con el siguiente registro

            return JsonResponse({
                'success': True,
                'registros_creados': registros_creados,
                'mensaje': f'Se transfirieron {registros_creados} registros a la sede {sede_destino}'
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
    Vista para la nueva interfaz de generación de reportes de asistencia.
    """
    context = {
        'meses_atencion': MESES_ATENCION,
    }
    
    # Obtener focalizaciones únicas de la base de datos
    focalizaciones_disponibles = ListadosFocalizacion.objects.values_list('focalizacion', flat=True).distinct().order_by('focalizacion')
    context['focalizaciones_disponibles'] = focalizaciones_disponibles
    
    # Obtener todos los municipios que tienen sedes
    municipios_con_sedes = SedesEducativas.objects.select_related('codigo_ie__id_municipios') \
                                                  .values_list('codigo_ie__id_municipios__nombre_municipio', flat=True) \
                                                  .distinct().order_by('codigo_ie__id_municipios__nombre_municipio')
    context['etc_values'] = municipios_con_sedes

    etc_filter = request.GET.get('etc', '').strip()
    if etc_filter:
        sedes = SedesEducativas.objects.filter(
            codigo_ie__id_municipios__nombre_municipio__icontains=etc_filter
        ).order_by('nombre_sede_educativa')
        context['sedes'] = sedes
        context['filtros_aplicados'] = {'etc': etc_filter}

    return render(request, 'facturacion/reportes_asistencia.html', context)

@login_required
def generar_pdf_asistencia(request, sede_cod_interprise, mes, focalizacion):
    """
    Genera los PDFs de asistencia para una sede, mes y focalización específicos.
    Crea un archivo ZIP con un PDF por cada tipo de complemento.
    """
    try:
        # Este objeto se usa principalmente para obtener el nombre de la sede para el filtro inicial.
        # Buscar sede
        sede_obj = get_object_or_404(SedesEducativas.objects.select_related(
            'codigo_ie__id_municipios'
        ), cod_interprise=sede_cod_interprise)

        # Obtener departamento usando la relación correcta según README.md
        municipio_obj = sede_obj.codigo_ie.id_municipios
        departamento_codigo = municipio_obj.codigo_departamento

        try:
            from principal.models import PrincipalDepartamento
            departamento_obj = PrincipalDepartamento.objects.get(codigo_departamento=departamento_codigo)
        except PrincipalDepartamento.DoesNotExist:
            departamento_obj = None

        # Buscar programa
        programa_obj = Programa.objects.filter(
            municipio=sede_obj.codigo_ie.id_municipios,
            estado='activo'  # Asegurar que solo se tome el contrato activo
        ).first()

        # Buscar estudiantes
        estudiantes_sede = ListadosFocalizacion.objects.filter(
            sede=sede_obj.nombre_sede_educativa,
            focalizacion=focalizacion
        ).order_by('apellido1', 'apellido2', 'nombre1')

        if not estudiantes_sede.exists():
            return HttpResponse(f"No se encontraron estudiantes para la sede {sede_obj.nombre_sede_educativa} con la focalización '{focalizacion}'.", status=404)

        # --- INICIO DE CAMBIOS SOLICITADOS ---
        # 1. La institución ahora proviene directamente del campo 'sede' de los datos de focalización.
        primer_estudiante = estudiantes_sede.first()
        nombre_sede_focalizacion = primer_estudiante.sede

        # 2. El DANE se busca en SedesEducativas usando el nombre de la sede de los datos de focalización.
        try:
            sede_info_dane = SedesEducativas.objects.get(nombre_sede_educativa=nombre_sede_focalizacion)
            dane_ie = sede_info_dane.cod_dane
        except SedesEducativas.DoesNotExist:
            dane_ie = 'DANE no encontrado'
        # --- FIN DE CAMBIOS SOLICITADOS ---

        # Obtener el año del primer estudiante (asumimos que todos tienen el mismo año para una focalización)
        ano = primer_estudiante.ano
        if not ano:
            return HttpResponse(f"No se pudo determinar el año para la focalización '{focalizacion}'.", status=404)
             
        # Mapeo de complementos a códigos
        mapeo_codigos = {
            "CAP AM": "CAJMPS", "CAP PM": "CAJTPS",
            "Almuerzo JU": "ALMUERZO", "Refuerzo": "RCPS"
        }

        # Identificar los códigos de complemento únicos
        codigos_presentes = set()
        for est in estudiantes_sede:
            for comp_amigable in est.complementos_activos:
                if comp_amigable in mapeo_codigos:
                    codigos_presentes.add(mapeo_codigos[comp_amigable])

        if not codigos_presentes:
            return HttpResponse("No hay estudiantes con complementos asignados en esta sede.", status=404)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for codigo in codigos_presentes:
                # Encontrar el nombre amigable correspondiente al código
                nombre_amigable_actual = next((key for key, value in mapeo_codigos.items() if value == codigo), None)
                if not nombre_amigable_actual:
                    continue

                # Filtrar estudiantes para este complemento específico
                estudiantes_filtrados = [
                    est for est in estudiantes_sede if nombre_amigable_actual in est.complementos_activos
                ]

                # Obtener la ruta del logo desde el programa
                ruta_logo_final = None
                if programa_obj and programa_obj.imagen:
                    ruta_logo_final = programa_obj.imagen.path

                datos_encabezado = {
                    'departamento': departamento_obj.nombre_departamento if departamento_obj else 'N/A',
                    'institucion': nombre_sede_focalizacion,
                    'municipio': sede_obj.codigo_ie.id_municipios.nombre_municipio,
                    'dane_ie': dane_ie,
                    'operador': programa_obj.programa if programa_obj else 'N/A',
                    'contrato': programa_obj.contrato if programa_obj else 'N/A',
                    'mes': mes.upper(),
                    'ano': ano,
                    'codigo_complemento': codigo,
                    'ruta_logo': ruta_logo_final
                }

                pdf_buffer = BytesIO()
                crear_formato_asistencia(pdf_buffer, datos_encabezado, estudiantes_filtrados)
                
                nombre_archivo_pdf = f"Asistencia_{sede_obj.nombre_sede_educativa.replace(' ', '_')}_{codigo}_{mes}_{ano}.pdf"
                zip_file.writestr(nombre_archivo_pdf, pdf_buffer.getvalue())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="Asistencias_{sede_obj.nombre_sede_educativa.replace(" ", "_")}_{focalizacion}_{mes}.zip"'
        return response

    except Exception as e:
        FacturacionLogger.log_procesamiento_error(f"generar_pdf_asistencia_{sede_cod_interprise}", str(e))
        return HttpResponse(f"Error al generar el PDF: {e}", status=500)

@login_required
def debug_sede_estudiantes(request, sede_cod_interprise):
    """Vista de debugging para verificar datos de una sede"""
    try:
        sede_obj = get_object_or_404(SedesEducativas.objects.select_related(
            'codigo_ie__id_municipios'
        ), cod_interprise=sede_cod_interprise)

        # Contar estudiantes por año
        estudiantes_por_ano = {}
        for ano in [2023, 2024, 2025]:
            count = ListadosFocalizacion.objects.filter(
                sede=sede_obj.nombre_sede_educativa,
                ano=ano
            ).count()
            estudiantes_por_ano[ano] = count

        # Obtener todos los nombres de sede únicos en la BD
        sedes_en_bd = ListadosFocalizacion.objects.values_list('sede', flat=True).distinct()[:20]

        response_data = {
            'sede_cod': sede_cod_interprise,
            'sede_nombre': sede_obj.nombre_sede_educativa,
            'estudiantes_por_ano': estudiantes_por_ano,
            'total_sedes_en_bd': ListadosFocalizacion.objects.values('sede').distinct().count(),
            'muestra_sedes_bd': list(sedes_en_bd)
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def verificar_sedes_con_estudiantes(request):
    """Vista para encontrar sedes que SÍ tienen estudiantes"""
    try:
        # Obtener sedes educativas de CALI con estudiantes
        sedes_cali = SedesEducativas.objects.filter(
            codigo_ie__id_municipios__nombre_municipio__icontains='CALI'
        ).select_related('codigo_ie')[:50]

        resultados = []
        for sede in sedes_cali:
            # Contar estudiantes por año
            estudiantes_2025 = ListadosFocalizacion.objects.filter(
                sede=sede.nombre_sede_educativa,
                ano=2025
            ).count()

            estudiantes_2024 = ListadosFocalizacion.objects.filter(
                sede=sede.nombre_sede_educativa,
                ano=2024
            ).count()

            if estudiantes_2025 > 0 or estudiantes_2024 > 0:
                resultados.append({
                    'codigo': sede.cod_interprise,
                    'nombre': sede.nombre_sede_educativa,
                    'institucion': sede.codigo_ie.nombre_institucion,
                    'estudiantes_2025': estudiantes_2025,
                    'estudiantes_2024': estudiantes_2024,
                    'url_test': f'/facturacion/generar-asistencia/{sede.cod_interprise}/enero/2025/'
                })

        # Ordenar por número de estudiantes
        resultados.sort(key=lambda x: x['estudiantes_2025'], reverse=True)

        return JsonResponse({
            'success': True,
            'total_sedes_verificadas': len(sedes_cali),
            'sedes_con_estudiantes': len(resultados),
            'resultados': resultados[:20]  # Solo primeras 20
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
