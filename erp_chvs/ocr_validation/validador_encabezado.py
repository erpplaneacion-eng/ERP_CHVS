"""
Validador de encabezado para PDFs de asistencia escolar.
Extrae y valida la información del encabezado del documento.
"""

import re
import logging
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class ValidadorEncabezado:
    """
    Validador para extraer y validar información del encabezado de PDFs.

    El encabezado contiene:
    - Departamento y código DANE
    - Municipio y código DANE
    - Operador y contrato
    - Institución educativa y código DANE
    - Sede educativa
    - Mes de atención y año
    - Tipo de complemento alimenticio
    """

    def __init__(self):
        """Inicializa el validador de encabezado."""
        self.meses_validos = [
            'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
            'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
        ]

        self.tipos_complemento = [
            'ALMUERZO', 'DESAYUNO', 'REFRIGERIO', 'CAJMPS', 'MEDIAMANANA'
        ]

    def extraer_encabezado(self, texto_ocr: str) -> Dict[str, Any]:
        """
        Extrae toda la información del encabezado del texto OCR.

        Args:
            texto_ocr: Texto completo extraído por OCR

        Returns:
            Dict con información del encabezado
        """
        encabezado = {
            'departamento': self._extraer_departamento(texto_ocr),
            'codigo_dane_departamento': self._extraer_codigo_dane_depto(texto_ocr),
            'municipio': self._extraer_municipio(texto_ocr),
            'codigo_dane_municipio': self._extraer_codigo_dane_mpio(texto_ocr),
            'operador': self._extraer_operador(texto_ocr),
            'contrato': self._extraer_contrato(texto_ocr),
            'mes_atencion': self._extraer_mes(texto_ocr),
            'ano': self._extraer_ano(texto_ocr),
            'nombre_institucion': self._extraer_nombre_institucion(texto_ocr),
            'codigo_dane_ie': self._extraer_codigo_dane_ie(texto_ocr),
            'tipo_complemento': self._extraer_tipo_complemento(texto_ocr),
            'sede_educativa': self._extraer_sede_educativa(texto_ocr)
        }

        logger.info(f"Encabezado extraído: Sede={encabezado['sede_educativa']}, Mes={encabezado['mes_atencion']}, Año={encabezado['ano']}")

        return encabezado

    def validar_encabezado(self, encabezado: Dict[str, Any], nombre_archivo: str) -> List[Dict[str, Any]]:
        """
        Valida la coherencia de la información del encabezado.

        Args:
            encabezado: Datos del encabezado extraídos
            nombre_archivo: Nombre del archivo para validación cruzada

        Returns:
            Lista de errores encontrados
        """
        errores = []

        # Validar campos obligatorios
        errores.extend(self._validar_campos_obligatorios(encabezado))

        # Validar formato de códigos DANE
        errores.extend(self._validar_codigos_dane(encabezado))

        # Validar mes y año
        errores.extend(self._validar_fecha(encabezado))

        # Validar coherencia con nombre de archivo
        errores.extend(self._validar_coherencia_archivo(encabezado, nombre_archivo))

        return errores

    def _extraer_departamento(self, texto_ocr: str) -> Optional[str]:
        """Extrae el nombre del departamento."""
        # Buscar patrón: DEPARTAMENTO: <nombre>
        patron = r'DEPARTAMENTO:\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+CÓDIGO DANE:|$)'
        match = re.search(patron, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if match:
            departamento = match.group(1).strip()
            return self._limpiar_valor(departamento)

        return None

    def _extraer_codigo_dane_depto(self, texto_ocr: str) -> Optional[str]:
        """Extrae el código DANE del departamento."""
        # Buscar patrón: CÓDIGO DANE: <número> (cerca de DEPARTAMENTO)
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            if 'DEPARTAMENTO:' in linea.upper():
                # Buscar CÓDIGO DANE en la misma línea o siguiente
                patron = r'CÓDIGO DANE:\s*(\d+)'
                match = re.search(patron, linea, re.IGNORECASE)

                if match:
                    return match.group(1).strip()

                # Buscar en línea siguiente
                if i + 1 < len(lineas):
                    match = re.search(patron, lineas[i + 1], re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

        return None

    def _extraer_municipio(self, texto_ocr: str) -> Optional[str]:
        """Extrae el nombre del municipio."""
        # Buscar patrón: MUNICIPIO: <nombre>
        patron = r'MUNICIPIO:\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+CÓDIGO DANE:|$)'
        match = re.search(patron, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if match:
            municipio = match.group(1).strip()
            return self._limpiar_valor(municipio)

        return None

    def _extraer_codigo_dane_mpio(self, texto_ocr: str) -> Optional[str]:
        """Extrae el código DANE del municipio."""
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            if 'MUNICIPIO:' in linea.upper():
                # Buscar CÓDIGO DANE después de MUNICIPIO
                patron = r'CÓDIGO DANE:\s*(\d+)'
                match = re.search(patron, linea, re.IGNORECASE)

                if match:
                    return match.group(1).strip()

                if i + 1 < len(lineas):
                    match = re.search(patron, lineas[i + 1], re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

        return None

    def _extraer_operador(self, texto_ocr: str) -> Optional[str]:
        """Extrae el nombre del operador."""
        patron = r'OPERADOR:\s*([A-Z0-9\s]+?)(?:\s+CONTRATO|$)'
        match = re.search(patron, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if match:
            operador = match.group(1).strip()
            return self._limpiar_valor(operador)

        return None

    def _extraer_contrato(self, texto_ocr: str) -> Optional[str]:
        """Extrae el número de contrato."""
        patron = r'CONTRATO\s*(?:No|N°|#)?:?\s*([A-Z0-9]+)'
        match = re.search(patron, texto_ocr, re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return None

    def _extraer_nombre_institucion(self, texto_ocr: str) -> Optional[str]:
        """Extrae el nombre de la institución educativa."""
        patron = r'NOMBRE\s+DE\s+INSTITUCIÓN\s+O\s+CENTRO\s+EDUCATIVO:\s*([A-Z0-9\sÁÉÍÓÚÑ]+?)(?:\s+CÓDIGO DANE|\n)'
        match = re.search(patron, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if match:
            nombre = match.group(1).strip()
            return self._limpiar_valor(nombre)

        return None

    def _extraer_codigo_dane_ie(self, texto_ocr: str) -> Optional[str]:
        """Extrae el código DANE de la institución educativa."""
        # Buscar el código DANE que aparece después del nombre de institución
        lineas = texto_ocr.split('\n')

        for i, linea in enumerate(lineas):
            if 'NOMBRE DE INSTITUCIÓN' in linea.upper() or 'CENTRO EDUCATIVO' in linea.upper():
                # Buscar código en las siguientes 3 líneas
                for j in range(i, min(i + 3, len(lineas))):
                    # Buscar patrón de código DANE IE (12 dígitos típicamente)
                    patron = r'CÓDIGO\s+DANE.*?:?\s*(\d{12,})'
                    match = re.search(patron, lineas[j], re.IGNORECASE)

                    if match:
                        return match.group(1).strip()

        return None

    def _extraer_sede_educativa(self, texto_ocr: str) -> Optional[str]:
        """
        Extrae el nombre de la sede educativa.
        Esta es la información más importante para identificar el documento.
        """
        # Patrón 1: Buscar directamente después de "NOMBRE DE INSTITUCIÓN"
        patron1 = r'NOMBRE\s+DE\s+INSTITUCIÓN.*?:\s*([A-Z0-9\s]+?)(?:\s*\d{12}|\n)'
        match = re.search(patron1, texto_ocr, re.IGNORECASE | re.MULTILINE)

        if match:
            sede = match.group(1).strip()
            sede_limpia = self._limpiar_valor(sede)

            # Validar que no sea el código DANE
            if sede_limpia and not self._es_codigo_dane(sede_limpia):
                return sede_limpia

        # Patrón 2: Buscar en líneas cercanas a "INSTITUCIÓN"
        lineas = texto_ocr.split('\n')
        for i, linea in enumerate(lineas):
            if 'NOMBRE DE INSTITUCIÓN' in linea.upper() or 'CENTRO EDUCATIVO' in linea.upper():
                # Analizar la misma línea
                partes = linea.split(':')
                if len(partes) > 1:
                    posible_sede = partes[1].strip()
                    posible_sede_limpia = self._limpiar_valor(posible_sede)

                    if posible_sede_limpia and not self._es_codigo_dane(posible_sede_limpia):
                        return posible_sede_limpia

        return None

    def _extraer_mes(self, texto_ocr: str) -> Optional[str]:
        """Extrae el mes de atención."""
        # Patrón 1: Con Ñ correcta
        patron1 = r'MES\s+DE\s+ATENCIÓN:\s*([A-ZÁÉÍÓÚÑ]+)'
        match = re.search(patron1, texto_ocr, re.IGNORECASE)

        if match:
            mes = match.group(1).strip().upper()
            if mes in self.meses_validos:
                return mes
            # Buscar coincidencia parcial
            for mes_valido in self.meses_validos:
                if mes_valido.startswith(mes[:3]):
                    return mes_valido

        # Patrón 2: Sin Ñ (OCR puede leer "ATENCION" sin Ñ)
        patron2 = r'MES\s+DE\s+ATEN[CÇ]I[OÓ]N:\s*([A-ZÁÉÍÓÚÑ]+)'
        match = re.search(patron2, texto_ocr, re.IGNORECASE)

        if match:
            mes = match.group(1).strip().upper()
            if mes in self.meses_validos:
                return mes
            for mes_valido in self.meses_validos:
                if mes_valido.startswith(mes[:3]):
                    return mes_valido

        # Patrón 3: Buscar solo "MES:" seguido del mes
        patron3 = r'MES[:\s]+([A-ZÁÉÍÓÚÑ]+)'
        match = re.search(patron3, texto_ocr, re.IGNORECASE)

        if match:
            mes = match.group(1).strip().upper()
            # Solo aceptar si es un mes válido
            if mes in self.meses_validos:
                return mes

        # Patrón 4: Buscar directamente por nombres de meses en el texto
        # (como último recurso)
        texto_upper = texto_ocr.upper()
        for mes_valido in self.meses_validos:
            # Buscar el mes con palabra completa cerca de "MES" o "ATENCIÓN"
            patron_mes = rf'(?:MES|ATEN[CÇ]I[OÓ]N)[^\n]*\b{mes_valido}\b'
            if re.search(patron_mes, texto_upper):
                return mes_valido

        return None

    def _extraer_ano(self, texto_ocr: str) -> Optional[int]:
        """Extrae el año de atención."""
        patron = r'AÑO:\s*(\d{4})'
        match = re.search(patron, texto_ocr, re.IGNORECASE)

        if match:
            ano = int(match.group(1))

            # Validar rango razonable (2020-2030)
            if 2020 <= ano <= 2030:
                return ano

        return None

    def _extraer_tipo_complemento(self, texto_ocr: str) -> Optional[str]:
        """Extrae el tipo de complemento alimenticio."""
        patron = r'TIPO\s+COMPLEMENTO\s+ALIMENTICIO:\s*([A-Z]+)'
        match = re.search(patron, texto_ocr, re.IGNORECASE)

        if match:
            tipo = match.group(1).strip().upper()

            # Validar que sea un tipo válido
            for tipo_valido in self.tipos_complemento:
                if tipo_valido in tipo or tipo in tipo_valido:
                    return tipo_valido

        return None

    def _limpiar_valor(self, valor: str) -> str:
        """Limpia un valor extraído por OCR."""
        if not valor:
            return ''

        # Eliminar espacios múltiples
        valor = re.sub(r'\s+', ' ', valor)

        # Eliminar caracteres especiales comunes de OCR
        valor = valor.replace('|', '').replace('_', '').replace('~', '')

        # Eliminar "CÓDIGO DANE" si aparece
        if 'CÓDIGO DANE' in valor.upper():
            return ''

        # Si es solo números de 8+ dígitos, probablemente es un código DANE
        if re.match(r'^\d{8,}$', valor.strip()):
            return ''

        return valor.strip()

    def _es_codigo_dane(self, valor: str) -> bool:
        """Verifica si un valor parece ser un código DANE."""
        if not valor:
            return False

        # Código DANE típicamente tiene 8-12 dígitos
        return bool(re.match(r'^\d{8,12}$', valor.strip()))

    def _validar_campos_obligatorios(self, encabezado: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida que los campos obligatorios estén presentes."""
        errores = []

        campos_obligatorios = {
            'departamento': 'Departamento',
            'municipio': 'Municipio',
            'sede_educativa': 'Sede Educativa',
            'mes_atencion': 'Mes de Atención',
            'ano': 'Año',
            'tipo_complemento': 'Tipo de Complemento'
        }

        for campo, nombre in campos_obligatorios.items():
            if not encabezado.get(campo):
                errores.append({
                    'tipo': 'campo_encabezado_faltante',
                    'descripcion': f'{nombre} no se pudo extraer del encabezado',
                    'pagina': 1,
                    'severidad': 'critico',
                    'campo': campo
                })

        return errores

    def _validar_codigos_dane(self, encabezado: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida el formato de los códigos DANE."""
        errores = []

        # Validar código DANE departamento (2 dígitos)
        codigo_depto = encabezado.get('codigo_dane_departamento')
        if codigo_depto and not re.match(r'^\d{2}$', codigo_depto):
            errores.append({
                'tipo': 'codigo_dane_invalido',
                'descripcion': f'Código DANE departamento inválido: {codigo_depto}',
                'pagina': 1,
                'severidad': 'advertencia',
                'campo': 'codigo_dane_departamento'
            })

        # Validar código DANE municipio (3 dígitos)
        codigo_mpio = encabezado.get('codigo_dane_municipio')
        if codigo_mpio and not re.match(r'^\d{3}$', codigo_mpio):
            errores.append({
                'tipo': 'codigo_dane_invalido',
                'descripcion': f'Código DANE municipio inválido: {codigo_mpio}',
                'pagina': 1,
                'severidad': 'advertencia',
                'campo': 'codigo_dane_municipio'
            })

        # Validar código DANE institución (12 dígitos)
        codigo_ie = encabezado.get('codigo_dane_ie')
        if codigo_ie and not re.match(r'^\d{12}$', codigo_ie):
            errores.append({
                'tipo': 'codigo_dane_invalido',
                'descripcion': f'Código DANE institución inválido: {codigo_ie}',
                'pagina': 1,
                'severidad': 'advertencia',
                'campo': 'codigo_dane_ie'
            })

        return errores

    def _validar_fecha(self, encabezado: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida mes y año."""
        errores = []

        mes = encabezado.get('mes_atencion')
        if mes and mes not in self.meses_validos:
            errores.append({
                'tipo': 'mes_invalido',
                'descripcion': f'Mes de atención inválido: {mes}',
                'pagina': 1,
                'severidad': 'critico',
                'campo': 'mes_atencion'
            })

        ano = encabezado.get('ano')
        if ano and (ano < 2020 or ano > 2030):
            errores.append({
                'tipo': 'ano_invalido',
                'descripcion': f'Año fuera de rango: {ano}',
                'pagina': 1,
                'severidad': 'advertencia',
                'campo': 'ano'
            })

        return errores

    def _validar_coherencia_archivo(self, encabezado: Dict[str, Any], nombre_archivo: str) -> List[Dict[str, Any]]:
        """Valida coherencia entre encabezado y nombre de archivo."""
        errores = []

        # Extraer información del nombre de archivo
        # Ejemplo: "Asistencia_F2_ANTONIA_SANTOS_ALMUERZO_OCTUBRE_2025.pdf"

        mes_encabezado = encabezado.get('mes_atencion') or ''
        ano_encabezado = encabezado.get('ano')

        # Convertir a mayúsculas solo si no está vacío
        if mes_encabezado and isinstance(mes_encabezado, str):
            mes_encabezado = mes_encabezado.upper()
            if mes_encabezado not in nombre_archivo.upper():
                errores.append({
                    'tipo': 'incoherencia_mes',
                    'descripcion': f'El mes en encabezado ({mes_encabezado}) no coincide con nombre de archivo',
                    'pagina': 1,
                    'severidad': 'advertencia',
                    'campo': 'mes_atencion'
                })

        if ano_encabezado and str(ano_encabezado) not in nombre_archivo:
            errores.append({
                'tipo': 'incoherencia_ano',
                'descripcion': f'El año en encabezado ({ano_encabezado}) no coincide con nombre de archivo',
                'pagina': 1,
                'severidad': 'advertencia',
                'campo': 'ano'
            })

        return errores

    def obtener_contexto_procesamiento(self, encabezado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene información de contexto para otras validaciones.

        Returns:
            Dict con contexto útil para validaciones
        """
        return {
            'sede': encabezado.get('sede_educativa'),
            'mes': encabezado.get('mes_atencion'),
            'ano': encabezado.get('ano'),
            'tipo_complemento': encabezado.get('tipo_complemento'),
            'departamento': encabezado.get('departamento'),
            'municipio': encabezado.get('municipio')
        }
