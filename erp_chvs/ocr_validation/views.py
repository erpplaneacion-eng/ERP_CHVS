"""
Vistas para el módulo de validación OCR con LandingAI ADE.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import logging
import csv
import json
import pandas as pd
import os
import tempfile

from .models import PDFValidation, ValidationError, OCRConfiguration
from .services import OCROrchestrator
from .ocr_orchestrator import OCROrchestrator as AdvancedOCROrchestrator

logger = logging.getLogger(__name__)


@login_required
def ocr_validation_index(request):
    return render(request, 'ocr_validation/index.html', {
        'titulo_pagina': 'Validación OCR con LandingAI ADE',
        'descripcion': 'Sistema de validación automática con IA avanzada'
    })


@login_required
@require_http_methods(["POST"])
def procesar_pdf_ocr(request):
    try:
        if 'archivo_pdf' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se proporcionó archivo PDF'})

        archivo_pdf = request.FILES['archivo_pdf']

        if not archivo_pdf.name.lower().endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'El archivo debe ser un PDF válido'})

        if archivo_pdf.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Archivo demasiado grande (máx 10MB)'})

        orchestrator = OCROrchestrator()
        resultado = orchestrator.process_pdf(archivo_pdf, request.user)

        if resultado['success']:
            validacion = PDFValidation.objects.get(id=resultado['validacion_id'])
            return JsonResponse({
                'success': True,
                'validacion_id': resultado['validacion_id'],
                'mensaje': 'PDF procesado exitosamente con LandingAI ADE',
                'total_errores': resultado['total_errores'],
                'errores_criticos': validacion.errores_criticos,
                'errores_advertencia': validacion.errores_advertencia,
                'tiempo_procesamiento': resultado['tiempo_procesamiento'],
                'redirect_url': f"/ocr_validation/resultados/{resultado['validacion_id']}/"
            })
        else:
            return JsonResponse({'success': False, 'error': resultado['error']})

    except Exception as e:
        logger.exception(f"Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def resultados_validacion(request, validacion_id):
    validacion = get_object_or_404(PDFValidation, id=validacion_id)
    errores = ValidationError.objects.filter(validacion=validacion)

    return render(request, 'ocr_validation/resultados.html', {
        'validacion': validacion,
        'errores_criticos': errores.filter(severidad='critico'),
        'errores_advertencia': errores.filter(severidad='advertencia'),
        'errores_info': errores.filter(severidad='info'),
        'total_errores': errores.count()
    })


@login_required
def listado_validaciones(request):
    validaciones = PDFValidation.objects.all().order_by('-fecha_procesamiento')
    paginator = Paginator(validaciones, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'ocr_validation/listado.html', {
        'validaciones': page_obj,
        'validaciones_completadas': PDFValidation.objects.filter(estado='completado').count(),
        'validaciones_con_errores': PDFValidation.objects.filter(total_errores__gt=0).count()
    })


@login_required
def estadisticas_ocr(request):
    return render(request, 'ocr_validation/estadisticas.html', {
        'total_validaciones': PDFValidation.objects.count(),
        'validaciones_completadas': PDFValidation.objects.filter(estado='completado').count()
    })


@login_required
@require_http_methods(["POST"])
def reintentar_validacion(request, validacion_id):
    try:
        validacion = get_object_or_404(PDFValidation, id=validacion_id)
        if not validacion.archivo_path:
            return JsonResponse({'success': False, 'error': 'Archivo no encontrado'})

        orchestrator = OCROrchestrator()
        resultado = orchestrator.process_pdf(validacion.archivo_path, request.user)

        if resultado['success']:
            return JsonResponse({'success': True, 'mensaje': 'PDF reprocesado', 'validacion_id': resultado['validacion_id']})
        else:
            return JsonResponse({'success': False, 'error': resultado['error']})
    except Exception as e:
        logger.exception(f"Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def marcar_error_resuelto(request, error_id):
    try:
        error = get_object_or_404(ValidationError, id=error_id)
        error.resuelto = True
        error.save()
        return JsonResponse({'success': True, 'mensaje': 'Error resuelto'})
    except Exception as e:
        logger.exception(f"Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def configuracion_ocr(request):
    try:
        configuracion = OCRConfiguration.objects.first()
        if request.method == 'POST':
            if configuracion:
                configuracion.confianza_minima = float(request.POST.get('confianza_minima', 60))
                configuracion.detectar_firmas = request.POST.get('detectar_firmas') == 'on'
                configuracion.save()
            else:
                configuracion = OCRConfiguration.objects.create(
                    confianza_minima=float(request.POST.get('confianza_minima', 60)),
                    detectar_firmas=request.POST.get('detectar_firmas') == 'on'
                )
            return JsonResponse({'success': True, 'mensaje': 'Configuración actualizada'})
        return render(request, 'ocr_validation/configuracion.html', {'configuracion': configuracion})
    except Exception as e:
        logger.exception(f"Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def descargar_reporte_errores(request, validacion_id):
    try:
        validacion = get_object_or_404(PDFValidation, id=validacion_id)
        errores = ValidationError.objects.filter(validacion=validacion)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="errores_{validacion_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Tipo', 'Descripción', 'Página', 'Severidad', 'Resuelto'])
        for error in errores:
            writer.writerow([error.tipo_error, error.descripcion, error.pagina, error.severidad, 'Sí' if error.resuelto else 'No'])
        return response
    except Exception as e:
        logger.exception(f"Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================
# NUEVAS VISTAS PARA DATAFRAMES
# ============================================

@login_required
@require_http_methods(["POST"])
def procesar_pdf_dataframe(request):
    """Vista para procesar PDF con extracción estructurada a DataFrames."""
    try:
        if 'archivo_pdf' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se proporcionó archivo PDF'})

        archivo_pdf = request.FILES['archivo_pdf']

        if not archivo_pdf.name.lower().endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'El archivo debe ser un PDF válido'})

        if archivo_pdf.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Archivo demasiado grande (máx 10MB)'})

        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in archivo_pdf.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        try:
            # Procesar con orquestador avanzado
            orchestrator = AdvancedOCROrchestrator()
            resultado = orchestrator.process_pdf_complete(
                pdf_path=temp_path,
                save_to_db=True,
                usuario=request.user
            )

            if resultado['success']:
                return JsonResponse({
                    'success': True,
                    'validacion_id': resultado['pdf_validation_id'],
                    'mensaje': 'PDF procesado exitosamente con extracción estructurada',
                    'total_estudiantes': resultado['resumen']['total_estudiantes'],
                    'total_raciones': resultado['resumen']['total_raciones'],
                    'calidad_extraccion': resultado['resumen']['calidad_extraccion'],
                    'redirect_url': f"/ocr_validation/dataframe/{resultado['pdf_validation_id']}/"
                })
            else:
                return JsonResponse({'success': False, 'error': resultado['error']})

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.exception(f"Error procesando PDF con DataFrames: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def ver_dataframe(request, validacion_id):
    """Vista para mostrar los DataFrames extraídos de forma interactiva."""
    try:
        validacion = get_object_or_404(PDFValidation, id=validacion_id)
        
        # Recuperar resultados del orquestador
        orchestrator = AdvancedOCROrchestrator()
        resultado = orchestrator.get_processing_results(validacion_id)
        
        if not resultado['success']:
            return render(request, 'ocr_validation/error.html', {
                'error': resultado['error']
            })
        
        df_estudiantes = resultado['df_estudiantes']
        df_encabezado = resultado['df_encabezado']
        
        # Convertir DataFrames a formato para el template
        estudiantes_data = {
            'columns': list(df_estudiantes.columns) if not df_estudiantes.empty else [],
            'data': df_estudiantes.to_dict('records') if not df_estudiantes.empty else [],
            'count': len(df_estudiantes)
        }
        
        encabezado_data = {
            'columns': list(df_encabezado.columns) if not df_encabezado.empty else [],
            'data': df_encabezado.to_dict('records') if not df_encabezado.empty else [],
            'count': len(df_encabezado)
        }
        
        # Estadísticas
        estadisticas = {}
        if not df_estudiantes.empty:
            estadisticas = {
                'total_estudiantes': len(df_estudiantes),
                'total_raciones': df_estudiantes['raciones_entregadas'].sum() if 'raciones_entregadas' in df_estudiantes.columns else 0,
                'estudiantes_con_firma': df_estudiantes['firma_presente'].sum() if 'firma_presente' in df_estudiantes.columns else 0,
                'campos_detectados': len([col for col in df_estudiantes.columns if not df_estudiantes[col].isna().all()])
            }
        
        return render(request, 'ocr_validation/dataframe_view.html', {
            'validacion': validacion,
            'estudiantes': estudiantes_data,
            'encabezado': encabezado_data,
            'estadisticas': estadisticas,
            'metadatos': resultado['metadatos']
        })
        
    except Exception as e:
        logger.exception(f"Error mostrando DataFrame: {e}")
        return render(request, 'ocr_validation/error.html', {
            'error': str(e)
        })


@login_required
def exportar_dataframe(request, validacion_id):
    """Vista para exportar DataFrames a diferentes formatos."""
    try:
        formato = request.GET.get('formato', 'csv')
        tipo = request.GET.get('tipo', 'estudiantes')  # estudiantes o encabezado
        
        # Recuperar datos
        orchestrator = AdvancedOCROrchestrator()
        resultado = orchestrator.get_processing_results(validacion_id)
        
        if not resultado['success']:
            return JsonResponse({'success': False, 'error': resultado['error']})
        
        # Seleccionar DataFrame
        if tipo == 'estudiantes':
            df = resultado['df_estudiantes']
            filename_base = f"estudiantes_{validacion_id}"
        else:
            df = resultado['df_encabezado']
            filename_base = f"encabezado_{validacion_id}"
        
        if df.empty:
            return JsonResponse({'success': False, 'error': 'No hay datos para exportar'})
        
        # Exportar según formato
        if formato == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'
            df.to_csv(response, index=False, encoding='utf-8-sig')
            return response
            
        elif formato == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename_base}.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return response
            
        elif formato == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename_base}.json"'
            df.to_json(response, orient='records', force_ascii=False, indent=2)
            return response
            
        else:
            return JsonResponse({'success': False, 'error': 'Formato no soportado'})
            
    except Exception as e:
        logger.exception(f"Error exportando DataFrame: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_dataframe_data(request, validacion_id):
    """API para obtener datos del DataFrame en formato JSON para tablas interactivas."""
    try:
        tipo = request.GET.get('tipo', 'estudiantes')
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Recuperar datos
        orchestrator = AdvancedOCROrchestrator()
        resultado = orchestrator.get_processing_results(validacion_id)
        
        if not resultado['success']:
            return JsonResponse({'error': resultado['error']})
        
        # Seleccionar DataFrame
        if tipo == 'estudiantes':
            df = resultado['df_estudiantes']
        else:
            df = resultado['df_encabezado']
        
        if df.empty:
            return JsonResponse({
                'draw': request.GET.get('draw', 1),
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': []
            })
        
        # Aplicar filtro de búsqueda
        df_filtered = df
        if search_value:
            # Buscar en todas las columnas de texto
            mask = df.astype(str).apply(
                lambda x: x.str.contains(search_value, case=False, na=False)
            ).any(axis=1)
            df_filtered = df[mask]
        
        # Paginación
        total_records = len(df)
        filtered_records = len(df_filtered)
        df_page = df_filtered.iloc[start:start + length]
        
        # Convertir a formato DataTables
        data = []
        for _, row in df_page.iterrows():
            data.append(list(row.astype(str)))
        
        return JsonResponse({
            'draw': request.GET.get('draw', 1),
            'recordsTotal': total_records,
            'recordsFiltered': filtered_records,
            'data': data
        })
        
    except Exception as e:
        logger.exception(f"Error en API DataFrame: {e}")
        return JsonResponse({'error': str(e)})


@login_required
def dashboard_dataframes(request):
    """Dashboard principal para gestión de DataFrames extraídos."""
    try:
        # Obtener estadísticas generales
        total_validaciones = PDFValidation.objects.filter(
            metodo_ocr='landingai',
            datos_estructurados__isnull=False
        ).count()
        
        validaciones_recientes = PDFValidation.objects.filter(
            metodo_ocr='landingai',
            datos_estructurados__isnull=False
        ).order_by('-fecha_procesamiento')[:10]
        
        # Calcular estadísticas de calidad
        estadisticas_calidad = {
            'buena': 0,
            'regular': 0,
            'mala': 0
        }
        
        total_estudiantes = 0
        total_raciones = 0
        
        for validacion in validaciones_recientes:
            if validacion.metadatos_extraccion:
                metadatos = validacion.metadatos_extraccion
                if isinstance(metadatos, dict):
                    total_estudiantes += metadatos.get('total_estudiantes', 0)
                    total_raciones += metadatos.get('total_raciones', 0)
        
        return render(request, 'ocr_validation/dashboard_dataframes_simple.html', {
            'total_validaciones': total_validaciones,
            'validaciones_recientes': validaciones_recientes,
            'estadisticas_calidad': estadisticas_calidad,
            'total_estudiantes': total_estudiantes,
            'total_raciones': total_raciones
        })
        
    except Exception as e:
        logger.exception(f"Error en dashboard: {e}")
        return render(request, 'ocr_validation/error.html', {
            'error': str(e)
        })
