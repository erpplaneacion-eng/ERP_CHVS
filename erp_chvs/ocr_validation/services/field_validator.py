"""
Servicio para validación de campos diligenciados en el PDF.
Valida raciones, nombres, firmas y otros campos manuales.
"""

from typing import Dict, List, Any

from .base import BaseOCRService


class FieldValidatorService(BaseOCRService):
    """
    Servicio para validar campos diligenciados manualmente en el PDF.
    Utiliza los validadores mejorados existentes.
    """

    def __init__(self, **kwargs):
        """Inicializa el servicio de validación de campos."""
        super().__init__(**kwargs)

        # Importar validadores existentes
        try:
            from ..validadores_mejorados import (
                ValidadorRacionesMejorado,
                ValidadorNombresFirmas,
                ValidadorAsistenciaMejorado
            )
            self.validador_raciones = ValidadorRacionesMejorado()
            self.validador_nombres = ValidadorNombresFirmas()
            self.validador_asistencia = ValidadorAsistenciaMejorado()
            self.log_debug("✅ Validadores de campos cargados")
        except ImportError as e:
            self.log_warning(f"⚠️ No se pudieron cargar validadores: {e}")
            self.validador_raciones = None
            self.validador_nombres = None
            self.validador_asistencia = None

    def validate_fields(self, resultados_ocr: List[Dict], info_pdf: Dict) -> List[Dict[str, Any]]:
        """
        Valida todos los campos del PDF.

        Args:
            resultados_ocr: Lista de resultados de OCR por página
            info_pdf: Información básica del PDF

        Returns:
            Lista de errores encontrados
        """
        errores = []

        self.log_info("🔍 Validando campos diligenciados...")

        # Procesar cada página
        for resultado in resultados_ocr:
            pagina_num = resultado['pagina']
            texto_ocr = resultado.get('texto_extraido', '')
            confianza = resultado.get('confianza', 0.0)

            # Validar confianza OCR
            if confianza < self.config.confianza_minima:
                errores.append({
                    'tipo': 'confianza_ocr_baja',
                    'descripcion': f'La confianza del OCR en página {pagina_num} es baja ({confianza:.1f}%)',
                    'pagina': pagina_num,
                    'severidad': 'advertencia',
                    'campo': 'ocr_general'
                })

            # Analizar texto OCR
            errores_pagina = self._validate_page_content(texto_ocr, pagina_num)
            errores.extend(errores_pagina)

        self.log_info(f"✅ Validación completada: {len(errores)} errores encontrados")
        return errores

    def _validate_page_content(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """
        Valida el contenido de una página.

        Args:
            texto_ocr: Texto extraído de la página
            pagina: Número de página

        Returns:
            Lista de errores de la página
        """
        errores = []

        if not texto_ocr.strip():
            return errores

        texto_lower = texto_ocr.lower()

        # 1. Validar raciones
        errores_raciones = self._validate_raciones(texto_ocr, pagina)
        errores.extend(errores_raciones)

        # 2. Validar nombres y firmas
        errores_nombres = self._validate_nombres_firmas(texto_ocr, pagina)
        errores.extend(errores_nombres)

        # 3. Validar asistencia
        errores_asistencia = self._validate_asistencia(texto_ocr, pagina)
        errores.extend(errores_asistencia)

        return errores

    def _validate_raciones(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida raciones diarias y mensuales."""
        if not self.validador_raciones:
            return []

        try:
            return self.validador_raciones.validar_raciones(texto_ocr, pagina)
        except Exception as e:
            self.log_error(f"❌ Error validando raciones en página {pagina}: {e}")
            return []

    def _validate_nombres_firmas(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida nombres de estudiantes y firmas."""
        if not self.validador_nombres:
            return []

        try:
            return self.validador_nombres.validar_nombres_firmas(texto_ocr, pagina)
        except Exception as e:
            self.log_error(f"❌ Error validando nombres/firmas en página {pagina}: {e}")
            return []

    def _validate_asistencia(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida registros de asistencia."""
        if not self.validador_asistencia:
            return []

        try:
            return self.validador_asistencia.validar_asistencia(texto_ocr, pagina)
        except Exception as e:
            self.log_error(f"❌ Error validando asistencia en página {pagina}: {e}")
            return []

    def categorize_errors(self, errores: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Categoriza errores por severidad.

        Args:
            errores: Lista de errores

        Returns:
            Dict con conteo por severidad
        """
        categorias = {
            'critico': 0,
            'advertencia': 0,
            'info': 0
        }

        for error in errores:
            severidad = error.get('severidad', 'info')
            if severidad in categorias:
                categorias[severidad] += 1

        self.log_info(f"📊 Errores categorizados: {categorias}")
        return categorias
