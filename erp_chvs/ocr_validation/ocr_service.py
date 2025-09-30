"""
Servicio principal para procesamiento OCR y validación de PDFs diligenciados.
"""

import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import re
import json
import tempfile
import shutil
from typing import Dict, List, Any, Tuple, Optional
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

# Importar Tesseract OCR
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Advertencia: Tesseract no está instalado. Instale pytesseract y PIL para usar OCR.")

from .models import PDFValidation, ValidationError, OCRConfiguration, FieldValidationRule
from .exceptions import OCRProcessingException, ValidationException


class OCRProcessor:
    """
    Procesador principal para OCR y validación de PDFs diligenciados.
    """

    def __init__(self):
        """Inicializa el procesador OCR."""
        self.config = self._get_or_create_config()
        self.validation_rules = self._load_validation_rules()

        if not TESSERACT_AVAILABLE:
            raise OCRProcessingException(
                "Tesseract OCR no está disponible. Instale las dependencias necesarias."
            )

    def _get_or_create_config(self) -> OCRConfiguration:
        """Obtiene o crea la configuración OCR por defecto."""
        try:
            return OCRConfiguration.objects.first()
        except OCRConfiguration.DoesNotExist:
            return OCRConfiguration.objects.create()

    def _load_validation_rules(self) -> Dict[str, FieldValidationRule]:
        """Carga las reglas de validación activas."""
        rules = FieldValidationRule.objects.filter(activo=True)
        return {rule.nombre_campo: rule for rule in rules}

    def procesar_pdf_ocr(self, archivo_pdf: UploadedFile) -> Dict[str, Any]:
        """
        Procesa un PDF con OCR y validación completa.

        Args:
            archivo_pdf: Archivo PDF subido por el usuario

        Returns:
            Dict[str, Any]: Resultado completo del procesamiento
        """
        inicio_tiempo = datetime.now()

        try:
            # Crear registro de validación
            validacion = self._crear_registro_validacion(archivo_pdf)

            # Extraer información básica del PDF
            info_pdf = self._extraer_info_pdf(archivo_pdf)

            # Procesar páginas con OCR
            resultados_ocr = self._procesar_paginas_ocr(archivo_pdf)

            # Validar campos manuales
            errores_validacion = self._validar_campos_manuales(resultados_ocr, info_pdf)

            # Actualizar registro con resultados
            tiempo_total = (datetime.now() - inicio_tiempo).total_seconds()
            self._actualizar_registro_validacion(
                validacion, errores_validacion, tiempo_total, info_pdf
            )

            return {
                'success': True,
                'validacion_id': validacion.id,
                'info_pdf': info_pdf,
                'errores': errores_validacion,
                'total_errores': len(errores_validacion),
                'tiempo_procesamiento': tiempo_total
            }

        except Exception as e:
            tiempo_total = (datetime.now() - inicio_tiempo).total_seconds()
            return {
                'success': False,
                'error': str(e),
                'tiempo_procesamiento': tiempo_total
            }

    def _crear_registro_validacion(self, archivo_pdf: UploadedFile) -> PDFValidation:
        """Crea un registro inicial de validación."""
        # Extraer información básica del nombre del archivo
        nombre_archivo = archivo_pdf.name
        info_basica = self._parsear_nombre_archivo(nombre_archivo)

        return PDFValidation.objects.create(
            archivo_nombre=nombre_archivo,
            archivo_path=archivo_pdf.temporary_file_path() if hasattr(archivo_pdf, 'temporary_file_path') else '',
            sede_educativa=info_basica.get('sede', 'Sede Desconocida'),
            mes_atencion=info_basica.get('mes', 'Mes Desconocido'),
            ano=info_basica.get('ano', datetime.now().year),
            tipo_complemento=info_basica.get('complemento', 'Tipo Desconocido'),
            estado='procesando'
        )

    def _parsear_nombre_archivo(self, nombre_archivo: str) -> Dict[str, str]:
        """Parsea información básica del nombre del archivo PDF."""
        info = {}

        # Ejemplo de patrón esperado: "Asistencia_Sede_Educativa_CAJMPS_OCTUBRE_2025.pdf"
        partes = nombre_archivo.replace('.pdf', '').split('_')

        if len(partes) >= 4:
            info['sede'] = partes[1] if len(partes) > 1 else 'Sede Desconocida'
            info['complemento'] = partes[2] if len(partes) > 2 else 'Tipo Desconocido'
            info['mes'] = partes[3] if len(partes) > 3 else 'Mes Desconocido'
            info['ano'] = partes[4] if len(partes) > 4 else str(datetime.now().year)

        return info

    def _extraer_info_pdf(self, archivo_pdf: UploadedFile) -> Dict[str, Any]:
        """Extrae información básica del PDF."""
        info = {
            'nombre_archivo': archivo_pdf.name,
            'tamano_archivo': archivo_pdf.size,
            'tipo_contenido': archivo_pdf.content_type,
            'num_paginas': 0,
            'dimensiones_paginas': []
        }

        try:
            # Crear archivo temporal para procesamiento
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(archivo_pdf.read())
                tmp_file_path = tmp_file.name

            # Aquí iría la lógica para extraer información del PDF
            # Por ahora retornamos información básica
            info['num_paginas'] = 1  # Placeholder
            info['dimensiones_paginas'] = [(612, 792)]  # A4 tamaño estándar

        except Exception as e:
            print(f"Error extrayendo info del PDF: {e}")
        finally:
            # Limpiar archivo temporal
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass

        return info

    def _procesar_paginas_ocr(self, archivo_pdf: UploadedFile) -> List[Dict[str, Any]]:
        """Procesa cada página del PDF con OCR usando Tesseract."""
        resultados = []

        try:
            # Crear archivo temporal para el PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                tmp_pdf.write(archivo_pdf.read())
                tmp_pdf_path = tmp_pdf.name

            # Aquí iría la lógica real de conversión PDF a imágenes
            # Por ahora simulamos el procesamiento
            imagenes_temporales = self._convertir_pdf_a_imagenes(tmp_pdf_path)

            # Procesar cada imagen con OCR
            for i, imagen_path in enumerate(imagenes_temporales):
                resultado_ocr = self._procesar_imagen_ocr(imagen_path, i + 1)
                resultados.append(resultado_ocr)

                # Limpiar imagen temporal si no se requiere guardar
                if not self.config.guardar_imagenes_temporales:
                    try:
                        os.unlink(imagen_path)
                    except:
                        pass

            # Limpiar PDF temporal
            try:
                os.unlink(tmp_pdf_path)
            except:
                pass

        except Exception as e:
            print(f"Error procesando páginas OCR: {e}")
            # Retornar resultado de error
            resultados = [{
                'pagina': 1,
                'texto_extraido': '',
                'confianza': 0.0,
                'error': str(e)
            }]

        return resultados

    def _convertir_pdf_a_imagenes(self, pdf_path: str) -> List[str]:
        """Convierte páginas de PDF a imágenes usando pdf2image."""
        imagenes_temporales = []

        try:
            # Aquí iría la conversión real con pdf2image
            # Por simplicidad, creamos imágenes temporales simuladas
            imagenes_temporales = [pdf_path.replace('.pdf', '_page_1.png')]

        except Exception as e:
            print(f"Error convirtiendo PDF a imágenes: {e}")

        return imagenes_temporales

    def _procesar_imagen_ocr(self, imagen_path: str, pagina_num: int) -> Dict[str, Any]:
        """Procesa una imagen con Tesseract OCR."""
        try:
            # Verificar que el archivo existe
            if not os.path.exists(imagen_path):
                return {
                    'pagina': pagina_num,
                    'texto_extraido': '',
                    'confianza': 0.0,
                    'error': f'Imagen no encontrada: {imagen_path}'
                }

            # Configurar Tesseract según la configuración
            config_tesseract = self.config.tesseract_config

            # Procesar imagen con OCR
            texto_extraido = pytesseract.image_to_string(
                Image.open(imagen_path),
                config=config_tesseract
            )

            # Obtener confianza del resultado
            confianza_data = pytesseract.image_to_data(
                Image.open(imagen_path),
                config=config_tesseract,
                output_type=pytesseract.Output.DICT
            )

            # Calcular confianza promedio
            confianza_promedio = 0.0
            if confianza_data and 'conf' in confianza_data:
                confidencias = [conf for conf in confianza_data['conf'] if conf > 0]
                if confidencias:
                    confianza_promedio = sum(confidencias) / len(confidencias)

            return {
                'pagina': pagina_num,
                'texto_extraido': texto_extraido,
                'confianza': confianza_promedio,
                'imagen_path': imagen_path if self.config.guardar_imagenes_temporales else None
            }

        except Exception as e:
            return {
                'pagina': pagina_num,
                'texto_extraido': '',
                'confianza': 0.0,
                'error': str(e)
            }

    def _validar_campos_manuales(self, resultados_ocr: List[Dict], info_pdf: Dict) -> List[Dict[str, Any]]:
        """Valida los campos que deben ser diligenciados manualmente."""
        errores = []

        # Procesar cada página con OCR
        for resultado in resultados_ocr:
            pagina_num = resultado['pagina']
            texto_ocr = resultado.get('texto_extraido', '')
            confianza = resultado.get('confianza', 0.0)

            # Validar confianza mínima del OCR
            if confianza < self.config.confianza_minima:
                errores.append({
                    'tipo': 'confianza_ocr_baja',
                    'descripcion': f'La confianza del OCR en página {pagina_num} es baja ({confianza:.1f}%)',
                    'pagina': pagina_num,
                    'severidad': 'advertencia',
                    'campo': 'ocr_general'
                })

            # Buscar campos manuales en el texto OCR
            errores.extend(self._analizar_texto_ocr(texto_ocr, pagina_num))

        return errores

    def _analizar_texto_ocr(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Analiza el texto OCR para detectar campos manuales y validar su contenido."""
        errores = []

        # Convertir texto a minúsculas para análisis
        texto_lower = texto_ocr.lower()

        # 1. Validar campos numéricos (raciones diarias y mensuales)
        errores.extend(self._validar_campos_numericos(texto_ocr, pagina))

        # 2. Validar firmas
        errores.extend(self._validar_firmas(texto_ocr, pagina))

        # 3. Validar celdas con "X"
        errores.extend(self._validar_celdas_x(texto_ocr, pagina))

        # 4. Validar campos de texto obligatorio
        errores.extend(self._validar_campos_texto(texto_ocr, pagina))

        return errores

    def _validar_campos_numericos(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida campos numéricos en el texto OCR."""
        errores = []

        # Buscar patrones de números que podrían ser raciones
        # Patrón para números enteros positivos
        patron_numeros = r'\b\d+\b'

        # Buscar líneas que contengan palabras clave de raciones
        lineas = texto_ocr.split('\n')
        for i, linea in enumerate(lineas):
            linea_lower = linea.lower().strip()

            # Buscar raciones diarias
            if any(palabra in linea_lower for palabra in ['diarias', 'diaria', 'daily']):
                numeros_en_linea = re.findall(patron_numeros, linea)
                if not numeros_en_linea:
                    errores.append({
                        'tipo': 'campo_numerico_vacio',
                        'descripcion': f'No se encontró número válido para raciones diarias en línea {i+1}',
                        'pagina': pagina,
                        'severidad': 'critico',
                        'campo': 'raciones_diarias',
                        'fila_ocr': i + 1
                    })
                else:
                    # Validar que el número sea razonable (no más de 1000 estudiantes)
                    for numero in numeros_en_linea:
                        if int(numero) > 1000:
                            errores.append({
                                'tipo': 'numero_irreal',
                                'descripcion': f'Número de raciones diarias irreal: {numero}',
                                'pagina': pagina,
                                'severidad': 'advertencia',
                                'campo': 'raciones_diarias',
                                'fila_ocr': i + 1
                            })

            # Buscar raciones mensuales
            if any(palabra in linea_lower for palabra in ['mensuales', 'mensual', 'monthly']):
                numeros_en_linea = re.findall(patron_numeros, linea)
                if not numeros_en_linea:
                    errores.append({
                        'tipo': 'campo_numerico_vacio',
                        'descripcion': f'No se encontró número válido para raciones mensuales en línea {i+1}',
                        'pagina': pagina,
                        'severidad': 'critico',
                        'campo': 'raciones_mensuales',
                        'fila_ocr': i + 1
                    })

        return errores

    def _validar_firmas(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida presencia de firmas en el texto OCR."""
        errores = []

        if not self.config.detectar_firmas:
            return errores

        lineas = texto_ocr.split('\n')
        firma_encontrada = False

        for i, linea in enumerate(lineas):
            linea_lower = linea.lower().strip()

            # Buscar palabras clave relacionadas con firmas
            if any(palabra in linea_lower for palabra in ['firma', 'firmado', 'signature', 'signed']):
                # Verificar si hay texto después de la palabra "firma"
                if len(linea.strip()) < 10:  # Firma muy corta
                    errores.append({
                        'tipo': 'firma_incompleta',
                        'descripcion': f'Firma muy corta o ilegible en línea {i+1}',
                        'pagina': pagina,
                        'severidad': 'critico',
                        'campo': 'firma',
                        'fila_ocr': i + 1
                    })
                else:
                    firma_encontrada = True

        # Si no se encontró ninguna firma en toda la página
        if not firma_encontrada:
            errores.append({
                'tipo': 'firma_faltante',
                'descripcion': 'No se detectó ninguna firma en la página',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'firma_general'
            })

        return errores

    def _validar_celdas_x(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida celdas que deben contener una 'X'."""
        errores = []

        # Buscar todas las "X" en el texto
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            # Buscar "X" en la línea
            posiciones_x = []
            for j, char in enumerate(linea):
                if char.upper() == 'X':
                    posiciones_x.append(j)

            # Si hay "X" en la línea, validar su posición
            for pos_x in posiciones_x:
                # Aquí iría lógica más sofisticada para determinar si la "X" está dentro de una celda
                # Por ahora, simulamos detección básica

                # Verificar si la "X" está aislada (como una marca de asistencia)
                if self._es_x_asistencia(linea, pos_x):
                    # Validar posición relativa en la línea
                    posicion_relativa = pos_x / len(linea) if len(linea) > 0 else 0

                    # Si la "X" está muy a la izquierda o derecha, podría estar fuera de celda
                    if posicion_relativa < 0.1 or posicion_relativa > 0.9:
                        errores.append({
                            'tipo': 'posicion_x_incorrecta',
                            'descripcion': f'Marca "X" posiblemente fuera de celda en línea {i+1}, posición {pos_x}',
                            'pagina': pagina,
                            'severidad': 'advertencia',
                            'campo': 'celda_x',
                            'fila_ocr': i + 1,
                            'posicion_x': pos_x
                        })

        return errores

    def _es_x_asistencia(self, linea: str, posicion_x: int) -> bool:
        """Determina si una 'X' parece ser una marca de asistencia."""
        # Verificar contexto alrededor de la "X"
        inicio = max(0, posicion_x - 2)
        fin = min(len(linea), posicion_x + 3)

        contexto = linea[inicio:fin]

        # Una marca de asistencia típicamente está sola o con espacios
        # No debería estar junto a otras letras
        letras_cercanas = sum(1 for char in contexto if char.isalpha() and char.upper() != 'X')

        return letras_cercanas <= 1  # Permite máximo 1 letra cercana (la X misma)

    def _validar_campos_texto(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida campos de texto obligatorio."""
        errores = []

        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            linea_lower = linea.lower().strip()

            # Buscar campos de observaciones
            if 'observaciones' in linea_lower or 'observations' in linea_lower:
                siguiente_linea = lineas[i + 1] if i + 1 < len(lineas) else ''

                # Si la línea de observaciones está vacía o muy corta
                if len(siguiente_linea.strip()) < 5:
                    errores.append({
                        'tipo': 'observaciones_vacias',
                        'descripcion': f'Campo de observaciones vacío o muy corto en línea {i+2}',
                        'pagina': pagina,
                        'severidad': 'advertencia',
                        'campo': 'observaciones',
                        'fila_ocr': i + 2
                    })

        return errores

    def _actualizar_registro_validacion(
        self,
        validacion: PDFValidation,
        errores: List[Dict],
        tiempo_procesamiento: float,
        info_pdf: Dict
    ):
        """Actualiza el registro de validación con los resultados."""
        # Contar errores por severidad
        errores_criticos = len([e for e in errores if e.get('severidad') == 'critico'])
        errores_advertencia = len([e for e in errores if e.get('severidad') == 'advertencia'])

        # Actualizar registro
        validacion.estado = 'completado'
        validacion.fecha_completado = timezone.now()
        validacion.tiempo_procesamiento = tiempo_procesamiento
        validacion.total_errores = len(errores)
        validacion.errores_criticos = errores_criticos
        validacion.errores_advertencia = errores_advertencia

        if errores_criticos > 0:
            validacion.observaciones = f"Documento con {errores_criticos} errores críticos que requieren revisión inmediata."
        elif errores_advertencia > 0:
            validacion.observaciones = f"Documento con {errores_advertencia} advertencias menores."

        validacion.save()

        # Guardar errores individuales
        for error_data in errores:
            ValidationError.objects.create(
                validacion=validacion,
                tipo_error=error_data.get('tipo', 'desconocido'),
                descripcion=error_data.get('descripcion', ''),
                pagina=error_data.get('pagina', 1),
                severidad=error_data.get('severidad', 'advertencia'),
                columna_campo=error_data.get('campo', '')
            )


class OCRValidator:
    """
    Clase especializada en validación de campos específicos del PDF.
    """

    def __init__(self):
        """Inicializa el validador."""
        self.campos_manuales = self._definir_campos_manuales()

    def _definir_campos_manuales(self) -> Dict[str, Dict[str, Any]]:
        """Define los campos que deben ser diligenciados manualmente."""
        return {
            'raciones_diarias_entregadas': {
                'tipo': 'numero',
                'obligatorio': True,
                'patron': r'^\d+$',
                'descripcion': 'Raciones diarias efectivamente entregadas'
            },
            'raciones_mensuales_entregadas': {
                'tipo': 'numero',
                'obligatorio': True,
                'patron': r'^\d+$',
                'descripcion': 'Raciones mensuales efectivamente entregadas'
            },
            'firma_responsable_operador': {
                'tipo': 'firma',
                'obligatorio': True,
                'descripcion': 'Firma del responsable del operador'
            },
            'firma_rector': {
                'tipo': 'firma',
                'obligatorio': True,
                'descripcion': 'Firma del rector del establecimiento'
            },
            'observaciones': {
                'tipo': 'texto',
                'obligatorio': False,
                'descripcion': 'Observaciones adicionales'
            },
            'celdas_asistencia': {
                'tipo': 'celda_x',
                'obligatorio': True,
                'descripcion': 'Casillas de asistencia diaria marcadas con X'
            }
        }

    def validar_campo(self, nombre_campo: str, valor_ocr: str, contexto: Dict = None) -> List[Dict[str, Any]]:
        """
        Valida un campo específico según las reglas definidas.

        Args:
            nombre_campo: Nombre del campo a validar
            valor_ocr: Valor extraído por OCR
            contexto: Información adicional de contexto

        Returns:
            List[Dict[str, Any]]: Lista de errores encontrados
        """
        errores = []

        if nombre_campo not in self.campos_manuales:
            return errores

        campo_config = self.campos_manuales[nombre_campo]

        # Validar campo obligatorio vacío
        if campo_config['obligatorio'] and not valor_ocr.strip():
            errores.append({
                'tipo': 'campo_obligatorio_vacio',
                'descripcion': f"El campo '{campo_config['descripcion']}' es obligatorio pero está vacío",
                'severidad': 'critico'
            })
            return errores  # Si está vacío, no continuar con otras validaciones

        # Validaciones específicas por tipo
        if campo_config['tipo'] == 'numero':
            errores.extend(self._validar_campo_numerico(valor_ocr, campo_config))
        elif campo_config['tipo'] == 'firma':
            errores.extend(self._validar_campo_firma(valor_ocr, campo_config))
        elif campo_config['tipo'] == 'celda_x':
            errores.extend(self._validar_campo_celda_x(valor_ocr, campo_config, contexto))
        elif campo_config['tipo'] == 'texto':
            errores.extend(self._validar_campo_texto(valor_ocr, campo_config))

        return errores

    def _validar_campo_numerico(self, valor: str, campo_config: Dict) -> List[Dict[str, Any]]:
        """Valida campos numéricos."""
        errores = []

        # Verificar patrón numérico
        patron = campo_config.get('patron')
        if patron and not re.match(patron, valor.strip()):
            errores.append({
                'tipo': 'formato_numerico_invalido',
                'descripcion': f"El valor '{valor}' no tiene formato numérico válido",
                'severidad': 'advertencia'
            })

        # Verificar rango si está definido
        valor_num = None
        try:
            valor_num = int(valor.strip())
        except ValueError:
            errores.append({
                'tipo': 'no_es_numero',
                'descripcion': f"El valor '{valor}' no es un número válido",
                'severidad': 'critico'
            })
            return errores

        valor_min = campo_config.get('valor_minimo')
        valor_max = campo_config.get('valor_maximo')

        if valor_min and valor_num < int(valor_min):
            errores.append({
                'tipo': 'valor_minimo',
                'descripcion': f"El valor {valor_num} es menor que el mínimo permitido ({valor_min})",
                'severidad': 'advertencia'
            })

        if valor_max and valor_num > int(valor_max):
            errores.append({
                'tipo': 'valor_maximo',
                'descripcion': f"El valor {valor_num} es mayor que el máximo permitido ({valor_max})",
                'severidad': 'advertencia'
            })

        return errores

    def _validar_campo_firma(self, valor: str, campo_config: Dict) -> List[Dict[str, Any]]:
        """Valida campos de firma."""
        errores = []

        # Una firma debe tener al menos algunos caracteres
        texto_limpio = valor.strip()

        if len(texto_limpio) < 3:
            errores.append({
                'tipo': 'firma_incompleta',
                'descripcion': f"Firma muy corta o ilegible: '{texto_limpio}'",
                'severidad': 'critico'
            })

        # Buscar patrones comunes de firma ilegible
        patrones_ilegibles = ['???', 'xxx', '...', '---']
        if any(patron in texto_limpio.lower() for patron in patrones_ilegibles):
            errores.append({
                'tipo': 'firma_ilegible',
                'descripcion': f"Firma marcada como ilegible: '{texto_limpio}'",
                'severidad': 'critico'
            })

        return errores

    def _validar_campo_celda_x(self, valor: str, campo_config: Dict, contexto: Dict = None) -> List[Dict[str, Any]]:
        """Valida celdas que deben contener una 'X'."""
        errores = []

        # Buscar 'X' en el texto OCR
        texto_limpio = valor.strip().upper()

        if 'X' not in texto_limpio:
            errores.append({
                'tipo': 'celda_sin_marca',
                'descripcion': f"No se encontró marca 'X' en la celda",
                'severidad': 'advertencia'
            })

        # Verificar posición de la 'X' (simulado)
        if contexto and 'posicion_x' in contexto:
            posicion = contexto['posicion_x']
            if posicion > 5:  # Tolerancia de 5 puntos
                errores.append({
                    'tipo': 'posicion_x_incorrecta',
                    'descripcion': f"Marca 'X' fuera de posición en celda (desplazada {posicion} puntos)",
                    'severidad': 'advertencia'
                })

        return errores

    def _validar_campo_texto(self, valor: str, campo_config: Dict) -> List[Dict[str, Any]]:
        """Valida campos de texto."""
        errores = []

        # Validaciones básicas de texto
        texto_limpio = valor.strip()

        if len(texto_limpio) > 500:  # Longitud máxima razonable
            errores.append({
                'tipo': 'texto_demasiado_largo',
                'descripcion': f"Texto demasiado largo ({len(texto_limpio)} caracteres)",
                'severidad': 'advertencia'
            })

        return errores


class OCRImageProcessor:
    """
    Procesador especializado en imágenes para mejorar resultados OCR.
    """

    def __init__(self):
        """Inicializa el procesador de imágenes."""
        if not cv2:
            raise OCRProcessingException("OpenCV no está disponible para procesamiento de imágenes.")

    def preprocesar_imagen(self, imagen_path: str) -> str:
        """
        Preprocesa una imagen para mejorar resultados OCR.

        Args:
            imagen_path: Ruta de la imagen a procesar

        Returns:
            str: Ruta de la imagen preprocesada
        """
        try:
            # Cargar imagen
            imagen = cv2.imread(imagen_path)

            if imagen is None:
                raise OCRProcessingException(f"No se pudo cargar la imagen: {imagen_path}")

            # Convertir a escala de grises
            gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

            # Aplicar filtro de ruido
            filtrada = cv2.medianBlur(gris, 3)

            # Mejorar contraste
            mejorada = cv2.adaptiveThreshold(
                filtrada, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Crear archivo temporal para imagen procesada
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, mejorada)
                return tmp_file.name

        except Exception as e:
            raise OCRProcessingException(f"Error procesando imagen: {str(e)}")

    def detectar_celdas_tabla(self, imagen_path: str) -> List[Dict[str, Any]]:
        """
        Detecta celdas de tabla en una imagen.

        Args:
            imagen_path: Ruta de la imagen

        Returns:
            List[Dict[str, Any]]: Lista de celdas detectadas con coordenadas
        """
        try:
            imagen = cv2.imread(imagen_path)
            gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

            # Detectar bordes
            bordes = cv2.Canny(gris, 50, 150)

            # Detectar líneas horizontales y verticales
            lineas_h = self._detectar_lineas_horizontal(bordes)
            lineas_v = self._detectar_lineas_vertical(bordes)

            # Crear celdas a partir de intersecciones
            celdas = self._crear_celdas_desde_lineas(lineas_h, lineas_v)

            return celdas

        except Exception as e:
            print(f"Error detectando celdas: {e}")
            return []

    def _detectar_lineas_horizontal(self, bordes):
        """Detecta líneas horizontales en imagen."""
        # Implementación simplificada
        return []

    def _detectar_lineas_vertical(self, bordes):
        """Detecta líneas verticales en imagen."""
        # Implementación simplificada
        return []

    def _crear_celdas_desde_lineas(self, lineas_h, lineas_v):
        """Crea celdas a partir de líneas detectadas."""
        # Implementación simplificada
        return []


def procesar_pdf_ocr_view(archivo_pdf: UploadedFile) -> Dict[str, Any]:
    """
    Función de conveniencia para procesar PDF desde vistas.

    Args:
        archivo_pdf: Archivo PDF subido

    Returns:
        Dict[str, Any]: Resultado del procesamiento
    """
    try:
        procesador = OCRProcessor()
        return procesador.procesar_pdf_ocr(archivo_pdf)
    except Exception as e:
        return {
            'success': False,
            'error': f"Error procesando PDF: {str(e)}"
        }