"""
Capa de servicios para orquestación de procesos complejos.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from django.core.files.uploadedfile import UploadedFile

from .excel_utils import ExcelProcessor
from .data_processors import DataTransformer
from .fuzzy_matching import FuzzyMatcher
from .validators import DataValidator
from .persistence_service import PersistenceService
from .config import ProcesamientoConfig, MensajesConfig
from .exceptions import (
    ArchivoInvalidoException, 
    ColumnasFaltantesException, 
    DatosInvalidosException,
    ProcesamientoException,
    ValidacionException
)

class ProcesamientoService:
    """Servicio principal para procesamiento de archivos Excel."""
    
    def __init__(self):
        """Inicializa el servicio de procesamiento."""
        self.excel_processor = ExcelProcessor()
        self.data_transformer = DataTransformer()
        self.fuzzy_matcher = FuzzyMatcher()
        self.data_validator = DataValidator()
        self.persistence_service = PersistenceService()
    
    def procesar_excel_nuevo_formato(
        self, 
        archivo: UploadedFile, 
        focalizacion: str
    ) -> Dict[str, Any]:
        """
        Servicio principal para procesamiento del nuevo formato (LOTE == 3).
        
        Args:
            archivo: Archivo Excel subido
            focalizacion: Focalización seleccionada
        
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        try:
            # 1. Validar archivo
            if not self.excel_processor.validar_archivo_excel(archivo):
                raise ArchivoInvalidoException(MensajesConfig.ARCHIVO_INVALIDO)
            
            # 2. Leer archivo Excel
            df = self.excel_processor.leer_excel(archivo)
            
            # 3. Validar estructura del nuevo formato
            es_valido, errores = self.excel_processor.validar_estructura_nuevo_formato(df)
            if not es_valido:
                raise ColumnasFaltantesException(errores)
            
            # 4. Procesar datos con formato nuevo
            df_procesado = self.data_transformer.procesar_formato_nuevo(df, focalizacion)
            
            # 5. Validar sedes usando coincidencia difusa
            resultado_validacion = self.fuzzy_matcher.validar_sedes_excel(
                df_procesado, 
                [ProcesamientoConfig.ETC_CALI]
            )
            
            # 6. Filtrar DataFrame por sedes válidas
            df_filtrado = self.fuzzy_matcher.filtrar_dataframe_por_sedes_validas(
                df_procesado, 
                resultado_validacion['sedes_validas']
            )
            
            # 7. Generar estadísticas
            estadisticas = self.data_transformer.generar_estadisticas_por_sede(
                df_filtrado, 
                resultado_validacion['mapeo_sedes'],
                [ProcesamientoConfig.ETC_CALI]
            )
            
            # 7.1. Aplicar mapeo de sedes para estandarizar los nombres antes de guardar.
            if resultado_validacion['mapeo_sedes']:
                df_filtrado = df_filtrado.copy()
                df_filtrado['SEDE'] = df_filtrado['SEDE'].map(resultado_validacion['mapeo_sedes']).fillna(df_filtrado['SEDE'])
            
            # 8. Preparar resultado
            resultado = self._preparar_resultado_exitoso(
                df_filtrado,
                resultado_validacion,
                estadisticas,
                ProcesamientoConfig.TIPO_PROCESAMIENTO_NUEVO
            )

            return resultado
            
        except Exception as e:
            return self._preparar_resultado_error(str(e))
    
    def procesar_excel_original(
        self, 
        archivo: UploadedFile, 
        focalizacion: str
    ) -> Dict[str, Any]:
        """
        Servicio principal para procesamiento del formato original.
        
        Args:
            archivo: Archivo Excel subido
            focalizacion: Focalización seleccionada
        
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        try:
            # 1. Validar archivo
            if not self.excel_processor.validar_archivo_excel(archivo):
                raise ArchivoInvalidoException(MensajesConfig.ARCHIVO_INVALIDO)
            
            # 2. Leer archivo Excel
            df = self.excel_processor.leer_excel(archivo)
            
            # 3. Validar estructura del formato original
            es_valido, errores = self.excel_processor.validar_estructura_original_formato(df)
            if not es_valido:
                raise ColumnasFaltantesException(errores)
            
            # 4. Procesar datos con formato original
            df_procesado = self.data_transformer.procesar_formato_original(df, focalizacion)
            
            # 5. Obtener municipios únicos del ETC
            municipios = df_procesado['ETC'].unique().tolist()
            
            # 6. Validar sedes usando coincidencia difusa
            resultado_validacion = self.fuzzy_matcher.validar_sedes_excel(
                df_procesado, 
                municipios
            )
            
            # 7. Filtrar DataFrame por sedes válidas
            df_filtrado = self.fuzzy_matcher.filtrar_dataframe_por_sedes_validas(
                df_procesado,
                resultado_validacion['sedes_validas']
            )

            # 8. Generar estadísticas
            # ¡IMPORTANTE! Generar estadísticas ANTES de mapear los nombres de las sedes.
            # La función de estadísticas necesita los nombres originales del Excel para agrupar.
            estadisticas = self.data_transformer.generar_estadisticas_por_sede(
                df_filtrado, 
                resultado_validacion['mapeo_sedes'],
                municipios
            )
            
            # 8.1. Ahora sí, aplicar mapeo de sedes para que los datos guardados sean consistentes.
            if resultado_validacion['mapeo_sedes']:
                df_filtrado = df_filtrado.copy()
                df_filtrado['SEDE'] = df_filtrado['SEDE'].map(resultado_validacion['mapeo_sedes']).fillna(df_filtrado['SEDE'])

            # 9. Preparar resultado
            resultado = self._preparar_resultado_exitoso(
                df_filtrado,
                resultado_validacion,
                estadisticas,
                ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL
            )

            return resultado
            
        except Exception as e:
            return self._preparar_resultado_error(str(e))
    
    def _preparar_resultado_exitoso(
        self,
        df: pd.DataFrame,
        resultado_validacion: Dict[str, Any],
        estadisticas: List[Dict[str, Any]],
        tipo_procesamiento: str
    ) -> Dict[str, Any]:
        """
        Prepara el resultado exitoso del procesamiento.
        
        Args:
            df: DataFrame procesado
            resultado_validacion: Resultado de validación de sedes
            estadisticas: Estadísticas generadas
            tipo_procesamiento: Tipo de procesamiento
        
        Returns:
            Dict[str, Any]: Resultado formateado
        """
        try:
            total_registros = len(df)
            
            # Generar mensaje de verificación
            mensaje_verificacion = self._generar_mensaje_verificacion(
                total_registros,
                resultado_validacion,
                tipo_procesamiento
            )
            
            # Preparar DataFrame HTML
            dataframe_html = self.data_transformer.preparar_dataframe_html(df)
            
            return {
                'success': True,
                'dataframe_html': dataframe_html,
                'dataframe': df,  # Agregar DataFrame para persistencia
                'verified_message': mensaje_verificacion,
                'invalid_sedes': resultado_validacion['sedes_invalidas'],
                'coincidencias_parciales': resultado_validacion['coincidencias_parciales'],
                'coincidencias_genericas': resultado_validacion['coincidencias_genericas'],
                'total_registros': total_registros,
                'agrupacion_sedes': estadisticas,
                'tipo_procesamiento': tipo_procesamiento
            }
            
        except Exception as e:
            return self._preparar_resultado_error(str(e))
    
    def _preparar_resultado_error(self, error: str) -> Dict[str, Any]:
        """
        Prepara el resultado de error del procesamiento.
        
        Args:
            error: Mensaje de error
        
        Returns:
            Dict[str, Any]: Resultado de error formateado
        """
        return {
            'success': False,
            'error': error,
            'dataframe_html': f"<div class='alert alert-danger'>Error al procesar el archivo: {error}</div>",
            'verified_message': None,
            'invalid_sedes': [],
            'coincidencias_parciales': [],
            'coincidencias_genericas': [],
            'total_registros': 0,
            'agrupacion_sedes': []
        }
    
    def _generar_mensaje_verificacion(
        self,
        total_registros: int,
        resultado_validacion: Dict[str, Any],
        tipo_procesamiento: str
    ) -> str:
        """
        Genera el mensaje de verificación basado en los resultados.
        
        Args:
            total_registros: Número total de registros procesados
            resultado_validacion: Resultado de validación de sedes
            tipo_procesamiento: Tipo de procesamiento
        
        Returns:
            str: Mensaje de verificación
        """
        try:
            if total_registros == 0:
                return MensajesConfig.NO_FILAS_VALIDAS
            
            sedes_invalidas = resultado_validacion['sedes_invalidas']
            coincidencias_parciales = resultado_validacion['coincidencias_parciales']
            coincidencias_genericas = resultado_validacion['coincidencias_genericas']
            
            if not sedes_invalidas:
                # Construir mensaje detallado sobre tipos de coincidencias
                mensaje_detalles = []
                
                if coincidencias_parciales:
                    mensaje_detalles.append(
                        MensajesConfig.COINCIDENCIAS_PARCIALES.format(
                            cantidad=len(coincidencias_parciales)
                        )
                    )
                
                if coincidencias_genericas:
                    mensaje_detalles.append(
                        MensajesConfig.COINCIDENCIAS_GENERICAS.format(
                            cantidad=len(coincidencias_genericas)
                        )
                    )
                
                if mensaje_detalles:
                    detalles_str = " y ".join(mensaje_detalles)
                    return f"Archivo procesado exitosamente con el {tipo_procesamiento} formato. Se procesaron {total_registros} registros. Se encontraron {detalles_str} que fueron aceptadas."
                else:
                    return f"Archivo procesado exitosamente con el {tipo_procesamiento} formato. Se procesaron {total_registros} registros. Todas las sedes coinciden exactamente con la base de datos."
            else:
                return f"Las siguientes sedes no se pudieron cargar: {', '.join(sedes_invalidas)}. Se procesaron {total_registros} registros con sedes válidas."
                
        except Exception as e:
            return f"Archivo procesado con {total_registros} registros."

    def procesar_y_guardar_excel(
        self,
        archivo: UploadedFile,
        focalizacion: str,
        tipo_procesamiento: str = ProcesamientoConfig.TIPO_PROCESAMIENTO_ORIGINAL,
        guardar_en_bd: bool = True
    ) -> Dict[str, Any]:
        """
        Procesa el archivo Excel y opcionalmente lo guarda en la base de datos.

        Args:
            archivo: Archivo Excel subido
            focalizacion: Focalización seleccionada
            tipo_procesamiento: Tipo de procesamiento a usar
            guardar_en_bd: Si debe guardar en la base de datos

        Returns:
            Dict[str, Any]: Resultado completo del procesamiento y persistencia
        """
        try:
            # 1. Procesar archivo según el tipo
            if tipo_procesamiento == ProcesamientoConfig.TIPO_PROCESAMIENTO_NUEVO:
                resultado_procesamiento = self.procesar_excel_nuevo_formato(archivo, focalizacion)
            else:
                resultado_procesamiento = self.procesar_excel_original(archivo, focalizacion)

            # 2. Si el procesamiento fue exitoso y se requiere guardar
            if resultado_procesamiento['success'] and guardar_en_bd:

                # Usar DataFrame directamente desde el resultado de procesamiento
                # Verificar si hay datos para guardar
                if resultado_procesamiento['total_registros'] > 0:
                    # Obtener DataFrame directamente del resultado
                    df_para_guardar = resultado_procesamiento.get('dataframe')

                    if df_para_guardar is not None and not df_para_guardar.empty:
                        # Guardar en la base de datos
                        resultado_persistencia = self.persistence_service.guardar_listados_focalizacion(
                            df_para_guardar
                        )

                        # Combinar resultados
                        resultado_procesamiento['persistencia'] = resultado_persistencia
                        resultado_procesamiento['registros_guardados_bd'] = resultado_persistencia.get('registros_guardados', 0)

                        # Actualizar mensaje de verificación
                        if resultado_persistencia['success']:
                            mensaje_original = resultado_procesamiento.get('verified_message', '')
                            mensaje_bd = f" Se guardaron {resultado_persistencia['registros_guardados']} registros en la base de datos."
                            resultado_procesamiento['verified_message'] = mensaje_original + mensaje_bd
                        else:
                            # Advertir sobre error en persistencia pero mantener éxito del procesamiento
                            resultado_procesamiento['advertencia_bd'] = resultado_persistencia.get('error', 'Error desconocido en persistencia')
                    else:
                        # DataFrame no disponible para persistencia
                        resultado_procesamiento['advertencia_bd'] = 'No se pudo obtener el DataFrame para persistencia. El procesamiento fue exitoso pero no se guardaron datos en la base de datos.'
                else:
                    resultado_procesamiento['advertencia_bd'] = 'No hay registros para guardar en la base de datos'

            return resultado_procesamiento

        except Exception as e:
            return {
                'success': False,
                'error': f"Error en procesamiento con persistencia: {str(e)}",
                'total_registros': 0,
                'registros_guardados_bd': 0
            }

    def _reconstruir_dataframe_desde_resultado(self, resultado: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Método auxiliar para reconstruir DataFrame desde el resultado HTML.
        En una implementación más robusta, se pasaría el DataFrame directamente.

        Args:
            resultado: Resultado del procesamiento

        Returns:
            Optional[pd.DataFrame]: DataFrame reconstruido o None
        """
        # Nota: Esta es una implementación temporal
        # En el futuro, sería mejor modificar los métodos de procesamiento
        # para retornar tanto el HTML como el DataFrame

        # Por ahora, retornamos None y manejamos este caso
        # En el futuro, aquí se implementaría la lógica para reconstruir
        # el DataFrame desde el HTML o mejor aún, retornarlo directamente
        # desde los métodos de procesamiento

        return None

