"""
Generador de análisis nutricional en formato Excel.

Este módulo genera archivos Excel con análisis nutricional completo
siguiendo el formato estándar del ICBF.
"""

import io
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from django.conf import settings

from .models import (
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaAlimentos2018Icbf,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel
)
from .services.analisis_service import AnalisisNutricionalService

# =====================================================================
# CONSTANTES DE CONFIGURACIÓN
# =====================================================================

@dataclass(frozen=True)
class ExcelLayout:
    """Constantes de diseño del Excel"""
    # Filas
    TITLE_ROW = 1
    ADMIN_START_ROW = 2
    ADMIN_END_ROW = 8
    HEADER_START_ROW = 8
    HEADER_END_ROW = 11
    DATA_START_ROW = 12

    # Columnas
    COL_COMPONENTE = 1
    COL_GRUPO = 2
    COL_PREPARACION = 3
    COL_INGREDIENTE = 4
    COL_CODIGO = 5
    COL_PESO_BRUTO = 6
    COL_PESO_NETO = 7
    COL_CALORIAS = 8
    COL_PROTEINA = 9
    COL_GRASA = 10
    COL_CHO = 11
    COL_CALCIO = 12
    COL_HIERRO = 13
    COL_SODIO = 14

    # Rangos
    TITLE_RANGE = 'A1:N1'
    TOTAL_LABEL_COLS = 3  # A:C


@dataclass(frozen=True)
class ExcelStyles:
    """Estilos predefinidos para el Excel"""
    HEADER_COLOR = "B8D4F0"
    TOTAL_COLOR = "E6F3FF"

    @staticmethod
    def get_header_fill() -> PatternFill:
        return PatternFill(
            start_color=ExcelStyles.HEADER_COLOR,
            end_color=ExcelStyles.HEADER_COLOR,
            fill_type="solid"
        )

    @staticmethod
    def get_total_fill() -> PatternFill:
        return PatternFill(
            start_color=ExcelStyles.TOTAL_COLOR,
            end_color=ExcelStyles.TOTAL_COLOR,
            fill_type="solid"
        )

    @staticmethod
    def get_border() -> Border:
        side = Side(style='thin')
        return Border(left=side, right=side, top=side, bottom=side)


@dataclass(frozen=True)
class ColumnWidths:
    """Anchos de columnas"""
    WIDTHS = {
        'A': 25, 'B': 15, 'C': 15, 'D': 20, 'E': 25, 'F': 30,
        'G': 15, 'H': 12, 'I': 12, 'J': 12, 'K': 10, 'L': 10,
        'M': 10, 'N': 10, 'O': 12, 'P': 12
    }


NUTRITIONAL_HEADERS = [
    "COMPONENTE",
    "GRUPO DE ALIMENTOS",
    "NOMBRE DE LA PREPARACION",
    "NOMBRE DEL ALIMENTO (Ingredientes)",
    "CÓDIGO DEL ALIMENTO",
    "PESO BRUTO (g)",
    "PESO NETO (g)",
    "CALORÍAS (Kcal)",
    "PROTEÍNA (g)",
    "GRASA (g)",
    "CHO (g)",
    "CALCIO (mg)",
    "HIERRO (mg)",
    "SODIO (mg)"
]

NUTRIENT_KEYS = [
    'calorias_kcal', 'proteina_g', 'grasa_g', 'cho_g',
    'calcio_mg', 'hierro_mg', 'sodio_mg'
]


# =====================================================================
# CLASE PRINCIPAL
# =====================================================================

