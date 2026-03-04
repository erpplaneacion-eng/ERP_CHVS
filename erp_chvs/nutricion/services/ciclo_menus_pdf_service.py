import io
import re
from collections import defaultdict
from html import escape
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo

from ..models import FirmaNutricionalContrato, TablaMenus, TablaPreparaciones
from ..utils.orden_componentes import ORDEN_COMPONENTES_POR_MODALIDAD


class CicloMenusPdfService:
    """Genera PDF consolidado del ciclo de 20 menus por programa y modalidad."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.style_title = ParagraphStyle(
            "ciclo_title",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            alignment=1,
            textColor=colors.white,
            leading=13,
        )
        self.style_subtitle = ParagraphStyle(
            "ciclo_subtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            alignment=1,
            textColor=colors.white,
            leading=12,
        )
        self.style_header = ParagraphStyle(
            "ciclo_header",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            alignment=1,
            leading=10,
        )
        self.style_cell = ParagraphStyle(
            "ciclo_cell",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            alignment=1,
            leading=9,
        )
        self.style_left = ParagraphStyle(
            "ciclo_left",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            alignment=0,
            leading=10,
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

    def _build_top_block(self, programa: Programa, modalidad: ModalidadesDeConsumo) -> List:
        elements: List = []

        logo_cell = ""
        if programa.imagen:
            try:
                logo = Image(programa.imagen.path)
                logo._restrictSize(45 * mm, 20 * mm)
                logo_cell = logo
            except Exception:
                logo_cell = self._p(programa.programa or "", self.style_left)

        top = Table(
            [[logo_cell, self._p(f"PROGRAMA: {programa.programa}", self.style_left)]],
            colWidths=[70 * mm, 180 * mm],
            hAlign="LEFT",
        )
        top.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "LEFT"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(top)

        title = Table(
            [[self._p("PLANEACION CICLO DE MENUS", self.style_title)]],
            colWidths=[250 * mm],
            hAlign="LEFT",
        )
        title.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(title)

        subtitle = Table(
            [[self._p(f"ANEXO - {modalidad.modalidad}", self.style_subtitle)]],
            colWidths=[250 * mm],
            hAlign="LEFT",
        )
        subtitle.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#7f7f7f")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(subtitle)

        meta_rows = [
            [self._p("OPERADOR", self.style_left), self._p(programa.programa or "N/A", self.style_cell)],
            [self._p("DEPARTAMENTO", self.style_left), self._p("VALLE DEL CAUCA", self.style_cell)],
            [self._p("MUNICIPIO", self.style_left), self._p(programa.municipio.nombre_municipio if programa.municipio else "N/A", self.style_cell)],
            [self._p("CONTRATO", self.style_left), self._p(programa.contrato or "N/A", self.style_cell)],
        ]
        meta = Table(meta_rows, colWidths=[55 * mm, 195 * mm], hAlign="LEFT")
        meta.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#d9d9d9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(meta)
        elements.append(Spacer(1, 3 * mm))
        return elements

    def _build_week_table(
        self,
        week_num: int,
        menus_by_number: Dict[int, TablaMenus],
        prep_map: Dict[int, Dict[str, List[str]]],
        ordered_components: List[Tuple[str, str]],
    ) -> Table:
        week_label = Table(
            [[self._p(f"SEMANA No. {week_num}", self.style_header)]],
            colWidths=[250 * mm],
            hAlign="LEFT",
        )
        week_label.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#bfbfbf")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        start = (week_num - 1) * 5 + 1
        menu_numbers = list(range(start, start + 5))
        data: List[List[Paragraph]] = [[self._p("COMPONENTES", self.style_header)]]
        data[0].extend([self._p(f"MENU No. {n}", self.style_header) for n in menu_numbers])

        for comp_id, comp_name in ordered_components:
            values_by_menu: List[List[str]] = []
            max_rows = 1
            for n in menu_numbers:
                menu_obj = menus_by_number.get(n)
                if not menu_obj:
                    cell_values = ["PENDIENTE"]
                else:
                    comp_preps = prep_map.get(n, {}).get(comp_id, [])
                    cell_values = comp_preps if comp_preps else ["N/A"]
                values_by_menu.append(cell_values)
                max_rows = max(max_rows, len(cell_values))

            for i in range(max_rows):
                row = [self._p(comp_name if i == 0 else "", self.style_left)]
                for values in values_by_menu:
                    row.append(self._p(values[i] if i < len(values) else "", self.style_cell))
                data.append(row)

        table = Table(
            data,
            colWidths=[50 * mm, 40 * mm, 40 * mm, 40 * mm, 40 * mm, 40 * mm],
            hAlign="LEFT",
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
                    ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#d9d9d9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        wrapper = Table([[week_label], [table]], colWidths=[250 * mm], hAlign="LEFT")
        wrapper.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return wrapper

    def _build_signature_table(self, programa: Programa) -> Table:
        firma = FirmaNutricionalContrato.objects.filter(programa=programa).first()
        elabora_nombre = (firma.elabora_nombre if firma else "") or "N/A"
        elabora_matricula = (firma.elabora_matricula if firma else "") or "N/A"
        aprueba_nombre = (firma.aprueba_nombre if firma else "") or "N/A"
        aprueba_matricula = (firma.aprueba_matricula if firma else "") or "N/A"

        rows = [
            [self._p("NOMBRE NUTRICIONISTA - DIETISTA DEL OPERADOR", self.style_left), self._p(elabora_nombre, self.style_cell)],
            [self._p("MATRICULA PROFESIONAL", self.style_left), self._p(elabora_matricula, self.style_cell)],
            [self._p("NOMBRE NUTRICIONISTA - DIETISTA QUE PLANEA EL CICLO", self.style_left), self._p(aprueba_nombre, self.style_cell)],
            [self._p("MATRICULA PROFESIONAL", self.style_left), self._p(aprueba_matricula, self.style_cell)],
        ]
        table = Table(rows, colWidths=[130 * mm, 120 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f1e5")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table

    def generate(self, programa_id: int, modalidad_id: str) -> io.BytesIO:
        programa = Programa.objects.select_related("municipio").get(id=programa_id)
        modalidad = ModalidadesDeConsumo.objects.get(id_modalidades=modalidad_id)

        menus = list(
            TablaMenus.objects.filter(id_contrato_id=programa_id, id_modalidad_id=modalidad_id)
            .select_related("id_modalidad", "id_contrato")
        )
        menus_by_number: Dict[int, TablaMenus] = {}
        for m in menus:
            n = self._menu_number(m.menu)
            if n and 1 <= n <= 20:
                menus_by_number[n] = m

        prep_rows = (
            TablaPreparaciones.objects.filter(id_menu__in=list(menus_by_number.values()))
            .select_related("id_componente", "id_menu")
            .order_by("preparacion")
        )

        prep_map: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        seen_components: Dict[str, str] = {}
        for prep in prep_rows:
            menu_n = self._menu_number(prep.id_menu.menu)
            if not menu_n:
                continue
            comp_id = str(prep.id_componente_id or "sin_componente")
            comp_name = (prep.id_componente.componente if prep.id_componente else "SIN COMPONENTE").upper()
            prep_map[menu_n][comp_id].append((prep.preparacion or "").upper())
            seen_components[comp_id] = comp_name

        ordered_ids = ORDEN_COMPONENTES_POR_MODALIDAD.get(str(modalidad_id), [])
        ordered_components: List[Tuple[str, str]] = []
        for comp_id in ordered_ids:
            ordered_components.append((comp_id, seen_components.get(comp_id, comp_id.upper())))
        for comp_id in sorted(k for k in seen_components.keys() if k not in ordered_ids):
            ordered_components.append((comp_id, seen_components[comp_id]))

        if not ordered_components:
            ordered_components = [("sin_componente", "SIN COMPONENTE")]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=8 * mm,
            bottomMargin=8 * mm,
        )

        elements: List = []
        elements.extend(self._build_top_block(programa, modalidad))
        for week in range(1, 5):
            elements.append(self._build_week_table(week, menus_by_number, prep_map, ordered_components))
            elements.append(Spacer(1, 2 * mm))
        elements.append(self._build_signature_table(programa))
        doc.build(elements)
        buffer.seek(0)
        return buffer
