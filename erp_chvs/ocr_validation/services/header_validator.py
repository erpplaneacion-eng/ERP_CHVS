"""
Servicio para validación del encabezado del PDF.
Extrae y valida la información del encabezado (sede, mes, año, etc.)
"""

from typing import Dict, Any, Optional, List

from .base import BaseOCRService


class HeaderValidatorService(BaseOCRService):
    """
    Servicio para extraer y validar el encabezado del PDF.
    Utiliza el ValidadorEncabezado existente para la lógica de extracción.
    """

    def __init__(self, **kwargs):
        """Inicializa el servicio de validación de encabezado."""
        super().__init__(**kwargs)

        # Importar ValidadorEncabezado existente
        try:
            from ..validador_encabezado import ValidadorEncabezado
            self.validador = ValidadorEncabezado()
            self.log_debug("✅ ValidadorEncabezado cargado")
        except ImportError as e:
            self.log_warning(f"⚠️ ValidadorEncabezado no disponible: {e}")
            self.validador = None

    def extract_header(self, texto_ocr: str) -> Dict[str, Any]:
        """
        Extrae información del encabezado del texto OCR.

        Args:
            texto_ocr: Texto completo extraído por OCR

        Returns:
            Dict con información del encabezado:
                - departamento
                - municipio
                - nombre_institucion
                - sede_educativa
                - mes_atencion
                - ano
                - tipo_complemento
                - codigo_dane_ie
        """
        if not self.validador:
            self.log_warning("⚠️ ValidadorEncabezado no disponible, retornando encabezado vacío")
            return self._empty_header()

        try:
            self.log_info("🔍 Extrayendo información del encabezado...")

            # Extraer encabezado usando ValidadorEncabezado
            encabezado = self.validador.extraer_encabezado(texto_ocr)

            # Log de información extraída
            self._log_extracted_header(encabezado)

            return encabezado

        except Exception as e:
            self.log_error(f"❌ Error extrayendo encabezado: {e}", exc_info=True)
            return self._empty_header()

    def validate_header(self, encabezado: Dict[str, Any], nombre_archivo: str) -> List[Dict[str, Any]]:
        """
        Valida la coherencia del encabezado extraído.

        Args:
            encabezado: Datos del encabezado extraídos
            nombre_archivo: Nombre del archivo para validación cruzada

        Returns:
            Lista de errores encontrados
        """
        if not self.validador:
            return []

        try:
            self.log_info("✅ Validando coherencia del encabezado...")
            errores = self.validador.validar_encabezado(encabezado, nombre_archivo)

            if errores:
                self.log_warning(f"⚠️ {len(errores)} errores encontrados en encabezado")
            else:
                self.log_info("✅ Encabezado válido, sin errores")

            return errores

        except Exception as e:
            self.log_error(f"❌ Error validando encabezado: {e}", exc_info=True)
            return []

    def extract_sede_educativa(self, texto_ocr: str) -> Optional[str]:
        """
        Extrae únicamente la sede educativa del texto OCR.

        Args:
            texto_ocr: Texto completo extraído por OCR

        Returns:
            str: Nombre de la sede educativa o None
        """
        encabezado = self.extract_header(texto_ocr)
        sede = encabezado.get('sede_educativa')

        if sede:
            self.log_info(f"✅ Sede educativa encontrada: '{sede}'")
        else:
            self.log_warning("⚠️ No se pudo extraer sede educativa del encabezado")

        return sede

    def get_context_info(self, encabezado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene información de contexto para otras validaciones.

        Args:
            encabezado: Datos del encabezado extraídos

        Returns:
            Dict con contexto de procesamiento
        """
        if not self.validador:
            return {}

        try:
            return self.validador.obtener_contexto_procesamiento(encabezado)
        except Exception as e:
            self.log_error(f"❌ Error obteniendo contexto: {e}")
            return {}

    def _empty_header(self) -> Dict[str, Any]:
        """Retorna un encabezado vacío."""
        return {
            'departamento': None,
            'codigo_dane_departamento': None,
            'municipio': None,
            'codigo_dane_municipio': None,
            'operador': None,
            'contrato': None,
            'mes_atencion': None,
            'ano': None,
            'nombre_institucion': None,
            'codigo_dane_ie': None,
            'tipo_complemento': None,
            'sede_educativa': None
        }

    def _log_extracted_header(self, encabezado: Dict[str, Any]):
        """Log detallado de información extraída del encabezado."""
        self.log_info("📋 Información del encabezado:")
        self.log_info(f"   🏫 Sede: {encabezado.get('sede_educativa')}")
        self.log_info(f"   🏢 Institución: {encabezado.get('nombre_institucion')}")
        self.log_info(f"   📅 Período: {encabezado.get('mes_atencion')} {encabezado.get('ano')}")
        self.log_info(f"   🍽️ Complemento: {encabezado.get('tipo_complemento')}")
        self.log_info(f"   📍 Municipio: {encabezado.get('municipio')}")
        self.log_info(f"   🏛️ Departamento: {encabezado.get('departamento')}")
