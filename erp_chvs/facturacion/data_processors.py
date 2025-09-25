"""
Módulo para procesamiento y transformación de datos.
"""

import pandas as pd
from typing import Dict, List, Any
from principal.models import TipoDocumento, TipoGenero, NivelGradoEscolar
from .config import ProcesamientoConfig
from .exceptions import DatosInvalidosException, ProcesamientoException
from .logging_config import FacturacionLogger

class DataTransformer:
    """Clase para transformación y procesamiento de datos."""
    
    @staticmethod
    def aplicar_mapeos_datos(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica los mapeos de transformación de datos comunes.
        
        Args:
            df: DataFrame a transformar
        
        Returns:
            pd.DataFrame: DataFrame transformado
        """
        try:
            transformaciones_aplicadas = []
            
            # Transformación de TIPODOC usando el modelo de 'principal'
            if 'TIPODOC' in df.columns:
                tipos_documento = TipoDocumento.objects.all()
                mapeo_modalidades = {m.tipo_documento: m.codigo_documento for m in tipos_documento}
                df['TIPODOC'] = df['TIPODOC'].map(mapeo_modalidades)
                transformaciones_aplicadas.append("TIPODOC")
            
            # Transformación de GENERO usando el modelo de 'principal'
            if 'GENERO' in df.columns:
                generos = TipoGenero.objects.all()
                mapeo_generos = {g.genero: g.codigo_genero for g in generos}
                df['GENERO'] = df['GENERO'].map(mapeo_generos)
                transformaciones_aplicadas.append("GENERO")
            
            FacturacionLogger.log_transformacion_datos(transformaciones_aplicadas)
            return df
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "aplicar_mapeos_datos", str(e)
            )
            raise ProcesamientoException(f"Error al aplicar mapeos de datos: {str(e)}")
    
    @staticmethod
    def procesar_formato_nuevo(df: pd.DataFrame, focalizacion: str) -> pd.DataFrame:
        """
        Procesa datos con formato nuevo (LOTE == 3).
        
        Args:
            df: DataFrame con datos del Excel
            focalizacion: Focalización seleccionada
        
        Returns:
            pd.DataFrame: DataFrame procesado
        """
        try:
            # --- PASO 1: FILTRADO INICIAL ---
            df = df[df['LOTE'] == 3].copy()  # .copy() evita SettingWithCopyWarning

            if len(df) == 0:
                raise DatosInvalidosException("No se encontraron filas con LOTE == 3 en el archivo")

            # --- PASO 2: AGREGAR COLUMNAS FIJAS ---
            df['AÑO'] = ProcesamientoConfig.AÑO_FIJO
            df['ETC'] = ProcesamientoConfig.ETC_CALI
            
            # --- PASO 3: RENOMBRAR COLUMNAS PARA COMPATIBILIDAD ---
            df = df.rename(columns={
                'NOMBRE INSTITUCION': 'INSTITUCION',
                'NOMBRE SEDE': 'SEDE',
                'ZONA': 'ZONA_SEDE',
                'TIPO_DOCUMENTO': 'TIPODOC',
                'NRO_DOCUMENTO': 'DOC',
                'TIPO_JORNADA': 'JORNADA'
            })
            
            # --- PASO 4: AGREGAR COLUMNAS ADICIONALES ---
            df['ESTADO'] = ProcesamientoConfig.ESTADO_MATRICULADO_NUEVO
            df['SECTOR'] = ProcesamientoConfig.SECTOR_OFICIAL_NUEVO
            df['MODELO'] = ProcesamientoConfig.MODELO_PROGRAMA_ALIMENTARIO
            df['focalizacion'] = focalizacion
            
            # Agregar columnas de complementos alimentarios
            df['COMPLEMENTO ALIMENTARIO PREPARADO AM'] = ''
            df['COMPLEMENTO ALIMENTARIO PREPARADO PM'] = ''
            df['ALMUERZO JORNADA UNICA'] = ''
            df['REFUERZO COMPLEMENTO AM/PM'] = ''
            
            # Aplicar lógica condicional para CALI
            df.loc[
                (df['ETC'] == ProcesamientoConfig.ETC_CALI) & 
                (df['JORNADA'] == ProcesamientoConfig.JORNADA_UNICA_CALI), 
                ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'ALMUERZO JORNADA UNICA']
            ] = 'x'
            
            df.loc[
                (df['ETC'] == ProcesamientoConfig.ETC_CALI) & 
                (df['JORNADA'].isin(ProcesamientoConfig.JORNADAS_DOBLES_CALI)), 
                ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'COMPLEMENTO ALIMENTARIO PREPARADO PM']
            ] = 'x'
            
            # --- PASO 5: TRANSFORMACIÓN DE GRADO PARA ESTADÍSTICAS ---
            df = DataTransformer._procesar_grados_escolares(df)
            
            FacturacionLogger.log_procesamiento_inicio(
                "formato_nuevo", "procesamiento_completado"
            )
            
            return df
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "procesar_formato_nuevo", str(e)
            )
            raise ProcesamientoException(f"Error al procesar formato nuevo: {str(e)}")
    
    @staticmethod
    def procesar_formato_original(df: pd.DataFrame, focalizacion: str) -> pd.DataFrame:
        """
        Procesa datos con formato original.
        
        Args:
            df: DataFrame con datos del Excel
            focalizacion: Focalización seleccionada
        
        Returns:
            pd.DataFrame: DataFrame procesado
        """
        try:
            # --- PASO 1: FILTRADO INICIAL ---
            df = df[df['ESTADO'] == ProcesamientoConfig.ESTADO_MATRICULADO]
            df = df[df['SECTOR'] == ProcesamientoConfig.SECTOR_OFICIAL]
            df = df[~df['MODELO'].isin(ProcesamientoConfig.MODELOS_EXCLUIDOS)]
            
            # --- PASO 2: SELECCIÓN DE COLUMNAS ---
            columnas_a_mantener = [
                'ANO', 'ETC', 'ESTADO', 'INSTITUCION', 'SECTOR', 'SEDE',
                'ZONA_SEDE', 'JORNADA', 'GRADO_COD', 'GRUPO',
                'MODELO', 'DOC', 'TIPODOC',
                'APELLIDO1', 'APELLIDO2', 'NOMBRE1', 'NOMBRE2', 'GENERO', 'FECHA_NACIMIENTO',
            ]
            
            columnas_existentes = [col for col in columnas_a_mantener if col in df.columns]
            df = df[columnas_existentes]
            
            # --- PASO 3: TRANSFORMACIÓN DE DATOS ---
            df = DataTransformer.aplicar_mapeos_datos(df)
            
            # --- PASO 4: TRANSFORMACIÓN DE GRADO PARA ESTADÍSTICAS ---
            df = DataTransformer._procesar_grados_escolares(df, columna_grado='GRADO_COD')
            
            # --- PASO 5: LÓGICA PARA JORNADA Y NUEVAS COLUMNAS ---
            df = DataTransformer._aplicar_logica_jornadas(df)
            
            # --- PASO 6: AÑADIR FOCALIZACIÓN ---
            df['focalizacion'] = focalizacion
            
            FacturacionLogger.log_procesamiento_inicio(
                "formato_original", "procesamiento_completado"
            )
            
            return df
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "procesar_formato_original", str(e)
            )
            raise ProcesamientoException(f"Error al procesar formato original: {str(e)}")
    
    @staticmethod
    def _procesar_grados_escolares(df: pd.DataFrame, columna_grado: str = 'GRADO') -> pd.DataFrame:
        """
        Procesa los grados escolares para crear columnas de estadísticas.
        
        Args:
            df: DataFrame a procesar
            columna_grado: Nombre de la columna de grado
        
        Returns:
            pd.DataFrame: DataFrame con columnas de grados procesadas
        """
        try:
            # Obtener mapeo de niveles de grado
            niveles_grado = NivelGradoEscolar.objects.all()
            mapeo_niveles = {n.grados_sedes: n.nivel_escolar_uapa for n in niveles_grado}
            
            # Convertir GRADO a entero primero, luego a string para el mapeo
            df[f'{columna_grado}_clean'] = df[columna_grado].fillna(0).astype(int).astype(str)
            df['nivel_grados'] = df[f'{columna_grado}_clean'].map(mapeo_niveles)
            
            # Combinar GRADO y GRUPO para consistencia
            if 'GRUPO' in df.columns:
                df['grado_grupos'] = df[f'{columna_grado}_clean'] + '-' + df['GRUPO'].astype(str)
            
            FacturacionLogger.log_mapeo_datos("grados_escolares", len(df))
            
            return df
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "procesar_grados_escolares", str(e)
            )
            raise ProcesamientoException(f"Error al procesar grados escolares: {str(e)}")
    
    @staticmethod
    def _aplicar_logica_jornadas(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica la lógica de jornadas para diferentes municipios.
        
        Args:
            df: DataFrame a procesar
        
        Returns:
            pd.DataFrame: DataFrame con lógica de jornadas aplicada
        """
        try:
            # Obtener municipios únicos
            unique_etc = df['ETC'].unique()
            
            # Inicializar nuevas columnas
            df['COMPLEMENTO ALIMENTARIO PREPARADO AM'] = ''
            df['COMPLEMENTO ALIMENTARIO PREPARADO PM'] = ''
            df['ALMUERZO JORNADA UNICA'] = ''
            df['REFUERZO COMPLEMENTO AM/PM'] = ''
            
            # Aplicar lógica para YUMBO
            if 'YUMBO' in unique_etc:
                df.loc[
                    (df['ETC'] == 'YUMBO') & (df['JORNADA'] == ProcesamientoConfig.JORNADA_UNICA_OTROS), 
                    ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'ALMUERZO JORNADA UNICA']
                ] = 'x'
                
                df.loc[
                    (df['ETC'] == 'YUMBO') & (df['JORNADA'].isin(ProcesamientoConfig.JORNADAS_DOBLES_OTROS)), 
                    ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'COMPLEMENTO ALIMENTARIO PREPARADO PM', 'REFUERZO COMPLEMENTO AM/PM']
                ] = 'x'
            
            # Aplicar lógica para GUADALAJARA DE BUGA
            if 'GUADALAJARA DE BUGA' in unique_etc:
                df.loc[
                    (df['ETC'] == 'GUADALAJARA DE BUGA') & (df['JORNADA'] == ProcesamientoConfig.JORNADA_UNICA_OTROS), 
                    ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'ALMUERZO JORNADA UNICA']
                ] = 'x'
                
                df.loc[
                    (df['ETC'] == 'GUADALAJARA DE BUGA') & (df['JORNADA'].isin(ProcesamientoConfig.JORNADAS_DOBLES_OTROS)), 
                    ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'COMPLEMENTO ALIMENTARIO PREPARADO PM']
                ] = 'x'
            
            FacturacionLogger.log_mapeo_datos("logica_jornadas", len(df))
            
            return df
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "aplicar_logica_jornadas", str(e)
            )
            raise ProcesamientoException(f"Error al aplicar lógica de jornadas: {str(e)}")
    
    @staticmethod
    def generar_estadisticas_por_sede(
        df: pd.DataFrame, 
        mapeo_sedes: Dict[str, str],
        municipios: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Genera estadísticas por sede para mostrar en la interfaz.
        
        Args:
            df: DataFrame procesado
            mapeo_sedes: Mapeo de sedes Excel -> BD
            municipios: Lista de municipios
        
        Returns:
            List[Dict[str, Any]]: Lista de estadísticas por sede
        """
        try:
            from planeacion.models import SedesEducativas
            
            # Obtener todas las sedes de BD para los municipios
            todas_sedes_bd = list(SedesEducativas.objects.filter(
                codigo_ie__id_municipios__nombre_municipio__in=municipios
            ).values_list('nombre_sede_educativa', flat=True))
            
            agrupacion_sedes = []
            
            # Para cada sede de BD, verificar si tiene coincidencias
            for sede_bd in todas_sedes_bd:
                # Buscar si esta sede BD tiene mapeos desde Excel
                sedes_excel_mapeadas = [
                    sede_excel for sede_excel, sede_bd_mapeada in mapeo_sedes.items() 
                    if sede_bd_mapeada == sede_bd
                ]
                
                if sedes_excel_mapeadas:
                    # Si hay mapeos, contar registros totales y por nivel
                    sede_excel_str = ', '.join(sedes_excel_mapeadas)
                    
                    # Crear DataFrame filtrado para esta sede
                    df_sede = df[df['SEDE'].isin(sedes_excel_mapeadas)]
                    total_count = len(df_sede)
                    
                    # Contar por cada nivel escolar
                    estadisticas_nivel = {}
                    for nivel in ProcesamientoConfig.NIVELES_ESCOLARES:
                        count_nivel = len(df_sede[df_sede['nivel_grados'] == nivel])
                        estadisticas_nivel[nivel] = count_nivel
                    
                    agrupacion_sedes.append({
                        'sede_bd': sede_bd,
                        'sede_excel': sede_excel_str,
                        'cantidad': total_count,
                        **estadisticas_nivel
                    })
                else:
                    # Si no hay mapeos, mostrar con 0 registros
                    estadisticas_nivel = {nivel: 0 for nivel in ProcesamientoConfig.NIVELES_ESCOLARES}
                    agrupacion_sedes.append({
                        'sede_bd': sede_bd,
                        'sede_excel': 'Sin coincidencias',
                        'cantidad': 0,
                        **estadisticas_nivel
                    })
            
            # Ordenar por cantidad descendente
            agrupacion_sedes.sort(key=lambda x: x['cantidad'], reverse=True)
            
            FacturacionLogger.log_estadisticas_generadas({
                'total_sedes': len(agrupacion_sedes),
                'sedes_con_datos': len([s for s in agrupacion_sedes if s['cantidad'] > 0])
            })
            
            return agrupacion_sedes
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "generar_estadisticas_por_sede", str(e)
            )
            raise ProcesamientoException(f"Error al generar estadísticas por sede: {str(e)}")
    
    @staticmethod
    def preparar_dataframe_html(df: pd.DataFrame, max_filas: int = 5) -> str:
        """
        Prepara el DataFrame para mostrar en HTML.
        
        Args:
            df: DataFrame a convertir
            max_filas: Número máximo de filas a mostrar
        
        Returns:
            str: HTML del DataFrame
        """
        try:
            if len(df) == 0:
                return "<div class='alert alert-warning'>No hay datos para mostrar.</div>"
            
            # Mostrar solo las primeras filas
            df_mostrar = df.head(max_filas)
            html = df_mostrar.to_html(
                classes='table table-striped table-bordered', 
                index=False, 
                na_rep=''
            )
            
            return html
            
        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "preparar_dataframe_html", str(e)
            )
            return f"<div class='alert alert-danger'>Error al preparar datos: {str(e)}</div>"
