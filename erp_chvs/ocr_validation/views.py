"""
Vistas para el módulo de validación OCR de PDFs.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import UploadedFile
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from .models import PDFValidation, ValidationError, OCRConfiguration
from django.db import models
from .services import OCROrchestrator
from .exceptions import OCRProcessingException


@login_required
def ocr_validation_index(request):
    """
    Vista principal para validación OCR de PDFs.
    """
    context = {
        'titulo_pagina': 'Validación OCR de PDFs',
        'descripcion': 'Sistema de validación automática de PDFs diligenciados manualmente',
        'configuracion_ocr': OCRConfiguration.objects.first(),
    }

    return render(request, 'ocr_validation/index.html', context)


@login_required
@require_http_methods(["POST"])
def procesar_pdf_ocr(request):
    """
    Vista para procesar un PDF con OCR y validación.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🔄 Iniciando procesamiento OCR para usuario: {request.user}")
        print(f"🔄 Iniciando procesamiento OCR para usuario: {request.user}")

        # Verificar método
        logger.info(f"📨 Método: {request.method}")
        print(f"📨 Método: {request.method}")

        # Verificar archivos recibidos
        logger.info(f"📁 Archivos en request.FILES: {list(request.FILES.keys())}")
        print(f"📁 Archivos en request.FILES: {list(request.FILES.keys())}")

        if 'archivo_pdf' not in request.FILES:
            logger.error("❌ No se encontró archivo PDF en request.FILES")
            print("❌ No se encontró archivo PDF en request.FILES")
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó archivo PDF'
            })

        archivo_pdf = request.FILES['archivo_pdf']
        logger.info(f"📄 Archivo recibido: {archivo_pdf.name}, tamaño: {archivo_pdf.size}")
        print(f"📄 Archivo recibido: {archivo_pdf.name}, tamaño: {archivo_pdf.size}")

        # Validar que sea un PDF
        if not archivo_pdf.name.lower().endswith('.pdf'):
            logger.error(f"❌ Archivo no es PDF: {archivo_pdf.name}")
            print(f"❌ Archivo no es PDF: {archivo_pdf.name}")
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser un PDF válido'
            })

        # Validar tamaño (máximo 10MB)
        if archivo_pdf.size > 10 * 1024 * 1024:
            logger.error(f"❌ Archivo demasiado grande: {archivo_pdf.size}")
            print(f"❌ Archivo demasiado grande: {archivo_pdf.size}")
            return JsonResponse({
                'success': False,
                'error': 'El archivo es demasiado grande (máximo 10MB)'
            })

        logger.info("🔧 Iniciando procesamiento OCR...")
        print("🔧 Iniciando procesamiento OCR...")

        # Procesar PDF con OCR usando la nueva arquitectura
        orchestrator = OCROrchestrator()
        resultado = orchestrator.process_pdf(archivo_pdf, request.user)

        logger.info(f"✅ Resultado del procesamiento: success={resultado.get('success')}")
        print(f"✅ Resultado del procesamiento: success={resultado.get('success')}")

        if resultado['success']:
            # Obtener datos de la validación creada
            validacion = PDFValidation.objects.get(id=resultado['validacion_id'])
            errores = ValidationError.objects.filter(validacion=validacion)

            response_data = {
                'success': True,
                'validacion_id': resultado['validacion_id'],
                'mensaje': 'PDF procesado exitosamente',
                'total_errores': resultado['total_errores'],
                'errores_criticos': validacion.errores_criticos,
                'errores_advertencia': validacion.errores_advertencia,
                'tiempo_procesamiento': resultado['tiempo_procesamiento'],
                'redirect_url': f"/ocr_validation/resultados/{resultado['validacion_id']}/"
            }

            logger.info(f"✅ Respuesta exitosa: {response_data}")
            print(f"✅ Respuesta exitosa: {response_data}")

            return JsonResponse(response_data)
        else:
            error_response = {
                'success': False,
                'error': resultado['error']
            }
            logger.error(f"❌ Error en procesamiento: {error_response}")
            print(f"❌ Error en procesamiento: {error_response}")
            return JsonResponse(error_response)

    except Exception as e:
        error_msg = f'Error interno del servidor: {str(e)}'
        logger.exception(f"💥 Excepción capturada: {error_msg}")
        print(f"💥 Excepción capturada: {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        })


@login_required
def resultados_validacion(request, validacion_id):
    """
    Vista para mostrar resultados detallados de una validación.
    """
    try:
        validacion = get_object_or_404(PDFValidation, id=validacion_id)

        # Verificar permisos (usuario debe ser el creador o superusuario)
        if validacion.usuario_creador != request.user and not request.user.is_superuser:
            raise PermissionDenied("No tienes permisos para ver esta validación")

        # Obtener errores agrupados por severidad
        errores = ValidationError.objects.filter(validacion=validacion)

        errores_criticos = errores.filter(severidad='critico')
        errores_advertencia = errores.filter(severidad='advertencia')
        errores_info = errores.filter(severidad='info')

        # Agrupar errores por página
        errores_por_pagina = {}
        for error in errores:
            pagina = error.pagina
            if pagina not in errores_por_pagina:
                errores_por_pagina[pagina] = []
            errores_por_pagina[pagina].append(error)

        context = {
            'validacion': validacion,
            'errores_criticos': errores_criticos,
            'errores_advertencia': errores_advertencia,
            'errores_info': errores_info,
            'errores_por_pagina': errores_por_pagina,
            'total_errores': errores.count(),
        }

        return render(request, 'ocr_validation/resultados.html', context)

    except Exception as e:
        context = {
            'error': f'Error al cargar resultados: {str(e)}',
            'validacion_id': validacion_id
        }
        return render(request, 'ocr_validation/error.html', context)


@login_required
def listado_validaciones(request):
    """
    Vista para listar todas las validaciones realizadas.
    """
    try:
        # Filtros
        sede_filter = request.GET.get('sede', '').strip()
        mes_filter = request.GET.get('mes', '').strip()
        estado_filter = request.GET.get('estado', '').strip()

        # Query base
        validaciones = PDFValidation.objects.all().order_by('-fecha_procesamiento')

        # Aplicar filtros
        if sede_filter:
            validaciones = validaciones.filter(sede_educativa__icontains=sede_filter)

        if mes_filter:
            validaciones = validaciones.filter(mes_atencion__icontains=mes_filter)

        if estado_filter:
            validaciones = validaciones.filter(estado=estado_filter)

        # Paginación
        paginator = Paginator(validaciones, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Obtener valores únicos para filtros
        sedes_unicas = PDFValidation.objects.values_list('sede_educativa', flat=True).distinct().order_by('sede_educativa')
        meses_unicos = PDFValidation.objects.values_list('mes_atencion', flat=True).distinct().order_by('mes_atencion')

        # Estadísticas básicas para la plantilla
        validaciones_completadas = PDFValidation.objects.filter(estado='completado').count()
        validaciones_con_errores = PDFValidation.objects.filter(total_errores__gt=0).count()
        validaciones_con_error = PDFValidation.objects.filter(estado='error').count()

        context = {
            'validaciones': page_obj,
            'validaciones_completadas': validaciones_completadas,
            'validaciones_con_errores': validaciones_con_errores,
            'validaciones_con_error': validaciones_con_error,
            'filtros_aplicados': {
                'sede': sede_filter,
                'mes': mes_filter,
                'estado': estado_filter,
            },
            'sedes_unicas': sedes_unicas,
            'meses_unicos': meses_unicos,
            'estados_disponibles': [
                ('procesando', 'Procesando'),
                ('completado', 'Completado'),
                ('error', 'Error'),
            ],
        }

        return render(request, 'ocr_validation/listado.html', context)

    except Exception as e:
        context = {
            'error': f'Error al cargar listado: {str(e)}'
        }
        return render(request, 'ocr_validation/error.html', context)


@login_required
@require_http_methods(["POST"])
def reintentar_validacion(request, validacion_id):
    """
    Vista para reintentar el procesamiento de una validación fallida.
    """
    try:
        validacion = get_object_or_404(PDFValidation, id=validacion_id)

        # Verificar permisos
        if validacion.usuario_creador != request.user and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para esta acción'
            })

        # Aquí iría la lógica para reintentar el procesamiento
        # Por ahora, solo cambiamos el estado
        validacion.estado = 'procesando'
        validacion.observaciones = 'Reintento de procesamiento iniciado'
        validacion.save()

        return JsonResponse({
            'success': True,
            'mensaje': 'Procesamiento reintentado exitosamente'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al reintentar: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def marcar_error_resuelto(request, error_id):
    """
    Vista para marcar un error específico como resuelto.
    """
    try:
        error = get_object_or_404(ValidationError, id=error_id)

        # Verificar permisos
        if error.validacion.usuario_creador != request.user and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para esta acción'
            })

        error.resuelto = True
        error.save()

        # Recalcular totales de la validación
        validacion = error.validacion
        errores_pendientes = ValidationError.objects.filter(
            validacion=validacion,
            resuelto=False
        )

        validacion.total_errores = errores_pendientes.count()
        validacion.errores_criticos = errores_pendientes.filter(severidad='critico').count()
        validacion.errores_advertencia = errores_pendientes.filter(severidad='advertencia').count()

        if validacion.total_errores == 0:
            validacion.observaciones = 'Todos los errores han sido resueltos'
        else:
            validacion.observaciones = f'Quedan {validacion.total_errores} errores por resolver'

        validacion.save()

        return JsonResponse({
            'success': True,
            'mensaje': 'Error marcado como resuelto',
            'errores_restantes': validacion.total_errores
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al marcar como resuelto: {str(e)}'
        })