class NutritionalAnalysisExcelGenerator:
    """
    Generador de análisis nutricional en Excel.

    Genera archivos Excel con el análisis nutricional completo de menús,
    siguiendo el formato estándar del ICBF.
    """

    def __init__(self):
        self.layout = ExcelLayout()
        self.styles = ExcelStyles()
        self.header_fill = self.styles.get_header_fill()
        self.total_fill = self.styles.get_total_fill()
        self.border = self.styles.get_border()

    # =================================================================
    # MÉTODOS PÚBLICOS - GENERACIÓN DE EXCEL
    # =================================================================

    def generate_from_analysis_service(
        self,
        menu_id: int,
        nivel_escolar_id: Optional[str] = None
    ) -> io.BytesIO:
        """
        Genera Excel usando el servicio de análisis nutricional.

        Este es el método principal y recomendado para generar Excel.

        Args:
            menu_id: ID del menú
            nivel_escolar_id: ID del nivel escolar (opcional)

        Returns:
            BytesIO con el archivo Excel
        """
        try:
            # Obtener análisis completo
            analisis_data = AnalisisNutricionalService.obtener_analisis_completo(menu_id)

            if not analisis_data.get('success'):
                raise ValueError("No se pudo obtener el análisis del menú")

            # Crear workbook
            wb = self._create_workbook()
            ws = wb.active

            # Poblar secciones
            self._populate_title(ws)
            self._populate_administrative_section(ws, analisis_data)

            # Obtener datos del nivel específico
            nivel_data = self._get_nivel_data(analisis_data, nivel_escolar_id)
            if not nivel_data:
                raise ValueError("No se encontró información del nivel escolar")

            # Poblar encabezados
            self._populate_headers(ws)

            # Poblar ingredientes
            current_row = self._populate_ingredients_from_analysis(ws, nivel_data)

            # Agregar cálculos
            self._add_calculations_section(ws, current_row, nivel_data)

            # Firmas
            self._add_signatures(ws, current_row + 10)

            # Formateo final
            self._apply_formatting(ws)

            # Combinar celdas AL FINAL (después de todo el formateo)
            self._merge_cells(ws)

            return self._save_to_stream(wb)

        except Exception as e:
            return self._generate_error_excel(f"Error generando Excel: {str(e)}")

    def generate_from_database(
        self,
        menu_id: int,
        nivel_escolar_id: Optional[str] = None
    ) -> io.BytesIO:
        """
        Genera Excel consultando directamente la base de datos.

        Método alternativo que consulta directamente las tablas.
        Útil cuando el servicio de análisis no está disponible.

        Args:
            menu_id: ID del menú
            nivel_escolar_id: ID del nivel escolar (opcional)

        Returns:
            BytesIO con el archivo Excel
        """
        try:
            # Obtener menú
            menu = TablaMenus.objects.select_related('id_contrato').get(id_menu=menu_id)

            # Crear workbook
            wb = self._create_workbook()
            ws = wb.active

            # Poblar título
            self._populate_title(ws)

            # Poblar información administrativa básica
            self._populate_admin_from_menu(ws, menu)

            # Poblar encabezados
            self._populate_headers(ws)

            # Obtener preparaciones
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu=menu
            ).prefetch_related(
                'ingredientes__id_ingrediente_siesa',
                'id_componente__id_grupo_alimentos'
            )

            # Poblar ingredientes
            current_row = self._populate_ingredients_from_database(
                ws, preparaciones, menu_id
            )

            # Agregar cálculos con fórmulas
            self._add_formula_calculations(ws, current_row)

            # Firmas
            self._add_signatures(ws, current_row + 10)

            # Formateo
            self._apply_formatting(ws)

            # Combinar celdas AL FINAL (después de todo el formateo)
            self._merge_cells(ws)

            return self._save_to_stream(wb)

        except TablaMenus.DoesNotExist:
            return self._generate_error_excel("Menú no encontrado")
        except Exception as e:
            return self._generate_error_excel(f"Error: {str(e)}")

    # =================================================================
    # MÉTODOS PRIVADOS - CREACIÓN Y CONFIGURACIÓN
    # =================================================================

    def _create_workbook(self) -> Workbook:
        """Crea un nuevo workbook (siempre desde cero para evitar problemas con plantillas)"""
        # Siempre crear desde cero para evitar conflictos con celdas combinadas
        wb = Workbook()
        wb.active.title = "Análisis Nutricional"
        return wb

    # =================================================================
    # MÉTODOS PRIVADOS - POBLACIÓN DE SECCIONES
    # =================================================================

    def _populate_title(self, ws: Worksheet) -> None:
        """Poblar título principal"""
        # Asignar valor sin combinar celdas (temporalmente deshabilitado)
        title_cell = ws['A1']
        title_cell.value = "ANÁLISIS NUTRICIONAL"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal='center', vertical='center')

        # MERGE DESHABILITADO para debug
        # ws.merge_cells(self.layout.TITLE_RANGE)

    def _populate_administrative_section(
        self,
        ws: Worksheet,
        analisis_data: Dict
    ) -> None:
        """Poblar información administrativa del menú"""
        menu_info = analisis_data.get('menu', {})

        # Obtener nivel escolar
        nivel_escolar = self._extract_nivel_escolar(analisis_data)

        # Datos administrativos
        admin_data = [
            ("ENTIDAD TERRITORIAL:", menu_info.get('programa', 'N/A')),
            ("MINUTA CON ENFOQUE ETNICO:", "No"),
            ("GRUPO ÉTNICO", "Sin Pertenencia Étnica"),
            ("MODALIDAD DE ATENCIÓN", menu_info.get('modalidad', 'N/A')),
            ("TIPO DE COMPLEMENTO", "Almuerzo"),
            ("NIVEL", nivel_escolar),
            ("MENÚ No.", menu_info.get('nombre', 'N/A'))
        ]

        self._populate_admin_rows(ws, admin_data)

    def _populate_admin_from_menu(self, ws: Worksheet, menu: TablaMenus) -> None:
        """Poblar información administrativa desde modelo de menú"""
        admin_data = [
            ("ENTIDAD TERRITORIAL:", menu.id_contrato.programa if menu.id_contrato else 'N/A'),
            ("MINUTA CON ENFOQUE ETNICO:", "No"),
            ("GRUPO ÉTNICO", "Sin Pertenencia Étnica"),
            ("MODALIDAD DE ATENCIÓN", menu.id_modalidad.modalidad if menu.id_modalidad else 'N/A'),
            ("TIPO DE COMPLEMENTO", "Almuerzo"),
            ("NIVEL", "N/A"),  # Se determina por análisis
            ("MENÚ No.", menu.menu)
        ]

        self._populate_admin_rows(ws, admin_data)

    def _populate_admin_rows(
        self,
        ws: Worksheet,
        admin_data: List[Tuple[str, str]]
    ) -> None:
        """Poblar filas administrativas sin combinar celdas (temporalmente)"""
        for row, (label, value) in enumerate(admin_data, start=self.layout.ADMIN_START_ROW):
            # Asignar valor y estilos sin combinar
            label_cell = ws[f'A{row}']
            label_cell.value = label
            label_cell.font = Font(bold=True)
            label_cell.alignment = Alignment(horizontal='right', vertical='center')

            # Value (columnas D)
            value_cell = ws[f'D{row}']
            value_cell.value = value
            value_cell.alignment = Alignment(horizontal='left', vertical='center')

            # MERGE DESHABILITADO para debug
            # ws.merge_cells(f'A{row}:C{row}')

    def _populate_headers(self, ws: Worksheet) -> None:
        """Poblar encabezados de columnas"""
        # Crear encabezados sin filas vacías
        for col, header in enumerate(NUTRITIONAL_HEADERS, start=1):
            cell = ws.cell(row=self.layout.HEADER_START_ROW, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = self.header_fill
            cell.alignment = Alignment(
                horizontal='center',
                vertical='center',
                wrap_text=True
            )
            cell.border = self.border

    def _populate_ingredients_from_analysis(
        self,
        ws: Worksheet,
        nivel_data: Dict
    ) -> int:
        """
        Poblar ingredientes desde datos de análisis.

        Returns:
            Última fila usada
        """
        current_row = self.layout.DATA_START_ROW

        for preparacion in nivel_data.get('preparaciones', []):
            componente = preparacion.get('componente', 'SIN COMPONENTE')
            grupo_alimentos = preparacion.get('grupo_alimentos', 'SIN GRUPO')

            for ingrediente in preparacion.get('ingredientes', []):
                if not ingrediente.get('alimento_encontrado'):
                    continue

                # Datos básicos
                ws.cell(current_row, self.layout.COL_COMPONENTE).value = componente
                ws.cell(current_row, self.layout.COL_GRUPO).value = grupo_alimentos
                ws.cell(current_row, self.layout.COL_PREPARACION).value = \
                    preparacion.get('nombre', '')
                ws.cell(current_row, self.layout.COL_INGREDIENTE).value = \
                    ingrediente.get('nombre', '')
                ws.cell(current_row, self.layout.COL_CODIGO).value = \
                    ingrediente.get('codigo_icbf', '')

                # Pesos
                ws.cell(current_row, self.layout.COL_PESO_BRUTO).value = \
                    ingrediente.get('peso_bruto_base', 0)
                ws.cell(current_row, self.layout.COL_PESO_NETO).value = \
                    ingrediente.get('peso_neto_base', 0)

                # Valores nutricionales
                valores = ingrediente.get('valores_por_100g', {})
                factor = self._to_float(ingrediente.get('peso_neto_base', 100)) / 100.0

                ws.cell(current_row, self.layout.COL_CALORIAS).value = \
                    self._to_float(valores.get('calorias_kcal', 0)) * factor
                ws.cell(current_row, self.layout.COL_PROTEINA).value = \
                    self._to_float(valores.get('proteina_g', 0)) * factor
                ws.cell(current_row, self.layout.COL_GRASA).value = \
                    self._to_float(valores.get('grasa_g', 0)) * factor
                ws.cell(current_row, self.layout.COL_CHO).value = \
                    self._to_float(valores.get('cho_g', 0)) * factor
                ws.cell(current_row, self.layout.COL_CALCIO).value = \
                    self._to_float(valores.get('calcio_mg', 0)) * factor
                ws.cell(current_row, self.layout.COL_HIERRO).value = \
                    self._to_float(valores.get('hierro_mg', 0)) * factor
                ws.cell(current_row, self.layout.COL_SODIO).value = \
                    self._to_float(valores.get('sodio_mg', 0)) * factor

                current_row += 1

        return current_row - 1  # Última fila con datos

    def _populate_ingredients_from_database(
        self,
        ws: Worksheet,
        preparaciones,
        menu_id: int
    ) -> int:
        """
        Poblar ingredientes consultando la base de datos.

        Returns:
            Última fila usada
        """
        current_row = self.layout.DATA_START_ROW

        for preparacion in preparaciones:
            componente = preparacion.id_componente.componente \
                if preparacion.id_componente else "SIN COMPONENTE"
            grupo_alimentos = (
                preparacion.id_componente.id_grupo_alimentos.grupo_alimentos
                if preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos
                else "SIN GRUPO"
            )

            ingredientes = TablaPreparacionIngredientes.objects.filter(
                id_preparacion=preparacion
            ).select_related('id_ingrediente_siesa')

            for ing_prep in ingredientes:
                ingrediente = ing_prep.id_ingrediente_siesa

                # Buscar información nutricional ICBF
                alimento_icbf = self._find_alimento_icbf(ingrediente)

                if not alimento_icbf:
                    continue

                # Obtener pesos del análisis guardado si existe
                peso_neto, peso_bruto = self._get_saved_weights(
                    menu_id, preparacion, ingrediente
                )

                # Calcular valores nutricionales
                factor = self._to_float(peso_neto) / 100.0
                valores_100g = self._extract_nutritional_values(alimento_icbf)

                # Poblar fila
                self._populate_ingredient_row(
                    ws, current_row, componente, grupo_alimentos,
                    preparacion.preparacion, ingrediente.nombre_ingrediente,
                    alimento_icbf.codigo, peso_bruto, peso_neto,
                    valores_100g, factor
                )

                current_row += 1

        return current_row - 1

    def _populate_ingredient_row(
        self,
        ws: Worksheet,
        row: int,
        componente: str,
        grupo: str,
        preparacion: str,
        ingrediente: str,
        codigo: str,
        peso_bruto: float,
        peso_neto: float,
        valores_100g: Dict[str, float],
        factor: float
    ) -> None:
        """Poblar una fila completa de ingrediente"""
        ws.cell(row, self.layout.COL_COMPONENTE).value = componente
        ws.cell(row, self.layout.COL_GRUPO).value = grupo
        ws.cell(row, self.layout.COL_PREPARACION).value = preparacion
        ws.cell(row, self.layout.COL_INGREDIENTE).value = ingrediente
        ws.cell(row, self.layout.COL_CODIGO).value = codigo
        ws.cell(row, self.layout.COL_PESO_BRUTO).value = round(peso_bruto, 1)
        ws.cell(row, self.layout.COL_PESO_NETO).value = round(peso_neto, 1)

        # Valores nutricionales
        ws.cell(row, self.layout.COL_CALORIAS).value = \
            round(valores_100g['calorias_kcal'] * factor, 1)
        ws.cell(row, self.layout.COL_PROTEINA).value = \
            round(valores_100g['proteina_g'] * factor, 1)
        ws.cell(row, self.layout.COL_GRASA).value = \
            round(valores_100g['grasa_g'] * factor, 1)
        ws.cell(row, self.layout.COL_CHO).value = \
            round(valores_100g['cho_g'] * factor, 1)
        ws.cell(row, self.layout.COL_CALCIO).value = \
            round(valores_100g['calcio_mg'] * factor, 1)
        ws.cell(row, self.layout.COL_HIERRO).value = \
            round(valores_100g['hierro_mg'] * factor, 1)
        ws.cell(row, self.layout.COL_SODIO).value = \
            round(valores_100g['sodio_mg'] * factor, 1)

    def _add_calculations_section(
        self,
        ws: Worksheet,
        last_data_row: int,
        nivel_data: Dict
    ) -> None:
        """Agregar sección de totales, recomendaciones y adecuación"""
        total_row = last_data_row + 2

        # Totales
        self._add_totals_row(ws, total_row, nivel_data)

        # Recomendaciones
        req_row = total_row + 2
        self._add_recommendations_row(ws, req_row, nivel_data)

        # % Adecuación (calculado automáticamente)
        pct_row = req_row + 1
        self._add_adequacy_row(ws, pct_row, total_row, req_row)

    def _add_totals_row(
        self,
        ws: Worksheet,
        row: int,
        nivel_data: Dict
    ) -> None:
        """Agregar fila de totales"""
        ws.cell(row, 1).value = "TOTAL MENÚ"
        ws.cell(row, 1).font = Font(bold=True)
        ws.cell(row, 1).fill = self.total_fill

        # Valores totales
        totales = nivel_data.get('totales', {})
        for i, key in enumerate(NUTRIENT_KEYS, start=self.layout.COL_CALORIAS):
            cell = ws.cell(row, i)
            cell.value = totales.get(key, 0)
            cell.fill = self.total_fill
            cell.border = self.border

    def _add_recommendations_row(
        self,
        ws: Worksheet,
        row: int,
        nivel_data: Dict
    ) -> None:
        """Agregar fila de recomendaciones"""
        ws.cell(row, 1).value = "RECOMENDACIÓN"
        ws.cell(row, 1).font = Font(bold=True)
        ws.cell(row, 1).fill = self.header_fill

        # Valores recomendados
        requerimientos = nivel_data.get('requerimientos', {})
        for i, key in enumerate(NUTRIENT_KEYS, start=self.layout.COL_CALORIAS):
            cell = ws.cell(row, i)
            # Valores por defecto como fallback
            default_values = [1300, 45.5, 43.3, 182, 700, 5.6, 1133]
            cell.value = requerimientos.get(key, default_values[i - self.layout.COL_CALORIAS])
            cell.fill = self.header_fill
            cell.border = self.border

    def _add_adequacy_row(
        self,
        ws: Worksheet,
        row: int,
        total_row: int,
        req_row: int
    ) -> None:
        """Agregar fila de % adecuación con fórmulas"""
        ws.cell(row, 1).value = "% ADECUACIÓN"
        ws.cell(row, 1).font = Font(bold=True)

        for col in range(self.layout.COL_CALORIAS, self.layout.COL_SODIO + 1):
            col_letter = get_column_letter(col)
            formula = f"=IF({col_letter}{req_row}=0,0,{col_letter}{total_row}/{col_letter}{req_row}*100)"
            cell = ws.cell(row, col)
            cell.value = formula
            cell.border = self.border
            cell.number_format = '0.00"%"'

    def _add_formula_calculations(
        self,
        ws: Worksheet,
        last_data_row: int
    ) -> None:
        """Agregar cálculos con fórmulas de Excel"""
        total_row = last_data_row + 2

        # Totales con fórmulas SUM
        ws.cell(total_row, 1).value = "TOTAL MENÚ"
        ws.cell(total_row, 1).font = Font(bold=True)
        ws.cell(total_row, 1).fill = self.total_fill

        for col in range(self.layout.COL_CALORIAS, self.layout.COL_SODIO + 1):
            col_letter = get_column_letter(col)
            formula = f"=SUM({col_letter}{self.layout.DATA_START_ROW}:{col_letter}{last_data_row})"
            cell = ws.cell(total_row, col)
            cell.value = formula
            cell.fill = self.total_fill
            cell.border = self.border

        # Recomendaciones (valores hardcoded como placeholder)
        req_row = total_row + 2
        ws.cell(req_row, 1).value = "RECOMENDACIÓN"
        ws.cell(req_row, 1).font = Font(bold=True)
        ws.cell(req_row, 1).fill = self.header_fill

        default_recommendations = [1300, 45.5, 43.3, 182, 700, 5.6, 1133]
        for i, valor in enumerate(default_recommendations, start=self.layout.COL_CALORIAS):
            cell = ws.cell(req_row, i)
            cell.value = valor
            cell.fill = self.header_fill
            cell.border = self.border

        # % Adecuación
        self._add_adequacy_row(ws, req_row + 1, total_row, req_row)

    def _add_signatures(self, ws: Worksheet, start_row: int) -> None:
        """Agregar sección de firmas"""
        row = start_row

        # Nutricionista que elabora
        ws.cell(row=row, column=1).value = "NOMBRE NUTRICIONISTA - DIETISTA QUE ELABORA EL ANÁLISIS"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=4).value = "SARA ISABEL DIAZ MARQUEZ"

        # Matrícula profesional
        row += 1
        ws.cell(row=row, column=1).value = "FIRMA"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=4).value = "MATRÍCULA PROFESIONAL"
        ws.cell(row=row, column=7).value = "1107089938"

        # Nutricionista que revisa
        row += 2
        ws.cell(row=row, column=1).value = "NOMBRE NUTRICIONISTA - DIETISTA QUE REVISA Y APRUEBA EL ANÁLISIS POR PARTE DE LA SEM"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=4).value = "GABRIELA GIRALDO MARTINEZ"

        # Matrícula profesional (revisa)
        row += 1
        ws.cell(row=row, column=1).value = "FIRMA"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=4).value = "MATRÍCULA PROFESIONAL"
        ws.cell(row=row, column=7).value = "1005964870"

    def _apply_formatting(self, ws: Worksheet) -> None:
        """Aplicar formateo profesional"""
        # Ajustar ancho de columnas solamente
        for col, width in ColumnWidths.WIDTHS.items():
            ws.column_dimensions[col].width = width

        # Bordes y alineación deshabilitados temporalmente para debug
        # TODO: Re-habilitar cuando se resuelva el problema de MergedCell

    def _merge_cells(self, ws: Worksheet) -> None:
        """
        Combinar celdas necesarias.

        Este método se ejecuta AL FINAL del proceso de generación,
        después de que todos los valores y estilos han sido asignados.
        Esto evita el error 'MergedCell' object attribute 'value' is read-only.
        """
        # Combinar celda del título (A1:N1)
        ws.merge_cells(self.layout.TITLE_RANGE)

        # Combinar celdas de etiquetas administrativas (A:C para cada fila)
        # ENTIDAD TERRITORIAL (fila 2)
        ws.merge_cells('A2:C2')

        # MINUTA CON ENFOQUE ETNICO (fila 3)
        ws.merge_cells('A3:C3')

        # GRUPO ÉTNICO (fila 4)
        ws.merge_cells('A4:C4')

        # MODALIDAD DE ATENCIÓN (fila 5)
        ws.merge_cells('A5:C5')

        # TIPO DE COMPLEMENTO (fila 6)
        ws.merge_cells('A6:C6')

        # NIVEL (fila 7)
        ws.merge_cells('A7:C7')

        # MENÚ No. (fila 8) - SIN COMBINAR

    # =================================================================
    # MÉTODOS AUXILIARES
    # =================================================================

    def _get_nivel_data(
        self,
        analisis_data: Dict,
        nivel_escolar_id: Optional[str]
    ) -> Optional[Dict]:
        """Obtener datos del nivel escolar"""
        analisis_por_nivel = analisis_data.get('analisis_por_nivel', [])

        if not analisis_por_nivel:
            return None

        # Si se especifica un nivel, buscarlo
        if nivel_escolar_id:
            for nivel_data in analisis_por_nivel:
                nivel_info = nivel_data.get('nivel_escolar', {})
                if str(nivel_info.get('id')) == str(nivel_escolar_id):
                    return nivel_data

        # Si no, buscar el nivel del programa actual
        for nivel_data in analisis_por_nivel:
            if nivel_data.get('es_programa_actual'):
                return nivel_data

        # Fallback: primer nivel disponible
        return analisis_por_nivel[0] if analisis_por_nivel else None

    def _extract_nivel_escolar(self, analisis_data: Dict) -> str:
        """Extraer nombre del nivel escolar"""
        analisis_por_nivel = analisis_data.get('analisis_por_nivel', [])

        if not analisis_por_nivel:
            return "N/A"

        # Buscar nivel del programa actual
        for nivel_data in analisis_por_nivel:
            if nivel_data.get('es_programa_actual'):
                return nivel_data.get('nivel_escolar', {}).get('nombre', 'N/A')

        # Fallback: primer nivel
        return analisis_por_nivel[0].get('nivel_escolar', {}).get('nombre', 'N/A')

    def _find_alimento_icbf(
        self,
        ingrediente_siesa: TablaIngredientesSiesa
    ) -> Optional[TablaAlimentos2018Icbf]:
        """Buscar información nutricional del ICBF"""
        # Buscar por código exacto
        alimento = TablaAlimentos2018Icbf.objects.filter(
            codigo=ingrediente_siesa.id_ingrediente_siesa
        ).first()

        if not alimento:
            # Buscar por nombre similar
            alimento = TablaAlimentos2018Icbf.objects.filter(
                nombre_del_alimento__icontains=ingrediente_siesa.nombre_ingrediente[:50]
            ).first()

        return alimento

    def _get_saved_weights(
        self,
        menu_id: int,
        preparacion: TablaPreparaciones,
        ingrediente: TablaIngredientesSiesa
    ) -> Tuple[float, float]:
        """Obtener pesos guardados del análisis previo"""
        peso_neto = 100.0  # Default
        peso_bruto = 100.0  # Default

        # Buscar análisis guardado
        analisis_guardado = TablaAnalisisNutricionalMenu.objects.filter(
            id_menu_id=menu_id
        ).first()

        if analisis_guardado:
            ingrediente_guardado = TablaIngredientesPorNivel.objects.filter(
                id_analisis=analisis_guardado,
                id_preparacion=preparacion,
                id_ingrediente_siesa=ingrediente
            ).first()

            if ingrediente_guardado:
                peso_neto = float(ingrediente_guardado.peso_neto)
                peso_bruto = float(ingrediente_guardado.peso_bruto)

        return peso_neto, peso_bruto

    def _extract_nutritional_values(
        self,
        alimento_icbf: TablaAlimentos2018Icbf
    ) -> Dict[str, float]:
        """Extraer valores nutricionales del alimento ICBF"""
        return {
            'calorias_kcal': self._to_float(alimento_icbf.energia_kcal),
            'proteina_g': self._to_float(alimento_icbf.proteina_g),
            'grasa_g': self._to_float(alimento_icbf.lipidos_g),
            'cho_g': self._to_float(alimento_icbf.carbohidratos_totales_g),
            'calcio_mg': self._to_float(alimento_icbf.calcio_mg),
            'hierro_mg': self._to_float(alimento_icbf.hierro_mg),
            'sodio_mg': self._to_float(alimento_icbf.sodio_mg)
        }

    @staticmethod
    def _to_float(value) -> float:
        """Convertir valor a float de forma segura"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _save_to_stream(self, workbook: Workbook) -> io.BytesIO:
        """Guardar workbook en stream de bytes"""
        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return stream

    def _generate_error_excel(self, error_message: str) -> io.BytesIO:
        """Generar Excel con mensaje de error"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Error"

        # Asignar valor y estilos sin combinar
        ws['A1'] = f"Error: {error_message}"
        ws['A1'].font = Font(bold=True, color="FF0000")

        # MERGE DESHABILITADO para debug
        # ws.merge_cells('A1:N1')

        return self._save_to_stream(wb)


