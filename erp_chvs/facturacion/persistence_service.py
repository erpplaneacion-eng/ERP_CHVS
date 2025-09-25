"""
Servicio de persistencia para guardar datos procesados en la base de datos.
"""

import pandas as pd
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction, IntegrityError
from django.utils import timezone

from .models import ListadosFocalizacion
from .config import ProcesamientoConfig
from .exceptions import ProcesamientoException
from .logging_config import FacturacionLogger


class PersistenceService:
    """Servicio para persistir datos procesados en la base de datos."""

    @staticmethod
    def guardar_listados_focalizacion(
        df: pd.DataFrame,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Guarda los datos procesados en la tabla ListadosFocalizacion.

        Args:
            df: DataFrame con los datos procesados
            batch_size: Tamaño del lote para inserción en batch

        Returns:
            Dict[str, Any]: Resultado de la operación
        """
        try:
            FacturacionLogger.log_procesamiento_inicio(
                "guardar_listados", "persistencia_bd"
            )

            # Preparar datos para inserción
            registros_para_insertar = []
            registros_duplicados = []
            registros_error = []

            for index, row in df.iterrows():
                try:
                    # Generar ID único para el listado
                    id_listado = PersistenceService._generar_id_listado(row)

                    # Crear objeto ListadosFocalizacion
                    registro = PersistenceService._crear_registro_listado(row, id_listado)

                    registros_para_insertar.append(registro)

                except Exception as e:
                    FacturacionLogger.log_procesamiento_error(
                        f"Fila {index}", f"Error al procesar registro: {str(e)}"
                    )
                    registros_error.append({
                        'fila': index,
                        'error': str(e),
                        'datos': row.to_dict()
                    })

            # Insertar en batch con transacción
            registros_guardados = PersistenceService._insertar_en_batch(
                registros_para_insertar,
                batch_size
            )

            resultado = {
                'success': True,
                'total_procesados': len(df),
                'registros_guardados': registros_guardados,
                'registros_error': len(registros_error),
                'errores_detalle': registros_error,
                'mensaje': f"Se guardaron {registros_guardados} de {len(df)} registros procesados."
            }

            FacturacionLogger.log_procesamiento_exito(
                "guardar_listados",
                len(df),
                registros_guardados
            )

            return resultado

        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "guardar_listados_focalizacion", str(e)
            )
            return {
                'success': False,
                'error': str(e),
                'total_procesados': len(df) if df is not None else 0,
                'registros_guardados': 0,
                'registros_error': 0,
                'errores_detalle': [],
                'mensaje': f"Error al guardar listados: {str(e)}"
            }

    @staticmethod
    def _generar_id_listado(row: pd.Series) -> str:
        """
        Genera un ID único para el listado.

        Args:
            row: Fila del DataFrame con los datos

        Returns:
            str: ID único generado
        """
        # Estrategia: año + ETC + documento + focalizacion + timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        doc_clean = str(row.get('doc', '')).replace(' ', '').replace('-', '')
        etc_short = str(row.get('ETC', ''))[:3].upper()
        focalizacion = str(row.get('focalizacion', ''))

        id_base = f"{row.get('ano', '')}{etc_short}{doc_clean[:8]}{focalizacion}"

        # Si el ID es muy largo, usar UUID parcial
        if len(id_base) > 30:
            unique_suffix = str(uuid.uuid4())[:8]
            return f"{id_base[:20]}{unique_suffix}"

        return f"{id_base}{timestamp[-4:]}"  # Últimos 4 dígitos del timestamp

    @staticmethod
    def _crear_registro_listado(row: pd.Series, id_listado: str) -> ListadosFocalizacion:
        """
        Crea un objeto ListadosFocalizacion a partir de una fila del DataFrame.

        Args:
            row: Fila del DataFrame
            id_listado: ID único para el registro

        Returns:
            ListadosFocalizacion: Objeto del modelo
        """
        # Calcular edad si no está disponible
        edad = PersistenceService._calcular_edad(row.get('fecha_nacimiento'), row.get('edad'))

        return ListadosFocalizacion(
            id_listados=id_listado,
            ano=int(row.get('AÑO', row.get('ano', 2025))),
            etc=str(row.get('ETC', '')),
            institucion=str(row.get('INSTITUCION', row.get('institucion', ''))),
            sede=str(row.get('SEDE', row.get('sede', ''))),
            tipodoc=str(row.get('TIPODOC', row.get('tipodoc', ''))),
            doc=str(row.get('DOC', row.get('doc', ''))),
            apellido1=PersistenceService._safe_string(row.get('APELLIDO1', row.get('apellido1'))),
            apellido2=PersistenceService._safe_string(row.get('APELLIDO2', row.get('apellido2'))),
            nombre1=str(row.get('NOMBRE1', row.get('nombre1', ''))),
            nombre2=PersistenceService._safe_string(row.get('NOMBRE2', row.get('nombre2'))),
            fecha_nacimiento=str(row.get('FECHA_NACIMIENTO', row.get('fecha_nacimiento', ''))),
            edad=edad,
            etnia=PersistenceService._safe_string(row.get('ETNIA', row.get('etnia'))),
            genero=str(row.get('GENERO', row.get('genero', ''))),
            grado_grupos=str(row.get('grado_grupos', '')),
            complemento_alimentario_preparado_am=PersistenceService._safe_string(
                row.get('COMPLEMENTO ALIMENTARIO PREPARADO AM')
            ),
            complemento_alimentario_preparado_pm=PersistenceService._safe_string(
                row.get('COMPLEMENTO ALIMENTARIO PREPARADO PM')
            ),
            almuerzo_jornada_unica=PersistenceService._safe_string(
                row.get('ALMUERZO JORNADA UNICA')
            ),
            refuerzo_complemento_am_pm=PersistenceService._safe_string(
                row.get('REFUERZO COMPLEMENTO AM/PM')
            ),
            focalizacion=str(row.get('focalizacion', ''))
        )

    @staticmethod
    def _safe_string(value) -> Optional[str]:
        """
        Convierte un valor a string de forma segura, retornando None si está vacío.

        Args:
            value: Valor a convertir

        Returns:
            Optional[str]: String o None
        """
        if pd.isna(value) or value == '' or value is None:
            return None
        return str(value)

    @staticmethod
    def _calcular_edad(fecha_nacimiento, edad_existente) -> int:
        """
        Calcula la edad a partir de la fecha de nacimiento o usa la edad existente.

        Args:
            fecha_nacimiento: Fecha de nacimiento
            edad_existente: Edad ya calculada

        Returns:
            int: Edad calculada
        """
        if edad_existente and not pd.isna(edad_existente):
            try:
                return int(edad_existente)
            except (ValueError, TypeError):
                pass

        # Intentar calcular desde fecha de nacimiento
        if fecha_nacimiento and not pd.isna(fecha_nacimiento):
            try:
                # Asumiendo formato DD/MM/YYYY
                fecha_str = str(fecha_nacimiento)
                if '/' in fecha_str:
                    parts = fecha_str.split('/')
                    if len(parts) == 3:
                        dia, mes, año = int(parts[0]), int(parts[1]), int(parts[2])
                        fecha_nac = datetime(año, mes, dia)
                        hoy = datetime.now()
                        edad = hoy.year - fecha_nac.year
                        if hoy.month < fecha_nac.month or (hoy.month == fecha_nac.month and hoy.day < fecha_nac.day):
                            edad -= 1
                        return edad
            except (ValueError, TypeError, IndexError):
                pass

        # Valor por defecto si no se puede calcular
        return 0

    @staticmethod
    def _insertar_en_batch(
        registros: List[ListadosFocalizacion],
        batch_size: int = 1000
    ) -> int:
        """
        Inserta registros en batch para optimizar el rendimiento.

        Args:
            registros: Lista de objetos ListadosFocalizacion
            batch_size: Tamaño del lote

        Returns:
            int: Número de registros guardados exitosamente
        """
        registros_guardados = 0

        try:
            # Dividir en lotes
            for i in range(0, len(registros), batch_size):
                lote = registros[i:i + batch_size]

                with transaction.atomic():
                    # Usar bulk_create con ignore_conflicts para manejar duplicados
                    objetos_creados = ListadosFocalizacion.objects.bulk_create(
                        lote,
                        ignore_conflicts=True,
                        batch_size=batch_size
                    )

                    registros_guardados += len(objetos_creados)

                    FacturacionLogger.log_procesamiento_inicio(
                        f"batch_{i//batch_size + 1}",
                        f"Guardado lote: {len(objetos_creados)} registros"
                    )

            return registros_guardados

        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "insertar_en_batch", str(e)
            )
            raise ProcesamientoException(f"Error al insertar en batch: {str(e)}")

    @staticmethod
    def verificar_duplicados(df: pd.DataFrame) -> Dict[str, List]:
        """
        Verifica si existen registros duplicados en la base de datos.

        Args:
            df: DataFrame con los datos a verificar

        Returns:
            Dict[str, List]: Diccionario con duplicados encontrados
        """
        try:
            documentos = df['DOC'].unique().tolist() if 'DOC' in df.columns else df['doc'].unique().tolist()
            focalizaciones = df['focalizacion'].unique().tolist()
            años = df['AÑO'].unique().tolist() if 'AÑO' in df.columns else df['ano'].unique().tolist()

            # Buscar duplicados en la base de datos
            duplicados_existentes = ListadosFocalizacion.objects.filter(
                doc__in=documentos,
                focalizacion__in=focalizaciones,
                ano__in=años
            ).values('doc', 'ano', 'focalizacion', 'id_listados')

            return {
                'duplicados_encontrados': list(duplicados_existentes),
                'total_duplicados': len(duplicados_existentes)
            }

        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "verificar_duplicados", str(e)
            )
            return {
                'duplicados_encontrados': [],
                'total_duplicados': 0,
                'error': str(e)
            }

    @staticmethod
    def obtener_estadisticas_bd() -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de la base de datos.

        Returns:
            Dict[str, Any]: Estadísticas de la base de datos
        """
        try:
            total_registros = ListadosFocalizacion.objects.count()

            # Estadísticas por año
            por_año = ListadosFocalizacion.objects.values('ano').distinct().count()

            # Estadísticas por ETC
            por_etc = ListadosFocalizacion.objects.values('etc').distinct().count()

            # Estadísticas por focalización
            por_focalizacion = ListadosFocalizacion.objects.values('focalizacion').distinct().count()

            return {
                'total_registros': total_registros,
                'años_distintos': por_año,
                'etc_distintos': por_etc,
                'focalizaciones_distintas': por_focalizacion,
                'fecha_consulta': timezone.now().isoformat()
            }

        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "obtener_estadisticas_bd", str(e)
            )
            return {
                'error': str(e),
                'total_registros': 0
            }