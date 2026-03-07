import io
import re
import unicodedata
import urllib.request
from collections import defaultdict
from html import escape
from typing import Dict, List, Optional, Tuple, Set

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepInFrame, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rapidfuzz import fuzz

from planeacion.models import Programa
from principal.models import ModalidadesDeConsumo

from ..models import FirmaNutricionalContrato, TablaMenus, TablaPreparaciones


def _get_rl_image(field):
    """
    Retorna fuente de imagen compatible con ReportLab Image desde un Django FieldFile.
    - Dev (almacenamiento local): retorna path string.
    - Prod (Cloudinary): descarga la URL y retorna BytesIO.
    Retorna None si el campo está vacío o todo falla.
    """
    if not field:
        return None
    try:
        return field.path
    except (FileNotFoundError, ValueError, NotImplementedError):
        pass
    try:
        url = field.url
        with urllib.request.urlopen(url) as resp:
            data = io.BytesIO(resp.read())
        data.seek(0)
        return data
    except Exception:
        return None


# Mapeos para municipios genéricos (Yumbo, Buga, etc.)
COMPONENTES_PDF_YUMBO = {
    "20501": [
        (["com11", "com1"], "BEBIDA CON LECHE"),
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREAL ACOMPAÑANTE"),
        (["com12"], "FRUTA"),
        (["com15"], "AGUA"),
    ],
    "20507": [
        (["com11", "com1"], "BEBIDA CON LECHE"),
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREAL ACOMPAÑANTE"),
        (["com12"], "FRUTA"),
        (["com15"], "AGUA"),
    ],
    "20503": [
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREALES"),
        (["com8"], "TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL"),
        (["com9"], "ENSALADA O VERDURA CALIENTE"),
        (["com14"], "BEBIDA"),
        (["com11"], "LECHE Y PRODUCTOS LACTEOS"),
        (["com15"], "AGUA"),
    ],
    "20502": [
        (["com11"], "LECHE Y PRODUCTOS LACTEOS"),
        (["com3", "com7"], "CEREA ACOMPAÑANTE"),
        (["com13"], "DULCE O POSTRE"),
        (["com12"], "FRUTA"),
    ],
    "020511": [
        (["com18"], "LACTEOS O JUGOS"),
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREAL ACOMPAÑANTE"),
        (["com13", "com12"], "FRUTA O POSTRE"),
    ],
    "20510": [
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREALES"),
        (["com8"], "TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL"),
        (["com9"], "ENSALADA O VERDURAS CALIENTES"),
        (["com14"], "BEBIDA"),
    ],
}

# Mapeos para Cali
COMPONENTES_PDF_CALI = {
    "20501": [
        (["com11", "com1"], "BEBIDA(LACTEOS)"),
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREAL ACOMPAÑANTE"),
        (["com9", "com12"], "FRUTA"),
    ],
    "20507": [
        (["com11", "com1"], "BEBIDA(LACTEOS)"),
        (["com2"], "ALIMENTO PROTEICO"),
        (["com3", "com7"], "CEREAL ACOMPAÑANTE"),
        (["com9", "com12"], "FRUTA"),
    ],
    "20502": [
        (["com11", "com1"], "LACTEOS"),
        (["com3", "com7"], "DERIVADO DE CEREAL"),
        (["com12"], "FRUTA"),
        (["com13"], "FRUTOS SECOS"),
    ],
    "20503": [
        (["com14"], "BEBIDA"),
        (["com2_proteina"], "ALIMENTO PROTEICO"),  # Split especial de com2
        (["com2_leguminosa"], "LEGUMINOSA"),       # Split especial de com2
        (["com3", "com7"], "CEREAL ACOMPAÑANTE"),
        (["com8"], "TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL"),
        (["com9"], "VERDURA FRIA O CALIENTE"),
        (["com15"], "AGUA"),
    ],
}

