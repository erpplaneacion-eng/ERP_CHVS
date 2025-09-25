"""
Utilidades para el manejo de archivos Excel.
"""

import pandas as pd
from django.core.files.uploadedfile import UploadedFile
from typing import List, Tuple
from .config import ProcesamientoConfig
from .exceptions import ArchivoInvalidoException, ColumnasFaltantesException
from .logging_config import FacturacionLogger

class ExcelProcessor:
    """Procesador de archivos Excel con validaciones y utilidades."""
    
    @staticmethod
    def validar_archivo_excel(archivo: UploadedFile) -> bool:
        """
        Valida que el archivo sea un Excel válido.
        
        Args:
            archivo: Archivo subido por el usuario
        
        Returns:
            bool: True si es válido, False si no
        """
        try:
            # Validar tipo MIME
            if archivo.content_type not in ProcesamientoConfig.MIME_TYPES_VALIDOS:
                FacturacionLogger.log_validacion_archivo(
                    archivo.name, False, archivo.content_type
                )
                return False
            
            # Validar extensión
            if not any(archivo.name.lower().endswith(ext) for ext in ProcesamientoConfig.EXTENSIONES_PERMITIDAS):
                FacturacionLogger.log_validacion_archivo(
                    archivo.name, False, "Extensión inválida"
                )
                return False
            
            # Validar tamaño
            if archivo.size > ProcesamientoConfig.TAMANO_MAXIMO_ARCHIVO:
                FacturacionLogger.log_validacion_archivo(
                    archivo.name, False, f"Tamaño excesivo: {archivo.size} bytes"
                )
                return False
            
            FacturacionLogger.log_validacion_archivo(
                archivo.name, True, archivo.content_type
            )
            return True
            
        except Exception as e:
            FacturacionLogger.log_validacion_archivo(
                archivo.name, False, f"Error de validación: {str(e)}"
            )
            return False
    
    @staticmethod
    def leer_excel(archivo: UploadedFile) -> pd.DataFrame:
        """
        Lee un archivo Excel y retorna un DataFrame.
        
        Args:
            archivo: Archivo Excel subido
        
        Returns:
            pd.DataFrame: DataFrame con los datos del Excel
            
        Raises:
            ArchivoInvalidoException: Si hay error al leer el archivo
        """
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)
            
            # Validar que no esté vacío
            if df.empty:
                raise ArchivoInvalidoException("El archivo Excel está vacío")
            
            FacturacionLogger.log_procesamiento_inicio(
                archivo.name, "lectura_excel"
            )
            
            return df
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                archivo.name, f"Error al leer Excel: {str(e)}"
            )
            raise ArchivoInvalidoException(f"Error al leer el archivo Excel: {str(e)}")
    
    @staticmethod
    def verificar_columnas_requeridas(df: pd.DataFrame, columnas_requeridas: List[str]) -> List[str]:
        """
        Verifica que el DataFrame tenga las columnas requeridas.
        
        Args:
            df: DataFrame a verificar
            columnas_requeridas: Lista de columnas requeridas
        
        Returns:
            List[str]: Lista de columnas faltantes (vacía si todas están presentes)
        """
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            FacturacionLogger.log_procesamiento_error(
                "verificacion_columnas", 
                f"Columnas faltantes: {columnas_faltantes}"
            )
        else:
            FacturacionLogger.log_procesamiento_inicio(
                "verificacion_columnas", "validacion_exitosa"
            )
        
        return columnas_faltantes
    
    @staticmethod
    def validar_estructura_nuevo_formato(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida la estructura específica del nuevo formato.
        
        Args:
            df: DataFrame a validar
        
        Returns:
            Tuple[bool, List[str]]: (es_valido, errores)
        """
        errores = []
        
        # Verificar columnas requeridas
        columnas_faltantes = ExcelProcessor.verificar_columnas_requeridas(
            df, ProcesamientoConfig.COLUMNAS_NUEVO_FORMATO
        )
        if columnas_faltantes:
            errores.append(f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}")
        
        # Verificar que existe la columna LOTE
        if 'LOTE' in df.columns:
            # Verificar que hay al menos una fila con LOTE == 3
            filas_lote_3 = df[df['LOTE'] == 3]
            if len(filas_lote_3) == 0:
                errores.append("No se encontraron filas con LOTE == 3")
        else:
            errores.append("Columna LOTE no encontrada")
        
        es_valido = len(errores) == 0
        
        if es_valido:
            FacturacionLogger.log_procesamiento_inicio(
                "validacion_nuevo_formato", "estructura_valida"
            )
        else:
            FacturacionLogger.log_procesamiento_error(
                "validacion_nuevo_formato", f"Errores: {errores}"
            )
        
        return es_valido, errores
    
    @staticmethod
    def validar_estructura_original_formato(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida la estructura específica del formato original.
        
        Args:
            df: DataFrame a validar
        
        Returns:
            Tuple[bool, List[str]]: (es_valido, errores)
        """
        errores = []
        
        # Verificar columnas requeridas
        columnas_faltantes = ExcelProcessor.verificar_columnas_requeridas(
            df, ProcesamientoConfig.COLUMNAS_ORIGINAL_FORMATO
        )
        if columnas_faltantes:
            errores.append(f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}")
        
        # Verificar que hay datos después de filtros básicos
        if 'ESTADO' in df.columns and 'SECTOR' in df.columns and 'MODELO' in df.columns:
            df_filtrado = df[
                (df['ESTADO'] == ProcesamientoConfig.ESTADO_MATRICULADO) &
                (df['SECTOR'] == ProcesamientoConfig.SECTOR_OFICIAL) &
                (~df['MODELO'].isin(ProcesamientoConfig.MODELOS_EXCLUIDOS))
            ]
            if len(df_filtrado) == 0:
                errores.append("No hay datos válidos después de aplicar filtros básicos")
        
        es_valido = len(errores) == 0
        
        if es_valido:
            FacturacionLogger.log_procesamiento_inicio(
                "validacion_original_formato", "estructura_valida"
            )
        else:
            FacturacionLogger.log_procesamiento_error(
                "validacion_original_formato", f"Errores: {errores}"
            )
        
        return es_valido, errores
    
    @staticmethod
    def obtener_informacion_archivo(df: pd.DataFrame) -> dict:
        """
        Obtiene información básica del archivo procesado.
        
        Args:
            df: DataFrame procesado
        
        Returns:
            dict: Información del archivo
        """
        info = {
            'total_filas': len(df),
            'total_columnas': len(df.columns),
            'columnas': list(df.columns),
            'memoria_uso': df.memory_usage(deep=True).sum(),
            'tipos_datos': df.dtypes.to_dict()
        }
        
        FacturacionLogger.log_estadisticas_generadas(info)
        return info
