from io import BytesIO
from pathlib import Path

from django.contrib.staticfiles import finders
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

VERDE_BANDA = colors.HexColor("#7FA36A")
VERDE_BANDA_SUAVE = colors.HexColor("#C8DDBA")
VERDE_DECORACION = colors.HexColor("#DDEAD2")
NEGRO = colors.HexColor("#111111")
GRIS = colors.HexColor("#5A5A5A")

MESES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

TIPO_LABELS = {
    "manipuladora": "Manipuladora de Alimentos",
    "planta": "Personal de Planta",
    "aprendiz": "Aprendiz SENA",
}

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_STATIC_REL = "calidad/images/logo.jpeg"
FIRMA_STATIC_REL = "calidad/images/firma.png"


def _resolver_static_image(static_rel_path: str) -> Path | None:
    """Resuelve un estático en dev/prod para uso de ReportLab (ruta de archivo local)."""
    found = finders.find(static_rel_path)
    if found:
        # finders.find puede devolver lista/tupla en algunos backends.
        if isinstance(found, (list, tuple)):
            if found:
                return Path(found[0])
        return Path(found)

    # Fallback explícito por si staticfiles finders no lo ubica en este entorno.
    candidate_paths = (
        BASE_DIR / "static" / static_rel_path,
        BASE_DIR / "staticfiles" / static_rel_path,
    )
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate

    return None


def _safe(value, max_len: int = 0) -> str:
    text = str(value) if value else ""
    if max_len and len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _fecha_es(fecha) -> str:
    return f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}"


def generar_certificado_calidad_pdf(certificado) -> BytesIO:
    buffer = BytesIO()
    ancho, alto = landscape(LETTER)
    c = canvas.Canvas(buffer, pagesize=landscape(LETTER))
    _dibujar_pagina(c, certificado, ancho, alto)
    c.save()
    buffer.seek(0)
    return buffer


def _dibujar_pagina(c: canvas.Canvas, cert, w: float, h: float):
    margin = 0.6 * cm
    center_x = w / 2

    c.setFillColor(colors.white)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.rect(margin, margin, w - 2 * margin, h - 2 * margin, fill=0, stroke=1)
    c.line(center_x, margin, center_x, h - margin)

    _dibujar_panel(c, cert, margin, margin, center_x - margin, h - 2 * margin, izquierdo=True)
    _dibujar_panel(c, cert, center_x, margin, w - margin - center_x, h - 2 * margin, izquierdo=False)


def _dibujar_panel(c: canvas.Canvas, cert, x: float, y: float, w: float, h: float, izquierdo: bool):
    _dibujar_fondo_panel(c, x, y, w, h)
    _dibujar_banda_superior(c, x, y, w, h)
    if izquierdo:
        _dibujar_contenido_izquierdo(c, cert, x, y, w, h)
    else:
        _dibujar_contenido_derecho(c, cert, x, y, w, h)