RANGOS_PESOS_YUMBO = {
    "20503": {
        "ALIMENTO PROTEICO": "15g-120g",
        "CEREALES": "55g-140g",
        "TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL": "40g-130g",
        "ENSALADA O VERDURA CALIENTE": "50g-90g",
        "BEBIDA": "200cc-220cc",
        "LECHE Y PRODUCTOS LACTEOS": "10g-45g",
        "AGUA": "100cc",
    },
    "20510": {
        "ALIMENTO PROTEICO": "35g",
        "CEREALES": "55g-140g",
        "TUBERCULOS, RAICES, PLATANOS Y DERIVADOS DE CEREAL": "40g-130g",
        "ENSALADA O VERDURAS CALIENTES": "50g-60g",
        "BEBIDA": "200cc-220cc",
    },
    "20501": {
        "BEBIDA CON LECHE": "200cc-200cc",
        "ALIMENTO PROTEICO": "15g-60g",
        "CEREAL ACOMPAÑANTE": "7g-140g",
        "FRUTA": "80g-135g",
        "AGUA": "100cc",
    },
    "020511": {
        "LACTEOS O JUGOS": "200cc",
        "ALIMENTO PROTEICO": "15g-20g",
        "CEREAL ACOMPAÑANTE": "14g-70g",
        "FRUTA O POSTRE": "10g-100g",
    },
    "20502": {
        "LECHE Y PRODUCTOS LACTEOS": "200cc",
        "CEREA ACOMPAÑANTE": "40g-110g",
        "FRUTA": "100g",
        "DULCE O POSTRE": "10g-25g",
    }
}