# =====================================================================
# FUNCIONES DE COMPATIBILIDAD
# =====================================================================

def generate_menu_excel(menu_id: int) -> io.BytesIO:
    """
    Genera análisis nutricional completo.

    Args:
        menu_id: ID del menú

    Returns:
        BytesIO con el archivo Excel
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id)


def generate_menu_excel_with_nivel(
    menu_id: int,
    nivel_escolar_id: str
) -> io.BytesIO:
    """
    Genera análisis nutricional para un nivel escolar específico.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar

    Returns:
        BytesIO con el archivo Excel
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)


def generate_menu_excel_from_database(menu_id: int) -> io.BytesIO:
    """
    Genera análisis nutricional consultando directamente la base de datos.

    Args:
        menu_id: ID del menú

    Returns:
        BytesIO con el archivo Excel
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_database(menu_id)


def generate_menu_excel_real_data(menu_id: int) -> io.BytesIO:
    """
    Genera análisis nutricional usando datos reales.

    Función de compatibilidad - usa el servicio de análisis.

    Args:
        menu_id: ID del menú

    Returns:
        BytesIO con el archivo Excel
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id)


def generate_advanced_nutritional_excel(
    menu_id: int,
    nivel_escolar_id: Optional[str] = None,
    use_saved_analysis: bool = True
) -> io.BytesIO:
    """
    Genera Excel nutricional avanzado.

    Función de compatibilidad - usa el servicio de análisis.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar (opcional)
        use_saved_analysis: Ignorado, siempre usa servicio de análisis

    Returns:
        BytesIO con el archivo Excel
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)


def generate_excel_from_service(
    menu_id: int,
    nivel_escolar_id: Optional[str] = None
) -> io.BytesIO:
    """
    Genera Excel usando el servicio de análisis nutricional.

    Función de compatibilidad.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar (opcional)

    Returns:
        BytesIO con el archivo Excel
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)
