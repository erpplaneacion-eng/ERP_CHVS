"""
Servicio para extraer datos tabulares de PDFs y convertirlos a DataFrames.
Utiliza LandingAI ADE para extracción estructurada con schemas.
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json

from .base import BaseOCRService
from .landingai_adapter import LandingAIAdapter
from ..exceptions import OCRProcessingException


# ============================================
# SCHEMAS DE DATOS - Define la estructura esperada
# ============================================

class EstudianteRegistro(BaseModel):
    """Registro individual de un estudiante en el PDF."""
    numero: Optional[int] = Field(None, description="Número de lista del estudiante")
    nombre_completo: Optional[str] = Field(None, description="Nombre completo del estudiante")
    cedula: Optional[str] = Field(None, description="Número de cédula o documento")
    grado: Optional[str] = Field(None, description="Grado del estudiante")
    raciones_entregadas: Optional[int] = Field(None, description="Número de raciones entregadas")
    fecha_asistencia: Optional[str] = Field(None, description="Fecha de asistencia")
    firma_presente: Optional[bool] = Field(None, description="Si hay firma del estudiante/acudiente")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")


class EncabezadoPDF(BaseModel):
    """Información del encabezado del documento."""
    departamento: Optional[str] = Field(None, description="Departamento")
    municipio: Optional[str] = Field(None, description="Municipio")
    institucion_educativa: Optional[str] = Field(None, description="Nombre de la IE")
    sede_educativa: Optional[str] = Field(None, description="Sede educativa")
    codigo_dane: Optional[str] = Field(None, description="Código DANE")
    mes_atencion: Optional[str] = Field(None, description="Mes de atención")
    ano: Optional[int] = Field(None, description="Año")
    tipo_complemento: Optional[str] = Field(None, description="Tipo de complemento (PME, JC, etc)")
    responsable: Optional[str] = Field(None, description="Nombre del responsable")


class DocumentoCompleto(BaseModel):
    """Estructura completa del documento PDF."""
    encabezado: EncabezadoPDF = Field(description="Información del encabezado")
    estudiantes: List[EstudianteRegistro] = Field(description="Lista de estudiantes")
    total_estudiantes: Optional[int] = Field(None, description="Total de estudiantes")
    total_raciones: Optional[int] = Field(None, description="Total de raciones entregadas")


# ============================================
# SERVICIO DE EXTRACCIÓN A DATAFRAME
# ============================================

class DataFrameExtractor(BaseOCRService):
    """
    Servicio para extraer datos estructurados de PDFs y convertirlos a DataFrames de pandas.

    Utiliza LandingAI ADE con schemas Pydantic para extraer:
    - Información del encabezado
    - Tablas de estudiantes/asistencia
    - Datos de raciones
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Inicializa el extractor de DataFrames."""
        super().__init__(**kwargs)

        # Inicializar adaptador de LandingAI
        try:
            self.landingai = LandingAIAdapter(api_key=api_key, config=self.config)
            self.log_info("✅ DataFrameExtractor inicializado")
        except Exception as e:
            raise OCRProcessingException(f"Error inicializando LandingAI: {e}")

    def extract_to_dataframe(
        self,
        pdf_path: str,
        model: str = "dpt-2-latest"
    ) -> Dict[str, Any]:
        """
        Extrae datos del PDF y los convierte a DataFrames.

        Args:
            pdf_path: Ruta al archivo PDF
            model: Modelo de LandingAI a usar

        Returns:
            Dict con:
                - df_estudiantes: DataFrame con datos de estudiantes
                - df_encabezado: DataFrame con info del encabezado
                - datos_json: Datos completos en formato JSON
                - metadatos: Información adicional
        """
        try:
            self.log_info(f"📊 Extrayendo datos estructurados de: {pdf_path}")

            # 1. Procesar documento con LandingAI
            result = self.landingai.process_document(pdf_path, model)

            if not result['success']:
                raise OCRProcessingException(f"Error procesando PDF: {result.get('error')}")

            # 2. Extraer texto completo de chunks
            chunks = result['chunks']
            texto_completo = self.landingai.extract_text_from_chunks(chunks)

            self.log_info(f"📝 Texto extraído: {len(texto_completo)} caracteres")

            # 3. Extraer datos estructurados usando schema
            schema = DocumentoCompleto.model_json_schema()

            datos_estructurados = self.landingai.extract_structured_data(
                markdown_content=texto_completo,
                schema=schema
            )

            if not datos_estructurados['success']:
                # Si falla la extracción estructurada, intentar método alternativo
                self.log_warning("⚠️ Extracción estructurada falló, usando método alternativo")
                return self._extract_with_fallback(texto_completo, chunks)

            # 4. Convertir a DataFrames
            datos = datos_estructurados['data']

            # DataFrame de estudiantes
            if hasattr(datos, 'estudiantes'):
                estudiantes_data = [e.model_dump() for e in datos.estudiantes]
            elif isinstance(datos, dict) and 'estudiantes' in datos:
                estudiantes_data = datos['estudiantes']
            else:
                estudiantes_data = []

            df_estudiantes = pd.DataFrame(estudiantes_data)

            # DataFrame de encabezado
            if hasattr(datos, 'encabezado'):
                encabezado_data = datos.encabezado.model_dump()
            elif isinstance(datos, dict) and 'encabezado' in datos:
                encabezado_data = datos['encabezado']
            else:
                encabezado_data = {}

            df_encabezado = pd.DataFrame([encabezado_data])

            # 5. Calcular metadatos
            metadatos = {
                'total_estudiantes': len(df_estudiantes),
                'total_raciones': df_estudiantes['raciones_entregadas'].sum() if 'raciones_entregadas' in df_estudiantes.columns else 0,
                'columnas_estudiantes': list(df_estudiantes.columns),
                'columnas_encabezado': list(df_encabezado.columns),
                'filas_con_firma': df_estudiantes['firma_presente'].sum() if 'firma_presente' in df_estudiantes.columns else 0,
                'texto_original_length': len(texto_completo),
                'chunks_procesados': len(chunks)
            }

            self.log_info(f"✅ Extracción completada: {metadatos['total_estudiantes']} estudiantes")

            return {
                'success': True,
                'df_estudiantes': df_estudiantes,
                'df_encabezado': df_encabezado,
                'datos_json': datos if isinstance(datos, dict) else datos.model_dump() if hasattr(datos, 'model_dump') else {},
                'metadatos': metadatos,
                'texto_completo': texto_completo
            }

        except Exception as e:
            self.log_error(f"❌ Error en extracción a DataFrame: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'df_estudiantes': pd.DataFrame(),
                'df_encabezado': pd.DataFrame(),
                'datos_json': {},
                'metadatos': {}
            }

    def _extract_with_fallback(
        self,
        texto: str,
        chunks: List[Any]
    ) -> Dict[str, Any]:
        """
        Método alternativo de extracción cuando falla el schema.
        Usa parsing manual del texto.
        """
        self.log_info("🔄 Usando método de extracción alternativo")

        # Parsear texto manualmente (implementación simplificada)
        lineas = texto.split('\n')

        # Intentar extraer tabla de estudiantes
        estudiantes = []
        for linea in lineas:
            # Lógica simple de detección (mejorar según el formato real)
            if any(palabra in linea.lower() for palabra in ['estudiante', 'alumno', 'nombre']):
                # Parsear datos de la línea
                pass

        df_estudiantes = pd.DataFrame(estudiantes)
        df_encabezado = pd.DataFrame([{'texto_raw': texto[:500]}])  # Primeros 500 caracteres

        return {
            'success': True,
            'df_estudiantes': df_estudiantes,
            'df_encabezado': df_encabezado,
            'datos_json': {'metodo': 'fallback', 'texto': texto},
            'metadatos': {
                'metodo_extraccion': 'fallback',
                'total_estudiantes': len(estudiantes),
                'chunks_procesados': len(chunks)
            },
            'texto_completo': texto
        }

    def export_to_formats(
        self,
        df: pd.DataFrame,
        output_path: str,
        formats: List[str] = ['csv', 'excel', 'json']
    ) -> Dict[str, str]:
        """
        Exporta el DataFrame a múltiples formatos.

        Args:
            df: DataFrame a exportar
            output_path: Ruta base para los archivos
            formats: Lista de formatos ('csv', 'excel', 'json', 'html')

        Returns:
            Dict con rutas de archivos generados
        """
        archivos_generados = {}

        try:
            if 'csv' in formats:
                csv_path = f"{output_path}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                archivos_generados['csv'] = csv_path
                self.log_info(f"✅ CSV exportado: {csv_path}")

            if 'excel' in formats:
                excel_path = f"{output_path}.xlsx"
                df.to_excel(excel_path, index=False, engine='openpyxl')
                archivos_generados['excel'] = excel_path
                self.log_info(f"✅ Excel exportado: {excel_path}")

            if 'json' in formats:
                json_path = f"{output_path}.json"
                df.to_json(json_path, orient='records', force_ascii=False, indent=2)
                archivos_generados['json'] = json_path
                self.log_info(f"✅ JSON exportado: {json_path}")

            if 'html' in formats:
                html_path = f"{output_path}.html"
                df.to_html(html_path, index=False, encoding='utf-8')
                archivos_generados['html'] = html_path
                self.log_info(f"✅ HTML exportado: {html_path}")

            return archivos_generados

        except Exception as e:
            self.log_error(f"❌ Error exportando DataFrame: {e}")
            return {}
