"""
Generador de análisis nutricional en formato Excel.

Este módulo genera archivos Excel con análisis nutricional completo
para un solo menú.
"""

import io
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from .services.analisis_service import AnalisisNutricionalService
from .excel_drawing_utils import ExcelReportDrawer


class NutritionalAnalysisExcelGenerator(ExcelReportDrawer):
    """
    Generador de análisis nutricional en Excel para un solo menú.
    Hereda la lógica de dibujo de ExcelReportDrawer.
    """

    def __init__(self):
        super().__init__()

    def generate_from_analysis_service(
        self,
        menu_id: int,
        nivel_escolar_id: Optional[str] = None
    ) -> io.BytesIO:
        """
        Genera un WORKBOOK completo para un solo menú.
        """
        try:
            analisis_data = AnalisisNutricionalService.obtener_analisis_completo(menu_id)

            if not analisis_data.get('success'):
                raise ValueError("No se pudo obtener el análisis del menú")

            wb = Workbook()
            ws = wb.active
            ws.title = "Análisis Nutricional"

            # Dibuja el reporte en la fila 1
            self._draw_single_report(ws, 1, analisis_data, nivel_escolar_id)
            
            self._apply_formatting(ws)
            self._apply_page_setup(ws)

            stream = io.BytesIO()
            wb.save(stream)
            stream.seek(0)
            return stream

        except Exception as e:
            return self._generate_error_excel(f"Error generando Excel: {str(e)}")

    def _generate_error_excel(self, error_message: str) -> io.BytesIO:
        """Generar Excel con mensaje de error."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Error"
        ws['A1'] = f"Error: {error_message}"
        ws['A1'].font = Font(bold=True, color="FF0000")
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

# =====================================================================
# FUNCIONES DE COMPATIBILIDAD (WRAPPER)
# =====================================================================

def generate_excel_from_service(
    menu_id: int,
    nivel_escolar_id: Optional[str] = None
) -> io.BytesIO:
    """
    Genera Excel usando el servicio de análisis nutricional.
    Función de compatibilidad.
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)

def generate_menu_excel(menu_id: int, nivel_escolar_id: Optional[str] = None) -> io.BytesIO:
    """Genera análisis nutricional completo."""
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)

def generate_menu_excel_with_nivel(menu_id: int, nivel_escolar_id: str) -> io.BytesIO:
    """Genera análisis nutricional para un nivel escolar específico."""
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)

def generate_advanced_nutritional_excel(
    menu_id: int,
    nivel_escolar_id: Optional[str] = None,
    use_saved_analysis: bool = True
) -> io.BytesIO:
    """Genera Excel nutricional avanzado (función de compatibilidad)."""
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id, nivel_escolar_id)

def generate_menu_excel_real_data(menu_id: int) -> io.BytesIO:
    """
    Genera análisis nutricional usando datos reales.
    Función de compatibilidad - usa el servicio de análisis.
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_from_analysis_service(menu_id)