class ValidacionService:
    """Servicio especializado en validaciones."""
    
    def __init__(self):
        """Inicializa el servicio de validación."""
        self.data_validator = DataValidator()
    
    def validar_archivo_completo(
        self, 
        df: pd.DataFrame, 
        tipo_formato: str
    ) -> Dict[str, Any]:
        """
        Ejecuta validación completa de un archivo.
        
        Args:
            df: DataFrame a validar
            tipo_formato: Tipo de formato
        
        Returns:
            Dict[str, Any]: Resultado de validación
        """
        try:
            return self.data_validator.validar_completo(df, tipo_formato)
            
        except Exception as e:
            return {
                'es_valido': False,
                'errores': [f"Error durante validación: {str(e)}"],
                'advertencias': [],
                'estadisticas': {},
                'tipo_formato': tipo_formato
            }

class EstadisticasService:
    """Servicio especializado en generación de estadísticas."""
    
    def __init__(self):
        """Inicializa el servicio de estadísticas."""
        self.data_transformer = DataTransformer()
    
    def generar_estadisticas_completas(
        self,
        df: pd.DataFrame,
        mapeo_sedes: Dict[str, str],
        municipios: List[str]
    ) -> Dict[str, Any]:
        """
        Genera estadísticas completas del procesamiento.
        
        Args:
            df: DataFrame procesado
            mapeo_sedes: Mapeo de sedes
            municipios: Lista de municipios
        
        Returns:
            Dict[str, Any]: Estadísticas completas
        """
        try:
            # Estadísticas por sede
            estadisticas_sedes = self.data_transformer.generar_estadisticas_por_sede(
                df, mapeo_sedes, municipios
            )
            
            # Estadísticas generales
            estadisticas_generales = {
                'total_registros': len(df),
                'total_sedes': len(estadisticas_sedes),
                'sedes_con_datos': len([s for s in estadisticas_sedes if s['cantidad'] > 0]),
                'municipios_procesados': municipios
            }
            
            # Estadísticas por nivel escolar
            estadisticas_niveles = {}
            for nivel in ProcesamientoConfig.NIVELES_ESCOLARES:
                total_nivel = sum(s.get(nivel, 0) for s in estadisticas_sedes)
                estadisticas_niveles[nivel] = total_nivel
            
            return {
                'sedes': estadisticas_sedes,
                'generales': estadisticas_generales,
                'niveles': estadisticas_niveles
            }
            
        except Exception as e:
            return {
                'sedes': [],
                'generales': {},
                'niveles': {}
            }