class CicloMenusPdfService:
    """Genera PDF de ciclo de menus (1-20) en una hoja vertical carta."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.style_title = ParagraphStyle(
            "ciclo_title",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.5,
            alignment=1,
            textColor=colors.white,
            leading=7.5,
        )
        self.style_subtitle = ParagraphStyle(
            "ciclo_subtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.0,
            alignment=1,
            textColor=colors.white,
            leading=7.0,
        )
        self.style_header = ParagraphStyle(
            "ciclo_header",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=5.0,
            alignment=1,
            leading=5.8,
        )
        self.style_cell_center = ParagraphStyle(
            "ciclo_cell_center",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=4.8,
            alignment=1,
            leading=5.5,
        )
        self.style_cell_left = ParagraphStyle(
            "ciclo_cell_left",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=4.8,
            alignment=0,
            leading=5.5,
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

    def _es_leguminosa(self, prep_name: str) -> bool:
        """Determina si una preparación es una leguminosa basándose en palabras clave usando fuzzy matching."""
        if not prep_name:
            return False
        
        # Normalizar: minúsculas, sin acentos
        nfkd_form = unicodedata.normalize('NFKD', prep_name.lower())
        norm_name = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
        
        keywords = ['arveja', 'lenteja', 'frijol', 'blanquillo']
        
        # Primero intentar coincidencia exacta para mayor rapidez
        for kw in keywords:
            if kw in norm_name:
                return True
                
        # Si no hay coincidencia exacta, intentar Fuzzy Matching (tolerancia a errores)
        for kw in keywords:
            score = fuzz.partial_ratio(kw, norm_name)
            if score >= 80:  # 80% de similitud es un buen umbral para palabras parecidas
                return True
                
        return False


    def _build_top_block(self, programa: Programa, modalidad: ModalidadesDeConsumo) -> List:
        items: List = []
        is_cali = programa.municipio and "cali" in programa.municipio.nombre_municipio.lower()

        logo_cell = ""
        if programa.imagen:
            src = _get_rl_image(programa.imagen)
            if src is not None:
                try:
                    logo = Image(src)
                    logo._restrictSize(28 * mm, 12 * mm)
                    logo_cell = logo
                except Exception:
                    logo_cell = self._p(programa.programa or "", self.style_cell_left)
            else:
                logo_cell = self._p(programa.programa or "", self.style_cell_left)

        if is_cali:
            # Fila 1: Logo
            head = Table([[logo_cell]], colWidths=[182 * mm], hAlign="LEFT")
            head.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            items.append(head)

            # Fila 2: Título
            title = Table([[self._p("PLANEACION CICLO DE MENUS - Resolución 335 de 2021 - SED PAE CALI", self.style_title)]], colWidths=[182 * mm], hAlign="LEFT")
            title.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            items.append(title)

            # Fila 3: Anexo
            mod_id = str(modalidad.id_modalidades)
            if mod_id == "20503":
                anexo_text = "8.3-JORNADA UNICA"
            elif mod_id == "20502":
                anexo_text = "8.4-COMPLEMENTO RACION INDUSTRIALIZADA"
            elif mod_id == "20507":
                anexo_text = "8.2-COMPLEMENTO PREPARADO EN SITIO JORNADA PM"
            elif mod_id == "20501":
                anexo_text = "8.1-COMPLEMENTO PREPARADO EN SITIO JORNADA AM"
            else:
                anexo_text = modalidad.modalidad

            sub = Table([[self._p(f"ANEXO - {anexo_text}", self.style_subtitle)]], colWidths=[182 * mm], hAlign="LEFT")
            sub.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#6f6f6f")),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            items.append(sub)

            # Filas 4 a 9: Metadatos y tabla de Grupos Étnicos
            col_widths = [26 * mm, 46 * mm, 30 * mm, 30 * mm, 50 * mm]

            meta_data = [
                # Row 4 (índice 0): OPERADOR
                [self._p("OPERADOR", self.style_cell_left), self._p(programa.programa or "N/A", self.style_cell_center), "", "", ""],
                # Row 5 (índice 1): DEPARTAMENTO / MUNICIPIO
                [self._p("DEPARTAMENTO", self.style_cell_left), self._p("VALLE DEL CAUCA", self.style_cell_center), self._p("MUNICIPIO", self.style_cell_left), self._p("CALI", self.style_cell_center), ""],
                # Row 6 (índice 2): Grupo Étnico 1
                [self._p("GRUPO ETNICO", self.style_cell_left), self._p("RAIZAL", self.style_cell_left), "", self._p("ROM", self.style_cell_left), ""],
                # Row 7 (índice 3): Grupo Étnico 2
                ["", self._p("SIN PERTENENCIA ETNICA", self.style_cell_left), "", self._p("INDIGENA", self.style_cell_left), ""],
                # Row 8 (índice 4): Grupo Étnico 3
                ["", self._p("COMUNIDAD/PUEBLO INDIGENA", self.style_cell_left), "", "", ""],
                # Row 9 (índice 5): Establecimiento Educativo
                [self._p("ESTABLECIMIENTO EDUCATIVO", self.style_cell_left), "", "", "", ""]
            ]

            meta = Table(meta_data, colWidths=col_widths, hAlign="LEFT")
            meta.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                
                # Fila 4: OPERADOR
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#d9d9d9")),
                ("SPAN", (1, 0), (4, 0)),
                
                # Fila 5: DEPARTAMENTO / MUNICIPIO
                ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#d9d9d9")),
                ("BACKGROUND", (2, 1), (2, 1), colors.HexColor("#d9d9d9")),
                ("SPAN", (3, 1), (4, 1)),
                
                # Filas 6, 7, 8: GRUPO ETNICO
                ("BACKGROUND", (0, 2), (0, 4), colors.HexColor("#d9d9d9")),
                ("SPAN", (0, 2), (0, 4)),
                ("SPAN", (3, 4), (4, 4)), # Merge empty cells below INDIGENA
                
                # Fila 9: ESTABLECIMIENTO EDUCATIVO
                ("BACKGROUND", (0, 5), (1, 5), colors.HexColor("#d9d9d9")),
                ("SPAN", (0, 5), (1, 5)), # Merge label
                ("SPAN", (2, 5), (4, 5)), # Merge input
            ]))
            items.append(meta)

        else:
            # Título pequeño centrado arriba
            title_table = Table([[self._p("REPORTE CICLOS MENU", self.style_title)]], colWidths=[182 * mm], hAlign="CENTER")
            # Cambiamos un poco el estilo del título para que no tenga fondo negro, según descripción
            title_style = ParagraphStyle(
                "yumbo_title",
                parent=getSampleStyleSheet()["Normal"],
                fontName="Helvetica-Bold",
                fontSize=5.5,
                alignment=1, # Centrado
                textColor=colors.black,
            )
            title_table = Table([[Paragraph("REPORTE CICLOS MENU", title_style)]], colWidths=[182 * mm], hAlign="CENTER")
            items.append(title_table)
            items.append(Spacer(1, 2 * mm))

            # Fila del logo (alineado a la derecha)
            logo_row = Table([["", logo_cell]], colWidths=[146 * mm, 36 * mm], hAlign="RIGHT")
            # Sin bordes para el logo
            items.append(logo_row)
            items.append(Spacer(1, 2 * mm))

            # Determinar "Modalidad de Atención" y "Tipo de Complemento"
            mod_texto = modalidad.modalidad.upper()
            if "INDUSTRIALIZADA" in mod_texto:
                mod_atencion = "RACIÓN INDUSTRIALIZADA"
            else:
                mod_atencion = "PREPARADA EN SITIO"

            mod_id = str(modalidad.id_modalidades)
            if mod_id == "20503":
                tipo_complemento = "ALMUERZO"
            elif mod_id == "20510":
                tipo_complemento = "REFUERZO COMPLEMENTO"
            elif mod_id == "20501":
                tipo_complemento = "COMPLEMENTO JM/JT"
            elif mod_id == "020511":
                tipo_complemento = "REFUERZO DEL COMPLEMENTO"
            elif mod_id == "20502":
                tipo_complemento = "COMPLEMENTO GJM/JT"
            else:
                tipo_complemento = mod_texto

            # Metadatos (8 filas divididas en dos bloques)
            # Columna izquierda: Etiqueta (ancho ~60mm), Columna derecha: Valor (ancho ~122mm)
            municipio_val = programa.municipio.nombre_municipio.upper() if programa.municipio else "N/A"
            
            meta_data = [
                [self._p("ENTIDAD TERRITORIAL", self.style_cell_left), self._p(municipio_val, self.style_cell_center)],
                [self._p("MUNICIPIO", self.style_cell_left), self._p(municipio_val, self.style_cell_center)],
                [self._p("SEDE EDUCATIVA", self.style_cell_left), ""],
                [self._p("OPERADOR", self.style_cell_left), self._p(programa.programa or "N/A", self.style_cell_center)],
                [self._p("MINUTA ENFOQUE ETNICO", self.style_cell_left), self._p("NO", self.style_cell_center)],
                [self._p("GRUPO ETNICO", self.style_cell_left), self._p("SIN PERTENENCIA ETNICA", self.style_cell_center)],
                [self._p("MODALIDAD DE ATENCION", self.style_cell_left), self._p(mod_atencion, self.style_cell_center)],
                [self._p("TIPO DE COMPLEMENTO", self.style_cell_left), self._p(tipo_complemento, self.style_cell_center)],
            ]

            meta = Table(meta_data, colWidths=[60 * mm, 122 * mm], hAlign="LEFT")
            meta.setStyle(
                TableStyle(
                    [
                        # Bordes SOLO para la columna de la derecha (índice 1)
                        ("BOX", (1, 0), (1, -1), 0.8, colors.black),
                        ("INNERGRID", (1, 0), (1, -1), 0.5, colors.black),
                        
                        # Fondo solo para la columna de etiquetas (índice 0)
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f1e5")),
                        
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
        ordered_components: List[Tuple[str, str, List[str]]],
        include_ranges: bool = False,
        modalidad_id: str = "",
    ) -> Tuple[List[List[Paragraph]], List[Tuple[int, int, int, int]]]:
        start_menu = (week_num - 1) * 5 + 1
        menu_nums = list(range(start_menu, start_menu + 5))

        rows: List[List[Paragraph]] = []
        spans: List[Tuple[int, int, int, int]] = []

        if include_ranges:
            rows.append([self._p(f"SEMANA No. {week_num}", self.style_header)] + ["", "", "", "", "", ""])
            spans.append((0, 0, 6, 0))
            rows.append(
                [
                    self._p("COMPONENTE", self.style_header),
                    self._p("RANGOS DE PESOS AL SEVIR RACION SERVIDA", self.style_header),
                    self._p(f"MENU No. {menu_nums[0]}", self.style_header),
                    self._p(f"MENU No. {menu_nums[1]}", self.style_header),
                    self._p(f"MENU No. {menu_nums[2]}", self.style_header),
                    self._p(f"MENU No. {menu_nums[3]}", self.style_header),
                    self._p(f"MENU No. {menu_nums[4]}", self.style_header),
                ]
            )
        else:
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

        for comp_group_id, comp_name, comp_ids_to_merge in ordered_components:
            per_menu_preps: List[List[str]] = []
            max_rows_for_component = 0
            has_any_prep_in_week = False

            for mn in menu_nums:
                if mn not in menus_by_number:
                    preps = []
                else:
                    # Agrupar las preparaciones de los componentes mapeados a esta fila
                    preps = []
                    for c_id in comp_ids_to_merge:
                        preps.extend(menu_component_preps.get(mn, {}).get(c_id, []))
                    # Remover duplicados manteniendo el orden
                    preps = list(dict.fromkeys(preps))
                    
                if preps:
                    has_any_prep_in_week = True
                max_rows_for_component = max(max_rows_for_component, len(preps))
                per_menu_preps.append(preps)

            # Siempre mostrar la fila si está en el mapeo, aunque no haya preps
            # (para mantener estructura uniforme)
            max_rows_for_component = max(1, max_rows_for_component)
            comp_row_start = len(rows)

            rango_texto = ""
            if include_ranges and str(modalidad_id) in RANGOS_PESOS_YUMBO:
                rango_texto = RANGOS_PESOS_YUMBO[str(modalidad_id)].get(comp_name, "")

            for prep_idx in range(max_rows_for_component):
                row = [self._p(comp_name if prep_idx == 0 else "", self.style_cell_left)]
                if include_ranges:
                    row.append(self._p(rango_texto if prep_idx == 0 else "", self.style_cell_center))
                    
                for mn_index, mn in enumerate(menu_nums):
                    if mn not in menus_by_number:
                        cell_html = "PENDIENTE"
                    else:
                        preps = per_menu_preps[mn_index]
                        cell_html = preps[prep_idx] if prep_idx < len(preps) else "N/A"
                    row.append(self._p(cell_html, self.style_cell_center))
                rows.append(row)

            if max_rows_for_component > 1:
                # El componente (y el rango si existe) hacen span vertical
                if include_ranges:
                    spans.append((0, comp_row_start, 0, len(rows) - 1))
                    spans.append((1, comp_row_start, 1, len(rows) - 1))
                else:
                    spans.append((0, comp_row_start, 0, len(rows) - 1))

        return rows, spans

    def _build_cycle_table(
        self,
        menus_by_number: Dict[int, TablaMenus],
        menu_component_preps: Dict[int, Dict[str, List[str]]],
        ordered_components: List[Tuple[str, str, List[str]]],
        include_ranges: bool = False,
        modalidad_id: str = "",
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
                include_ranges=include_ranges,
                modalidad_id=modalidad_id,
            )
            row_offset = len(data)
            data.extend(week_rows)
            week_end = len(data) - 1
            week_ranges.append((week_start, week_end))
            for x1, y1, x2, y2 in week_spans:
                spans.append((x1, y1 + row_offset, x2, y2 + row_offset))

        if include_ranges:
            col_widths = [26 * mm, 26 * mm, 26 * mm, 26 * mm, 26 * mm, 26 * mm, 26 * mm]
        else:
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
            if include_ranges:
                style_cmds.extend(
                    [
                        ("BACKGROUND", (0, week_start), (6, week_start), colors.HexColor("#bfbfbf")),
                        ("BACKGROUND", (0, week_start + 1), (6, week_start + 1), colors.HexColor("#d9d9d9")),
                    ]
                )
            else:
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

        elabora_img = ""
        if firma and firma.elabora_firma_imagen:
            src = _get_rl_image(firma.elabora_firma_imagen)
            if src is not None:
                try:
                    elabora_img = Image(src)
                    elabora_img._restrictSize(60 * mm, 14 * mm)
                except Exception:
                    elabora_img = ""

        aprueba_img = ""
        if firma and firma.aprueba_firma_imagen:
            src = _get_rl_image(firma.aprueba_firma_imagen)
            if src is not None:
                try:
                    aprueba_img = Image(src)
                    aprueba_img._restrictSize(60 * mm, 14 * mm)
                except Exception:
                    aprueba_img = ""

        data = [
            # Fila 1: Nombre Elabora (combina col 0-1 y col 2-3)
            [self._p("NOMBRE NUTRICIONISTA - DIETISTA DEL OPERADOR", self.style_cell_left), "", self._p(elabora_nombre, self.style_cell_center), ""],
            # Fila 2: Firma y Matrícula Elabora
            [self._p("FIRMA", self.style_cell_left), elabora_img, self._p("MATRICULA PROFESIONAL", self.style_cell_left), self._p(elabora_matricula, self.style_cell_center)],
            # Fila 3: Nombre Aprueba (combina col 0-1 y col 2-3)
            [self._p("NOMBRE NUTRICIONISTA - DIETISTA QUE PLANEA EL CICLO Y REVISA POR PARTE DE LA ETC.", self.style_cell_left), "", self._p(aprueba_nombre, self.style_cell_center), ""],
            # Fila 4: Firma y Matrícula Aprueba
            [self._p("FIRMA", self.style_cell_left), aprueba_img, self._p("MATRICULA PROFESIONAL", self.style_cell_left), self._p(aprueba_matricula, self.style_cell_center)],
        ]
        
        # Redimensionamos las columnas a un total de 182mm (20 + 62 + 50 + 50)
        table = Table(data, colWidths=[20 * mm, 62 * mm, 50 * mm, 50 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    
                    # Fondos grises para las celdas de etiquetas
                    ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#f3f1e5")), # Etiqueta Nombre Elabora
                    ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#f3f1e5")), # Etiqueta Firma Elabora
                    ("BACKGROUND", (2, 1), (2, 1), colors.HexColor("#f3f1e5")), # Etiqueta Matrícula Elabora
                    ("BACKGROUND", (0, 2), (1, 2), colors.HexColor("#f3f1e5")), # Etiqueta Nombre Aprueba
                    ("BACKGROUND", (0, 3), (0, 3), colors.HexColor("#f3f1e5")), # Etiqueta Firma Aprueba
                    ("BACKGROUND", (2, 3), (2, 3), colors.HexColor("#f3f1e5")), # Etiqueta Matrícula Aprueba

                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    
                    # Combinaciones para Fila 1
                    ("SPAN", (0, 0), (1, 0)), # Une celda Etiqueta Nombre Elabora
                    ("SPAN", (2, 0), (3, 0)), # Une celda Valor Nombre Elabora
                    
                    # Combinaciones para Fila 3
                    ("SPAN", (0, 2), (1, 2)), # Une celda Etiqueta Nombre Aprueba
                    ("SPAN", (2, 2), (3, 2)), # Une celda Valor Nombre Aprueba
                    
                    # Centrado de imágenes
                    ("ALIGN", (1, 1), (1, 1), "CENTER"),
                    ("ALIGN", (1, 3), (1, 3), "CENTER"),
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
            .prefetch_related("ingredientes")
            .order_by("preparacion")
        )

        # Preparar mapeo según municipio (Cali vs Resto)
        municipio_nombre = (programa.municipio.nombre_municipio if programa.municipio else "").upper()
        es_cali = "CALI" in municipio_nombre
        
        mapa_componentes = COMPONENTES_PDF_CALI if es_cali else COMPONENTES_PDF_YUMBO
        config_modalidad = mapa_componentes.get(str(modalidad_id), [])

        menu_component_preps: Dict[int, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        menu_g3_componentes: Dict[int, List[str]] = defaultdict(list)
        menu_g1_componentes: Dict[int, List[str]] = defaultdict(list)

        for prep in prep_rows:
            num = self._menu_number(prep.id_menu.menu)
            if not num:
                continue

            comp_id = str(prep.id_componente_id or "sin_componente")
            prep_name = (prep.preparacion or "").upper()

            # Lógica especial para Cali 20503: Separar Leguminosas de Proteínas
            if es_cali and str(modalidad_id) == "20503" and comp_id == "com2":
                if self._es_leguminosa(prep_name):
                    comp_id = "com2_leguminosa"
                else:
                    comp_id = "com2_proteina"

            # Transformar 'AGUA' a 'AGUA APTA PARA CONSUMO' en el contenido de la celda
            if prep_name == "AGUA" and comp_id == "com15":
                prep_name = "AGUA APTA PARA CONSUMO"

            menu_component_preps[num][comp_id].append(prep_name)

            ingredientes_lista = list(prep.ingredientes.all())

            # Rastrear si la preparación tiene algún ingrediente del grupo 3 (g3) - Lácteos
            tiene_g3 = any(ing.id_grupo_alimentos_id == "g3" for ing in ingredientes_lista)
            if tiene_g3:
                menu_g3_componentes[num].append(comp_id)

            # Rastrear si la preparación tiene algún ingrediente del grupo 1 (g1) - Tubérculos/Raíces/Plátanos
            tiene_g1 = any(ing.id_grupo_alimentos_id == "g1" for ing in ingredientes_lista)
            if tiene_g1:
                menu_g1_componentes[num].append(comp_id)

        # Construir mapeo comp_id → label para las lógicas de "INCLUIDO EN..."
        comp_id_to_label = {}
        for comp_ids, comp_label in config_modalidad:
            for cid in comp_ids:
                comp_id_to_label[cid] = comp_label

        # Lógica especial COM11 (Lácteos escondidos en otra preparación)
        # Aplica para Cali y Yumbo/Buga en cualquier modalidad que tenga COM11 en su config
        config_tiene_com11 = any("com11" in comp_ids for comp_ids, _ in config_modalidad)
        if config_tiene_com11:
            for num in menus_by_number.keys():
                com11_preps = menu_component_preps[num].get("com11", [])
                if not com11_preps:
                    # No hay preparación de lácteo per se, buscar si hay ingrediente G3 en otro componente
                    # Prioridad: proteico (COM2) > tubérculos (COM8) > cereales (COM3) > resto
                    _orden_prioridad_g3 = ["com2", "com2_proteina", "com2_leguminosa", "com8", "com3"]
                    g3_comps_todos = [c for c in menu_g3_componentes[num] if c != "com11"]
                    g3_comps_ordenados = sorted(
                        g3_comps_todos,
                        key=lambda c: _orden_prioridad_g3.index(c) if c in _orden_prioridad_g3 else 999
                    )
                    if g3_comps_ordenados:
                        comp_donde_esta = g3_comps_ordenados[0]
                        label = comp_id_to_label.get(comp_donde_esta, "LA PREPARACIÓN")

                        label_upper = label.upper()
                        if "TUBERCULO" in label_upper:
                            prefijo = "LOS TUBERCULOS"
                        elif "BEBIDA" in label_upper:
                            prefijo = "LA BEBIDA"
                        elif "PROTEICO" in label_upper:
                            prefijo = "EL ALIMENTO PROTEICO"
                        elif "ENSALADA" in label_upper or "VERDURA" in label_upper:
                            prefijo = "LA ENSALADA"
                        elif "CEREAL" in label_upper:
                            prefijo = "LOS CEREALES"
                        else:
                            prefijo = f"{label_upper}"

                        menu_component_preps[num]["com11"].append(f"INCLUIDO EN {prefijo}")

        # Lógica especial COM8 (Tubérculos/Raíces/Plátanos escondidos en COM2 o COM3)
        # Aplica para Cali y Yumbo/Buga en cualquier modalidad que tenga COM8 en su config
        config_tiene_com8 = any("com8" in comp_ids for comp_ids, _ in config_modalidad)
        if config_tiene_com8:
            # COM2 puede aparecer dividido en Cali 20503
            componentes_proteico = {"com2", "com2_proteina", "com2_leguminosa"}
            componentes_cereal = {"com3"}
            for num in menus_by_number.keys():
                com8_preps = menu_component_preps[num].get("com8", [])
                if not com8_preps:
                    # No hay preparación propia de tubérculos; buscar G1 dentro de COM2 o COM3
                    # Prioridad: proteico (COM2) > cereal (COM3)
                    g1_en_proteico = [c for c in menu_g1_componentes[num] if c in componentes_proteico]
                    g1_en_cereal = [c for c in menu_g1_componentes[num] if c in componentes_cereal]
                    if g1_en_proteico:
                        prefijo = "EL ALIMENTO PROTEICO"
                        menu_component_preps[num]["com8"].append(f"INCLUIDO EN {prefijo}")
                    elif g1_en_cereal:
                        prefijo = "LOS CEREALES"
                        menu_component_preps[num]["com8"].append(f"INCLUIDO EN {prefijo}")

        # Ordenar alfabéticamente dentro de cada componente-menú
        for menu_data in menu_component_preps.values():
            for c_id, prep_list in list(menu_data.items()):
                menu_data[c_id] = sorted(set(prep_list))

        # Construir la estructura ordenada para la tabla: (group_id, title, [comp_ids])
        ordered_components: List[Tuple[str, str, List[str]]] = []
        if config_modalidad:
            for idx, (comp_ids, comp_label) in enumerate(config_modalidad):
                group_id = f"group_{idx}"
                ordered_components.append((group_id, comp_label, comp_ids))
        else:
            # Fallback si no hay configuración para la modalidad
            seen_components = set()
            for menu_data in menu_component_preps.values():
                seen_components.update(menu_data.keys())
            
            # Ordenar los componentes detectados e incluirlos individualmente
            for cid in sorted(seen_components):
                ordered_components.append((cid, cid.upper(), [cid]))

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
        
        include_ranges = not es_cali
        content.append(self._build_cycle_table(menus_by_number, menu_component_preps, ordered_components, include_ranges=include_ranges, modalidad_id=str(modalidad_id)))
        
        content.append(Spacer(1, 1.1 * mm))
        content.append(self._build_signatures(programa))

        fit = KeepInFrame(doc.width, doc.height, content, mode="shrink")
        doc.build([fit])
        buffer.seek(0)
        return buffer