@login_required
def estadisticas_ocr(request):
    """
    Vista para mostrar estadísticas generales del sistema OCR.
    """
    try:
        # Estadísticas generales
        total_validaciones = PDFValidation.objects.count()
        validaciones_completadas = PDFValidation.objects.filter(estado='completado').count()
        validaciones_con_errores = PDFValidation.objects.filter(total_errores__gt=0).count()

        # Estadísticas por severidad
        errores_criticos_total = ValidationError.objects.filter(severidad='critico').count()
        errores_advertencia_total = ValidationError.objects.filter(severidad='advertencia').count()
        errores_info_total = ValidationError.objects.filter(severidad='info').count()

        # Estadísticas por tipo de error
        errores_por_tipo = ValidationError.objects.values('tipo_error').annotate(
            total=models.Count('id')
        ).order_by('-total')

        # Estadísticas por sede
        errores_por_sede = PDFValidation.objects.values('sede_educativa').annotate(
            total_errores=models.Sum('total_errores'),
            errores_criticos=models.Sum('errores_criticos')
        ).order_by('-total_errores')[:10]

        context = {
            'estadisticas_generales': {
                'total_validaciones': total_validaciones,
                'validaciones_completadas': validaciones_completadas,
                'validaciones_con_errores': validaciones_con_errores,
                'tasa_exito': (validaciones_completadas / total_validaciones * 100) if total_validaciones > 0 else 0,
            },
            'estadisticas_errores': {
                'errores_criticos': errores_criticos_total,
                'errores_advertencia': errores_advertencia_total,
                'errores_info': errores_info_total,
                'total_errores': errores_criticos_total + errores_advertencia_total + errores_info_total,
            },
            'errores_por_tipo': errores_por_tipo,
            'errores_por_sede': errores_por_sede,
        }

        return render(request, 'ocr_validation/estadisticas.html', context)

    except Exception as e:
        context = {
            'error': f'Error al cargar estadísticas: {str(e)}'
        }
        return render(request, 'ocr_validation/error.html', context)