def _dibujar_fondo_panel(c: canvas.Canvas, x: float, y: float, w: float, h: float):
    c.setFillColor(colors.white)
    c.rect(x, y, w, h, fill=1, stroke=0)

    c.setFillColor(VERDE_DECORACION)
    c.circle(x + w * 0.90, y - h * 0.05, h * 0.18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.circle(x + w * 0.88, y - h * 0.06, h * 0.16, fill=1, stroke=0)


def _dibujar_banda_superior(c: canvas.Canvas, x: float, y: float, w: float, h: float):
    banda_h = 0.45 * cm
    top = y + h
    c.setFillColor(VERDE_BANDA_SUAVE)
    c.rect(x + 0.3 * cm, top - banda_h - 0.18 * cm, w - 0.6 * cm, banda_h, fill=1, stroke=0)
    c.setFillColor(VERDE_BANDA)
    c.rect(x + 0.3 * cm, top - 0.16 * cm, w - 0.6 * cm, 0.12 * cm, fill=1, stroke=0)


def _draw_wrapped_text(c: canvas.Canvas, text: str, x: float, y: float, width: float, leading: float):
    text_obj = c.beginText(x, y)
    text_obj.setLeading(leading)
    font_name = c._fontname
    font_size = c._fontsize

    words = (text or "").split()
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if c.stringWidth(candidate, font_name, font_size) <= width:
            current = candidate
            continue
        if current:
            text_obj.textLine(_safe(current))
        current = word

    if current:
        text_obj.textLine(_safe(current))
    c.drawText(text_obj)
    return text_obj.getY()


def _draw_justified_text(c: canvas.Canvas, text: str, x: float, y: float, width: float, leading: float):
    words = (text or "").split()
    if not words:
        return y

    font_name = c._fontname
    font_size = c._fontsize
    space_w = c.stringWidth(" ", font_name, font_size)

    lines = []
    line_words = []
    line_w = 0.0

    for word in words:
        word_w = c.stringWidth(word, font_name, font_size)
        projected = word_w if not line_words else line_w + space_w + word_w
        if projected <= width:
            line_words.append(word)
            line_w = projected
            continue
        lines.append(line_words)
        line_words = [word]
        line_w = word_w

    if line_words:
        lines.append(line_words)

    current_y = y
    for i, lw in enumerate(lines):
        is_last = i == len(lines) - 1
        if len(lw) == 1 or is_last:
            c.drawString(x, current_y, _safe(" ".join(lw)))
            current_y -= leading
            continue

        words_w = sum(c.stringWidth(wd, font_name, font_size) for wd in lw)
        gaps = len(lw) - 1
        extra = max(0.0, width - words_w)
        gap_w = extra / gaps if gaps else space_w

        cursor_x = x
        for idx, wd in enumerate(lw):
            c.drawString(cursor_x, current_y, _safe(wd))
            cursor_x += c.stringWidth(wd, font_name, font_size)
            if idx < gaps:
                cursor_x += gap_w
        current_y -= leading

    return current_y


def _dibujar_placeholder_logo(c: canvas.Canvas, x: float, y: float):
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.6)
    c.rect(x, y, 2.9 * cm, 2.1 * cm, fill=0, stroke=1)
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS)
    c.drawCentredString(x + 1.45 * cm, y + 0.9 * cm, _safe("LOGO"))


def _dibujar_imagen_ajustada(
    c: canvas.Canvas,
    image_path: Path | None,
    x: float,
    y: float,
    max_w: float,
    max_h: float,
    anchor_top: bool = False,
) -> bool:
    if not image_path or not image_path.exists():
        return False

    try:
        img = ImageReader(str(image_path))
        img_w, img_h = img.getSize()
        if not img_w or not img_h:
            return False

        scale = min(max_w / img_w, max_h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        draw_x = x + (max_w - draw_w) / 2
        draw_y = y + (max_h - draw_h) if anchor_top else y

        c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h, mask="auto")
        return True
    except Exception:
        return False


