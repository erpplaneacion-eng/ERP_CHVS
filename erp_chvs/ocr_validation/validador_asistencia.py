"""
Validador especializado para marcas de asistencia (X) en tabla de estudiantes.
Detecta, cuenta y valida la posición de las marcas X por cada estudiante.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple


logger = logging.getLogger(__name__)


class ValidadorAsistenciaDetallado:
    """
    Validador detallado de marcas de asistencia por estudiante.

    Funcionalidades:
    - Detecta cada fila de estudiante
    - Cuenta las marcas X por estudiante
    - Valida que las X estén dentro de las celdas de días
    - Genera reporte de asistencia por estudiante
    """

    def __init__(self):
        """Inicializa el validador de asistencia."""
        # Días del mes esperados (columnas 01-31)
        self.dias_mes = list(range(1, 32))

        # Umbral de asistencia mínima esperada (por ejemplo, 15 días)
        self.asistencia_minima = 10

    def validar_asistencia_detallada(
        self,
        texto_ocr: str,
        pagina: int
    ) -> Dict[str, Any]:
        """
        Valida la asistencia de todos los estudiantes en la página.

        Args:
            texto_ocr: Texto extraído por OCR de la página
            pagina: Número de página

        Returns:
            Dict con resultados de validación:
                - estudiantes: Lista de estudiantes con su asistencia
                - errores: Lista de errores encontrados
                - estadisticas: Resumen de asistencia
        """
        resultado = {
            'estudiantes': [],
            'errores': [],
            'estadisticas': {
                'total_estudiantes': 0,
                'con_asistencia': 0,
                'sin_asistencia': 0,
                'asistencia_baja': 0,
                'total_marcas_x': 0
            }
        }

        # Extraer todas las filas de estudiantes
        estudiantes = self._extraer_filas_estudiantes(texto_ocr, pagina)
        resultado['estudiantes'] = estudiantes
        resultado['estadisticas']['total_estudiantes'] = len(estudiantes)

        # Validar cada estudiante
        for estudiante in estudiantes:
            # Contar marcas X
            num_marcas = estudiante['num_marcas_x']
            resultado['estadisticas']['total_marcas_x'] += num_marcas

            # Validar asistencia
            if num_marcas == 0:
                resultado['estadisticas']['sin_asistencia'] += 1
                resultado['errores'].append({
                    'tipo': 'estudiante_sin_asistencia',
                    'descripcion': f"Estudiante '{estudiante['nombre']}' sin marcas de asistencia",
                    'pagina': pagina,
                    'fila_estudiante': estudiante['fila'],
                    'severidad': 'critico',
                    'campo': 'asistencia'
                })
            elif num_marcas < self.asistencia_minima:
                resultado['estadisticas']['asistencia_baja'] += 1
                resultado['errores'].append({
                    'tipo': 'asistencia_baja',
                    'descripcion': f"Estudiante '{estudiante['nombre']}' con asistencia baja ({num_marcas} días)",
                    'pagina': pagina,
                    'fila_estudiante': estudiante['fila'],
                    'severidad': 'advertencia',
                    'campo': 'asistencia'
                })
            else:
                resultado['estadisticas']['con_asistencia'] += 1

            # Validar posición de las X
            errores_posicion = self._validar_posicion_marcas(estudiante, pagina)
            resultado['errores'].extend(errores_posicion)

        return resultado

    def _extraer_filas_estudiantes(self, texto_ocr: str, pagina: int) -> List[Dict[str, Any]]:
        """
        Extrae información de cada fila de estudiante.

        Args:
            texto_ocr: Texto completo de la página
            pagina: Número de página

        Returns:
            Lista de diccionarios con información de cada estudiante
        """
        estudiantes = []
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            # Detectar si es una fila de estudiante
            if self._es_fila_estudiante(linea):
                estudiante = self._parsear_fila_estudiante(linea, i + 1, pagina)
                if estudiante:
                    estudiantes.append(estudiante)

        logger.info(f"📊 Página {pagina}: {len(estudiantes)} estudiantes detectados")
        return estudiantes

    def _es_fila_estudiante(self, linea: str) -> bool:
        """
        Determina si una línea es una fila de estudiante.

        Patrón esperado:
        N° | TIPO_DOC | NUM_DOC | NOMBRES | APELLIDOS | FECHA | SEXO | MODALIDAD | X X X X...

        Args:
            linea: Línea de texto a analizar

        Returns:
            True si es una fila de estudiante
        """
        # Patrón: número + tipo doc (1-2 dígitos) + documento (8-11 dígitos) + nombres
        patron = r'^\s*\d+\s+\d{1,2}\s+\d{8,11}\s+[A-ZÁÉÍÓÚÑ]'
        return bool(re.match(patron, linea, re.IGNORECASE))

    def _parsear_fila_estudiante(
        self,
        linea: str,
        fila: int,
        pagina: int
    ) -> Optional[Dict[str, Any]]:
        """
        Parsea una fila de estudiante y extrae su información.

        Args:
            linea: Línea de texto
            fila: Número de fila en el texto
            pagina: Número de página

        Returns:
            Dict con información del estudiante o None si no se pudo parsear
        """
        try:
            # Patrón completo de fila de estudiante
            # Grupos: (num_fila) (tipo_doc) (num_doc) (nombres...) (resto con marcas X)
            patron = r'^\s*(\d+)\s+(\d{1,2})\s+(\d{8,11})\s+([A-ZÁÉÍÓÚÑ\s]+?)\s+(\d{4}-\d{2}-\d{2})?\s*([MF])?\s*([\d-]+)?\s*(.*)$'
            match = re.match(patron, linea, re.IGNORECASE)

            if not match:
                return None

            num_fila = match.group(1)
            tipo_doc = match.group(2)
            num_doc = match.group(3)
            nombres_completos = match.group(4).strip()
            fecha_nac = match.group(5)
            sexo = match.group(6)
            modalidad = match.group(7)
            resto_linea = match.group(8)  # Aquí están las marcas X

            # Contar marcas X en el resto de la línea
            marcas_x = self._contar_marcas_x(resto_linea)

            # Extraer posiciones de las X
            posiciones_x = self._extraer_posiciones_x(resto_linea)

            estudiante = {
                'fila': fila,
                'pagina': pagina,
                'num_fila': num_fila,
                'tipo_documento': tipo_doc,
                'num_documento': num_doc,
                'nombre': nombres_completos,
                'fecha_nacimiento': fecha_nac,
                'sexo': sexo,
                'modalidad': modalidad,
                'num_marcas_x': marcas_x['total'],
                'marcas_x_detectadas': marcas_x['marcas'],
                'posiciones_x': posiciones_x,
                'linea_completa': linea
            }

            return estudiante

        except Exception as e:
            logger.error(f"Error parseando fila {fila}: {e}")
            return None

    def _contar_marcas_x(self, texto: str) -> Dict[str, Any]:
        """
        Cuenta todas las marcas X en un texto.

        Args:
            texto: Texto donde buscar marcas X

        Returns:
            Dict con total y lista de marcas encontradas
        """
        # Buscar todas las X (mayúsculas y minúsculas)
        marcas = re.finditer(r'[Xx]', texto)

        marcas_lista = []
        for match in marcas:
            marcas_lista.append({
                'caracter': match.group(),
                'posicion': match.start(),
                'contexto': texto[max(0, match.start()-2):match.end()+2]
            })

        return {
            'total': len(marcas_lista),
            'marcas': marcas_lista
        }

    def _extraer_posiciones_x(self, texto: str) -> List[int]:
        """
        Extrae las posiciones de todas las X en el texto.

        Args:
            texto: Texto donde buscar

        Returns:
            Lista de posiciones (índices) donde se encontraron X
        """
        posiciones = []
        for i, char in enumerate(texto):
            if char.upper() == 'X':
                posiciones.append(i)
        return posiciones

    def _validar_posicion_marcas(
        self,
        estudiante: Dict[str, Any],
        pagina: int
    ) -> List[Dict[str, Any]]:
        """
        Valida que las marcas X estén correctamente posicionadas.

        Args:
            estudiante: Dict con información del estudiante
            pagina: Número de página

        Returns:
            Lista de errores de posición encontrados
        """
        errores = []
        posiciones = estudiante['posiciones_x']

        if not posiciones:
            return errores

        # Detectar X muy juntas (posible error de OCR o diligenciamiento)
        for i in range(len(posiciones) - 1):
            distancia = posiciones[i + 1] - posiciones[i]

            # Si hay X con distancia menor a 2 caracteres, es sospechoso
            if distancia < 2:
                errores.append({
                    'tipo': 'marcas_x_muy_juntas',
                    'descripcion': f"Estudiante '{estudiante['nombre']}' tiene marcas X muy juntas (posible error)",
                    'pagina': pagina,
                    'fila_estudiante': estudiante['fila'],
                    'severidad': 'advertencia',
                    'campo': 'asistencia_posicion'
                })
                break  # Solo reportar una vez por estudiante

        # Detectar patrón sospechoso: todas las X consecutivas sin espacios
        if len(posiciones) > 5:
            todas_consecutivas = all(
                posiciones[i + 1] - posiciones[i] <= 1
                for i in range(len(posiciones) - 1)
            )

            if todas_consecutivas:
                errores.append({
                    'tipo': 'patron_asistencia_sospechoso',
                    'descripcion': f"Estudiante '{estudiante['nombre']}' tiene patrón sospechoso: todas las X consecutivas",
                    'pagina': pagina,
                    'fila_estudiante': estudiante['fila'],
                    'severidad': 'advertencia',
                    'campo': 'asistencia_patron'
                })

        return errores

    def _validar_marcas_en_celdas(
        self,
        estudiante: Dict[str, Any],
        ancho_celda: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Valida que las marcas X estén dentro de celdas esperadas.

        Args:
            estudiante: Información del estudiante
            ancho_celda: Ancho aproximado de cada celda de día

        Returns:
            Lista de errores de posición en celdas
        """
        errores = []
        posiciones = estudiante['posiciones_x']

        # Calcular en qué celda debería estar cada X
        for pos in posiciones:
            celda_estimada = pos // ancho_celda
            posicion_en_celda = pos % ancho_celda

            # Si la X está muy al borde de la celda, puede estar fuera
            if posicion_en_celda == 0 or posicion_en_celda == ancho_celda - 1:
                errores.append({
                    'tipo': 'marca_x_borde_celda',
                    'descripcion': f"Marca X en posición {pos} puede estar fuera de celda (estudiante: {estudiante['nombre']})",
                    'pagina': estudiante['pagina'],
                    'fila_estudiante': estudiante['fila'],
                    'severidad': 'info',
                    'campo': 'asistencia_celda'
                })

        return errores

    def generar_reporte_asistencia(
        self,
        resultado_validacion: Dict[str, Any]
    ) -> str:
        """
        Genera un reporte legible de asistencia.

        Args:
            resultado_validacion: Resultado de validar_asistencia_detallada()

        Returns:
            String con reporte formateado
        """
        estudiantes = resultado_validacion['estudiantes']
        stats = resultado_validacion['estadisticas']

        reporte = []
        reporte.append("=" * 80)
        reporte.append("📊 REPORTE DE ASISTENCIA DETALLADO")
        reporte.append("=" * 80)
        reporte.append(f"Total de estudiantes: {stats['total_estudiantes']}")
        reporte.append(f"Con asistencia normal: {stats['con_asistencia']}")
        reporte.append(f"Con asistencia baja: {stats['asistencia_baja']}")
        reporte.append(f"Sin asistencia: {stats['sin_asistencia']}")
        reporte.append(f"Total marcas X: {stats['total_marcas_x']}")
        reporte.append("")
        reporte.append("-" * 80)
        reporte.append("DETALLE POR ESTUDIANTE:")
        reporte.append("-" * 80)

        for est in estudiantes:
            reporte.append(f"Fila {est['fila']}: {est['nombre']}")
            reporte.append(f"  Documento: {est['num_documento']}")
            reporte.append(f"  Días asistidos: {est['num_marcas_x']}")
            reporte.append(f"  Posiciones X: {est['posiciones_x']}")
            reporte.append("")

        reporte.append("=" * 80)

        return "\n".join(reporte)

    def obtener_estudiantes_sin_asistencia(
        self,
        resultado_validacion: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Obtiene lista de estudiantes sin marcas de asistencia.

        Args:
            resultado_validacion: Resultado de validación

        Returns:
            Lista de estudiantes sin asistencia
        """
        return [
            est for est in resultado_validacion['estudiantes']
            if est['num_marcas_x'] == 0
        ]

    def obtener_estudiantes_asistencia_baja(
        self,
        resultado_validacion: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Obtiene estudiantes con asistencia baja.

        Args:
            resultado_validacion: Resultado de validación

        Returns:
            Lista de estudiantes con asistencia baja
        """
        return [
            est for est in resultado_validacion['estudiantes']
            if 0 < est['num_marcas_x'] < self.asistencia_minima
        ]
