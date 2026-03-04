import io
import re
from collections import defaultdict
from html import escape
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepInFrame, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo

from ..models import FirmaNutricionalContrato, TablaMenus, TablaPreparaciones


COMPONENTES_PDF_POR_MODALIDAD = {
    "20501": [
        ("com1", "BEBIDA CON LECHE"),
        ("com2", "ALIMENTO PROTEICO"),
        ("com3", "CEREAL ACOMPANANTE"),
        ("com4", "FRUTA"),
    ],
    "20507": [
        ("com1", "BEBIDA CON LECHE"),
        ("com2", "ALIMENTO PROTEICO"),
        ("com3", "CEREAL ACOMPANANTE"),
        ("com4", "FRUTA"),
    ],
    "20503": [
        ("com14", "BEBIDA"),
        ("com2", "ALIMENTO PROTEICO"),
        ("com3", "CEREAL ACOMPANANTE"),
        ("com8", "TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL"),
        ("com9", "COM9"),
    ],
    "20502": [
        ("com11", "LECHE Y PRODUCTOS LACTEOS"),
        ("com7", "CEREALES"),
        ("com4", "FRUTA"),
    ],
}


class CicloMenusPdfService:
    """Genera PDF de ciclo de menus (1-20) en una hoja vertical carta."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.style_title = ParagraphStyle(
            "ciclo_title",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            alignment=1,
            textColor=colors.white,
            leading=9.0,
        )
        self.style_subtitle = ParagraphStyle(
            "ciclo_subtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.6,
            alignment=1,
            textColor=colors.white,
            leading=8.5,
        )
        self.style_header = ParagraphStyle(
            "ciclo_header",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.3,
            alignment=1,
            leading=7.1,
        )
        self.style_cell_center = ParagraphStyle(
            "ciclo_cell_center",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=6.0,
            alignment=1,
            leading=6.8,
        )
        self.style_cell_left = ParagraphStyle(
            "ciclo_cell_left",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.0,
            alignment=0,
            leading=6.8,
        )

    @staticmethod
    def _menu_number(menu_text: str) -> Optional[int]:
        match = re.fullmatch(r"\s*(\d+)\s*", str(menu_text or ""))
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _p(text: str, style: ParagraphStyle) -> Paragraph:
        return Paragraph(escape(text or ""), style)

    def _componentes_por_modalidad(self, modalidad_id: str, seen_components: Dict[str, str]) -> List[Tuple[str, str]]:
        modalidad_key = str(modalidad_id or "")
        configured = COMPONENTES_PDF_POR_MODALIDAD.get(modalidad_key, [])
        if configured:
            resolved = []
            for comp_id, comp_label in configured:
                resolved.append((comp_id, seen_components.get(comp_id, comp_label)))
            return resolved
        # Fallback defensivo para modalidades no especificadas.
        return sorted([(cid, cname) for cid, cname in seen_components.items()], key=lambda x: x[1])

    def _build_top_block(self, programa: Programa, modalidad: ModalidadesDeConsumo) -> List:
        items: List = []

        logo_cell = ""
        if programa.imagen:
            try:
                logo = Image(programa.imagen.path)
                logo._restrictSize(28 * mm, 12 * mm)
                logo_cell = logo
            except Exception:
                logo_cell = self._p(programa.programa or "", self.style_cell_left)

        head = Table(
            [[logo_cell, self._p("PLANEACION CICLO DE MENUS", self.style_title)]],
            colWidths=[36 * mm, 146 * mm],
            hAlign="LEFT",
        )
        head.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                    ("BACKGROUND", (1, 0), (1, 0), colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        items.append(head)

        sub = Table(
            [[self._p(f"ANEXO - {modalidad.modalidad}", self.style_subtitle)]],
            colWidths=[182 * mm],
            hAlign="LEFT",
        )
        sub.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#6f6f6f")),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        items.append(sub)

        meta_data = [
            [self._p("OPERADOR", self.style_cell_left), self._p(programa.programa or "N/A", self.style_cell_center)],
            [self._p("DEPARTAMENTO", self.style_cell_left), self._p("VALLE DEL CAUCA", self.style_cell_center)],
            [self._p("MUNICIPIO", self.style_cell_left), self._p(programa.municipio.nombre_municipio if programa.municipio else "N/A", self.style_cell_center)],
            [self._p("CONTRATO", self.style_cell_left), self._p(programa.contrato or "N/A", self.style_cell_center)],
        ]
        meta = Table(meta_data, colWidths=[40 * mm, 142 * mm], hAlign="LEFT")
        meta.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#d9d9d9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        items.append(meta)
        items.append(Spacer(1, 1.2 * mm))
        return items

    def _build_week_rows(
        self,
        week_num: int,
        menus_by_number: Dict[int, TablaMenus],
        menu_component_preps: Dict[int, Dict[str, List[str]]],
        ordered_components: List[Tuple[str, str]],
    ) -> Tuple[List[List[Paragraph]], List[Tuple[int, int, int, int]]]:
        start_menu = (week_num - 1) * 5 + 1
        menu_nums = list(range(start_menu, start_menu + 5))

        rows: List[List[Paragraph]] = []
        spans: List[Tuple[int, int, int, int]] = []

        rows.append([self._p(f"SEMANA No. {week_num}", self.style_header)] + ["", "", "", "", ""])
        spans.append((0, 0, 5, 0))

        rows.append(
            [
                self._p("COMPONENTE", self.style_header),
                self._p(f"MENU No. {menu_nums[0]}", self.style_header),
                self._p(f"MENU No. {menu_nums[1]}", self.style_header),
                self._p(f"MENU No. {menu_nums[2]}", self.style_header),
                self._p(f"MENU No. {menu_nums[3]}", self.style_header),
                self._p(f"MENU No. {menu_nums[4]}", self.style_header),
            ]
        )

        for comp_id, comp_name in ordered_components:
            per_menu_preps: List[List[str]] = []
            max_rows_for_component = 0
            has_any_prep_in_week = False

            for mn in menu_nums:
                if mn not in menus_by_number:
                    preps = []
                else:
                    preps = list(menu_component_preps.get(mn, {}).get(comp_id, []))
                if preps:
                    has_any_prep_in_week = True
                max_rows_for_component = max(max_rows_for_component, len(preps))
                per_menu_preps.append(preps)

            # Solo mostrar componentes con preparaciones en la semana.
            if not has_any_prep_in_week:
                continue

            max_rows_for_component = max(1, max_rows_for_component)
            comp_row_start = len(rows)

            for prep_idx in range(max_rows_for_component):
                row = [self._p(comp_name if prep_idx == 0 else "", self.style_cell_left)]
                for mn_index, mn in enumerate(menu_nums):
                    if mn not in menus_by_number:
                        cell_html = "PENDIENTE"
                    else:
                        preps = per_menu_preps[mn_index]
                        cell_html = preps[prep_idx] if prep_idx < len(preps) else "N/A"
                    row.append(self._p(cell_html, self.style_cell_center))
                rows.append(row)

            if max_rows_for_component > 1:
                spans.append((0, comp_row_start, 0, len(rows) - 1))

        return rows, spans

    def _build_cycle_table(
        self,
        menus_by_number: Dict[int, TablaMenus],
        menu_component_preps: Dict[int, Dict[str, List[str]]],
        ordered_components: List[Tuple[str, str]],
    ) -> Table:
        data: List[List[Paragraph]] = []
        spans: List[Tuple[int, int, int, int]] = []
        week_ranges: List[Tuple[int, int]] = []

        for week in range(1, 5):
            week_start = len(data)
            week_rows, week_spans = self._build_week_rows(
                week_num=week,
                menus_by_number=menus_by_number,
                menu_component_preps=menu_component_preps,
                ordered_components=ordered_components,
            )
            row_offset = len(data)
            data.extend(week_rows)
            week_end = len(data) - 1
            week_ranges.append((week_start, week_end))
            for x1, y1, x2, y2 in week_spans:
                spans.append((x1, y1 + row_offset, x2, y2 + row_offset))

        col_widths = [32 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm]
        table = Table(data, colWidths=col_widths, hAlign="LEFT")

        style_cmds = [
            ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]

        for week_start, week_end in week_ranges:
            style_cmds.extend(
                [
                    ("BACKGROUND", (0, week_start), (5, week_start), colors.HexColor("#bfbfbf")),
                    ("BACKGROUND", (0, week_start + 1), (5, week_start + 1), colors.HexColor("#d9d9d9")),
                ]
            )
            if week_end >= week_start + 2:
                style_cmds.append(
                    ("BACKGROUND", (0, week_start + 2), (0, week_end), colors.HexColor("#efefef"))
                )

        for x1, y1, x2, y2 in spans:
            style_cmds.append(("SPAN", (x1, y1), (x2, y2)))

        table.setStyle(TableStyle(style_cmds))
        return table

    def _build_signatures(self, programa: Programa) -> Table:
        firma = FirmaNutricionalContrato.objects.filter(programa=programa).first()
        elabora_nombre = (firma.elabora_nombre if firma else "") or "N/A"
        elabora_matricula = (firma.elabora_matricula if firma else "") or "N/A"
        aprueba_nombre = (firma.aprueba_nombre if firma else "") or "N/A"
        aprueba_matricula = (firma.aprueba_matricula if firma else "") or "N/A"

        data = [
            [self._p("NOMBRE NUTRICIONISTA - DIETISTA DEL OPERADOR", self.style_cell_left), self._p(elabora_nombre, self.style_cell_center)],
            [self._p("MATRICULA PROFESIONAL", self.style_cell_left), self._p(elabora_matricula, self.style_cell_center)],
            [self._p("NOMBRE NUTRICIONISTA - DIETISTA QUE PLANEA EL CICLO", self.style_cell_left), self._p(aprueba_nombre, self.style_cell_center)],
            [self._p("MATRICULA PROFESIONAL", self.style_cell_left), self._p(aprueba_matricula, self.style_cell_center)],
        ]
        table = Table(data, colWidths=[90 * mm, 92 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f1e5")),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return table

    def generate(self, programa_id: int, modalidad_id: str) -> io.BytesIO:
        programa = Programa.objects.select_related("municipio").get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        menus = list(
            TablaMenus.objects.filter(id_contrato_id=programa_id, id_modalidad_id=modalidad_id)
            .select_related("id_contrato", "id_modalidad")
        )

        menus_by_number: Dict[int, TablaMenus] = {}
        for menu in menus:
            num = self._menu_number(menu.menu)
            if num and 1 <= num <= 20:
                menus_by_number[num] = menu

        prep_rows = list(
            TablaPreparaciones.objects.filter(id_menu__in=list(menus_by_number.values()))
            .select_related("id_componente", "id_menu")
            .order_by("preparacion")
        )

        menu_component_preps: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        seen_components: Dict[str, str] = {}
        for prep in prep_rows:
            num = self._menu_number(prep.id_menu.menu)
            if not num:
                continue
            comp_id = str(prep.id_componente_id or "sin_componente")
            comp_name = (prep.id_componente.componente if prep.id_componente else "SIN COMPONENTE").upper()
            prep_name = (prep.preparacion or "").upper()
            menu_component_preps[num][comp_id].append(prep_name)
            seen_components[comp_id] = comp_name

        for menu_data in menu_component_preps.values():
            for comp_id, prep_list in list(menu_data.items()):
                menu_data[comp_id] = sorted(set(prep_list))

        ordered_components = self._componentes_por_modalidad(modalidad_id, seen_components)
        if not ordered_components:
            ordered_components = [("sin_componente", "SIN COMPONENTE")]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=7 * mm,
            rightMargin=7 * mm,
            topMargin=6 * mm,
            bottomMargin=6 * mm,
        )

        content: List = []
        content.extend(self._build_top_block(programa, modalidad))
        content.append(self._build_cycle_table(menus_by_number, menu_component_preps, ordered_components))
        content.append(Spacer(1, 1.1 * mm))
        content.append(self._build_signatures(programa))

        fit = KeepInFrame(doc.width, doc.height, content, mode="shrink")
        doc.build([fit])
        buffer.seek(0)
        return buffer