def _dibujar_contenido_izquierdo(c: canvas.Canvas, cert, x: float, y: float, w: float, h: float):
    pad = 1.0 * cm
    top_y = y + h - 1.4 * cm

    _dibujar_marca_agua_somos_q(c, x, y, w, h)

    logo_x = x + pad - 0.55 * cm
    logo_y = top_y - 1.05 * cm
    logo_path = _resolver_static_image(LOGO_STATIC_REL)
    logo_ok = _dibujar_imagen_ajustada(
        c,
        logo_path,
        logo_x,
        logo_y,
        max_w=1.95 * cm,
        max_h=1.35 * cm,
        anchor_top=True,
    )
    if not logo_ok:
        _dibujar_placeholder_logo(c, logo_x, logo_y)

    c.setFillColor(NEGRO)
    c.setFont("Times-BoldItalic", 10.5)
    c.drawCentredString(
        x + w / 2,
        top_y - 0.4 * cm,
        _safe("LA CORPORACION HACIA UN VALLE SOLIDARIO"),
    )

    intro = (
        "Identificado con NIT. 805.029.170-0 y en uso de sus facultades para capacitar y "
        "certificar el desarrollo de actividades de Manipulacion de Alimentos, de acuerdo a la "
        "Resolucion 2674 de 2013 expedido por el Ministerio de Salud y Proteccion Social"
    )
    c.setFont("Times-BoldItalic", 8.8)
    y_text = _draw_wrapped_text(c, intro, x + pad, top_y - 1.65 * cm, w - 2 * pad, 11.6)

    c.setFont("Times-BoldItalic", 9.2)
    y_text -= 0.55 * cm
    c.drawCentredString(x + w / 2, y_text, _safe("Certifica que:"))

    tipo = TIPO_LABELS.get(cert.tipo_empleado, cert.tipo_empleado)
    fecha_curso = _fecha_es(cert.fecha_emision)
    parrafo = (
        f"Que {(_safe(cert.nombre_completo)).upper()} Identificado con cédula de ciudadanía C.C. "
        f"{_safe(cert.cedula)} quien se desempeña como {(_safe(cert.cargo or tipo)).upper()} asistió a módulo del curso básico de manipulación de "
        f"alimentos realizado el día {fecha_curso} en las instalaciones de la "
        "CORPORACION HACIA UN VALLE SOLIDARIO CL 15 # 26 - 101 BG 34 COMPLEJO "
        "INDUSTRIAL Y COMERCIAL CIC 1, en el Municipio de YUMBO; de acuerdo a lo ordenado en "
        "el Articulo 12 y 13 de la Resolución 2674 de 2013 y el Decreto 3075 de 1997. Adicionalmente, "
        "el titular de esta certificación ha sido capacitado en higiene y saneamiento en el manejo de "
        "cárnicos, cadena de frío, transporte sanitario de productos cárnicos, control de temperatura, "
        "trazabilidad y prevención de contaminación cruzada, conforme a la normativa sanitaria vigente, "
        "Decreto 1500 de 2007."
    )
    c.setFont("Helvetica", 9.0)
    y_text = _draw_justified_text(c, parrafo, x + pad, y_text - 0.9 * cm, w - 2 * pad, 12.2)

    cierre_1 = "El curso se reforzara con las capacitaciones contempladas mensualmente, para la vigencia de 1 ano."
    cierre_2 = f"Para constancia de lo anterior, la presente certificacion se firma en Yumbo el {_fecha_es(cert.fecha_emision)}."
    c.setFont("Helvetica", 9.0)
    y_text = _draw_justified_text(c, cierre_1, x + pad, y_text - 0.45 * cm, w - 2 * pad, 12.2)
    _draw_justified_text(c, cierre_2, x + pad, y_text - 0.55 * cm, w - 2 * pad, 12.2)

    firma_y = y + 1.95 * cm
    firma_path = _resolver_static_image(FIRMA_STATIC_REL)
    firma_ok = _dibujar_imagen_ajustada(
        c,
        firma_path,
        x + w * 0.37,
        firma_y + 0.05 * cm,
        max_w=w * 0.26,
        max_h=1.25 * cm,
    )

    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.7)
    c.line(x + w * 0.34, firma_y, x + w * 0.66, firma_y)
    c.setFillColor(NEGRO)
    c.setFont("Helvetica", 8.3)

    if not firma_ok:
        c.setFont("Times-Italic", 12)
        c.setFillColor(colors.grey)
        c.drawCentredString(x + w * 0.5, firma_y + 0.25 * cm, _safe("Firma"))
        c.setFillColor(NEGRO)
        c.setFont("Helvetica", 8.3)

    c.drawCentredString(x + w * 0.5, firma_y - 0.35 * cm, _safe("ING. Msc. SANDRA HENAO TORO"))
    c.drawCentredString(x + w * 0.5, firma_y - 0.75 * cm, _safe("JEFE DE ASEGURAMIENTO DE CALIDAD"))
    c.drawCentredString(x + w * 0.5, firma_y - 1.15 * cm, _safe("INGENIERA DE ALIMENTOS / MP 26254-244061 VLL"))
    c.drawCentredString(x + w * 0.5, firma_y - 1.55 * cm, _safe("CORPORACION HACIA UN VALLE SOLIDARIO"))

    # Se elimina el pie de "Certificado N." por requerimiento.


def _dibujar_marca_agua_somos_q(c: canvas.Canvas, x: float, y: float, w: float, h: float):
    c.saveState()
    c.translate(x + w * 0.34, y + h * 0.20)
    c.rotate(28)

    c.setFillColor(colors.Color(0.38, 0.62, 0.38, alpha=0.10))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(0, 40, _safe("SOMOS"))

    c.setFillColor(colors.Color(0.30, 0.54, 0.30, alpha=0.14))
    c.setFont("Times-BoldItalic", 72)
    c.drawCentredString(0, -2, _safe("Q."))

    c.setStrokeColor(colors.Color(0.36, 0.60, 0.36, alpha=0.10))
    c.setLineWidth(1.6)
    c.circle(0, 8, 36, stroke=1, fill=0)
    c.restoreState()