@login_required
def configuracion_ocr(request):
    """
    Vista para configurar parámetros del sistema OCR.
    """
    try:
        configuracion = OCRConfiguration.objects.first()

        if request.method == 'POST':
            # Actualizar configuración
            if configuracion:
                configuracion.tesseract_config = request.POST.get('tesseract_config', configuracion.tesseract_config)
                configuracion.confianza_minima = float(request.POST.get('confianza_minima', configuracion.confianza_minima))
                configuracion.tolerancia_posicion_x = float(request.POST.get('tolerancia_posicion_x', configuracion.tolerancia_posicion_x))
                configuracion.tolerancia_posicion_y = float(request.POST.get('tolerancia_posicion_y', configuracion.tolerancia_posicion_y))
                configuracion.permitir_texto_parcial = request.POST.get('permitir_texto_parcial') == 'on'
                configuracion.detectar_firmas = request.POST.get('detectar_firmas') == 'on'
                configuracion.procesar_imagenes = request.POST.get('procesar_imagenes') == 'on'
                configuracion.guardar_imagenes_temporales = request.POST.get('guardar_imagenes_temporales') == 'on'
                configuracion.save()

                context = {
                    'configuracion': configuracion,
                    'mensaje_exito': 'Configuración actualizada exitosamente'
                }
            else:
                context = {
                    'error': 'No se pudo actualizar la configuración'
                }
        else:
            context = {
                'configuracion': configuracion
            }

        return render(request, 'ocr_validation/configuracion.html', context)

    except Exception as e:
        context = {
            'error': f'Error al cargar configuración: {str(e)}'
        }
        return render(request, 'ocr_validation/error.html', context)


@login_required
def descargar_reporte_errores(request, validacion_id):
    """
    Vista para descargar reporte de errores en formato Excel.
    """
    try:
        validacion = get_object_or_404(PDFValidation, id=validacion_id)
        errores = ValidationError.objects.filter(validacion=validacion)

        # Crear DataFrame con errores
        datos_errores = []
        for error in errores:
            datos_errores.append({
                'Tipo Error': error.tipo_error,
                'Descripción': error.descripcion,
                'Página': error.pagina,
                'Fila Estudiante': error.fila_estudiante or '',
                'Campo': error.columna_campo or '',
                'Severidad': error.severidad,
                'Resuelto': 'Sí' if error.resuelto else 'No',
                'Fecha Creación': error.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
            })

        # Verificar si pandas está disponible
        try:
            import pandas as pd
            from io import BytesIO

            df = pd.DataFrame(datos_errores)

            # Crear buffer para Excel
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)

            # Crear respuesta HTTP
            response = HttpResponse(
                excel_buffer.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            filename = f"errores_validacion_{validacion.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except ImportError:
            # Si pandas no está disponible, crear CSV simple
            import csv
            from io import StringIO

            csv_buffer = StringIO()
            if datos_errores:
                writer = csv.DictWriter(csv_buffer, fieldnames=datos_errores[0].keys())
                writer.writeheader()
                writer.writerows(datos_errores)

            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
            filename = f"errores_validacion_{validacion.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

    except Exception as e:
        return HttpResponse(f'Error generando reporte: {str(e)}', status=500)


# Funciones auxiliares para compatibilidad
def validar_pdf_ocr(archivo_pdf: UploadedFile, usuario=None) -> Dict[str, Any]:
    """
    Función de compatibilidad para validar PDF con OCR.
    Utiliza la nueva arquitectura de servicios.
    """
    orchestrator = OCROrchestrator()
    return orchestrator.process_pdf(archivo_pdf, usuario)