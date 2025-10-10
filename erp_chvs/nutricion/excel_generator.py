import io
import os
from typing import Dict, List, Optional
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.conf import settings

from .models import (
    TablaMenus,
    TablaPreparaciones,
    TablaIngredientesSiesa,
    TablaPreparacionIngredientes,
    TablaAlimentos2018Icbf,
    ComponentesAlimentos,
    GruposAlimentos, 
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel
)
from .services.analisis_service import AnalisisNutricionalService


class NutritionalAnalysisExcelGenerator:
    """
    Generador avanzado de análisis nutricional en Excel.

    Utiliza el formato estándar del ICBF como plantilla y lo popula
    automáticamente con datos reales del menú.
    """

    def __init__(self):
        # Colores para formateo
        self.header_fill = PatternFill(start_color="B8D4F0", end_color="B8D4F0", fill_type="solid")
        self.total_fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    def generate_nutritional_analysis_excel(self, menu_id: int, nivel_escolar_id: str = None) -> io.BytesIO:
        """
        Genera el análisis nutricional completo en formato Excel.

        Args:
            menu_id: ID del menú a analizar
            nivel_escolar_id: ID específico del nivel escolar (opcional)

        Returns:
            BytesIO con el archivo Excel generado
        """
        try:
            # 1. Obtener datos del menú usando el servicio existente
            analisis_data = AnalisisNutricionalService.obtener_analisis_completo(menu_id)

            if not analisis_data.get('success'):
                raise ValueError("No se pudo obtener el análisis del menú")

            # 2. Crear workbook basado en plantilla o desde cero
            wb = self._create_workbook_from_template()

            # 3. Poblar información administrativa
            self._populate_administrative_data(wb.active, analisis_data)

            # 4. Poblar datos nutricionales
            if nivel_escolar_id:
                # Si se especifica un nivel, usar solo ese
                nivel_data = self._find_nivel_data(analisis_data, nivel_escolar_id)
                if nivel_data:
                    self._populate_nutritional_data(wb.active, nivel_data)
            else:
                # Si no se especifica, usar el nivel del programa actual
                for nivel_data in analisis_data['analisis_por_nivel']:
                    if nivel_data.get('es_programa_actual'):
                        self._populate_nutritional_data(wb.active, nivel_data)
                        break

            # 5. Aplicar formateo profesional
            self._apply_formatting(wb.active)

            # 6. Generar archivo
            return self._save_to_stream(wb)

        except Exception as e:
            # En caso de error, generar Excel básico con mensaje de error
            return self._generate_error_excel(str(e))

    def _create_workbook_from_template(self) -> Workbook:
        """Crear workbook desde plantilla o desde cero"""
        template_path = os.path.join(
            settings.BASE_DIR,
            'archivos excel',
            'nutricion excel',
            'formatonutricional.xlsx'
        )

        if os.path.exists(template_path):
            try:
                wb = load_workbook(template_path)
                # Usar la primera hoja o crear nueva si no existe
                if len(wb.sheetnames) > 0:
                    ws = wb[wb.sheetnames[0]]
                else:
                    ws = wb.active
                    ws.title = "Análisis Nutricional"
            except Exception:
                # Si falla la carga de plantilla, crear desde cero
                wb = Workbook()
                ws = wb.active
                ws.title = "Análisis Nutricional"
        else:
            # Crear desde cero
            wb = Workbook()
            ws = wb.active
            ws.title = "Análisis Nutricional"

        return wb

    def _populate_administrative_data(self, worksheet, analisis_data: Dict):
        """Poblar información administrativa del menú"""
        menu_info = analisis_data.get('menu', {})

        # Título principal (celdas combinadas A1:N1)
        worksheet.merge_cells('A1:N1')
        title_cell = worksheet['A1']
        title_cell.value = "ANÁLISIS NUTRICIONAL"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal='center', vertical='center')

        # Información administrativa (filas 2-7)
        admin_data = [
            ("ENTIDAD TERRITORIAL:", menu_info.get('programa', 'N/A')),
            ("MINUTA CON ENFOQUE ETNICO:", "No"),
            ("GRUPO ÉTNICO", "Sin Pertenencia Étnica"),
            ("MODALIDAD DE ATENCIÓN", menu_info.get('modalidad', 'N/A')),
            ("TIPO DE COMPLEMENTO", "Almuerzo"),
            ("NIVEL", "Preescolar"),
            ("MENÚ No.", menu_info.get('nombre', 'N/A'))
        ]

        for row, (label, value) in enumerate(admin_data, start=2):
            # Label (columnas A-C)
            worksheet.merge_cells(f'A{row}:C{row}')
            label_cell = worksheet[f'A{row}']
            label_cell.value = label
            label_cell.font = Font(bold=True)
            label_cell.alignment = Alignment(horizontal='right', vertical='center')

            # Value (columnas D-N)
            worksheet.merge_cells(f'D{row}:N{row}')
            value_cell = worksheet[f'D{row}']
            value_cell.value = value
            value_cell.alignment = Alignment(horizontal='left', vertical='center')

    def _populate_nutritional_data(self, worksheet, nivel_data: Dict):
        """Poblar datos nutricionales del nivel escolar"""
        start_row = 12  # Fila donde comienzan los ingredientes

        # Encabezados de columnas (filas 8-11)
        headers = [
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

        # Crear encabezados combinados
        col = 1
        for header in headers:
            cell = worksheet.cell(row=8, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = self.border
            col += 1

        # Combinar celdas de encabezado para componentes
        worksheet.merge_cells('A8:C11')  # COMPONENTE
        worksheet.merge_cells('D8:D11')  # GRUPO DE ALIMENTOS
        worksheet.merge_cells('E8:E11')  # NOMBRE DE LA PREPARACION
        worksheet.merge_cells('F8:F11')  # NOMBRE DEL ALIMENTO
        worksheet.merge_cells('G8:G11')  # CÓDIGO DEL ALIMENTO
        worksheet.merge_cells('H8:H11')  # PESO BRUTO
        worksheet.merge_cells('I8:I11')  # PESO NETO
        worksheet.merge_cells('J8:N8')  # CALORIAS Y NUTRIENTES

        # Poblar ingredientes
        current_row = start_row
        for preparacion in nivel_data.get('preparaciones', []):
            for ingrediente in preparacion.get('ingredientes', []):
                if ingrediente.get('alimento_encontrado'):
                    # Componente y grupo
                    worksheet.cell(current_row, 1).value = "ALIMENTO PROTEICO"  # Ejemplo
                    worksheet.cell(current_row, 4).value = ingrediente.get('grupo_alimentos', '')
                    worksheet.cell(current_row, 5).value = preparacion.get('nombre', '')
                    worksheet.cell(current_row, 6).value = ingrediente.get('nombre', '')
                    worksheet.cell(current_row, 7).value = ingrediente.get('codigo_icbf', '')

                    # Pesos
                    worksheet.cell(current_row, 8).value = ingrediente.get('peso_bruto_base', 0)
                    worksheet.cell(current_row, 9).value = ingrediente.get('peso_neto_base', 0)

                    # Valores nutricionales
                    valores = ingrediente.get('valores_por_100g', {})
                    factor = float(ingrediente.get('peso_neto_base', 100)) / 100.0

                    worksheet.cell(current_row, 10).value = float(valores.get('calorias_kcal', 0)) * factor
                    worksheet.cell(current_row, 11).value = float(valores.get('proteina_g', 0)) * factor
                    worksheet.cell(current_row, 12).value = float(valores.get('grasa_g', 0)) * factor
                    worksheet.cell(current_row, 13).value = float(valores.get('cho_g', 0)) * factor
                    worksheet.cell(current_row, 14).value = float(valores.get('calcio_mg', 0)) * factor
                    worksheet.cell(current_row, 15).value = float(valores.get('hierro_mg', 0)) * factor
                    worksheet.cell(current_row, 16).value = float(valores.get('sodio_mg', 0)) * factor

                    current_row += 1

        # Agregar filas para otros componentes (ejemplo)
        self._add_example_components(worksheet, current_row)

        # Totales (fila dinámica)
        total_row = current_row + 2
        self._add_totals_section(worksheet, total_row, nivel_data)

        # Recomendaciones
        req_row = total_row + 2
        self._add_recommendations_section(worksheet, req_row, nivel_data)

        # Firmas
        signature_row = req_row + 4
        self._add_signature_section(worksheet, signature_row)

    def _add_example_components(self, worksheet, start_row: int):
        """Agregar componentes de ejemplo (bebida, cereal, etc.)"""
        components = [
            ("CEREAL ACOMPAÑANTE", "Grupo I", "ARROZ CON PIMENTON", "Arroz", "001", 25, 25, 87, 2, 0.3, 19, 3, 0.1, 2),
            ("TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL", "Grupo I", "PAPA CRIOLLA DORADA", "Papa", "002", 50, 50, 77, 2, 0.1, 17, 8, 0.3, 5),
            ("LECHE Y PRODUCTOS LACTEOS", "Grupo III", "SORBETE DE GUAYABA", "Sorbete", "003", 100, 100, 65, 0.5, 0, 17, 15, 0.1, 5),
        ]

        for row, (componente, grupo, preparacion, alimento, codigo, peso_bruto, peso_neto, cal, prot, grasa, cho, calcio, hierro, sodio) in enumerate(components, start=start_row):
            worksheet.cell(row, 1).value = componente
            worksheet.cell(row, 4).value = grupo
            worksheet.cell(row, 5).value = preparacion
            worksheet.cell(row, 6).value = alimento
            worksheet.cell(row, 7).value = codigo
            worksheet.cell(row, 8).value = peso_bruto
            worksheet.cell(row, 9).value = peso_neto
            worksheet.cell(row, 10).value = cal
            worksheet.cell(row, 11).value = prot
            worksheet.cell(row, 12).value = grasa
            worksheet.cell(row, 13).value = cho
            worksheet.cell(row, 14).value = calcio
            worksheet.cell(row, 15).value = hierro
            worksheet.cell(row, 16).value = sodio

    def _add_totals_section(self, worksheet, row: int, nivel_data: Dict):
        """Agregar sección de totales"""
        # Títulos
        worksheet.merge_cells(f'A{row}:C{row}')
        worksheet.cell(row, 1).value = "TOTAL MENÚ"
        worksheet.cell(row, 1).font = Font(bold=True)
        worksheet.cell(row, 1).fill = self.total_fill

        # Valores totales
        totales = nivel_data.get('totales', {})
        valores = [
            totales.get('calorias_kcal', 0),
            totales.get('proteina_g', 0),
            totales.get('grasa_g', 0),
            totales.get('cho_g', 0),
            totales.get('calcio_mg', 0),
            totales.get('hierro_mg', 0),
            totales.get('sodio_mg', 0)
        ]

        for col, valor in enumerate(valores, start=10):
            cell = worksheet.cell(row, col)
            cell.value = valor
            cell.fill = self.total_fill
            cell.border = self.border

    def _add_recommendations_section(self, worksheet, row: int, nivel_data: Dict):
        """Agregar sección de recomendaciones"""
        # Títulos
        worksheet.merge_cells(f'A{row}:C{row}')
        worksheet.cell(row, 1).value = "RECOMENDACIÓN"
        worksheet.cell(row, 1).font = Font(bold=True)
        worksheet.cell(row, 1).fill = self.header_fill

        # Valores recomendados
        requerimientos = nivel_data.get('requerimientos', {})
        recomendaciones = [
            1300,  # calorías
            requerimientos.get('proteina_g', 45.5),
            requerimientos.get('grasa_g', 43.3),
            requerimientos.get('cho_g', 182),
            requerimientos.get('calcio_mg', 700),
            requerimientos.get('hierro_mg', 5.6),
            requerimientos.get('sodio_mg', 1133)
        ]

        for col, valor in enumerate(recomendaciones, start=10):
            cell = worksheet.cell(row, col)
            cell.value = valor
            cell.fill = self.header_fill
            cell.border = self.border

    def _add_signature_section(self, worksheet, row: int):
        """Agregar sección de firmas"""
        # Nutricionista que elabora
        worksheet.merge_cells(f'A{row}:C{row}')
        worksheet.cell(row, 1).value = "NOMBRE NUTRICIONISTA - DIETISTA QUE ELABORA EL ANÁLISIS"
        worksheet.cell(row, 1).font = Font(bold=True)

        worksheet.merge_cells(f'D{row}:N{row}')
        worksheet.cell(row, 4).value = "SARA ISABEL DIAZ MARQUEZ"

        # Matrícula profesional
        row += 1
        worksheet.merge_cells(f'A{row}:C{row}')
        worksheet.cell(row, 1).value = "FIRMA"
        worksheet.cell(row, 1).font = Font(bold=True)

        worksheet.merge_cells(f'D{row}:F{row}')
        worksheet.cell(row, 4).value = "MATRÍCULA PROFESIONAL"
        worksheet.merge_cells(f'G{row}:N{row}')
        worksheet.cell(row, 7).value = "1107089938"

        # Nutricionista que revisa
        row += 2
        worksheet.merge_cells(f'A{row}:C{row}')
        worksheet.cell(row, 1).value = "NOMBRE NUTRICIONISTA - DIETISTA QUE REVISA Y APRUBA EL ANALISIS POR PARTE DE LA SEM"
        worksheet.cell(row, 1).font = Font(bold=True)

        worksheet.merge_cells(f'D{row}:N{row}')
        worksheet.cell(row, 4).value = "GABRIELA GIRALDO MARTINEZ"

        # Matrícula profesional (revisa)
        row += 1
        worksheet.merge_cells(f'A{row}:C{row}')
        worksheet.cell(row, 1).value = "FIRMA"
        worksheet.cell(row, 1).font = Font(bold=True)

        worksheet.merge_cells(f'D{row}:F{row}')
        worksheet.cell(row, 4).value = "MATRÍCULA PROFESIONAL"
        worksheet.merge_cells(f'G{row}:N{row}')
        worksheet.cell(row, 7).value = "1005964870"

    def _apply_formatting(self, worksheet):
        """Aplicar formateo profesional a toda la hoja"""
        # Ajustar ancho de columnas
        column_widths = {
            'A': 25, 'B': 15, 'C': 15, 'D': 20, 'E': 25, 'F': 30,
            'G': 15, 'H': 12, 'I': 12, 'J': 12, 'K': 10, 'L': 10,
            'M': 10, 'N': 10, 'O': 12, 'P': 12
        }

        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

        # Aplicar bordes a todas las celdas con contenido
        for row in worksheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.border = self.border
                    cell.alignment = Alignment(vertical='center', wrap_text=True)

    def _find_nivel_data(self, analisis_data: Dict, nivel_escolar_id: str) -> Optional[Dict]:
        """Encontrar datos de un nivel escolar específico"""
        for nivel_data in analisis_data.get('analisis_por_nivel', []):
            nivel_info = nivel_data.get('nivel_escolar', {})
            if str(nivel_info.get('id')) == str(nivel_escolar_id):
                return nivel_data
        return None

    def _save_to_stream(self, workbook) -> io.BytesIO:
        """Guardar workbook en stream de bytes"""
        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return stream

    def _generate_error_excel(self, error_message: str) -> io.BytesIO:
        """Generar Excel básico con mensaje de error"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Error"

        ws.merge_cells('A1:N1')
        ws['A1'] = f"Error generando análisis nutricional: {error_message}"
        ws['A1'].font = Font(bold=True, color="FF0000")

        return self._save_to_stream(wb)


    def _populate_real_nutritional_data(self, worksheet, nivel_data: Dict, menu_id: int):
        """Poblar datos nutricionales reales desde la base de datos"""
        start_row = 12

        # Obtener preparaciones reales del menú
        preparaciones = TablaPreparaciones.objects.filter(id_menu_id=menu_id).prefetch_related(
            'ingredientes__id_ingrediente_siesa'
        )

        current_row = start_row

        for preparacion in preparaciones:
            # Obtener componente
            componente = preparacion.id_componente.componente if preparacion.id_componente else "SIN COMPONENTE"
            grupo_alimentos = preparacion.id_componente.id_grupo_alimentos.grupo_alimentos if preparacion.id_componente else "SIN GRUPO"

            ingredientes = TablaPreparacionIngredientes.objects.filter(
                id_preparacion=preparacion
            ).select_related('id_ingrediente_siesa')

            for ing_prep in ingredientes:
                ingrediente = ing_prep.id_ingrediente_siesa

                # Buscar información nutricional del ICBF
                alimento_icbf = TablaAlimentos2018Icbf.objects.filter(
                    codigo=ingrediente.id_ingrediente_siesa
                ).first()

                if not alimento_icbf:
                    alimento_icbf = TablaAlimentos2018Icbf.objects.filter(
                        nombre_del_alimento__icontains=ingrediente.nombre_ingrediente[:50]
                    ).first()

                if alimento_icbf:
                    # Calcular valores reales usando el servicio existente
                    peso_neto_base = float(nivel_data.get('peso_neto_base', 100))
                    factor = peso_neto_base / 100.0

                    valores_100g = {
                        'calorias_kcal': float(alimento_icbf.energia_kcal or 0),
                        'proteina_g': float(alimento_icbf.proteina_g or 0),
                        'grasa_g': float(alimento_icbf.lipidos_g or 0),
                        'cho_g': float(alimento_icbf.carbohidratos_totales_g or 0),
                        'calcio_mg': float(alimento_icbf.calcio_mg or 0),
                        'hierro_mg': float(alimento_icbf.hierro_mg or 0),
                        'sodio_mg': float(alimento_icbf.sodio_mg or 0)
                    }

                    # Poblar fila con datos reales
                    worksheet.cell(current_row, 1).value = componente
                    worksheet.cell(current_row, 4).value = grupo_alimentos
                    worksheet.cell(current_row, 5).value = preparacion.preparacion
                    worksheet.cell(current_row, 6).value = ingrediente.nombre_ingrediente
                    worksheet.cell(current_row, 7).value = alimento_icbf.codigo

                    # Calcular peso bruto usando la lógica del servicio
                    parte_comestible = float(alimento_icbf.parte_comestible_field or 100)
                    peso_bruto = self._calculo_service.calcular_peso_bruto(peso_neto_base, parte_comestible)

                    worksheet.cell(current_row, 8).value = round(float(peso_bruto), 1)
                    worksheet.cell(current_row, 9).value = peso_neto_base

                    # Valores nutricionales calculados
                    worksheet.cell(current_row, 10).value = float(valores_100g['calorias_kcal']) * factor
                    worksheet.cell(current_row, 11).value = float(valores_100g['proteina_g']) * factor
                    worksheet.cell(current_row, 12).value = float(valores_100g['grasa_g']) * factor
                    worksheet.cell(current_row, 13).value = float(valores_100g['cho_g']) * factor
                    worksheet.cell(current_row, 14).value = float(valores_100g['calcio_mg']) * factor
                    worksheet.cell(current_row, 15).value = float(valores_100g['hierro_mg']) * factor
                    worksheet.cell(current_row, 16).value = float(valores_100g['sodio_mg']) * factor

                    current_row += 1

        # Si no hay ingredientes reales, usar datos de ejemplo
        if current_row == start_row:
            self._add_example_components(worksheet, start_row)

        return current_row

    def generate_excel_with_nivel_escolar(self, menu_id: int, nivel_escolar_id: str) -> io.BytesIO:
        """
        Genera Excel para un menú y nivel escolar específico.

        Args:
            menu_id: ID del menú
            nivel_escolar_id: ID del nivel escolar

        Returns:
            BytesIO con el archivo Excel generado
        """
        generator = NutritionalAnalysisExcelGenerator()
        return generator.generate_nutritional_analysis_excel(menu_id, nivel_escolar_id)

    def generate_excel_from_real_data(self, menu_id: int, nivel_escolar_id: str = None) -> io.BytesIO:
        """
        Genera Excel usando datos reales de ingredientes desde la base de datos.

        Args:
            menu_id: ID del menú
            nivel_escolar_id: ID del nivel escolar (opcional)

        Returns:
            BytesIO con el archivo Excel generado
        """
        try:
            # Obtener menú
            menu = TablaMenus.objects.select_related('id_contrato').get(id_menu=menu_id)

            # Crear workbook
            wb = self._create_workbook_from_template()

            # Poblar información administrativa
            self._populate_administrative_data(wb.active, {
                'menu': {
                    'id': menu.id_menu,
                    'nombre': menu.menu,
                    'modalidad': menu.id_modalidad.modalidad if menu.id_modalidad else 'N/A',
                    'programa': menu.id_contrato.programa if menu.id_contrato else 'N/A'
                }
            })

            # Obtener preparaciones con ingredientes reales
            preparaciones = TablaPreparaciones.objects.filter(id_menu=menu).prefetch_related(
                'ingredientes__id_ingrediente_siesa',
                'id_componente__id_grupo_alimentos'
            )

            # Poblar datos nutricionales reales
            current_row = self._populate_real_ingredients_data(wb.active, preparaciones, 12)

            # Agregar componentes adicionales de ejemplo si es necesario
            if current_row == 12:  # No se agregaron ingredientes reales
                self._add_example_components(wb.active, current_row)
                current_row += 3

            # Agregar cálculos automáticos usando las nuevas funciones
            total_row, req_row, pct_row = self.add_nutritional_calculations(
                wb.active, 12, current_row - 1
            )

            # Firmas
            signature_row = pct_row + 4
            self._add_signature_section(wb.active, signature_row)

            # Aplicar formateo
            self._apply_formatting(wb.active)

            return self._save_to_stream(wb)

        except TablaMenus.DoesNotExist:
            return self._generate_error_excel("Menú no encontrado")
        except Exception as e:
            return self._generate_error_excel(f"Error generando Excel: {str(e)}")

    def _populate_real_ingredients_data(self, worksheet, preparaciones, start_row: int) -> int:
        """Poblar datos reales de ingredientes desde la base de datos"""
        current_row = start_row

        for preparacion in preparaciones:
            componente = preparacion.id_componente.componente if preparacion.id_componente else "SIN COMPONENTE"
            grupo_alimentos = (preparacion.id_componente.id_grupo_alimentos.grupo_alimentos
                             if preparacion.id_componente and preparacion.id_componente.id_grupo_alimentos
                             else "SIN GRUPO")

            ingredientes = TablaPreparacionIngredientes.objects.filter(
                id_preparacion=preparacion
            ).select_related('id_ingrediente_siesa')

            for ing_prep in ingredientes:
                ingrediente = ing_prep.id_ingrediente_siesa

                # Buscar datos nutricionales del ICBF
                alimento_icbf = self._find_alimento_icbf(ingrediente)

                if alimento_icbf:
                    # Usar valores por defecto o de análisis guardado
                    peso_neto = 100  # Valor por defecto
                    peso_bruto = 100

                    # Buscar análisis guardado para obtener pesos reales
                    analisis_guardado = TablaAnalisisNutricionalMenu.objects.filter(
                        id_menu=preparacion.id_menu
                    ).first()

                    if analisis_guardado:
                        ingrediente_guardado = TablaIngredientesPorNivel.objects.filter(
                            id_analisis=analisis_guardado,
                            id_preparacion=preparacion,
                            id_ingrediente_siesa=ingrediente
                        ).first()

                        if ingrediente_guardado:
                            peso_neto = ingrediente_guardado.peso_neto
                            peso_bruto = ingrediente_guardado.peso_bruto

                    # Calcular valores nutricionales
                    factor = float(peso_neto) / 100.0
                    valores_100g = {
                        'calorias_kcal': float(alimento_icbf.energia_kcal or 0),
                        'proteina_g': float(alimento_icbf.proteina_g or 0),
                        'grasa_g': float(alimento_icbf.lipidos_g or 0),
                        'cho_g': float(alimento_icbf.carbohidratos_totales_g or 0),
                        'calcio_mg': float(alimento_icbf.calcio_mg or 0),
                        'hierro_mg': float(alimento_icbf.hierro_mg or 0),
                        'sodio_mg': float(alimento_icbf.sodio_mg or 0)
                    }

                    # Poblar fila
                    self._populate_ingredient_row(
                        worksheet, current_row, componente, grupo_alimentos,
                        preparacion.preparacion, ingrediente.nombre_ingrediente,
                        alimento_icbf.codigo, peso_bruto, peso_neto,
                        valores_100g, factor
                    )

                    current_row += 1

        return current_row

    def _find_alimento_icbf(self, ingrediente_siesa):
        """Buscar información nutricional del ICBF para un ingrediente"""
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

    def _populate_ingredient_row(self, worksheet, row: int, componente: str, grupo: str,
                               preparacion: str, ingrediente: str, codigo: str,
                               peso_bruto: float, peso_neto: float,
                               valores_100g: dict, factor: float):
        """Poblar una fila completa de ingrediente"""
        worksheet.cell(row, 1).value = componente
        worksheet.cell(row, 4).value = grupo
        worksheet.cell(row, 5).value = preparacion
        worksheet.cell(row, 6).value = ingrediente
        worksheet.cell(row, 7).value = codigo
        worksheet.cell(row, 8).value = round(float(peso_bruto), 1)
        worksheet.cell(row, 9).value = round(float(peso_neto), 1)
        worksheet.cell(row, 10).value = round(float(valores_100g['calorias_kcal']) * float(factor), 1)
        worksheet.cell(row, 11).value = round(float(valores_100g['proteina_g']) * float(factor), 1)
        worksheet.cell(row, 12).value = round(float(valores_100g['grasa_g']) * float(factor), 1)
        worksheet.cell(row, 13).value = round(float(valores_100g['cho_g']) * float(factor), 1)
        worksheet.cell(row, 14).value = round(float(valores_100g['calcio_mg']) * float(factor), 1)
        worksheet.cell(row, 15).value = round(float(valores_100g['hierro_mg']) * float(factor), 1)
        worksheet.cell(row, 16).value = round(float(valores_100g['sodio_mg']) * float(factor), 1)

    def add_nutritional_calculations(self, worksheet, start_row: int, end_row: int):
        """Agregar fórmulas de cálculo nutricional automático"""
        # Fila de totales
        total_row = end_row + 1

        # Título de totales
        worksheet.merge_cells(f'A{total_row}:C{total_row}')
        worksheet.cell(total_row, 1).value = "TOTAL MENÚ"
        worksheet.cell(total_row, 1).font = Font(bold=True)
        worksheet.cell(total_row, 1).fill = self.total_fill

        # Fórmulas de suma para cada columna nutricional
        for col in range(10, 17):  # Columnas J-P (10-16)
            col_letter = get_column_letter(col)
            formula = f"=SUM({col_letter}{start_row}:{col_letter}{end_row})"
            worksheet.cell(total_row, col).value = formula
            worksheet.cell(total_row, col).fill = self.total_fill
            worksheet.cell(total_row, col).border = self.border

        # Fila de recomendaciones
        req_row = total_row + 2
        worksheet.merge_cells(f'A{req_row}:C{req_row}')
        worksheet.cell(req_row, 1).value = "RECOMENDACIÓN"
        worksheet.cell(req_row, 1).font = Font(bold=True)
        worksheet.cell(req_row, 1).fill = self.header_fill

        # Valores recomendados por defecto (pueden ser parametrizados)
        recomendaciones = [1300, 45.5, 43.3, 182, 700, 5.6, 1133]
        for col, valor in enumerate(recomendaciones, start=10):
            worksheet.cell(req_row, col).value = valor
            worksheet.cell(req_row, col).fill = self.header_fill
            worksheet.cell(req_row, col).border = self.border

        # Fila de porcentajes de adecuación
        pct_row = req_row + 1
        worksheet.merge_cells(f'A{pct_row}:C{pct_row}')
        worksheet.cell(pct_row, 1).value = "% ADECUACIÓN"
        worksheet.cell(pct_row, 1).font = Font(bold=True)

        for col in range(10, 17):
            col_letter = get_column_letter(col)
            total_cell = f"{col_letter}{total_row}"
            req_cell = f"{col_letter}{req_row}"
            formula = f"=IF({req_cell}=0,0,{total_cell}/{req_cell}*100)"
            worksheet.cell(pct_row, col).value = formula
            worksheet.cell(pct_row, col).border = self.border
            worksheet.cell(pct_row, col).number_format = '0.00"%"'

        return total_row, req_row, pct_row


# Función de compatibilidad con el código existente
def generate_menu_excel(menu_id: int) -> io.BytesIO:
    """
    Función de compatibilidad que genera análisis nutricional completo.

    Args:
        menu_id: ID del menú a generar

    Returns:
        BytesIO con el archivo Excel generado
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_nutritional_analysis_excel(menu_id)


# Nueva función para generar con nivel específico
def generate_menu_excel_with_nivel(menu_id: int, nivel_escolar_id: str) -> io.BytesIO:
    """
    Genera análisis nutricional para un menú y nivel escolar específico.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar

    Returns:
        BytesIO con el archivo Excel generado
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_excel_from_real_data(menu_id, nivel_escolar_id)


# Función mejorada que usa datos reales
def generate_menu_excel_real_data(menu_id: int) -> io.BytesIO:
    """
    Genera análisis nutricional usando datos reales de ingredientes.

    Args:
        menu_id: ID del menú

    Returns:
        BytesIO con el archivo Excel generado
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_excel_from_real_data(menu_id)


# Nueva función para generar desde análisis guardado
def generate_excel_from_saved_analysis(menu_id: int, nivel_escolar_id: str) -> io.BytesIO:
    """
    Genera Excel usando datos reales de análisis nutricional guardado.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar

    Returns:
        BytesIO con el archivo Excel generado
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_excel_from_saved_analysis(menu_id, nivel_escolar_id)


# Función avanzada que detecta automáticamente si usar datos reales o guardados
def generate_advanced_nutritional_excel(menu_id: int, nivel_escolar_id: str = None, use_saved_analysis: bool = True) -> io.BytesIO:
    """
    Genera Excel nutricional avanzado con detección automática de datos.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar (opcional)
        use_saved_analysis: Si True, intenta usar análisis guardado primero

    Returns:
        BytesIO con el archivo Excel generado
    """
    generator = NutritionalAnalysisExcelGenerator()

    if use_saved_analysis and nivel_escolar_id:
        # Intentar generar desde análisis guardado
        try:
            return generator.generate_excel_from_saved_analysis(menu_id, nivel_escolar_id)
        except Exception:
            # Si falla, usar datos reales
            pass

    # Usar datos reales como fallback
    return generator.generate_excel_from_real_data(menu_id, nivel_escolar_id)


# Función para generar Excel usando directamente el servicio de análisis
def generate_excel_from_service(menu_id: int, nivel_escolar_id: str = None) -> io.BytesIO:
    """
    Genera Excel usando directamente el servicio de análisis nutricional existente.

    Args:
        menu_id: ID del menú
        nivel_escolar_id: ID del nivel escolar (opcional)

    Returns:
        BytesIO con el archivo Excel generado
    """
    generator = NutritionalAnalysisExcelGenerator()
    return generator.generate_excel_from_service_analysis(menu_id, nivel_escolar_id)
