"""
Orquestador principal del sistema OCR con LandingAI ADE.
"""
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from .base import BaseOCRService
from .landingai_adapter import LandingAIAdapter
from .header_validator import HeaderValidatorService
from .field_validator import FieldValidatorService
from ..models import PDFValidation, ValidationError
from ..exceptions import OCRProcessingException


class OCROrchestrator(BaseOCRService):
    def __init__(self, landingai_api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        try:
            self.landingai_adapter = LandingAIAdapter(api_key=landingai_api_key, config=self.config)
        except Exception as e:
            raise OCRProcessingException(f"Error inicializando LandingAI: {e}")
        self.header_validator = HeaderValidatorService(config=self.config)
        self.field_validator = FieldValidatorService(config=self.config)

    def process_pdf(self, archivo_pdf: UploadedFile, usuario=None) -> Dict[str, Any]:
        inicio = datetime.now()
        tmp_path = None
        try:
            validacion = self._create_validation_record(archivo_pdf, usuario)
            tmp_path = self._save_temp_pdf(archivo_pdf)
            resultados = self.landingai_adapter.process_pdf_pages(tmp_path, "dpt-2-latest")
            if not resultados:
                raise OCRProcessingException("LandingAI no retornó resultados")
            encabezado = self._extract_header(resultados, archivo_pdf.name)
            errores = self._validate_fields(resultados, encabezado)
            tiempo = (datetime.now() - inicio).total_seconds()
            self._update_record(validacion, encabezado, errores, tiempo)
            return {'success': True, 'validacion_id': validacion.id, 'total_errores': len(errores),
                    'tiempo_procesamiento': tiempo, 'metodo_ocr': 'landingai', 'errores': errores}
        except Exception as e:
            return {'success': False, 'error': str(e), 'metodo_ocr': 'landingai'}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _save_temp_pdf(self, archivo):
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        archivo.seek(0)
        tmp.write(archivo.read())
        tmp.close()
        return tmp.name

    def _create_validation_record(self, archivo, usuario):
        info = self._parse_filename(archivo.name)
        return PDFValidation.objects.create(
            archivo_nombre=archivo.name, archivo_path='',
            sede_educativa=info.get('sede', 'Pendiente'),
            mes_atencion=info.get('mes', 'Pendiente'),
            ano=info.get('ano', datetime.now().year),
            tipo_complemento=info.get('complemento', 'Pendiente'),
            usuario_creador=usuario, estado='procesando', metodo_ocr='landingai')

    def _extract_header(self, resultados, nombre):
        texto = "\n".join([r.get('texto_extraido', '') for r in resultados])
        encabezado = self.header_validator.extract_header(texto)
        self.header_validator.validate_header(encabezado, nombre)
        return encabezado

    def _validate_fields(self, resultados, encabezado):
        return self.field_validator.validate_fields(resultados, encabezado)

    def _update_record(self, val, enc, err, tiempo):
        cat = self.field_validator.categorize_errors(err)
        val.sede_educativa = enc.get('sede_educativa') or val.sede_educativa
        val.mes_atencion = enc.get('mes_atencion') or val.mes_atencion
        val.ano = enc.get('ano') or val.ano
        val.tipo_complemento = enc.get('tipo_complemento') or val.tipo_complemento
        val.estado = 'completado'
        val.fecha_completado = timezone.now()
        val.tiempo_procesamiento = tiempo
        val.total_errores = len(err)
        val.errores_criticos = cat.get('critico', 0)
        val.errores_advertencia = cat.get('advertencia', 0)
        val.metodo_ocr = 'landingai'
        val.observaciones = f"LandingAI: {cat.get('critico',0)} críticos" if cat.get('critico') else "LandingAI: OK"
        val.save()
        if err:
            ValidationError.objects.bulk_create([ValidationError(validacion=val, tipo_error=e.get('tipo','?'),
                descripcion=e.get('descripcion',''), pagina=e.get('pagina',1), fila_estudiante=e.get('fila_estudiante'),
                columna_campo=e.get('campo'), severidad=e.get('severidad','info'), resuelto=False) for e in err])

    def _parse_filename(self, filename):
        partes = filename.replace('.pdf', '').split('_')
        return {'sede': partes[1] if len(partes) > 1 else '?',
                'complemento': partes[2] if len(partes) > 2 else '?',
                'mes': partes[3] if len(partes) > 3 else '?',
                'ano': int(partes[4]) if len(partes) > 4 and partes[4].isdigit() else datetime.now().year}
