"""
Adaptador para LandingAI ADE (Advanced Document Extraction).
Integra la API de LandingAI Vision Agent para procesamiento OCR avanzado.
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile
import tempfile

from .base import BaseOCRService
from ..exceptions import OCRProcessingException


# Importar LandingAI ADE
try:
    from landingai_ade import LandingAIADE
    LANDINGAI_AVAILABLE = True
except ImportError:
    LANDINGAI_AVAILABLE = False


class LandingAIAdapter(BaseOCRService):
    """
    Adaptador para integrar LandingAI ADE con el sistema OCR existente.

    Características:
    - Procesamiento OCR avanzado con IA
    - Extracción estructurada de datos
    - Análisis de layouts complejos
    - Mayor precisión que Tesseract tradicional
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Inicializa el adaptador de LandingAI.

        Args:
            api_key: API key de LandingAI (si no se provee, usa variable de entorno)
            **kwargs: Argumentos adicionales para BaseOCRService
        """
        super().__init__(**kwargs)

        if not LANDINGAI_AVAILABLE:
            raise OCRProcessingException(
                "LandingAI ADE no está disponible. Instale con: pip install landingai-ade"
            )

        # Configurar API key
        self.api_key = api_key or os.environ.get("VISION_AGENT_API_KEY")
        if not self.api_key:
            raise OCRProcessingException(
                "API Key de LandingAI no configurada. "
                "Configure VISION_AGENT_API_KEY en variables de entorno."
            )

        # Inicializar cliente LandingAI
        self.client = LandingAIADE(
            apikey=self.api_key,
            environment="production"  # Usar "eu" para servidores europeos
        )

        self.log_info("✅ LandingAI ADE Adapter inicializado")

    def process_document(
        self,
        document_path: str,
        model: str = "dpt-2-latest"
    ) -> Dict[str, Any]:
        """
        Procesa un documento usando LandingAI ADE.

        Args:
            document_path: Ruta al documento (PDF, imagen, etc.)
            model: Modelo de LandingAI a usar (dpt-2-latest es recomendado)

        Returns:
            Dict con chunks de texto extraído y metadatos
        """
        try:
            self.log_info(f"📄 Procesando documento con LandingAI: {document_path}")

            # Llamar a LandingAI API
            response = self.client.parse(
                document_url=document_path,
                model=model
            )

            # Procesar respuesta
            chunks = response.chunks if hasattr(response, 'chunks') else []

            self.log_info(f"✅ Documento procesado: {len(chunks)} chunks extraídos")

            return {
                'success': True,
                'chunks': chunks,
                'raw_response': response,
                'total_chunks': len(chunks),
                'error': None
            }

        except Exception as e:
            self.log_error(f"❌ Error procesando con LandingAI: {e}", exc_info=True)
            return {
                'success': False,
                'chunks': [],
                'raw_response': None,
                'total_chunks': 0,
                'error': str(e)
            }

    def process_uploaded_file(
        self,
        archivo: UploadedFile,
        model: str = "dpt-2-latest"
    ) -> Dict[str, Any]:
        """
        Procesa un archivo subido por el usuario.

        Args:
            archivo: Archivo subido (Django UploadedFile)
            model: Modelo de LandingAI a usar

        Returns:
            Dict con resultados del procesamiento
        """
        tmp_path = None

        try:
            # Guardar archivo temporalmente
            tmp_file = tempfile.NamedTemporaryFile(
                suffix=Path(archivo.name).suffix,
                delete=False
            )
            archivo.seek(0)
            tmp_file.write(archivo.read())
            tmp_file.close()
            tmp_path = tmp_file.name

            self.log_debug(f"💾 Archivo guardado temporalmente: {tmp_path}")

            # Procesar con LandingAI
            result = self.process_document(tmp_path, model)

            return result

        except Exception as e:
            self.log_error(f"❌ Error procesando archivo subido: {e}")
            return {
                'success': False,
                'chunks': [],
                'error': str(e)
            }

        finally:
            # Limpiar archivo temporal
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                    self.log_debug("🗑️ Archivo temporal eliminado")
                except Exception as e:
                    self.log_warning(f"⚠️ No se pudo eliminar archivo temporal: {e}")

    def extract_text_from_chunks(self, chunks: List[Any]) -> str:
        """
        Extrae texto plano de los chunks de LandingAI.

        Args:
            chunks: Lista de chunks retornados por LandingAI

        Returns:
            Texto completo concatenado
        """
        texto_completo = []

        for chunk in chunks:
            # Acceder al contenido del chunk
            if hasattr(chunk, 'content'):
                texto_completo.append(chunk.content)
            elif isinstance(chunk, dict) and 'content' in chunk:
                texto_completo.append(chunk['content'])
            elif hasattr(chunk, 'text'):
                texto_completo.append(chunk.text)
            elif isinstance(chunk, dict) and 'text' in chunk:
                texto_completo.append(chunk['text'])
            else:
                # Intentar convertir a string
                texto_completo.append(str(chunk))

        return "\n\n".join(texto_completo)

    def extract_structured_data(
        self,
        markdown_content: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extrae datos estructurados usando un schema de Pydantic.

        Args:
            markdown_content: Contenido en markdown
            schema: Schema JSON generado desde Pydantic

        Returns:
            Dict con datos extraídos
        """
        try:
            self.log_info("📊 Extrayendo datos estructurados con schema")

            response = self.client.extract(
                schema=schema,
                markdown=markdown_content
            )

            self.log_info("✅ Extracción estructurada completada")

            return {
                'success': True,
                'data': response,
                'error': None
            }

        except Exception as e:
            self.log_error(f"❌ Error en extracción estructurada: {e}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }

    def process_pdf_pages(
        self,
        pdf_path: str,
        model: str = "dpt-2-latest"
    ) -> List[Dict[str, Any]]:
        """
        Procesa todas las páginas de un PDF.

        Args:
            pdf_path: Ruta al archivo PDF
            model: Modelo de LandingAI

        Returns:
            Lista de resultados por página
        """
        try:
            # Procesar documento completo
            result = self.process_document(pdf_path, model)

            if not result['success']:
                return []

            # Convertir chunks a formato compatible con el sistema existente
            resultados = []
            chunks = result['chunks']

            # Agrupar chunks por página si es posible
            # (LandingAI puede incluir metadata de página en cada chunk)
            for i, chunk in enumerate(chunks, start=1):
                texto = ""
                pagina_num = i

                # Extraer texto y número de página
                if hasattr(chunk, 'content'):
                    texto = chunk.content
                if hasattr(chunk, 'page_number'):
                    pagina_num = chunk.page_number
                elif isinstance(chunk, dict):
                    texto = chunk.get('content', chunk.get('text', str(chunk)))
                    pagina_num = chunk.get('page_number', i)

                resultados.append({
                    'pagina': pagina_num,
                    'texto_extraido': texto,
                    'confianza': 95.0,  # LandingAI tiene alta confianza por defecto
                    'caracteres': len(texto),
                    'error': None,
                    'chunk_index': i,
                    'source': 'landingai'
                })

            self.log_info(f"✅ PDF procesado: {len(resultados)} páginas/chunks")
            return resultados

        except Exception as e:
            self.log_error(f"❌ Error procesando PDF: {e}")
            return []

    def get_available_models(self) -> List[str]:
        """
        Retorna lista de modelos disponibles de LandingAI.

        Returns:
            Lista de nombres de modelos
        """
        return [
            "dpt-2-latest",  # Modelo más reciente y recomendado
            "dpt-1",         # Versión anterior
        ]


# Función de utilidad para crear cliente
def create_landingai_client(api_key: Optional[str] = None) -> LandingAIAdapter:
    """
    Crea una instancia del adaptador de LandingAI.

    Args:
        api_key: API key de LandingAI (opcional)

    Returns:
        LandingAIAdapter configurado
    """
    return LandingAIAdapter(api_key=api_key)
