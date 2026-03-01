from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
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

IMAGES_DIR = Path(__file__).resolve().parent.parent / "staticfiles" / "calidad" / "images"
LOGO_PATH = IMAGES_DIR / "logo.jpeg"
FIRMA_PATH = IMAGES_DIR / "firma.png"


def _safe(value, max_len: int = 0) -> str:
    text = str(value) if value else ""
    if max_len and len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _fecha_es(fecha) -> str:
    return f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}"


def generar_certificado_calidad_pdf(certificado) -> BytesIO:
    buffer = BytesIO()
    ancho, alto = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
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


def _dibujar_placeholder_logo(c: canvas.Canvas, x: float, y: float):
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.6)
    c.rect(x, y, 2.9 * cm, 2.1 * cm, fill=0, stroke=1)
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS)
    c.drawCentredString(x + 1.45 * cm, y + 0.9 * cm, _safe("LOGO"))


def _dibujar_imagen_ajustada(
    c: canvas.Canvas,
    image_path: Path,
    x: float,
    y: float,
    max_w: float,
    max_h: float,
    anchor_top: bool = False,
) -> bool:
    if not image_path.exists():
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

    logo_x = x + pad
    logo_y = top_y - 1.8 * cm
    logo_ok = _dibujar_imagen_ajustada(
        c,
        LOGO_PATH,
        logo_x,
        logo_y,
        max_w=3.0 * cm,
        max_h=2.2 * cm,
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
    c.setFont("Times-BoldItalic", 10)
    y_text = _draw_wrapped_text(c, intro, x + pad, top_y - 1.3 * cm, w - 2 * pad, 13)

    c.setFont("Times-BoldItalic", 10.5)
    y_text -= 0.55 * cm
    c.drawCentredString(x + w / 2, y_text, _safe("Certifica que:"))

    tipo = TIPO_LABELS.get(cert.tipo_empleado, cert.tipo_empleado)
    parrafo = (
        f"Que {(_safe(cert.nombre_completo)).upper()} identificado(a) con cedula de ciudadania C.C. "
        f"{_safe(cert.cedula)} quien se desempena como {(_safe(cert.cargo or tipo)).upper()} asistio al "
        "modulo del curso basico de manipulacion de alimentos implementado en las instalaciones de la "
        "CORPORACION HACIA UN VALLE SOLIDARIO CL 15 # 26 - 101 BG 34 COMPLEJO INDUSTRIAL Y COMERCIAL IC 1, "
        "en el Municipio de YUMBO; de acuerdo a la normatividad sanitaria vigente."
    )
    c.setFont("Helvetica", 11)
    y_text = _draw_wrapped_text(c, parrafo, x + pad, y_text - 0.9 * cm, w - 2 * pad, 15)

    cierre_1 = "El curso se reforzara con las capacitaciones contempladas mensualmente, para la vigencia de 1 ano."
    cierre_2 = f"Para constancia de lo anterior, la presente certificacion se firma en Yumbo el {_fecha_es(cert.fecha_emision)}."
    c.setFont("Helvetica", 11)
    y_text = _draw_wrapped_text(c, cierre_1, x + pad, y_text - 0.45 * cm, w - 2 * pad, 15)
    _draw_wrapped_text(c, cierre_2, x + pad, y_text - 0.55 * cm, w - 2 * pad, 15)

    firma_y = y + 1.95 * cm
    firma_ok = _dibujar_imagen_ajustada(
        c,
        FIRMA_PATH,
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

    c.drawCentredString(x + w * 0.5, firma_y - 0.35 * cm, _safe("JEFE DE ASEGURAMIENTO DE CALIDAD"))
    c.drawCentredString(x + w * 0.5, firma_y - 0.75 * cm, _safe("INGENIERA DE ALIMENTOS"))
    c.drawCentredString(x + w * 0.5, firma_y - 1.15 * cm, _safe("CORPORACION HACIA UN VALLE SOLIDARIO"))

    pie = f"Certificado N. {_safe(cert.numero_certificado)}"
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 8)
    c.drawString(x + pad, y + 0.65 * cm, pie)


def _dibujar_contenido_derecho(c: canvas.Canvas, cert, x: float, y: float, w: float, h: float):
    del cert

    pad = 1.0 * cm
    top_y = y + h - 2.0 * cm

    c.setFillColor(NEGRO)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + pad, top_y, _safe("CERTIFICADO 16 #- DEPARTAMENTO DE CALIDAD"))

    bloque_12 = (
        "Articulo 12. Educacion y capacitacion. Todas las personas que realizan actividades de manipulacion "
        "de alimentos deben tener formacion en educacion sanitaria, principios basicos de Buenas Practicas de "
        "Manufactura y practicas higienicas en manipulacion de alimentos. Igualmente, deben estar capacitados "
        "para llevar a cabo las tareas que se les asignen o desempenen, con el fin de que se encuentren en "
        "capacidad de adoptar las precauciones y medidas preventivas necesarias para evitar la contaminacion o "
        "deterioro de los alimentos. Las empresas deben tener un plan de capacitacion continuo y permanente para "
        "el personal MANIPULADOR(A) de alimentos desde el momento de su contratacion y luego ser reforzado "
        "mediante charlas, cursos u otros medios efectivos de actualizacion."
    )
    c.setFont("Helvetica", 10)
    y_text = _draw_wrapped_text(c, bloque_12, x + pad, top_y - 0.8 * cm, w - 2 * pad, 14.5)

    bloque_13 = (
        "Articulo 13. Plan de capacitacion. El plan de capacitacion debe contener, al menos, los siguientes "
        "aspectos: metodologia, duracion, docentes, cronograma y temas especificos a impartir. El enfoque, "
        "contenido y alcance de la capacitacion impartida debe ser acorde con la empresa, el proceso tecnologico "
        "y tipo de establecimiento de que se trate. En todo caso, la empresa debe demostrar a traves del desempeno "
        "de los operarios y la condicion sanitaria del establecimiento la efectividad e impacto de la capacitacion "
        "impartida."
    )
    c.setFont("Helvetica", 10)
    _draw_wrapped_text(c, bloque_13, x + pad, y_text - 1.1 * cm, w - 2 * pad, 14.5)

    c.saveState()
    c.translate(x + w * 0.56, y + h * 0.43)
    c.rotate(45)
    c.setFont("Helvetica-Bold", 46)
    c.setFillColor(colors.Color(0.55, 0.72, 0.55, alpha=0.15))
    c.drawCentredString(0, 0, _safe("CHVS"))
    c.restoreState()
