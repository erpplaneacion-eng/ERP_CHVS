"""
Generador de Excel: Guias de preparacion.

Estructura funcional equivalente al formato solicitado:
- Una pestana por menu.
- Bloque administrativo por hoja.
- Tabla por preparacion con filas de ingredientes.
- Columnas por nivel: peso bruto, peso neto y peso servido.
"""

import io
from decimal import Decimal
from typing import Dict, List, Tuple

from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from principal.models import TablaGradosEscolaresUapa

from .models import (
    FirmaNutricionalContrato,
    TablaAnalisisNutricionalMenu,
    TablaIngredientesPorNivel,
    TablaMenus,
    TablaPreparacionIngredientes,
    TablaPreparaciones,
)


NIVELES_ORDEN = [
    "prescolar",
    "primaria_1_2_3",
    "primaria_4_5",
    "secundaria",
    "media_ciclo_complementario",
]

NIVELES_LABEL = {
    "prescolar": "PREESCOLAR",
    "primaria_1_2_3": "PRIMARIA: 1, 2 Y 3",
    "primaria_4_5": "PRIMARIA: 4 Y 5",
    "secundaria": "SECUNDARIA",
    "media_ciclo_complementario": "MEDIA Y CICLO COMPLEMENTARIO",
}


class GuiaPreparacionExcelGenerator:
    def __init__(self):
        side = Side(style="thin", color="000000")
        self.border = Border(left=side, right=side, top=side, bottom=side)
        self.header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        self.center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    def generate(self, programa_id: int, modalidad_id: str) -> io.BytesIO:
        menus = list(
            TablaMenus.objects.filter(
                id_contrato_id=programa_id,
                id_modalidad_id=modalidad_id,
            )
            .select_related("id_contrato", "id_modalidad")
            .order_by("menu")
        )

        wb = Workbook()
        wb.remove(wb.active)

        if not menus:
            ws = wb.create_sheet("SIN DATOS")
            ws["A1"] = "No se encontraron menus para el programa/modalidad seleccionados."
            stream = io.BytesIO()
            wb.save(stream)
            stream.seek(0)
            return stream

        for menu in menus:
            ws = wb.create_sheet(title=f"Menu {menu.menu}"[:31])
            self._build_sheet(ws, menu)

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    def _build_sheet(self, ws, menu: TablaMenus) -> None:
        self._set_columns(ws)
        self._draw_top(ws, menu)
        row = 10
        row = self._draw_table_header(ws, row)
        row_end = self._draw_table_body(ws, row, menu)
        self._draw_signature_block(ws, row_end + 2, menu)

    def _set_columns(self, ws):
        ws.column_dimensions["A"].width = 24  # preparacion
        ws.column_dimensions["B"].width = 24  # ingrediente
        for col in "CDEFGHIJKLMNOPQ":
            ws.column_dimensions[col].width = 10
        ws.column_dimensions["R"].width = 46  # procedimiento

    def _draw_top(self, ws, menu: TablaMenus):
        ws.row_dimensions[1].height = 38
        ws.row_dimensions[2].height = 38

        # Logo programa (si existe)
        try:
            if menu.id_contrato and menu.id_contrato.imagen:
                img = Image(menu.id_contrato.imagen.path)
                img.height = min(70, img.height)
                img.width = min(220, img.width)
                ws.add_image(img, "O1")
        except Exception:
            pass

        ws.merge_cells("A3:R3")
        ws["A3"] = "GUIA DE PREPARACION DE ALIMENTOS Y ESTANDARIZACION DE RECETAS"
        ws["A3"].font = Font(bold=True, size=11)
        ws["A3"].alignment = self.center
        ws["A3"].fill = self.header_fill
        ws["A3"].border = self.border

        ws.merge_cells("A4:R4")
        ws["A4"] = "COMPLEMENTO ALIMENTARIO JORNADA AM/PM PREPARADO EN SITIO"
        ws["A4"].font = Font(bold=True, size=11)
        ws["A4"].alignment = self.center
        ws["A4"].fill = self.header_fill
        ws["A4"].border = self.border

        # Fila 5 (encabezados superiores)
        ws.merge_cells("B5:D5")
        ws["B5"] = "PREESCOLAR - MEDIA Y CICLO COMPLEMENTARIO"
        ws["B5"].alignment = self.center
        ws["B5"].font = Font(bold=True)
        ws["B5"].fill = self.header_fill
        ws["B5"].border = self.border

        ws.merge_cells("E5:G5")
        ws["E5"] = "OPERADOR"
        ws["E5"].alignment = self.center
        ws["E5"].font = Font(bold=True)
        ws["E5"].fill = self.header_fill
        ws["E5"].border = self.border

        ws.merge_cells("H5:R5")
        ws["H5"] = ""
        ws["H5"].alignment = self.center
        ws["H5"].fill = self.header_fill
        ws["H5"].border = self.border

        # Fila 6
        ws["A6"] = "ESCOLARIDAD"
        ws["A6"].font = Font(bold=True)
        ws["A6"].alignment = self.center
        ws["A6"].fill = self.header_fill
        ws["A6"].border = self.border

        ws["B6"] = "INDÍGENA"
        ws["B6"].alignment = self.center
        ws["B6"].fill = self.header_fill
        ws["B6"].border = self.border

        ws["D6"] = "COMUNIDAD / PUEBLO INDÍGENA"
        ws["D6"].alignment = self.center
        ws["D6"].fill = self.header_fill
        ws["D6"].border = self.border

        ws.merge_cells("E6:G6")
        ws["E6"] = ""
        ws["E6"].alignment = self.center
        ws["E6"].fill = self.header_fill
        ws["E6"].border = self.border

        ws["H6"] = "AFROCOLOMBIANO / PALENQUEROS"
        ws["H6"].alignment = self.center
        ws["H6"].fill = self.header_fill
        ws["H6"].border = self.border

        ws.merge_cells("K6:R6")
        ws["K6"] = str(menu.id_contrato.programa).upper()
        ws["K6"].alignment = self.center
        ws["K6"].font = Font(bold=True)
        ws["K6"].fill = self.header_fill
        ws["K6"].border = self.border

        # Fila 7
        ws.merge_cells("A7:A8")
        ws["A7"] = "GRUPO ETNICO"
        ws["A7"].alignment = self.center
        ws["A7"].font = Font(bold=True)
        ws["A7"].fill = self.header_fill
        ws["A7"].border = self.border

        ws["B7"] = "RAIZAL"
        ws["B7"].alignment = self.center
        ws["B7"].fill = self.header_fill
        ws["B7"].border = self.border

        ws["D7"] = "ROM"
        ws["D7"].alignment = self.center
        ws["D7"].fill = self.header_fill
        ws["D7"].border = self.border

        ws.merge_cells("E7:G7")
        ws["E7"] = ""
        ws["E7"].alignment = self.center
        ws["E7"].fill = self.header_fill
        ws["E7"].border = self.border

        ws.merge_cells("I7:R7")
        ws["I7"] = "X"
        ws["I7"].alignment = self.center
        ws["I7"].font = Font(bold=True, size=13)
        ws["I7"].fill = self.header_fill
        ws["I7"].border = self.border

        ws["H7"] = "SIN PERTENENCIA ÉTNICA"
        ws["H7"].alignment = self.center
        ws["H7"].fill = self.header_fill
        ws["H7"].border = self.border

        ws.merge_cells("A9:R9")
        ws["A9"] = f"Menu {menu.menu}"
        ws["A9"].font = Font(bold=True)
        ws["A9"].alignment = self.center
        ws["A9"].fill = self.header_fill
        ws["A9"].border = self.border

    def _draw_table_header(self, ws, start_row: int) -> int:
        row1 = start_row
        row2 = start_row + 1

        ws.merge_cells(start_row=row1, start_column=1, end_row=row2, end_column=1)
        ws.cell(row=row1, column=1, value="PREPARACION")
        ws.cell(row=row1, column=1).font = Font(bold=True)
        ws.cell(row=row1, column=1).alignment = self.center
        ws.cell(row=row1, column=1).fill = self.header_fill

        ws.merge_cells(start_row=row1, start_column=2, end_row=row2, end_column=2)
        ws.cell(row=row1, column=2, value="NOMBRE DEL ALIMENTO\n(Ingredientes)")
        ws.cell(row=row1, column=2).font = Font(bold=True)
        ws.cell(row=row1, column=2).alignment = self.center
        ws.cell(row=row1, column=2).fill = self.header_fill

        col = 3
        for nivel_id in NIVELES_ORDEN:
            ws.merge_cells(start_row=row1, start_column=col, end_row=row1, end_column=col + 2)
            ws.cell(row=row1, column=col, value=NIVELES_LABEL[nivel_id])
            ws.cell(row=row1, column=col).font = Font(bold=True)
            ws.cell(row=row1, column=col).alignment = self.center
            ws.cell(row=row1, column=col).fill = self.header_fill

            ws.cell(row=row2, column=col, value="PESO\nBRUTO (g)")
            ws.cell(row=row2, column=col + 1, value="PESO\nNETO (g)")
            ws.cell(row=row2, column=col + 2, value="PESO\nSERVIDO (g)")
            for c in range(col, col + 3):
                ws.cell(row=row2, column=c).font = Font(bold=True, size=9)
                ws.cell(row=row2, column=c).alignment = self.center
                ws.cell(row=row2, column=c).fill = self.header_fill
            col += 3

        ws.merge_cells(start_row=row1, start_column=18, end_row=row2, end_column=18)
        ws.cell(row=row1, column=18, value="PROCEDIMIENTO DE PREPARACION")
        ws.cell(row=row1, column=18).font = Font(bold=True)
        ws.cell(row=row1, column=18).alignment = self.center
        ws.cell(row=row1, column=18).fill = self.header_fill

        for r in (row1, row2):
            for c in range(1, 19):
                ws.cell(row=r, column=c).border = self.border

        return row2 + 1

    def _draw_table_body(self, ws, start_row: int, menu: TablaMenus) -> int:
        niveles = self._get_niveles()
        preps = list(TablaPreparaciones.objects.filter(id_menu=menu).order_by("preparacion"))
        rels = list(
            TablaPreparacionIngredientes.objects.filter(id_preparacion__in=preps)
            .select_related("id_preparacion", "id_ingrediente_siesa")
            .order_by("id_preparacion__preparacion", "id_ingrediente_siesa__nombre_del_alimento")
        )

        analisis_por_nivel = {
            a.id_nivel_escolar_uapa_id: a
            for a in TablaAnalisisNutricionalMenu.objects.filter(id_menu=menu)
        }
        ings_guardados = list(
            TablaIngredientesPorNivel.objects.filter(
                id_analisis__in=list(analisis_por_nivel.values()),
                id_preparacion__in=preps,
            )
        )
        idx = self._build_index(ings_guardados)

        rels_by_prep: Dict[int, List[TablaPreparacionIngredientes]] = {}
        for rel in rels:
            rels_by_prep.setdefault(rel.id_preparacion_id, []).append(rel)

        row = start_row
        for prep in preps:
            prep_rels = rels_by_prep.get(prep.id_preparacion, [])
            if not prep_rels:
                continue

            # Peso servido por nivel = suma de netos de todos los ingredientes de la preparacion
            peso_servido_by_nivel = {}
            for nivel_id in niveles:
                total = Decimal("0")
                for rel in prep_rels:
                    _, neto = self._get_bruto_neto(rel, prep.id_preparacion, nivel_id, idx, analisis_por_nivel)
                    total += neto
                peso_servido_by_nivel[nivel_id] = total

            prep_start = row
            for rel in prep_rels:
                ws.cell(row=row, column=2, value=rel.id_ingrediente_siesa.nombre_del_alimento)
                ws.cell(row=row, column=2).alignment = self.left
                ws.cell(row=row, column=2).border = self.border

                col = 3
                for nivel_id in NIVELES_ORDEN:
                    bruto, neto = self._get_bruto_neto(rel, prep.id_preparacion, nivel_id, idx, analisis_por_nivel)
                    servido = peso_servido_by_nivel.get(nivel_id, Decimal("0"))

                    ws.cell(row=row, column=col, value=float(round(bruto, 2)))
                    ws.cell(row=row, column=col + 1, value=float(round(neto, 2)))
                    ws.cell(row=row, column=col + 2, value=float(round(servido, 2)))
                    for c in (col, col + 1, col + 2):
                        ws.cell(row=row, column=c).alignment = self.center
                        ws.cell(row=row, column=c).border = self.border
                    col += 3

                ws.cell(row=row, column=18, value="")
                ws.cell(row=row, column=18).alignment = self.left
                ws.cell(row=row, column=18).border = self.border
                row += 1

            prep_end = row - 1
            ws.merge_cells(start_row=prep_start, start_column=1, end_row=prep_end, end_column=1)
            ws.cell(row=prep_start, column=1, value=prep.preparacion.upper())
            ws.cell(row=prep_start, column=1).font = Font(bold=True)
            ws.cell(row=prep_start, column=1).alignment = self.center
            ws.cell(row=prep_start, column=1).border = self.border

            # Procedimiento en blanco pero combinado por preparacion
            ws.merge_cells(start_row=prep_start, start_column=18, end_row=prep_end, end_column=18)
            ws.cell(row=prep_start, column=18, value="")
            ws.cell(row=prep_start, column=18).alignment = self.left
            ws.cell(row=prep_start, column=18).border = self.border

            # borde columna A/T en filas internas de merge
            for r in range(prep_start, prep_end + 1):
                ws.cell(row=r, column=1).border = self.border
                ws.cell(row=r, column=18).border = self.border

        ws.freeze_panes = "C12"
        return row

    def _build_index(self, ingredientes_guardados: List[TablaIngredientesPorNivel]) -> Dict[Tuple[str, int, str], TablaIngredientesPorNivel]:
        idx = {}
        for item in ingredientes_guardados:
            nivel_id = item.id_analisis.id_nivel_escolar_uapa_id
            prep_id = item.id_preparacion_id
            codigo = str(item.codigo_icbf or item.id_ingrediente_siesa_id or "").strip()
            if not codigo:
                continue
            idx[(nivel_id, prep_id, codigo)] = item
        return idx

    def _get_niveles(self) -> List[str]:
        disponibles = set(TablaGradosEscolaresUapa.objects.values_list("id_grado_escolar_uapa", flat=True))
        return [n for n in NIVELES_ORDEN if n in disponibles]

    def _get_bruto_neto(
        self,
        rel: TablaPreparacionIngredientes,
        prep_id: int,
        nivel_id: str,
        idx: Dict[Tuple[str, int, str], TablaIngredientesPorNivel],
        analisis_por_nivel: Dict[str, TablaAnalisisNutricionalMenu],
    ) -> Tuple[Decimal, Decimal]:
        codigo = str(rel.id_ingrediente_siesa.codigo).strip()
        guardado = idx.get((nivel_id, prep_id, codigo))

        if guardado:
            neto = Decimal(guardado.peso_neto or 0)
        else:
            neto = Decimal(rel.gramaje or 0)

        parte_comestible = Decimal(rel.id_ingrediente_siesa.parte_comestible_field or 100)
        if parte_comestible <= 0:
            parte_comestible = Decimal("100")
        bruto = (neto * Decimal("100")) / parte_comestible
        return bruto, neto

    def _draw_signature_block(self, ws, start_row: int, menu: TablaMenus) -> None:
        """
        Bloque inferior de firmas usando nutricion_firma_nutricional_contrato.
        """
        ws.row_dimensions[start_row].height = 50
        ws.row_dimensions[start_row + 1].height = 50
        firma_cfg = FirmaNutricionalContrato.objects.filter(programa=menu.id_contrato).first()
        elabora_nombre = (firma_cfg.elabora_nombre if firma_cfg else "") or ""
        elabora_matricula = (firma_cfg.elabora_matricula if firma_cfg else "") or ""
        elabora_firma_texto = (firma_cfg.elabora_firma_texto if firma_cfg else "") or ""
        aprueba_nombre = (firma_cfg.aprueba_nombre if firma_cfg else "") or ""
        aprueba_matricula = (firma_cfg.aprueba_matricula if firma_cfg else "") or ""
        aprueba_firma_texto = (firma_cfg.aprueba_firma_texto if firma_cfg else "") or ""

        elabora_img = None
        aprueba_img = None
        if firma_cfg:
            try:
                elabora_img = firma_cfg.elabora_firma_imagen.path if firma_cfg.elabora_firma_imagen else None
            except Exception:
                elabora_img = None
            try:
                aprueba_img = firma_cfg.aprueba_firma_imagen.path if firma_cfg.aprueba_firma_imagen else None
            except Exception:
                aprueba_img = None

        rows = [start_row, start_row + 1]
        for r in rows:
            for c in range(1, 21):
                ws.cell(row=r, column=c).border = self.border
                ws.cell(row=r, column=c).alignment = self.center
                ws.cell(row=r, column=c).fill = self.header_fill

        # Fila 1
        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=4)
        ws.cell(row=start_row, column=1, value="NOMBRE NUTRICIONISTA - DIETISTA POR PARTE DEL OPERADOR")
        ws.cell(row=start_row, column=1).alignment = self.left
        ws.cell(row=start_row, column=1).font = Font(bold=True)

        ws.merge_cells(start_row=start_row, start_column=5, end_row=start_row, end_column=9)
        ws.cell(row=start_row, column=5, value=elabora_nombre)
        ws.cell(row=start_row, column=5).font = Font(bold=True)

        ws.merge_cells(start_row=start_row, start_column=10, end_row=start_row, end_column=12)
        ws.cell(row=start_row, column=10, value="MATRÍCULA PROFESIONAL")
        ws.cell(row=start_row, column=10).font = Font(bold=True)

        ws.merge_cells(start_row=start_row, start_column=13, end_row=start_row, end_column=14)
        ws.cell(row=start_row, column=13, value=elabora_matricula)
        ws.cell(row=start_row, column=13).font = Font(bold=True)

        ws.merge_cells(start_row=start_row, start_column=15, end_row=start_row, end_column=16)
        ws.cell(row=start_row, column=15, value="FIRMA")
        ws.cell(row=start_row, column=15).font = Font(bold=True)

        ws.merge_cells(start_row=start_row, start_column=17, end_row=start_row, end_column=20)
        if elabora_img:
            self._insert_signature_image(ws, elabora_img, f"Q{start_row}")
        else:
            ws.cell(row=start_row, column=17, value=elabora_firma_texto)
            ws.cell(row=start_row, column=17).alignment = self.left

        # Fila 2
        ws.merge_cells(start_row=start_row + 1, start_column=1, end_row=start_row + 1, end_column=4)
        ws.cell(
            row=start_row + 1,
            column=1,
            value="NOMBRE NUTRICIONISTA - DIETISTA QUE APRUEBA LA GUIA POR PARTE DEL PAE SEM"
        )
        ws.cell(row=start_row + 1, column=1).alignment = self.left
        ws.cell(row=start_row + 1, column=1).font = Font(bold=True)

        ws.merge_cells(start_row=start_row + 1, start_column=5, end_row=start_row + 1, end_column=9)
        ws.cell(row=start_row + 1, column=5, value=aprueba_nombre)
        ws.cell(row=start_row + 1, column=5).font = Font(bold=True)

        ws.merge_cells(start_row=start_row + 1, start_column=10, end_row=start_row + 1, end_column=12)
        ws.cell(row=start_row + 1, column=10, value="MATRÍCULA PROFESIONAL")
        ws.cell(row=start_row + 1, column=10).font = Font(bold=True)

        ws.merge_cells(start_row=start_row + 1, start_column=13, end_row=start_row + 1, end_column=14)
        ws.cell(row=start_row + 1, column=13, value=aprueba_matricula)
        ws.cell(row=start_row + 1, column=13).font = Font(bold=True)

        ws.merge_cells(start_row=start_row + 1, start_column=15, end_row=start_row + 1, end_column=16)
        ws.cell(row=start_row + 1, column=15, value="FIRMA")
        ws.cell(row=start_row + 1, column=15).font = Font(bold=True)

        ws.merge_cells(start_row=start_row + 1, start_column=17, end_row=start_row + 1, end_column=20)
        if aprueba_img:
            self._insert_signature_image(ws, aprueba_img, f"Q{start_row + 1}")
        else:
            ws.cell(row=start_row + 1, column=17, value=aprueba_firma_texto)
            ws.cell(row=start_row + 1, column=17).alignment = self.left

    @staticmethod
    def _insert_signature_image(ws, image_path: str, anchor_cell: str) -> None:
        if not image_path:
            return
        try:
            img = Image(image_path)
            img.width = min(img.width, 240)
            img.height = min(img.height, 70)
            ws.add_image(img, anchor_cell)
        except Exception:
            return
