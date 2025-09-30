"""
Orquestador principal del sistema OCR.
Coordina todos los servicios para procesar PDFs completos.
"""

import tempfile
from datetime import datetime
from typing import Dict, Any, List
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from .base import BaseOCRService
from .pdf_converter import PDFConverterService
from .image_processor import ImageProcessorService
from .text_extractor import TextExtractorService
from .header_validator import HeaderValidatorService
from .field_validator import FieldValidatorService
from ..models import PDFValidation, ValidationError
from ..exceptions import OCRProcessingException


class OCROrchestrator(BaseOCRService):
    """
    Orquestador principal que coordina todo el flujo de procesamiento OCR.

    Flujo:
    1. Convertir PDF → Imágenes (PDFConverterService)
    2. Preprocesar imágenes (ImageProcessorService)
    3. Extraer texto OCR (TextExtractorService)
    4. Validar encabezado (HeaderValidatorService)
    5. Validar campos (FieldValidatorService)
    6. Guardar resultados en BD
    """

    def __init__(self, **kwargs):
        """Inicializa el orquestador y todos los servicios."""
        super().__init__(**kwargs)

        # Inicializar servicios
        self.pdf_converter = PDFConverterService(dpi=400, config=self.config)
        self.image_processor = ImageProcessorService(config=self.config)
        self.text_extractor = TextExtractorService(language='spa', config=self.config)
        self.header_validator = HeaderValidatorService(config=self.config)
        self.field_validator = FieldValidatorService(config=self.config)

        self.log_info("✅ OCROrchestrator inicializado con todos los servicios")

    def process_pdf(self, archivo_pdf: UploadedFile, usuario=None) -> Dict[str, Any]:
        """
        Procesa un PDF completo con OCR y validación.

        Args:
            archivo_pdf: Archivo PDF subido por el usuario
            usuario: Usuario que realizó la carga

        Returns:
            Dict con resultados del procesamiento
        """
        inicio_tiempo = datetime.now()
        tmp_pdf_path = None
        image_paths = []

        self.log_info("="*80)
        self.log_info(f"🚀 Iniciando procesamiento OCR: {archivo_pdf.name}")
        self.log_info(f"👤 Usuario: {usuario}")
        self.log_info("="*80)

        try:
            # === PASO 1: Crear registro inicial ===
            validacion = self._create_validation_record(archivo_pdf, usuario)
            self.log_info(f"✅ Registro creado (ID: {validacion.id})")

            # === PASO 2: Guardar PDF temporalmente ===
            tmp_pdf_path = self._save_temp_pdf(archivo_pdf)

            # === PASO 3: Convertir PDF a imágenes ===
            image_paths = self.pdf_converter.convert_to_images(tmp_pdf_path)

            # === PASO 4: Procesar imágenes y extraer texto ===
            resultados_ocr = self._process_images(image_paths)

            # === PASO 5: Extraer y validar encabezado ===
            encabezado = self._extract_and_validate_header(resultados_ocr, archivo_pdf.name)

            # === PASO 6: Validar campos diligenciados ===
            errores = self._validate_fields(resultados_ocr, encabezado)

            # === PASO 7: Actualizar registro con resultados ===
            tiempo_total = (datetime.now() - inicio_tiempo).total_seconds()
            self._update_validation_record(validacion, encabezado, errores, tiempo_total)

            self.log_info("="*80)
            self.log_info(f"✅ Procesamiento completado en {tiempo_total:.2f}s")
            self.log_info(f"📊 Total de errores: {len(errores)}")
            self.log_info("="*80)

            return {
                'success': True,
                'validacion_id': validacion.id,
                'total_errores': len(errores),
                'tiempo_procesamiento': tiempo_total,
                'sede_educativa': encabezado.get('sede_educativa'),
                'errores': errores
            }

        except Exception as e:
            self.log_error(f"❌ Error en procesamiento: {e}", exc_info=True)
            tiempo_total = (datetime.now() - inicio_tiempo).total_seconds()

            return {
                'success': False,
                'error': str(e),
                'tiempo_procesamiento': tiempo_total
            }

        finally:
            # Limpieza de archivos temporales
            self._cleanup(tmp_pdf_path, image_paths)

    def _create_validation_record(self, archivo_pdf: UploadedFile, usuario) -> PDFValidation:
        """Crea registro inicial de validación en BD."""
        self.log_info("📝 Creando registro de validación...")

        info_basica = self._parse_filename(archivo_pdf.name)

        validacion = PDFValidation.objects.create(
            archivo_nombre=archivo_pdf.name,
            archivo_path='',
            sede_educativa=info_basica.get('sede', 'Pendiente de OCR'),
            mes_atencion=info_basica.get('mes', 'Pendiente'),
            ano=info_basica.get('ano', datetime.now().year),
            tipo_complemento=info_basica.get('complemento', 'Pendiente'),
            usuario_creador=usuario,
            estado='procesando'
        )

        return validacion

    def _save_temp_pdf(self, archivo_pdf: UploadedFile) -> str:
        """Guarda PDF en archivo temporal."""
        self.log_debug("💾 Guardando PDF temporal...")

        tmp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        archivo_pdf.seek(0)
        tmp_file.write(archivo_pdf.read())
        tmp_file.close()

        self.log_debug(f"  → {tmp_file.name}")
        return tmp_file.name

    def _process_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Procesa imágenes: preprocesamiento + extracción OCR."""
        self.log_info(f"🖼️ Procesando {len(image_paths)} imágenes...")

        resultados = []

        for i, image_path in enumerate(image_paths, start=1):
            self.log_info(f"📄 Procesando página {i}/{len(image_paths)}")

            # Preprocesar imagen
            processed_image = self.image_processor.process_image(image_path)

            # Extraer texto OCR
            resultado = self.text_extractor.extract_text(processed_image, page_num=i)
            resultados.append(resultado)

        return resultados

    def _extract_and_validate_header(self, resultados_ocr: List[Dict], nombre_archivo: str) -> Dict[str, Any]:
        """Extrae y valida encabezado del PDF."""
        self.log_info("📋 Extrayendo encabezado...")

        # Combinar texto de todas las páginas
        texto_completo = self._combine_ocr_text(resultados_ocr)

        # Extraer encabezado
        encabezado = self.header_validator.extract_header(texto_completo)

        # Validar encabezado
        errores_encabezado = self.header_validator.validate_header(encabezado, nombre_archivo)

        if errores_encabezado:
            self.log_warning(f"⚠️ {len(errores_encabezado)} errores en encabezado")

        return encabezado

    def _validate_fields(self, resultados_ocr: List[Dict], encabezado: Dict) -> List[Dict[str, Any]]:
        """Valida campos diligenciados del PDF."""
        self.log_info("✅ Validando campos diligenciados...")

        errores = self.field_validator.validate_fields(resultados_ocr, encabezado)

        return errores

    def _update_validation_record(
        self,
        validacion: PDFValidation,
        encabezado: Dict[str, Any],
        errores: List[Dict[str, Any]],
        tiempo_procesamiento: float
    ):
        """Actualiza registro de validación con resultados."""
        self.log_info("💾 Actualizando registro de validación...")

        # Categorizar errores
        categorias = self.field_validator.categorize_errors(errores)

        # Actualizar campos del registro
        validacion.sede_educativa = encabezado.get('sede_educativa') or validacion.sede_educativa
        validacion.mes_atencion = encabezado.get('mes_atencion') or validacion.mes_atencion
        validacion.ano = encabezado.get('ano') or validacion.ano
        validacion.tipo_complemento = encabezado.get('tipo_complemento') or validacion.tipo_complemento
        validacion.estado = 'completado'
        validacion.fecha_completado = timezone.now()
        validacion.tiempo_procesamiento = tiempo_procesamiento
        validacion.total_errores = len(errores)
        validacion.errores_criticos = categorias.get('critico', 0)
        validacion.errores_advertencia = categorias.get('advertencia', 0)

        # Observaciones
        if categorias.get('critico', 0) > 0:
            validacion.observaciones = f"Documento con {categorias['critico']} errores críticos."
        elif categorias.get('advertencia', 0) > 0:
            validacion.observaciones = f"Documento con {categorias['advertencia']} advertencias."
        else:
            validacion.observaciones = "Documento procesado exitosamente sin errores."

        validacion.save()

        # Guardar errores en BD
        self._save_errors(validacion, errores)

        self.log_info(f"✅ Registro actualizado (ID: {validacion.id})")

    def _save_errors(self, validacion: PDFValidation, errores: List[Dict[str, Any]]):
        """Guarda errores en la base de datos."""
        if not errores:
            return

        self.log_debug(f"💾 Guardando {len(errores)} errores en BD...")

        error_objects = [
            ValidationError(
                validacion=validacion,
                tipo_error=error.get('tipo', 'desconocido'),
                descripcion=error.get('descripcion', ''),
                pagina=error.get('pagina', 1),
                fila_estudiante=error.get('fila_estudiante'),
                columna_campo=error.get('campo'),
                severidad=error.get('severidad', 'info'),
                resuelto=False
            )
            for error in errores
        ]

        ValidationError.objects.bulk_create(error_objects)
        self.log_debug(f"  ✅ {len(error_objects)} errores guardados")

    def _combine_ocr_text(self, resultados_ocr: List[Dict]) -> str:
        """Combina texto OCR de todas las páginas."""
        texto_completo = ""
        for resultado in resultados_ocr:
            texto_completo += resultado.get('texto_extraido', '') + "\n"
        return texto_completo

    def _parse_filename(self, filename: str) -> Dict[str, str]:
        """Parsea información del nombre del archivo."""
        partes = filename.replace('.pdf', '').split('_')

        return {
            'sede': partes[1] if len(partes) > 1 else 'Desconocida',
            'complemento': partes[2] if len(partes) > 2 else 'Desconocido',
            'mes': partes[3] if len(partes) > 3 else 'Desconocido',
            'ano': int(partes[4]) if len(partes) > 4 and partes[4].isdigit() else datetime.now().year
        }

    def _cleanup(self, tmp_pdf_path: str, image_paths: List[str]):
        """Limpia archivos temporales."""
        import os

        self.log_debug("🗑️ Limpiando archivos temporales...")

        # Eliminar PDF temporal
        if tmp_pdf_path and os.path.exists(tmp_pdf_path):
            try:
                os.unlink(tmp_pdf_path)
                self.log_debug(f"  ✓ PDF temporal eliminado")
            except Exception as e:
                self.log_warning(f"  ⚠️ No se pudo eliminar PDF: {e}")

        # Eliminar imágenes
        self.pdf_converter.cleanup_images(image_paths)