def _dibujar_contenido_derecho(c: canvas.Canvas, cert, x: float, y: float, w: float, h: float):
    pad = 1.0 * cm
    top_y = y + h - 2.0 * cm

    c.setFillColor(NEGRO)
    c.setFont("Helvetica-Bold", 12)
    cert_id = getattr(cert, "id", None) or getattr(cert, "pk", "")
    c.drawString(x + pad, top_y, _safe(f"CERTIFICADO # {cert_id} - DEPARTAMENTO DE CALIDAD"))

    bloque_12 = (
        "Artículo 12. Educación y capacitación. Todas las personas que realizan actividades de manipulación de alimentos "
        "deben tener formación en educación sanitaria, principios básicos de Buenas Prácticas de Manufactura y prácticas "
        "higiénicas en manipulación de alimentos. Igualmente, deben estar capacitados para llevar a cabo las tareas que se "
        "les asignen o desempeñen, con el fin de que se encuentren en capacidad de adoptar las precauciones y medidas "
        "preventivas necesarias para evitar la contaminación o deterioro de los alimentos. Las empresas deben tener un "
        "plan de capacitación continuo y permanente para el personal MANIPULADOR(A) de alimentos desde el momento "
        "de su contratación y luego ser reforzado mediante charlas, cursos u otros medios efectivos de actualización. Dicho "
        "plan debe ser de por lo menos 10 horas anuales, sobre asuntos específicos de que trata la presente resolución. Esta "
        "capacitación estará bajo la responsabilidad de la empresa y podrá ser efectuada por esta, por personas naturales "
        "o jurídicas contratadas y por las autoridades sanitarias. Cuando el plan de capacitación se realice a través de "
        "personas naturales o jurídicas diferentes a la empresa, estas deben demostrar su idoneidad técnica y científica y "
        "su formación y experiencia específica en las áreas de higiene de los alimentos, Buenas Prácticas de Manufactura y "
        "sistemas preventivos de aseguramiento de la inocuidad."
    )
    c.setFont("Helvetica", 8.6)
    y_text = _draw_justified_text(c, bloque_12, x + pad, top_y - 0.8 * cm, w - 2 * pad, 12.0)

    bloque_13 = (
        "Artículo 13. Plan de capacitación. El plan de capacitación debe contener, al menos, los siguientes aspectos: "
        "Metodología, duración, docentes, cronograma y temas específicos a impartir. El enfoque, contenido y alcance de "
        "la capacitación impartida debe ser acorde con la empresa, el proceso tecnológico y tipo de establecimiento de que "
        "se trate. En todo caso, la empresa debe demostrar a través del desempeño de los operarios y la condición sanitaria "
        "del establecimiento la efectividad e impacto de la capacitación impartida. Parágrafo 1°. Para reforzar el "
        "cumplimiento de las prácticas higiénicas, se colocarán en sitios estratégicos avisos alusivos a la obligatoriedad y "
        "necesidad de su observancia durante la manipulación de alimentos. Parágrafo 2°. El MANIPULADOR(A)(A) de "
        "alimentos debe ser entrenado para comprender y manejar el control de los puntos del proceso que están bajo su "
        "responsabilidad y la importancia de su vigilancia o monitoreo; además, debe conocer los límites del punto del "
        "proceso y las acciones correctivas a tomar cuando existan desviaciones en dichos límites."
    )
    c.setFont("Helvetica", 8.6)
    _draw_justified_text(c, bloque_13, x + pad, y_text - 1.0 * cm, w - 2 * pad, 12.0)

    c.saveState()
    c.translate(x + w * 0.54, y + h * 0.35)
    c.rotate(40)
    c.setFont("Helvetica-Bold", 44)
    c.setFillColor(colors.Color(0.55, 0.72, 0.55, alpha=0.18))
    c.drawCentredString(0, 0, _safe("COPIA CONTROLADA"))
    c.restoreState()
