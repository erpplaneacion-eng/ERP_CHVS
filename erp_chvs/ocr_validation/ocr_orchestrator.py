"""
Orquestador principal para el procesamiento OCR avanzado.
Coordina la extracción de texto, datos estructurados y DataFrames.
"""

import os
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.files.storage import default_storage
import pandas as pd

from .models import PDFValidation
from .dataframe_extractor import DataFrameExtractor
from .services.landingai_adapter import LandingAIAdapter
from .exceptions import OCRProcessingException


class OCROrchestrator:
    """
    Orquestador principal que coordina todo el procesamiento OCR:
    
    1. Extracción básica de texto
    2. Extracción estructurada con schemas
    3. Conversión a DataFrames
    4. Validación de datos
    5. Persistencia en base de datos
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa el orquestador con los servicios necesarios."""
        self.api_key = api_key or getattr(settings, 'LANDINGAI_API_KEY', None)
        
        # Inicializar servicios
        self.dataframe_extractor = DataFrameExtractor(api_key=self.api_key)
        self.landingai_adapter = LandingAIAdapter(api_key=self.api_key)
        
    def process_pdf_complete(
        self,
        pdf_path: str,
        model: str = "dpt-2-latest",
        save_to_db: bool = True,
        usuario=None
    ) -> Dict[str, Any]:
        """
        Procesa un PDF completamente con extracción estructurada.
        
        Args:
            pdf_path: Ruta al archivo PDF
            model: Modelo de LandingAI a usar
            save_to_db: Si guardar en base de datos
            
        Returns:
            Dict con todos los resultados del procesamiento
        """
        try:
            # 1. Validar archivo
            if not os.path.exists(pdf_path):
                raise OCRProcessingException(f"Archivo no encontrado: {pdf_path}")
                
            # 2. Extracción estructurada a DataFrames
            resultado_dataframes = self.dataframe_extractor.extract_to_dataframe(
                pdf_path=pdf_path,
                model=model
            )
            
            if not resultado_dataframes['success']:
                raise OCRProcessingException(f"Error en extracción: {resultado_dataframes.get('error')}")
            
            # 3. Extraer componentes
            df_estudiantes = resultado_dataframes['df_estudiantes']
            df_encabezado = resultado_dataframes['df_encabezado']
            datos_json = resultado_dataframes['datos_json']
            metadatos = resultado_dataframes['metadatos']
            texto_completo = resultado_dataframes['texto_completo']
            
            # 4. Validaciones adicionales
            validaciones = self._validar_datos_extraidos(df_estudiantes, df_encabezado)
            
            # 5. Crear resumen
            resumen = self._crear_resumen_procesamiento(
                df_estudiantes, df_encabezado, metadatos, validaciones
            )
            
            # 6. Guardar en base de datos si se solicita
            pdf_validation_id = None
            if save_to_db:
                pdf_validation_id = self._guardar_en_db(
                    pdf_path=pdf_path,
                    datos_json=datos_json,
                    metadatos=metadatos,
                    texto_completo=texto_completo,
                    resumen=resumen,
                    usuario=usuario
                )
            
            return {
                'success': True,
                'pdf_validation_id': pdf_validation_id,
                'df_estudiantes': df_estudiantes,
                'df_encabezado': df_encabezado,
                'datos_json': datos_json,
                'metadatos': metadatos,
                'texto_completo': texto_completo,
                'validaciones': validaciones,
                'resumen': resumen,
                'archivo_procesado': pdf_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'archivo_procesado': pdf_path
            }
    
    def _validar_datos_extraidos(
        self,
        df_estudiantes: pd.DataFrame,
        df_encabezado: pd.DataFrame
    ) -> Dict[str, Any]:
        """Valida la calidad de los datos extraídos."""
        validaciones = {
            'estudiantes': {
                'total_filas': len(df_estudiantes),
                'columnas_con_datos': 0,
                'filas_completas': 0,
                'campos_faltantes': []
            },
            'encabezado': {
                'campos_detectados': 0,
                'campos_faltantes': []
            },
            'calidad_general': 'buena'  # buena, regular, mala
        }
        
        # Validar estudiantes
        if not df_estudiantes.empty:
            # Contar columnas con datos
            validaciones['estudiantes']['columnas_con_datos'] = df_estudiantes.count().sum()
            
            # Contar filas con datos completos
            validaciones['estudiantes']['filas_completas'] = df_estudiantes.dropna().shape[0]
            
            # Campos esperados
            campos_esperados = ['numero', 'nombre_completo', 'cedula', 'grado', 'raciones_entregadas']
            for campo in campos_esperados:
                if campo not in df_estudiantes.columns or df_estudiantes[campo].isna().all():
                    validaciones['estudiantes']['campos_faltantes'].append(campo)
        
        # Validar encabezado
        if not df_encabezado.empty:
            campos_encabezado = ['departamento', 'municipio', 'institucion_educativa', 'sede_educativa']
            for campo in campos_encabezado:
                if campo in df_encabezado.columns and not df_encabezado[campo].isna().all():
                    validaciones['encabezado']['campos_detectados'] += 1
                else:
                    validaciones['encabezado']['campos_faltantes'].append(campo)
        
        # Determinar calidad general
        if len(validaciones['estudiantes']['campos_faltantes']) <= 1 and validaciones['encabezado']['campos_detectados'] >= 2:
            validaciones['calidad_general'] = 'buena'
        elif len(validaciones['estudiantes']['campos_faltantes']) <= 3:
            validaciones['calidad_general'] = 'regular'
        else:
            validaciones['calidad_general'] = 'mala'
            
        return validaciones
    
    def _crear_resumen_procesamiento(
        self,
        df_estudiantes: pd.DataFrame,
        df_encabezado: pd.DataFrame,
        metadatos: Dict[str, Any],
        validaciones: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea un resumen del procesamiento."""
        return {
            'total_estudiantes': len(df_estudiantes),
            'total_raciones': df_estudiantes['raciones_entregadas'].sum() if 'raciones_entregadas' in df_estudiantes.columns else 0,
            'calidad_extraccion': validaciones['calidad_general'],
            'campos_estudiantes_detectados': len([col for col in df_estudiantes.columns if not df_estudiantes[col].isna().all()]),
            'campos_encabezado_detectados': validaciones['encabezado']['campos_detectados'],
            'texto_procesado_chars': metadatos.get('texto_original_length', 0),
            'metodo_extraccion': 'landingai_dataframe'
        }
    
    def _guardar_en_db(
        self,
        pdf_path: str,
        datos_json: Dict[str, Any],
        metadatos: Dict[str, Any],
        texto_completo: str,
        resumen: Dict[str, Any],
        usuario=None
    ) -> int:
        """Guarda los resultados en la base de datos."""
        try:
            # Extraer información del encabezado si está disponible
            encabezado = datos_json.get('encabezado', {})
            
            # Crear registro PDFValidation con los campos correctos
            pdf_validation = PDFValidation.objects.create(
                archivo_nombre=os.path.basename(pdf_path),
                archivo_path=pdf_path,
                sede_educativa=encabezado.get('institucion_educativa', 'No detectada'),
                mes_atencion=encabezado.get('mes_atencion', 'No detectado'),
                ano=encabezado.get('ano', 2025),
                tipo_complemento=encabezado.get('tipo_complemento', 'No detectado'),
                usuario_creador=usuario,
                estado='completado',
                metodo_ocr='landingai',
                datos_estructurados=datos_json,
                metadatos_extraccion=metadatos,
                texto_completo=texto_completo[:10000],  # Limitar tamaño
                total_errores=0,  # Para DataFrames no calculamos errores tradicionales
                errores_criticos=0,
                errores_advertencia=0,
                observaciones=f"Procesamiento completo. Calidad: {resumen['calidad_extraccion']}"
            )
            
            return pdf_validation.id
            
        except Exception as e:
            raise OCRProcessingException(f"Error guardando en BD: {e}")
    
    def export_dataframes(
        self,
        df_estudiantes: pd.DataFrame,
        df_encabezado: pd.DataFrame,
        output_dir: str,
        base_name: str = "extraccion_pdf"
    ) -> Dict[str, str]:
        """
        Exporta los DataFrames a múltiples formatos.
        
        Args:
            df_estudiantes: DataFrame de estudiantes
            df_encabezado: DataFrame de encabezado
            output_dir: Directorio de salida
            base_name: Nombre base para los archivos
            
        Returns:
            Dict con rutas de archivos generados
        """
        archivos_generados = {}
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Exportar estudiantes
            estudiantes_path = os.path.join(output_dir, f"{base_name}_estudiantes")
            archivos_estudiantes = self.dataframe_extractor.export_to_formats(
                df_estudiantes, estudiantes_path
            )
            
            # Exportar encabezado
            encabezado_path = os.path.join(output_dir, f"{base_name}_encabezado")
            archivos_encabezado = self.dataframe_extractor.export_to_formats(
                df_encabezado, encabezado_path
            )
            
            # Combinar resultados
            for formato, ruta in archivos_estudiantes.items():
                archivos_generados[f"estudiantes_{formato}"] = ruta
                
            for formato, ruta in archivos_encabezado.items():
                archivos_generados[f"encabezado_{formato}"] = ruta
            
            return archivos_generados
            
        except Exception as e:
            raise OCRProcessingException(f"Error exportando archivos: {e}")
    
    def get_processing_results(self, pdf_validation_id: int) -> Dict[str, Any]:
        """
        Recupera los resultados de un procesamiento previo.
        
        Args:
            pdf_validation_id: ID del registro PDFValidation
            
        Returns:
            Dict con los datos procesados
        """
        try:
            validation = PDFValidation.objects.get(id=pdf_validation_id)
            
            # Reconstruir DataFrames desde JSON
            datos_json = validation.datos_estructurados or {}
            
            df_estudiantes = pd.DataFrame()
            df_encabezado = pd.DataFrame()
            
            if 'estudiantes' in datos_json:
                df_estudiantes = pd.DataFrame(datos_json['estudiantes'])
                
            if 'encabezado' in datos_json:
                df_encabezado = pd.DataFrame([datos_json['encabezado']])
            
            return {
                'success': True,
                'pdf_validation': validation,
                'df_estudiantes': df_estudiantes,
                'df_encabezado': df_encabezado,
                'datos_json': datos_json,
                'metadatos': validation.metadatos_extraccion or {},
                'texto_completo': validation.texto_completo or ''
            }
            
        except PDFValidation.DoesNotExist:
            return {
                'success': False,
                'error': f"No se encontró el registro con ID {pdf_validation_id}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }