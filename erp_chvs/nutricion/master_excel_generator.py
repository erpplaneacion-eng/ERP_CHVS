"""
Generador del Reporte Maestro de Análisis Nutricional por Modalidad.
"""

import io
from typing import Dict

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from .excel_drawing_utils import ExcelReportDrawer


class MasterNutritionalExcelGenerator(ExcelReportDrawer):
    """
    Genera un único archivo Excel con múltiples pestañas (una por nivel escolar),
    cada una conteniendo los análisis de todos los menús de una modalidad.
    """

    def __init__(self):
        super().__init__()

    def generate(self, masive_analysis_data: Dict) -> io.BytesIO:
        """
        Método principal para generar el reporte maestro.
        Cada nivel escolar tiene su propia pestaña con todos sus menús.
        Cada menú se imprime en una página separada.

        Args:
            masive_analysis_data: El diccionario de datos masivos del servicio.

        Returns:
            Un stream de bytes con el archivo Excel.
        """
        wb = Workbook()
        wb.remove(wb.active)  # Eliminar la hoja por defecto

        analysis_by_level = masive_analysis_data.get("analisis_por_nivel", {})

        for nivel_nombre, menus_analisis in analysis_by_level.items():
            # Crear una hoja por cada nivel escolar
            # Truncar el nombre si es muy largo para el límite de Excel (31 chars)
            sheet_name = nivel_nombre[:31]
            ws = wb.create_sheet(title=sheet_name)

            current_row = 1
            for i, menu_analisis in enumerate(menus_analisis):
                try:
                    # Reconstruir la estructura de datos que espera `_draw_single_report`
                    reconstructed_data = {
                        'menu': menu_analisis['menu_info'],
                        'analisis_por_nivel': [menu_analisis['analisis']]
                    }

                    menu_nombre = menu_analisis['menu_info'].get('nombre', f'Menu {i+1}')
                    print(f"[DEBUG] Dibujando menú '{menu_nombre}' en nivel '{nivel_nombre}' (fila {current_row})")

                    # Dibujar el reporte y obtener la última fila real utilizada
                    end_row = self._draw_single_report(ws, current_row, reconstructed_data, nivel_escolar_id=None)

                    print(f"[DEBUG] Menú '{menu_nombre}' dibujado correctamente (filas {current_row}-{end_row})")

                    # Agregar un salto de página después de cada menú (excepto el último)
                    if i < len(menus_analisis) - 1:
                        # Colocar el salto de página en la fila siguiente al final del reporte
                        ws.row_dimensions[end_row + 1].page_break = True
                        # El siguiente reporte comienza 2 filas después del salto
                        current_row = end_row + 2

                except Exception as e:
                    menu_nombre = menu_analisis['menu_info'].get('nombre', f'Menu {i+1}')
                    print(f"[ERROR] Error al dibujar menú '{menu_nombre}' en nivel '{nivel_nombre}':")
                    print(f"[ERROR] Fila actual: {current_row}")
                    print(f"[ERROR] Menú index: {i+1}/{len(menus_analisis)}")
                    import traceback
                    print(traceback.format_exc())
                    raise Exception(f"Error dibujando menú '{menu_nombre}' en nivel '{nivel_nombre}': {str(e)}")

            # Aplicar formato y configuración de página a la hoja completa
            self._apply_formatting(ws)
            self._apply_page_setup(ws)

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream
