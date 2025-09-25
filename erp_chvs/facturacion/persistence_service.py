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
            # Log inicial solo con información esencial
            FacturacionLogger.log_procesamiento_inicio(
                "guardar_listados",
                f"Procesando {len(df)} registros del DataFrame"
            )

            # Preparar datos para inserción
            registros_para_insertar = []
            registros_error = []

            for index, row in df.iterrows():
                try:
                    # Generar ID único para el listado
                    id_listado = PersistenceService._generar_id_listado(row)

                    # Crear objeto ListadosFocalizacion
                    registro = PersistenceService._crear_registro_listado(row, id_listado)

                    registros_para_insertar.append(registro)

                except Exception as e:
                    # Solo log errores críticos, no cada fila individual
                    if len(registros_error) < 5:  # Limitar logs de error
                        FacturacionLogger.log_procesamiento_error(
                            f"fila_{index}", f"Error al procesar registro: {str(e)}"
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
                'duplicados_detectados': 0,  # Ya no hay duplicados bloqueados
                'errores_detalle': registros_error,
                'mensaje': f"Se guardaron {registros_guardados} de {len(df)} registros procesados."
            }

            # Log solo si hay problemas, éxito silencioso
            if registros_guardados < len(df):
                FacturacionLogger.log_procesamiento_inicio(
                    "guardar_listados_parcial",
                    f"Guardado parcial: {registros_guardados}/{len(df)} registros"
                )
            # Éxito completo no se loguea para evitar saturación

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
        Genera un ID único para el listado usando UUID para garantizar unicidad.

        Args:
            row: Fila del DataFrame con los datos

        Returns:
            str: ID único generado
        """
        # Estrategia: usar UUID para garantizar unicidad completa
        doc_clean = str(row.get('DOC', row.get('doc', ''))).replace(' ', '').replace('-', '')
        focalizacion = str(row.get('focalizacion', ''))
        ano = str(row.get('ANO', row.get('ano', '')))

        # Usar UUID4 + información del registro para garantizar unicidad
        unique_id = str(uuid.uuid4())[:12]  # 12 caracteres únicos

        # Prefijo con año y focalización para identificación
        prefix = f"{ano}{focalizacion}"

        # ID final: año + focalización + UUID único
        id_final = f"{prefix}_{unique_id}"

        # Truncar si es muy largo (máximo 50 caracteres según modelo)
        if len(id_final) > 50:
            id_final = id_final[:50]

        return id_final

    @staticmethod
    def _crear_registro_listado(row: pd.Series, id_listado: str) -> ListadosFocalizacion:
        """
        Crea un objeto ListadosFocalizacion a partir de una fila del DataFrame.
        Valida y trunca campos que excedan la longitud máxima permitida.

        Args:
            row: Fila del DataFrame
            id_listado: ID único para el registro

        Returns:
            ListadosFocalizacion: Objeto del modelo
        """
        # Calcular edad si no está disponible
        edad = PersistenceService._calcular_edad(row.get('fecha_nacimiento'), row.get('edad'))

        # Truncar campos que excedan la longitud máxima (según modelo)
        doc = PersistenceService._truncate_field(str(row.get('DOC', row.get('doc', ''))), 20)
        fecha_nacimiento = PersistenceService._truncate_field(
            str(row.get('FECHA_NACIMIENTO', row.get('fecha_nacimiento', ''))), 20
        )
        tipodoc = PersistenceService._truncate_field(str(row.get('TIPODOC', row.get('tipodoc', ''))), 10)
        genero = PersistenceService._truncate_field(str(row.get('GENERO', row.get('genero', ''))), 10)
        grado_grupos = PersistenceService._truncate_field(str(row.get('grado_grupos', '')), 20)

        # Truncar campos de texto largo
        etc = PersistenceService._truncate_field(str(row.get('ETC', '')), 100)
        institucion = PersistenceService._truncate_field(str(row.get('INSTITUCION', row.get('institucion', ''))), 200)
        sede = PersistenceService._truncate_field(str(row.get('SEDE', row.get('sede', ''))), 200)

        return ListadosFocalizacion(
            id_listados=id_listado,
            ano=int(row.get('AÑO', row.get('ano', 2025))),
            etc=etc,
            institucion=institucion,
            sede=sede,
            tipodoc=tipodoc,
            doc=doc,
            apellido1=PersistenceService._safe_string(row.get('APELLIDO1', row.get('apellido1'))),
            apellido2=PersistenceService._safe_string(row.get('APELLIDO2', row.get('apellido2'))),
            nombre1=str(row.get('NOMBRE1', row.get('nombre1', ''))),
            nombre2=PersistenceService._safe_string(row.get('NOMBRE2', row.get('nombre2'))),
            fecha_nacimiento=fecha_nacimiento,
            edad=edad,
            etnia=PersistenceService._safe_string(row.get('ETNIA', row.get('etnia'))),
            genero=genero,
            grado_grupos=grado_grupos,
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
    def _truncate_field(value: str, max_length: int) -> str:
        """
        Trunca un campo de texto si excede la longitud máxima permitida.

        Args:
            value: Valor a truncar
            max_length: Longitud máxima permitida

        Returns:
            str: Valor truncado si es necesario
        """
        if not value:
            return value
        if len(value) > max_length:
            # Solo log en casos excepcionales (muy largos), no logs rutinarios
            if len(value) > max_length * 2:  # Solo si es mucho más largo
                FacturacionLogger.log_procesamiento_inicio(
                    "truncate_field",
                    f"Campo truncado de {len(value)} a {max_length} caracteres"
                )
            return value[:max_length]
        return value

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
        Maneja errores de forma robusta sin corromper transacciones.

        Args:
            registros: Lista de objetos ListadosFocalizacion
            batch_size: Tamaño del lote

        Returns:
            int: Número de registros guardados exitosamente
        """
        registros_guardados = 0

        try:
            # Solo log inicial, sin logs por cada lote
            FacturacionLogger.log_procesamiento_inicio(
                "insertar_en_batch",
                f"Iniciando inserción de {len(registros)} registros"
            )

            # Dividir en lotes
            for i in range(0, len(registros), batch_size):
                lote = registros[i:i + batch_size]
                numero_lote = i//batch_size + 1

                # Usar transacción independiente para cada lote
                try:
                    with transaction.atomic():
                        objetos_creados = ListadosFocalizacion.objects.bulk_create(
                            lote,
                            batch_size=batch_size
                        )

                        registros_guardados += len(objetos_creados)

                except Exception as lote_error:
                    # Si falla el lote completo, intentar guardar uno por uno
                    FacturacionLogger.log_procesamiento_error(
                        f"lote_{numero_lote}",
                        f"Error en lote {numero_lote}: {str(lote_error)}. Intentando inserción individual."
                    )

                    registros_lote = 0
                    for registro in lote:
                        try:
                            # Usar transacción independiente para cada registro
                            with transaction.atomic():
                                registro.save()
                                registros_lote += 1
                                registros_guardados += 1
                        except Exception as registro_error:
                            # Solo log errores críticos, no cada registro individual
                            continue

                    if registros_lote > 0:
                        FacturacionLogger.log_procesamiento_inicio(
                            f"lote_{numero_lote}_recuperado",
                            f"Lote {numero_lote} recuperado: {registros_lote} registros"
                        )

            # Log final solo si hay errores significativos
            if registros_guardados < len(registros):
                FacturacionLogger.log_procesamiento_inicio(
                    "insertar_en_batch_parcial",
                    f"Inserción parcial: {registros_guardados}/{len(registros)} registros guardados"
                )
            else:
                FacturacionLogger.log_procesamiento_exito(
                    "insertar_en_batch",
                    len(registros),
                    registros_guardados
                )

            return registros_guardados

        except Exception as e:
            FacturacionLogger.log_procesamiento_error(
                "insertar_en_batch_general",
                f"Error general en inserción por lotes: {str(e)}"
            )
            # Fallback final: intentar guardar todos uno por uno
            registros_guardados = 0
            for registro in registros:
                try:
                    with transaction.atomic():
                        registro.save()
                        registros_guardados += 1
                except Exception as registro_error:
                    FacturacionLogger.log_procesamiento_error(
                        f"registro_fallback_{registro.id_listados}",
                        f"Error en fallback: {str(registro_error)}"
                    )
                    continue

            return registros_guardados

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
    def test_conexion_bd() -> Dict[str, Any]:
        """
        Método de prueba para verificar la conexión y permisos de la base de datos.
        
        Returns:
            Dict[str, Any]: Resultado del test
        """
        try:
            # Contar registros existentes
            total_actual = ListadosFocalizacion.objects.count()
            
            # Intentar crear un registro de prueba
            registro_prueba = ListadosFocalizacion(
                id_listados="TEST_001",
                ano=2025,
                etc="TEST",
                institucion="TEST",
                sede="TEST",
                tipodoc="CC",
                doc="12345678",
                nombre1="TEST",
                fecha_nacimiento="01/01/2000",
                edad=25,
                genero="M",
                grado_grupos="TEST",
                focalizacion="F1"
            )
            
            # Guardar el registro de prueba
            registro_prueba.save()
            
            # Verificar que se guardó
            total_despues = ListadosFocalizacion.objects.count()
            
            # Eliminar el registro de prueba
            registro_prueba.delete()
            
            return {
                'success': True,
                'total_antes': total_actual,
                'total_despues': total_despues,
                'mensaje': 'Conexión a BD y permisos funcionando correctamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mensaje': f'Error en conexión a BD: {str(e)}'
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