"""
Utilidades de dibujo para reportes de análisis nutricional en Excel.

Este módulo contiene una clase base con lógica reutilizable para dibujar
las diferentes secciones de un reporte de análisis nutricional.
"""

import io
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from openpyxl.drawing.image import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

# =====================================================================
# CONSTANTES Y CLASES DE DATOS REUTILIZABLES
# =====================================================================

@dataclass(frozen=True)
class ExcelLayout:
    """Constantes de diseño del Excel"""
    # Filas
    TITLE_ROW = 1
    ADMIN_START_ROW = 2
    ADMIN_END_ROW = 8
    HEADER_START_ROW = 10
    HEADER_END_ROW = 10
    DATA_START_ROW = 11

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
    TITLE_RANGE = 'D1:N1'
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
# CLASE BASE PARA DIBUJAR REPORTES
# =====================================================================

class ExcelReportDrawer:
    """
    Clase base que contiene métodos reutilizables para dibujar un análisis
    nutricional en una hoja de cálculo de openpyxl.
    """

    def __init__(self):
        self.layout = ExcelLayout()
        self.styles = ExcelStyles()
        self.header_fill = self.styles.get_header_fill()
        self.total_fill = self.styles.get_total_fill()
        self.border = self.styles.get_border()

    def _insert_logo(self, ws: Worksheet, logo_path: str, start_cell: str = 'A1') -> None:
        """Inserta el logo del programa en la celda especificada."""
        if not logo_path:
            return

        try:
            img = Image(logo_path)
            img.height = 60
            img.width = 200
            ws.add_image(img, start_cell)
            ws.row_dimensions[int(start_cell[1:])].height = 50
        except FileNotFoundError:
            print(f"Warning: Logo file not found at {logo_path}")
            pass

    def _populate_title(self, ws: Worksheet, start_row: int) -> None:
        """Poblar título principal en una fila específica."""
        title_cell = ws[f'D{start_row}']
        title_cell.value = "ANÁLISIS NUTRICIONAL"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal='center', vertical='center')

    def _populate_administrative_section(self, ws: Worksheet, start_row: int, analisis_data: Dict) -> None:
        """Poblar información administrativa del menú."""
        menu_info = analisis_data.get('menu', {})
        nivel_escolar = self._extract_nivel_escolar(analisis_data)

        admin_data = [
            ("ENTIDAD TERRITORIAL:", menu_info.get('programa', 'N/A')),
            ("MINUTA CON ENFOQUE ETNICO:", "No"),
            ("GRUPO ÉTNICO", "Sin Pertenencia Étnica"),
            ("MODALIDAD DE ATENCIÓN", menu_info.get('modalidad', 'N/A')),
            ("TIPO DE COMPLEMENTO", "Almuerzo"),
            ("NIVEL", nivel_escolar),
            ("MENÚ No.", menu_info.get('nombre', 'N/A'))
        ]

        for i, (label, value) in enumerate(admin_data):
            row = start_row + i
            label_cell = ws[f'A{row}']
            label_cell.value = label
            label_cell.font = Font(bold=True)
            label_cell.alignment = Alignment(horizontal='right', vertical='center')

            value_cell = ws[f'D{row}']
            value_cell.value = value
            value_cell.alignment = Alignment(horizontal='left', vertical='center')

    def _populate_headers(self, ws: Worksheet, start_row: int) -> None:
        """Poblar encabezados de columnas."""
        for col, header in enumerate(NUTRITIONAL_HEADERS, start=1):
            cell = ws.cell(row=start_row, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = self.border

    def _populate_ingredients_from_analysis(self, ws: Worksheet, start_row: int, nivel_data: Dict) -> int:
        """Poblar ingredientes desde datos de análisis."""
        current_row = start_row
        center_align = Alignment(vertical='center', horizontal='center', wrap_text=True)

        for preparacion in nivel_data.get('preparaciones', []):
            start_row_for_prep = current_row
            ingredients_in_prep = [ing for ing in preparacion.get('ingredientes', []) if ing.get('alimento_encontrado')]
            num_ingredients = len(ingredients_in_prep)

            if num_ingredients == 0:
                continue

            ws.cell(row=start_row_for_prep, column=self.layout.COL_COMPONENTE).value = preparacion.get('componente', 'SIN COMPONENTE')
            ws.cell(row=start_row_for_prep, column=self.layout.COL_GRUPO).value = preparacion.get('grupo_alimentos', 'SIN GRUPO')
            ws.cell(row=start_row_for_prep, column=self.layout.COL_PREPARACION).value = preparacion.get('nombre', '')

            for ingrediente in ingredients_in_prep:
                ws.cell(row=current_row, column=self.layout.COL_INGREDIENTE).value = ingrediente.get('nombre', '')
                ws.cell(row=current_row, column=self.layout.COL_CODIGO).value = ingrediente.get('codigo_icbf', '')
                ws.cell(row=current_row, column=self.layout.COL_PESO_BRUTO).value = ingrediente.get('peso_bruto_base', 0)
                ws.cell(row=current_row, column=self.layout.COL_PESO_NETO).value = ingrediente.get('peso_neto_base', 0)

                if 'valores_finales_guardados' in ingrediente:
                    valores_finales = ingrediente['valores_finales_guardados']
                    ws.cell(row=current_row, column=self.layout.COL_CALORIAS).value = valores_finales.get('calorias', 0)
                    ws.cell(row=current_row, column=self.layout.COL_PROTEINA).value = valores_finales.get('proteina', 0)
                    ws.cell(row=current_row, column=self.layout.COL_GRASA).value = valores_finales.get('grasa', 0)
                    ws.cell(row=current_row, column=self.layout.COL_CHO).value = valores_finales.get('cho', 0)
                    ws.cell(row=current_row, column=self.layout.COL_CALCIO).value = valores_finales.get('calcio', 0)
                    ws.cell(row=current_row, column=self.layout.COL_HIERRO).value = valores_finales.get('hierro', 0)
                    ws.cell(row=current_row, column=self.layout.COL_SODIO).value = valores_finales.get('sodio', 0)
                
                current_row += 1

            if num_ingredients > 1:
                end_row_for_prep = current_row - 1
                cols_to_merge = [self.layout.COL_COMPONENTE, self.layout.COL_GRUPO, self.layout.COL_PREPARACION]
                for col_idx in cols_to_merge:
                    ws.merge_cells(start_row=start_row_for_prep, start_column=col_idx, end_row=end_row_for_prep, end_column=col_idx)
                    cell_to_align = ws.cell(row=start_row_for_prep, column=col_idx)
                    cell_to_align.alignment = center_align

        return current_row - 1

    def _add_calculations_section(self, ws: Worksheet, last_data_row: int, nivel_data: Dict) -> None:
        """Agregar sección de totales, recomendaciones y adecuación."""
        total_row = last_data_row + 2
        self._add_totals_row(ws, total_row, nivel_data)
        req_row = total_row + 1
        self._add_recommendations_row(ws, req_row, nivel_data)
        pct_row = req_row + 1
        self._add_adequacy_row(ws, pct_row, total_row, req_row)

    def _add_totals_row(self, ws: Worksheet, row: int, nivel_data: Dict) -> None:
        """Agregar fila de totales."""
        ws.cell(row, 1).value = "TOTAL MENÚ"
        ws.cell(row, 1).font = Font(bold=True)
        ws.cell(row, 1).fill = self.total_fill
        ws.merge_cells(f'A{row}:G{row}')

        totales = nivel_data.get('totales', {})
        for i, key in enumerate(NUTRIENT_KEYS, start=self.layout.COL_CALORIAS):
            cell = ws.cell(row, i)
            cell.value = totales.get(key, 0)
            cell.fill = self.total_fill
            cell.border = self.border

    def _add_recommendations_row(self, ws: Worksheet, row: int, nivel_data: Dict) -> None:
        """Agregar fila de recomendaciones."""
        ws.cell(row, 1).value = "RECOMENDACIÓN"
        ws.cell(row, 1).font = Font(bold=True)
        ws.cell(row, 1).fill = self.header_fill
        ws.merge_cells(f'A{row}:G{row}')

        requerimientos = nivel_data.get('requerimientos', {})
        for i, key in enumerate(NUTRIENT_KEYS, start=self.layout.COL_CALORIAS):
            cell = ws.cell(row, i)
            default_values = [1300, 45.5, 43.3, 182, 700, 5.6, 1133]
            cell.value = requerimientos.get(key, default_values[i - self.layout.COL_CALORIAS])
            cell.fill = self.header_fill
            cell.border = self.border

    def _add_adequacy_row(self, ws: Worksheet, row: int, total_row: int, req_row: int) -> None:
        """Agregar fila de % adecuación con fórmulas."""
        ws.cell(row, 1).value = "% ADECUACIÓN"
        ws.cell(row, 1).font = Font(bold=True)
        ws.merge_cells(f'A{row}:G{row}')

        for col in range(self.layout.COL_CALORIAS, self.layout.COL_SODIO + 1):
            col_letter = get_column_letter(col)
            formula = f'=IF({col_letter}{req_row}=0,0,{col_letter}{total_row}/{col_letter}{req_row}*100)'
            cell = ws.cell(row, col)
            cell.value = formula
            cell.border = self.border
            cell.number_format = '0.00"%"'

    def _add_signatures(self, ws: Worksheet, start_row: int) -> None:
        """Agregar sección de firmas."""
        row = start_row
        ws.cell(row=row, column=1).value = "NOMBRE NUTRICIONISTA - DIETISTA QUE ELABORA EL ANÁLISIS"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=5).value = "SARA ISABEL DIAZ MARQUEZ"
        ws.merge_cells(f'A{row}:D{row}')

        row += 1
        ws.cell(row=row, column=1).value = "FIRMA"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.merge_cells(f'A{row}:C{row}')
        ws.cell(row=row, column=8).value = "MATRÍCULA PROFESIONAL"
        ws.cell(row=row, column=11).value = "1107089938"
        ws.merge_cells(f'H{row}:J{row}')

        row += 2
        ws.cell(row=row, column=1).value = "NOMBRE NUTRICIONISTA - DIETISTA QUE REVISA Y APRUEBA EL ANÁLISIS POR PARTE DE LA SEM"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=5).value = "GABRIELA GIRALDO MARTINEZ"
        ws.merge_cells(f'A{row}:D{row}')

        row += 1
        ws.cell(row=row, column=1).value = "FIRMA"
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.merge_cells(f'A{row}:C{row}')
        ws.cell(row=row, column=8).value = "MATRÍCULA PROFESIONAL"
        ws.cell(row=row, column=11).value = "1005964870"
        ws.merge_cells(f'H{row}:J{row}')

    def _apply_formatting(self, ws: Worksheet) -> None:
        """Aplica formato a todo el worksheet."""
        for col, width in ColumnWidths.WIDTHS.items():
            ws.column_dimensions[col].width = width

    def _apply_page_setup(self, ws: Worksheet) -> None:
        """Configura la página para impresión."""
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.paper_size = 9
        ws.page_setup.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0 # Allow multiple pages vertically

    def _merge_cells_for_section(self, ws: Worksheet, start_row: int) -> None:
        """Combina las celdas para una sección de análisis completa."""
        ws.merge_cells(start_row=start_row, start_column=4, end_row=start_row, end_column=14)
        admin_start = start_row + 1
        for i in range(7):
            row = admin_start + i
            ws.merge_cells(f'A{row}:C{row}')

    def _extract_nivel_escolar(self, analisis_data: Dict) -> str:
        """Extraer nombre del nivel escolar."""
        analisis_por_nivel = analisis_data.get('analisis_por_nivel', [])
        if not analisis_por_nivel:
            return "N/A"
        for nivel_data in analisis_por_nivel:
            if nivel_data.get('es_programa_actual'):
                return nivel_data.get('nivel_escolar', {}).get('nombre', 'N/A')
        return analisis_por_nivel[0].get('nivel_escolar', {}).get('nombre', 'N/A')

    def _extract_nivel_data(self, analisis_data: Dict, nivel_escolar_id: Optional[str] = None) -> Optional[Dict]:
        """
        Extraer los datos del nivel escolar específico o del nivel actual del programa.

        Args:
            analisis_data: Diccionario con todos los análisis por nivel.
            nivel_escolar_id: ID del nivel escolar específico (opcional).

        Returns:
            Diccionario con los datos del nivel escolar o None si no se encuentra.
        """
        analisis_por_nivel = analisis_data.get('analisis_por_nivel', [])

        if not analisis_por_nivel:
            return None

        # Si se especificó un nivel escolar ID, buscarlo
        if nivel_escolar_id:
            for nivel_data in analisis_por_nivel:
                nivel_id = nivel_data.get('nivel_escolar', {}).get('id', '')
                if str(nivel_id) == str(nivel_escolar_id):
                    return nivel_data

        # Si no se especificó o no se encontró, buscar el nivel del programa actual
        for nivel_data in analisis_por_nivel:
            if nivel_data.get('es_programa_actual'):
                return nivel_data

        # Como último recurso, devolver el primer nivel
        return analisis_por_nivel[0] if analisis_por_nivel else None

    def _draw_single_report(self, ws: Worksheet, start_row: int, analisis_data: Dict, nivel_escolar_id: Optional[str] = None) -> None:
        """
        Dibuja un reporte de análisis completo en la hoja y fila especificadas.

        Args:
            ws: Hoja de Excel donde dibujar.
            start_row: Fila inicial para el reporte.
            analisis_data: Datos del análisis nutricional.
            nivel_escolar_id: ID del nivel escolar (opcional).
        """
        menu_info = analisis_data.get('menu', {})
        logo_path = menu_info.get('logo_path')
        self._insert_logo(ws, logo_path, f'A{start_row}')

        self._populate_title(ws, start_row=start_row)

        admin_start_row = start_row + 1
        self._populate_administrative_section(ws, start_row=admin_start_row, analisis_data=analisis_data)

        nivel_data = self._extract_nivel_data(analisis_data, nivel_escolar_id)
        if not nivel_data:
            raise ValueError("No se encontró información del nivel escolar para el reporte")

        header_start_row = start_row + 9
        self._populate_headers(ws, start_row=header_start_row)

        data_start_row = start_row + 10
        last_data_row = self._populate_ingredients_from_analysis(
            ws, start_row=data_start_row, nivel_data=nivel_data
        )

        self._add_calculations_section(ws, last_data_row, nivel_data)
        self._add_signatures(ws, last_data_row + 6)

        self._merge_cells_for_section(ws, start_row=start_row)
