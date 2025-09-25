"""
Módulo para validación de datos y reglas de negocio.
"""

import pandas as pd
from typing import List, Dict, Tuple, Any
from .config import ProcesamientoConfig
from .exceptions import DatosInvalidosException, ValidacionException
from .logging_config import FacturacionLogger

class DataValidator:
    """Clase para validación de datos y reglas de negocio."""
    
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
        
        try:
            # Verificar columnas requeridas
            columnas_faltantes = [col for col in ProcesamientoConfig.COLUMNAS_NUEVO_FORMATO if col not in df.columns]
            if columnas_faltantes:
                errores.append(f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}")
            
            # Verificar que existe la columna LOTE
            if 'LOTE' in df.columns:
                # Verificar que hay al menos una fila con LOTE == 3
                filas_lote_3 = df[df['LOTE'] == 3]
                if len(filas_lote_3) == 0:
                    errores.append("No se encontraron filas con LOTE == 3 en el archivo")
            else:
                errores.append("Columna LOTE no encontrada")
            
            # Verificar tipos de datos críticos
            if 'NRO_DOCUMENTO' in df.columns:
                if df['NRO_DOCUMENTO'].isna().all():
                    errores.append("Columna NRO_DOCUMENTO está completamente vacía")
            
            if 'FECHA_NACIMIENTO' in df.columns:
                if df['FECHA_NACIMIENTO'].isna().all():
                    errores.append("Columna FECHA_NACIMIENTO está completamente vacía")
            
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
            
        except Exception as e:
            error_msg = f"Error durante validación de nuevo formato: {str(e)}"
            FacturacionLogger.log_procesamiento_error("validacion_nuevo_formato", error_msg)
            return False, [error_msg]
    
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
        
        try:
            # Verificar columnas requeridas
            columnas_faltantes = [col for col in ProcesamientoConfig.COLUMNAS_ORIGINAL_FORMATO if col not in df.columns]
            if columnas_faltantes:
                errores.append(f"Columnas requeridas faltantes: {', '.join(columnas_faltantes)}")
            
            # Verificar que hay datos después de filtros básicos
            if all(col in df.columns for col in ['ESTADO', 'SECTOR', 'MODELO']):
                df_filtrado = df[
                    (df['ESTADO'] == ProcesamientoConfig.ESTADO_MATRICULADO) &
                    (df['SECTOR'] == ProcesamientoConfig.SECTOR_OFICIAL) &
                    (~df['MODELO'].isin(ProcesamientoConfig.MODELOS_EXCLUIDOS))
                ]
                if len(df_filtrado) == 0:
                    errores.append("No hay datos válidos después de aplicar filtros básicos")
            
            # Verificar columnas críticas
            columnas_criticas = ['DOC', 'TIPODOC', 'APELLIDO1', 'NOMBRE1']
            for col in columnas_criticas:
                if col in df.columns and df[col].isna().all():
                    errores.append(f"Columna {col} está completamente vacía")
            
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
            
        except Exception as e:
            error_msg = f"Error durante validación de formato original: {str(e)}"
            FacturacionLogger.log_procesamiento_error("validacion_original_formato", error_msg)
            return False, [error_msg]
    
    @staticmethod
    def validar_datos_obligatorios(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida datos obligatorios en el DataFrame.
        
        Args:
            df: DataFrame a validar
        
        Returns:
            Dict[str, Any]: Resultado de la validación
        """
        try:
            resultado = {
                'es_valido': True,
                'errores': [],
                'advertencias': [],
                'estadisticas': {}
            }
            
            # Validar que no esté vacío
            if df.empty:
                resultado['es_valido'] = False
                resultado['errores'].append("El DataFrame está vacío")
                return resultado
            
            # Estadísticas básicas
            resultado['estadisticas'] = {
                'total_filas': len(df),
                'total_columnas': len(df.columns),
                'filas_con_nulos': df.isnull().any(axis=1).sum(),
                'columnas_con_nulos': df.isnull().any().sum()
            }
            
            # Validar columnas críticas
            columnas_criticas = ['SEDE', 'DOC', 'NOMBRE1', 'APELLIDO1']
            for col in columnas_criticas:
                if col in df.columns:
                    nulos = df[col].isnull().sum()
                    if nulos > 0:
                        resultado['advertencias'].append(f"Columna {col} tiene {nulos} valores nulos")
                        if nulos == len(df):
                            resultado['es_valido'] = False
                            resultado['errores'].append(f"Columna {col} está completamente vacía")
            
            # Validar duplicados en documento
            if 'DOC' in df.columns:
                duplicados = df['DOC'].duplicated().sum()
                if duplicados > 0:
                    resultado['advertencias'].append(f"Se encontraron {duplicados} documentos duplicados")
            
            FacturacionLogger.log_estadisticas_generadas(resultado['estadisticas'])
            
            return resultado
            
        except Exception as e:
            error_msg = f"Error durante validación de datos obligatorios: {str(e)}"
            FacturacionLogger.log_procesamiento_error("validar_datos_obligatorios", error_msg)
            return {
                'es_valido': False,
                'errores': [error_msg],
                'advertencias': [],
                'estadisticas': {}
            }
    
    @staticmethod
    def validar_sedes_requeridas(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida que existan sedes en el DataFrame.
        
        Args:
            df: DataFrame a validar
        
        Returns:
            Dict[str, Any]: Resultado de la validación
        """
        try:
            resultado = {
                'es_valido': True,
                'errores': [],
                'advertencias': [],
                'sedes_unicas': []
            }
            
            if 'SEDE' not in df.columns:
                resultado['es_valido'] = False
                resultado['errores'].append("Columna SEDE no encontrada")
                return resultado
            
            # Obtener sedes únicas
            sedes_unicas = df['SEDE'].dropna().unique()
            resultado['sedes_unicas'] = list(sedes_unicas)
            
            if len(sedes_unicas) == 0:
                resultado['es_valido'] = False
                resultado['errores'].append("No se encontraron sedes en el archivo")
            elif len(sedes_unicas) < 5:
                resultado['advertencias'].append(f"Solo se encontraron {len(sedes_unicas)} sedes únicas")
            
            FacturacionLogger.log_estadisticas_generadas({
                'sedes_unicas': len(sedes_unicas),
                'sedes_lista': sedes_unicas[:10]  # Solo las primeras 10 para el log
            })
            
            return resultado
            
        except Exception as e:
            error_msg = f"Error durante validación de sedes: {str(e)}"
            FacturacionLogger.log_procesamiento_error("validar_sedes_requeridas", error_msg)
            return {
                'es_valido': False,
                'errores': [error_msg],
                'advertencias': [],
                'sedes_unicas': []
            }
    
    @staticmethod
    def validar_integridad_datos(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida la integridad general de los datos.
        
        Args:
            df: DataFrame a validar
        
        Returns:
            Dict[str, Any]: Resultado de la validación
        """
        try:
            resultado = {
                'es_valido': True,
                'errores': [],
                'advertencias': [],
                'estadisticas': {}
            }
            
            # Verificar que el DataFrame no esté vacío
            if df.empty:
                resultado['es_valido'] = False
                resultado['errores'].append("El DataFrame está vacío")
                return resultado
            
            # Estadísticas de integridad
            total_filas = len(df)
            total_columnas = len(df.columns)
            
            # Verificar filas completamente vacías
            filas_vacias = df.isnull().all(axis=1).sum()
            if filas_vacias > 0:
                resultado['advertencias'].append(f"Se encontraron {filas_vacias} filas completamente vacías")
            
            # Verificar columnas completamente vacías
            columnas_vacias = df.isnull().all().sum()
            if columnas_vacias > 0:
                resultado['advertencias'].append(f"Se encontraron {columnas_vacias} columnas completamente vacías")
            
            # Verificar tipos de datos
            tipos_problematicos = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Verificar si hay valores que no son strings
                    valores_no_string = df[col].apply(lambda x: not isinstance(x, str) and pd.notna(x)).sum()
                    if valores_no_string > 0:
                        tipos_problematicos.append(col)
            
            if tipos_problematicos:
                resultado['advertencias'].append(f"Columnas con tipos de datos inconsistentes: {tipos_problematicos}")
            
            resultado['estadisticas'] = {
                'total_filas': total_filas,
                'total_columnas': total_columnas,
                'filas_vacias': filas_vacias,
                'columnas_vacias': columnas_vacias,
                'tipos_problematicos': len(tipos_problematicos)
            }
            
            FacturacionLogger.log_estadisticas_generadas(resultado['estadisticas'])
            
            return resultado
            
        except Exception as e:
            error_msg = f"Error durante validación de integridad: {str(e)}"
            FacturacionLogger.log_procesamiento_error("validar_integridad_datos", error_msg)
            return {
                'es_valido': False,
                'errores': [error_msg],
                'advertencias': [],
                'estadisticas': {}
            }
    
    @staticmethod
    def validar_completo(df: pd.DataFrame, tipo_formato: str) -> Dict[str, Any]:
        """
        Ejecuta todas las validaciones para un DataFrame.
        
        Args:
            df: DataFrame a validar
            tipo_formato: Tipo de formato ('nuevo' o 'original')
        
        Returns:
            Dict[str, Any]: Resultado completo de validación
        """
        try:
            resultado = {
                'es_valido': True,
                'errores': [],
                'advertencias': [],
                'estadisticas': {},
                'tipo_formato': tipo_formato
            }
            
            # Validación de estructura específica
            if tipo_formato == 'nuevo':
                es_valido_estructura, errores_estructura = DataValidator.validar_estructura_nuevo_formato(df)
            else:
                es_valido_estructura, errores_estructura = DataValidator.validar_estructura_original_formato(df)
            
            resultado['errores'].extend(errores_estructura)
            if not es_valido_estructura:
                resultado['es_valido'] = False
            
            # Validación de datos obligatorios
            validacion_obligatorios = DataValidator.validar_datos_obligatorios(df)
            resultado['errores'].extend(validacion_obligatorios['errores'])
            resultado['advertencias'].extend(validacion_obligatorios['advertencias'])
            resultado['estadisticas'].update(validacion_obligatorios['estadisticas'])
            
            if not validacion_obligatorios['es_valido']:
                resultado['es_valido'] = False
            
            # Validación de sedes
            validacion_sedes = DataValidator.validar_sedes_requeridas(df)
            resultado['errores'].extend(validacion_sedes['errores'])
            resultado['advertencias'].extend(validacion_sedes['advertencias'])
            resultado['sedes_unicas'] = validacion_sedes['sedes_unicas']
            
            if not validacion_sedes['es_valido']:
                resultado['es_valido'] = False
            
            # Validación de integridad
            validacion_integridad = DataValidator.validar_integridad_datos(df)
            resultado['errores'].extend(validacion_integridad['errores'])
            resultado['advertencias'].extend(validacion_integridad['advertencias'])
            resultado['estadisticas'].update(validacion_integridad['estadisticas'])
            
            if not validacion_integridad['es_valido']:
                resultado['es_valido'] = False
            
            # Log del resultado final
            if resultado['es_valido']:
                FacturacionLogger.log_procesamiento_inicio(
                    "validacion_completa", "validacion_exitosa"
                )
            else:
                FacturacionLogger.log_procesamiento_error(
                    "validacion_completa", f"Errores: {len(resultado['errores'])}"
                )
            
            return resultado
            
        except Exception as e:
            error_msg = f"Error durante validación completa: {str(e)}"
            FacturacionLogger.log_procesamiento_error("validar_completo", error_msg)
            return {
                'es_valido': False,
                'errores': [error_msg],
                'advertencias': [],
                'estadisticas': {},
                'tipo_formato': tipo_formato
            }
