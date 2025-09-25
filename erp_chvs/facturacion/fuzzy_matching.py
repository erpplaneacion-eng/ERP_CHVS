"""
Módulo para coincidencia difusa y validación de sedes.
"""

import re
import pandas as pd
from typing import List, Tuple, Dict, Optional
from fuzzywuzzy import fuzz, process
from planeacion.models import SedesEducativas
from .config import ProcesamientoConfig
from .exceptions import SedesInvalidasException
from .logging_config import FacturacionLogger

class FuzzyMatcher:
    """Clase para manejo de coincidencia difusa de sedes."""
    
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """
        Normaliza un texto para comparación difusa:
        - Convierte a minúsculas
        - Elimina espacios extra
        - Elimina caracteres especiales comunes
        - Normaliza acentos
        
        Args:
            texto: Texto a normalizar
        
        Returns:
            str: Texto normalizado
        """
        if pd.isna(texto) or texto is None:
            return ""
        
        # Convertir a string y minúsculas
        texto = str(texto).lower().strip()
        
        # Eliminar espacios múltiples y reemplazar por uno solo
        texto = re.sub(r'\s+', ' ', texto)
        
        # Eliminar caracteres especiales comunes que pueden causar problemas
        texto = re.sub(r'[^\w\s]', '', texto)
        
        # Normalizar acentos básicos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            texto = texto.replace(old, new)
        
        return texto.strip()
    
    @staticmethod
    def encontrar_coincidencia_difusa(
        sede_excel: str, 
        sedes_bd: List[str], 
        umbral: int = None
    ) -> Tuple[Optional[str], float]:
        """
        Encuentra la mejor coincidencia difusa para una sede del Excel
        contra las sedes de la base de datos.
        
        Args:
            sede_excel: Nombre de la sede del Excel
            sedes_bd: Lista de sedes de la base de datos
            umbral: Porcentaje mínimo de similitud
        
        Returns:
            Tuple[Optional[str], float]: (sede_encontrada, porcentaje_similitud) o (None, 0)
        """
        if umbral is None:
            umbral = ProcesamientoConfig.UMBRAL_COINCIDENCIA_DIFUSA
        
        sede_normalizada = FuzzyMatcher.normalizar_texto(sede_excel)
        
        if not sede_normalizada:
            return None, 0
        
        # Usar fuzzywuzzy para encontrar la mejor coincidencia
        resultado = process.extractOne(
            sede_normalizada, 
            sedes_bd, 
            scorer=fuzz.ratio,
            score_cutoff=umbral
        )
        
        if resultado:
            sede_encontrada, porcentaje = resultado
            FacturacionLogger.log_coincidencia_difusa(
                sede_excel, sede_encontrada, porcentaje, "difusa"
            )
            return sede_encontrada, porcentaje
        else:
            return None, 0
    
    @staticmethod
    def obtener_sedes_por_municipio(municipios: List[str]) -> Dict[str, List[str]]:
        """
        Obtiene sedes de la base de datos filtradas por municipio.
        
        Args:
            municipios: Lista de municipios a filtrar
        
        Returns:
            Dict[str, List[str]]: Diccionario con sedes por municipio
        """
        sedes_por_municipio = {}
        
        for municipio in municipios:
            # Obtener sedes por nombre completo
            sedes_principales = list(SedesEducativas.objects.filter(
                codigo_ie__id_municipios__nombre_municipio=municipio
            ).values_list('nombre_sede_educativa', flat=True))
            
            # Obtener sedes por nombre genérico
            sedes_genericas = list(SedesEducativas.objects.exclude(
                nombre_generico_sede__isnull=True
            ).exclude(
                nombre_generico_sede__exact=''
            ).exclude(
                nombre_generico_sede__exact='Sin especificar'
            ).filter(
                codigo_ie__id_municipios__nombre_municipio=municipio
            ).values_list('nombre_generico_sede', 'nombre_sede_educativa'))
            
            sedes_por_municipio[municipio] = {
                'principales': sedes_principales,
                'genericas': sedes_genericas
            }
        
        return sedes_por_municipio
    
    @staticmethod
    def crear_mapeos_sedes(sedes_por_municipio: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Crea mapeos normalizados de sedes para comparación.
        
        Args:
            sedes_por_municipio: Diccionario con sedes por municipio
        
        Returns:
            Dict[str, Dict]: Mapeos normalizados
        """
        mapeos = {}
        
        for municipio, sedes_data in sedes_por_municipio.items():
            # Mapeo principal (nombre completo)
            mapeo_principal = {}
            sedes_normalizadas_principal = []
            
            for sede_raw in sedes_data['principales']:
                sede_normalizada = FuzzyMatcher.normalizar_texto(sede_raw)
                sedes_normalizadas_principal.append(sede_normalizada)
                mapeo_principal[sede_normalizada] = sede_raw
            
            # Mapeo genérico
            mapeo_generico = {}
            sedes_normalizadas_generico = []
            
            for nombre_generico, nombre_completo in sedes_data['genericas']:
                sede_normalizada = FuzzyMatcher.normalizar_texto(nombre_generico)
                if sede_normalizada and sede_normalizada not in sedes_normalizadas_generico:
                    sedes_normalizadas_generico.append(sede_normalizada)
                    clave_unica = f"{sede_normalizada}_{municipio}"
                    mapeo_generico[clave_unica] = {
                        'nombre_completo': nombre_completo,
                        'municipio': municipio,
                        'nombre_generico': nombre_generico
                    }
            
            mapeos[municipio] = {
                'principal': {
                    'mapeo': mapeo_principal,
                    'sedes_normalizadas': sedes_normalizadas_principal
                },
                'generico': {
                    'mapeo': mapeo_generico,
                    'sedes_normalizadas': sedes_normalizadas_generico
                }
            }
        
        return mapeos
    
    @staticmethod
    def validar_sedes_excel(
        df: pd.DataFrame, 
        municipios: List[str]
    ) -> Dict[str, any]:
        """
        Valida sedes del Excel contra la base de datos usando coincidencia difusa.
        
        Args:
            df: DataFrame con datos del Excel
            municipios: Lista de municipios a validar
        
        Returns:
            Dict[str, any]: Resultado de la validación
        """
        # Obtener sedes únicas del Excel
        unique_sedes = df['SEDE'].dropna().unique()
        
        if len(unique_sedes) == 0:
            return {
                'sedes_validas': [],
                'sedes_invalidas': [],
                'coincidencias_parciales': [],
                'coincidencias_genericas': [],
                'mapeo_sedes': {}
            }
        
        # Obtener sedes de la base de datos
        sedes_por_municipio = FuzzyMatcher.obtener_sedes_por_municipio(municipios)
        mapeos = FuzzyMatcher.crear_mapeos_sedes(sedes_por_municipio)
        
        # Variables para tracking
        sedes_validas = []
        sedes_invalidas = []
        coincidencias_parciales = []
        coincidencias_genericas = []
        mapeo_sedes = {}
        
        # Validar cada sede del Excel
        for sede_excel in unique_sedes:
            sede_validada = False
            
            # Obtener el municipio correspondiente para esta sede
            municipio_sede = None
            if 'ETC' in df.columns:
                etc_sede = df[df['SEDE'] == sede_excel]['ETC'].iloc[0] if len(df[df['SEDE'] == sede_excel]) > 0 else None
                if etc_sede and etc_sede in mapeos:
                    municipio_sede = etc_sede
            else:
                # Si no hay columna ETC, usar el primer municipio disponible
                municipio_sede = municipios[0] if municipios else None
            
            if not municipio_sede or municipio_sede not in mapeos:
                sedes_invalidas.append(sede_excel)
                continue
            
            mapeo_municipio = mapeos[municipio_sede]
            
            # PRIMERA VALIDACIÓN: Por nombre completo de sede
            sede_encontrada, porcentaje = FuzzyMatcher.encontrar_coincidencia_difusa(
                sede_excel,
                mapeo_municipio['principal']['sedes_normalizadas'],
                ProcesamientoConfig.UMBRAL_COINCIDENCIA_DIFUSA
            )
            
            if sede_encontrada:
                sede_original_bd = mapeo_municipio['principal']['mapeo'].get(sede_encontrada)
                if sede_original_bd:
                    sedes_validas.append(sede_excel)
                    mapeo_sedes[sede_excel] = sede_original_bd
                    sede_validada = True
                    
                    if porcentaje < 100:
                        coincidencias_parciales.append({
                            'excel': sede_excel,
                            'bd': sede_original_bd,
                            'porcentaje': porcentaje,
                            'tipo': 'nombre_completo'
                        })
            
            # SEGUNDA VALIDACIÓN: Si la primera falló, intentar por nombre genérico
            if not sede_validada and mapeo_municipio['generico']['sedes_normalizadas']:
                sede_encontrada_generica, porcentaje_generico = FuzzyMatcher.encontrar_coincidencia_difusa(
                    sede_excel,
                    mapeo_municipio['generico']['sedes_normalizadas'],
                    ProcesamientoConfig.UMBRAL_COINCIDENCIA_DIFUSA
                )
                
                if sede_encontrada_generica:
                    clave_unica = f"{sede_encontrada_generica}_{municipio_sede}"
                    sede_info_generica = mapeo_municipio['generico']['mapeo'].get(clave_unica)
                    
                    if sede_info_generica:
                        sedes_validas.append(sede_excel)
                        mapeo_sedes[sede_excel] = sede_info_generica['nombre_completo']
                        sede_validada = True
                        
                        coincidencias_genericas.append({
                            'excel': sede_excel,
                            'bd': sede_info_generica['nombre_completo'],
                            'nombre_generico': sede_info_generica['nombre_generico'],
                            'municipio': sede_info_generica['municipio'],
                            'porcentaje': porcentaje_generico
                        })
            
            # Si ninguna validación funcionó, marcar como inválida
            if not sede_validada:
                sedes_invalidas.append(sede_excel)
        
        # Log de resultados
        FacturacionLogger.log_validacion_sedes(
            len(sedes_validas),
            len(sedes_invalidas),
            len(coincidencias_parciales),
            len(coincidencias_genericas)
        )
        
        return {
            'sedes_validas': sedes_validas,
            'sedes_invalidas': sedes_invalidas,
            'coincidencias_parciales': coincidencias_parciales,
            'coincidencias_genericas': coincidencias_genericas,
            'mapeo_sedes': mapeo_sedes
        }
    
    @staticmethod
    def filtrar_dataframe_por_sedes_validas(
        df: pd.DataFrame, 
        sedes_validas: List[str]
    ) -> pd.DataFrame:
        """
        Filtra el DataFrame para incluir solo sedes válidas.
        
        Args:
            df: DataFrame original
            sedes_validas: Lista de sedes válidas
        
        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        if not sedes_validas:
            return df
        
        df_original_count = len(df)
        df_filtrado = df[df['SEDE'].isin(sedes_validas)]
        df_filtrado_count = len(df_filtrado)
        
        FacturacionLogger.log_filtrado_datos(
            "sedes_validas", df_original_count, df_filtrado_count
        )
        
        return df_filtrado
