"""
Validadores mejorados para campos específicos del PDF de asistencia.
Valida raciones, nombres, firmas y asistencia.
"""

import re
import logging
from typing import Dict, List, Any, Optional


logger = logging.getLogger(__name__)


class ValidadorRacionesMejorado:
    """
    Validador para raciones diarias y mensuales.

    Valida:
    - Raciones programadas vs entregadas
    - Coherencia entre raciones diarias y mensuales
    - Formato numérico correcto
    """

    def validar_raciones(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """
        Valida las raciones diarias y mensuales del PDF.

        Args:
            texto_ocr: Texto extraído por OCR de la página
            pagina: Número de página

        Returns:
            Lista de errores encontrados
        """
        errores = []

        # Extraer raciones
        raciones = self._extraer_raciones(texto_ocr)

        # Validar que se hayan extraído
        if not raciones.get('diarias_programadas'):
            errores.append({
                'tipo': 'raciones_diarias_programadas_faltantes',
                'descripcion': 'No se encontraron raciones diarias programadas',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'raciones_diarias_programadas'
            })

        if not raciones.get('mensuales_programadas'):
            errores.append({
                'tipo': 'raciones_mensuales_programadas_faltantes',
                'descripcion': 'No se encontraron raciones mensuales programadas',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'raciones_mensuales_programadas'
            })

        # Validar raciones entregadas (deben estar diligenciadas manualmente)
        if not raciones.get('diarias_entregadas'):
            errores.append({
                'tipo': 'raciones_diarias_entregadas_faltantes',
                'descripcion': 'Raciones diarias entregadas no está diligenciado',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'raciones_diarias_entregadas'
            })

        if not raciones.get('mensuales_entregadas'):
            errores.append({
                'tipo': 'raciones_mensuales_entregadas_faltantes',
                'descripcion': 'Raciones mensuales entregadas no está diligenciado',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'raciones_mensuales_entregadas'
            })

        # Validar coherencia numérica
        errores.extend(self._validar_coherencia_raciones(raciones, pagina))

        return errores

    def _extraer_raciones(self, texto_ocr: str) -> Dict[str, Optional[int]]:
        """Extrae los valores de raciones del texto OCR."""
        raciones = {
            'diarias_programadas': None,
            'diarias_entregadas': None,
            'mensuales_programadas': None,
            'mensuales_entregadas': None
        }

        # Patrón para raciones diarias programadas
        patron_diarias_prog = r'RACIONES\s+DIARIAS\s+PROGRAMADAS.*?:\s*(\d+)'
        match = re.search(patron_diarias_prog, texto_ocr, re.IGNORECASE | re.MULTILINE)
        if match:
            raciones['diarias_programadas'] = int(match.group(1))

        # Patrón para raciones diarias entregadas
        patron_diarias_ent = r'RACIONES\s+DIARIAS\s+ENTREGADAS.*?:\s*(\d+)'
        match = re.search(patron_diarias_ent, texto_ocr, re.IGNORECASE | re.MULTILINE)
        if match:
            raciones['diarias_entregadas'] = int(match.group(1))

        # Patrón para raciones mensuales programadas
        patron_mensuales_prog = r'RACIONES\s+MENSUALES\s+PROGRAMADAS.*?:\s*(\d+)'
        match = re.search(patron_mensuales_prog, texto_ocr, re.IGNORECASE | re.MULTILINE)
        if match:
            raciones['mensuales_programadas'] = int(match.group(1))

        # Patrón para raciones mensuales entregadas
        patron_mensuales_ent = r'RACIONES\s+MENSUALES\s+ENTREGADAS.*?:\s*(\d+)'
        match = re.search(patron_mensuales_ent, texto_ocr, re.IGNORECASE | re.MULTILINE)
        if match:
            raciones['mensuales_entregadas'] = int(match.group(1))

        return raciones

    def _validar_coherencia_raciones(self, raciones: Dict[str, Optional[int]], pagina: int) -> List[Dict[str, Any]]:
        """Valida coherencia entre raciones."""
        errores = []

        diarias_prog = raciones.get('diarias_programadas')
        diarias_ent = raciones.get('diarias_entregadas')
        mensuales_prog = raciones.get('mensuales_programadas')
        mensuales_ent = raciones.get('mensuales_entregadas')

        # Validar que entregadas no superen programadas
        if diarias_prog and diarias_ent and diarias_ent > diarias_prog:
            errores.append({
                'tipo': 'raciones_diarias_excedidas',
                'descripcion': f'Raciones diarias entregadas ({diarias_ent}) superan programadas ({diarias_prog})',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'raciones_diarias'
            })

        if mensuales_prog and mensuales_ent and mensuales_ent > mensuales_prog:
            errores.append({
                'tipo': 'raciones_mensuales_excedidas',
                'descripcion': f'Raciones mensuales entregadas ({mensuales_ent}) superan programadas ({mensuales_prog})',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'raciones_mensuales'
            })

        # Validar rangos razonables
        if diarias_prog and (diarias_prog < 1 or diarias_prog > 500):
            errores.append({
                'tipo': 'raciones_diarias_fuera_rango',
                'descripcion': f'Raciones diarias programadas fuera de rango razonable: {diarias_prog}',
                'pagina': pagina,
                'severidad': 'advertencia',
                'campo': 'raciones_diarias_programadas'
            })

        if mensuales_prog and (mensuales_prog < 20 or mensuales_prog > 15000):
            errores.append({
                'tipo': 'raciones_mensuales_fuera_rango',
                'descripcion': f'Raciones mensuales programadas fuera de rango razonable: {mensuales_prog}',
                'pagina': pagina,
                'severidad': 'advertencia',
                'campo': 'raciones_mensuales_programadas'
            })

        return errores


class ValidadorNombresFirmas:
    """
    Validador para nombres de estudiantes y firmas de responsables.
    """

    def validar_nombres_firmas(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """
        Valida nombres de estudiantes y firmas en el documento.

        Args:
            texto_ocr: Texto extraído por OCR
            pagina: Número de página

        Returns:
            Lista de errores encontrados
        """
        errores = []

        # Validar firmas de responsables
        errores.extend(self._validar_firmas_responsables(texto_ocr, pagina))

        # Validar nombres de estudiantes en la tabla
        errores.extend(self._validar_nombres_estudiantes(texto_ocr, pagina))

        return errores

    def _validar_firmas_responsables(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida las firmas del operador y rector."""
        errores = []

        # Buscar nombre del responsable del operador
        patron_responsable = r'NOMBRE\s+DEL\s+RESPONSABLE\s+DEL\s+OPERADOR:\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\n|$)'
        match = re.search(patron_responsable, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if not match or len(match.group(1).strip()) < 3:
            errores.append({
                'tipo': 'nombre_responsable_operador_faltante',
                'descripcion': 'Nombre del responsable del operador no está diligenciado',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'nombre_responsable_operador'
            })

        # Buscar firma del responsable del operador
        patron_firma_operador = r'FIRMA\s+DEL\s+RESPONSABLE\s+DEL\s+OPERADOR'
        if not re.search(patron_firma_operador, texto_ocr, re.IGNORECASE):
            errores.append({
                'tipo': 'firma_responsable_operador_faltante',
                'descripcion': 'No se detectó firma del responsable del operador',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'firma_responsable_operador'
            })

        # Buscar nombre del rector
        patron_rector = r'NOMBRE\s+RECTOR\s+ESTABLECIMIENTO\s+EDUCATIVO:\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\n|$)'
        match = re.search(patron_rector, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if not match or len(match.group(1).strip()) < 3:
            errores.append({
                'tipo': 'nombre_rector_faltante',
                'descripcion': 'Nombre del rector no está diligenciado',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'nombre_rector'
            })

        # Buscar firma del rector
        patron_firma_rector = r'FIRMA\s+DEL\s+RECTOR\s+ESTABLECIMIENTO'
        if not re.search(patron_firma_rector, texto_ocr, re.IGNORECASE):
            errores.append({
                'tipo': 'firma_rector_faltante',
                'descripcion': 'No se detectó firma del rector',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'firma_rector'
            })

        return errores

    def _validar_nombres_estudiantes(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Valida que los nombres de estudiantes estén completos."""
        errores = []

        # Buscar líneas que parecen ser registros de estudiantes
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            # Buscar patrón de estudiante: número + tipo doc + número doc + nombres
            # Ejemplo: "1  2  1077140421  KEVIN  SMITH  ACOSTA  ROMERO"
            patron_estudiante = r'^\s*\d+\s+\d+\s+\d{8,11}\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+\d{4}-\d{2}-\d{2}|$)'
            match = re.search(patron_estudiante, linea)

            if match:
                nombres = match.group(1).strip()

                # Validar que tenga al menos 2 palabras (nombre y apellido)
                palabras = nombres.split()
                if len(palabras) < 2:
                    errores.append({
                        'tipo': 'nombre_estudiante_incompleto',
                        'descripcion': f'Nombre de estudiante incompleto en línea {i+1}: "{nombres}"',
                        'pagina': pagina,
                        'severidad': 'advertencia',
                        'campo': 'nombre_estudiante',
                        'fila_estudiante': i + 1
                    })

        return errores


class ValidadorAsistenciaMejorado:
    """
    Validador mejorado para marcas de asistencia (X) en la tabla.
    Utiliza el ValidadorAsistenciaDetallado para análisis completo.
    """

    def __init__(self):
        """Inicializa el validador."""
        try:
            from .validador_asistencia import ValidadorAsistenciaDetallado
            self.validador_detallado = ValidadorAsistenciaDetallado()
        except ImportError:
            self.validador_detallado = None
            logger.warning("ValidadorAsistenciaDetallado no disponible")

    def validar_asistencia(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """
        Valida las marcas de asistencia en el documento.

        Args:
            texto_ocr: Texto extraído por OCR
            pagina: Número de página

        Returns:
            Lista de errores encontrados
        """
        # Si tenemos el validador detallado, usarlo
        if self.validador_detallado:
            resultado = self.validador_detallado.validar_asistencia_detallada(texto_ocr, pagina)

            # Imprimir reporte de asistencia en logs
            logger.info(f"📊 Asistencia - Total estudiantes: {resultado['estadisticas']['total_estudiantes']}")
            logger.info(f"📊 Asistencia - Total marcas X: {resultado['estadisticas']['total_marcas_x']}")
            logger.info(f"📊 Asistencia - Sin asistencia: {resultado['estadisticas']['sin_asistencia']}")

            return resultado['errores']

        # Fallback: validación básica
        return self._validar_asistencia_basica(texto_ocr, pagina)

    def _validar_asistencia_basica(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """Validación básica de asistencia (fallback)."""
        errores = []
        lineas = texto_ocr.split('\n')
        estudiantes_sin_asistencia = 0

        for i, linea in enumerate(lineas):
            if self._es_linea_estudiante(linea):
                marcas_x = linea.upper().count('X')

                if marcas_x == 0:
                    estudiantes_sin_asistencia += 1
                    errores.append({
                        'tipo': 'estudiante_sin_asistencia',
                        'descripcion': f'Estudiante sin marcas de asistencia en línea {i+1}',
                        'pagina': pagina,
                        'severidad': 'advertencia',
                        'campo': 'asistencia',
                        'fila_estudiante': i + 1
                    })

                if self._detectar_patron_sospechoso(linea):
                    errores.append({
                        'tipo': 'patron_asistencia_sospechoso',
                        'descripcion': f'Patrón de asistencia sospechoso en línea {i+1}',
                        'pagina': pagina,
                        'severidad': 'info',
                        'campo': 'asistencia',
                        'fila_estudiante': i + 1
                    })

        if estudiantes_sin_asistencia > 5:
            errores.append({
                'tipo': 'multiples_estudiantes_sin_asistencia',
                'descripcion': f'{estudiantes_sin_asistencia} estudiantes sin marcas de asistencia',
                'pagina': pagina,
                'severidad': 'advertencia',
                'campo': 'asistencia_general'
            })

        return errores

    def _es_linea_estudiante(self, linea: str) -> bool:
        """Determina si una línea parece ser un registro de estudiante."""
        # Buscar patrón: número + tipo doc + número doc + nombres
        patron = r'^\s*\d+\s+\d+\s+\d{8,11}\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]'
        return bool(re.match(patron, linea))

    def _detectar_patron_sospechoso(self, linea: str) -> bool:
        """
        Detecta patrones sospechosos de asistencia.
        Por ejemplo: Todas X seguidas sin espacios.
        """
        # Buscar 5 o más X consecutivas sin espacios (patrón sospechoso)
        return bool(re.search(r'X{5,}', linea.upper()))


class ValidadorModalidadConsumo:
    """
    Validador para la modalidad de consumo (Preparada en sitio, Industrializada, Catering).
    """

    def validar_modalidad(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """
        Valida que se haya marcado una modalidad de consumo.

        Args:
            texto_ocr: Texto extraído por OCR
            pagina: Número de página

        Returns:
            Lista de errores encontrados
        """
        errores = []

        # Buscar secciones de modalidad
        modalidades_marcadas = []

        if 'PREPARADA EN SITIO' in texto_ocr.upper():
            # Buscar marca cerca de "PREPARADA EN SITIO"
            if self._buscar_marca_checkbox(texto_ocr, 'PREPARADA EN SITIO'):
                modalidades_marcadas.append('PREPARADA EN SITIO')

        if 'INDUSTRIALIZADA' in texto_ocr.upper():
            if self._buscar_marca_checkbox(texto_ocr, 'INDUSTRIALIZADA'):
                modalidades_marcadas.append('INDUSTRIALIZADA')

        if 'CATERING' in texto_ocr.upper() or 'CATTERING' in texto_ocr.upper():
            if self._buscar_marca_checkbox(texto_ocr, 'CATERING'):
                modalidades_marcadas.append('CATERING')

        # Validar que haya al menos una modalidad marcada
        if len(modalidades_marcadas) == 0:
            errores.append({
                'tipo': 'modalidad_consumo_faltante',
                'descripcion': 'No se detectó ninguna modalidad de consumo marcada',
                'pagina': pagina,
                'severidad': 'critico',
                'campo': 'modalidad_consumo'
            })

        # Advertir si hay múltiples modalidades marcadas
        if len(modalidades_marcadas) > 1:
            errores.append({
                'tipo': 'multiples_modalidades_marcadas',
                'descripcion': f'Se marcaron múltiples modalidades: {", ".join(modalidades_marcadas)}',
                'pagina': pagina,
                'severidad': 'advertencia',
                'campo': 'modalidad_consumo'
            })

        return errores

    def _buscar_marca_checkbox(self, texto_ocr: str, modalidad: str) -> bool:
        """
        Busca marcas cerca de una modalidad (X, ✓, etc.).

        Args:
            texto_ocr: Texto completo
            modalidad: Nombre de la modalidad a buscar

        Returns:
            True si se encontró marca cerca de la modalidad
        """
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            if modalidad.upper() in linea.upper():
                # Buscar X, ✓ u otros símbolos en la misma línea o siguientes 2
                for j in range(i, min(i + 3, len(lineas))):
                    if re.search(r'[X✓✔☑]', lineas[j], re.IGNORECASE):
                        return True

        return False
