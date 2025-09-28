from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime
import os


class AsistenciaPDFGenerator:
    def __init__(self, buffer, datos_encabezado):
        self.buffer = buffer
        self.datos_encabezado = datos_encabezado
        self.c = canvas.Canvas(self.buffer, pagesize=landscape(A4))
        self.width, self.height = landscape(A4)
        self.margen = 10
        self.y_actual = self.height - self.margen
        self.alto_fila = 10
        self.max_filas_por_pagina = 25
        self.y_inicio_filas = 0
        self.anchos_cols = self._calcular_anchos_columnas()

    def _calcular_anchos_columnas(self):
        ancho_total_tabla = self.width - 2 * self.margen
        proporciones = [3, 5, 9, 11, 11, 12, 12, 8, 3, 3, 3, 3]
        ancho_col13 = 300
        ancho_disponible_12_cols = ancho_total_tabla - ancho_col13
        suma_proporciones = sum(proporciones)
        anchos = [int(prop * ancho_disponible_12_cols / suma_proporciones) for prop in proporciones]
        anchos[-1] += ancho_disponible_12_cols - sum(anchos)
        return anchos

    def _dibujar_encabezado_pagina(self):
        c = self.c
        margen = self.margen
        width, height = self.width, self.height

        c.setStrokeColor(colors.darkblue)
        c.setLineWidth(2)
        c.rect(margen, margen, width - 2*margen, height - 2*margen)

        y_linea_logo = height - margen - 50
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(margen, y_linea_logo, width - margen, y_linea_logo)

        ruta_imagen = self.datos_encabezado.get('ruta_logo')
        try:
            if ruta_imagen and os.path.exists(ruta_imagen):
                c.drawImage(ruta_imagen, margen + 5, y_linea_logo + 2, width=170, height=45, preserveAspectRatio=True, mask="auto")
            else:
                raise FileNotFoundError("Logo no encontrado")
        except:
            c.setFont("Helvetica", 8)
            c.drawCentredString(margen + 5 + 85, y_linea_logo + 22, "LOGO")

        y_texto_titulo = y_linea_logo - 9
        c.setFillColor(colors.black)
        c.rect(margen, y_texto_titulo, width - 2*margen, 9, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(width/2, y_texto_titulo + 2, "FORMATO: REGISTRO Y CONTROL DIARIO DE ASISTENCIA")

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 5)
        y_actual = y_texto_titulo - 10

        c.drawString(margen + 2, y_actual, "DEPARTAMENTO:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('departamento', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
        x_der = margen + 500
        c.drawString(x_der, y_actual, "NOMBRE DE INSTITUCIÓN O CENTRO EDUCATIVO:")
        c.drawString(x_der + 150, y_actual, self.datos_encabezado.get('institucion', 'N/A'))
        c.line(x_der + 150, y_actual - 2, width - margen - 10, y_actual - 2)
        y_actual -= 10

        c.drawString(margen + 2, y_actual, "MUNICIPIO:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('municipio', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
        c.drawString(x_der, y_actual, "CÓDIGO DANE DE INSTITUCIÓN O CENTRO EDUCATIVO:")
        c.drawString(x_der + 150, y_actual, self.datos_encabezado.get('dane_ie', 'N/A'))
        c.line(x_der + 150, y_actual - 2, width - margen - 10, y_actual - 2)
        y_actual -= 10

        c.drawString(margen + 2, y_actual, "OPERADOR:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('operador', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
        x_mes = margen + 500
        c.drawString(x_mes, y_actual, "MES DE ATENCIÓN:")
        c.drawString(x_mes + 50, y_actual, self.datos_encabezado.get('mes', 'N/A'))
        c.line(x_mes + 50, y_actual - 2, width - margen - 200, y_actual - 2)
        x_ano = x_mes + 120
        c.drawString(x_ano, y_actual, "AÑO:")
        c.drawString(x_ano + 15, y_actual, str(self.datos_encabezado.get('ano', 'N/A')))
        c.line(x_ano + 15, y_actual - 2, width - margen - 120, y_actual - 2)
        y_actual -= 12

        c.drawString(margen + 2, y_actual, "CONTRATO No:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('contrato', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
        x_tipo = margen + 500
        c.drawString(x_tipo, y_actual, "TIPO COMPLEMENTO:")
        c.drawString(x_tipo + 60, y_actual, self.datos_encabezado.get('codigo_complemento', 'N/A'))
        c.line(x_tipo + 60, y_actual - 2, width - margen - 100, y_actual - 2)
        
        self.y_actual = y_actual - 5

    def _dibujar_cabecera_tabla(self):
        c = self.c
        y_tabla_header = self.y_actual - 60
        alto_tabla_header = 60
        
        headers = [
            "N°", "TIPO\nDE\nDOCUMENTO", "NÚMERO\nDE\nDOCUMENTO\nDE IDENTIDAD",
            "PRIMER NOMBRE\n...", "SEGUNDO NOMBRE\n...", "PRIMER APELLIDO\n...", "SEGUNDO APELLIDO\n...",
            "FECHA\nDE\nNACIMIENTO", "PERTENENCIA\nÉTNICA",
            "1. Sexo", "2. Grado\nEducativo", "3. Tipo de\nComplemento"
        ]

        x = self.margen
        c.setFont("Helvetica", 4)
        c.setFillColor(colors.black)
        for i, (ancho, header) in enumerate(zip(self.anchos_cols, headers)):
            c.rect(x, y_tabla_header, ancho, alto_tabla_header)
            lines = header.split('\n')
            y_text_start = y_tabla_header + alto_tabla_header/2 + (len(lines)*4)/2
            for j, line in enumerate(lines):
                c.drawCentredString(x + ancho/2, y_text_start - j*6, line)
            x += ancho

        # --- Cabecera de la Columna 13 (Fechas) ---
        x_col13 = x
        ancho_col13 = 300

        # 1. Título superior
        alto_titulo = 15
        c.rect(x_col13, y_tabla_header + alto_tabla_header - alto_titulo, ancho_col13, alto_titulo)
        c.setFont("Helvetica", 4)
        titulo_col13 = "FECHA DE ENTREGA - Escriba el día hábil al cual corresponde la entrega del complemento Alimentario"
        c.drawCentredString(x_col13 + ancho_col13/2, y_tabla_header + alto_tabla_header - alto_titulo/2 - 2, titulo_col13)

        # 2. Casillas de días (01-22) y Total
        alto_casillas = 20
        y_casillas = y_tabla_header + alto_tabla_header - alto_titulo - alto_casillas
        ancho_total_dias_col = 25
        ancho_disponible_dias = ancho_col13 - ancho_total_dias_col
        casilla_ancho = ancho_disponible_dias / 22

        for i in range(22):
            x_casilla = x_col13 + i * casilla_ancho
            c.rect(x_casilla, y_casillas, casilla_ancho, alto_casillas)
            c.drawCentredString(x_casilla + casilla_ancho/2, y_casillas + alto_casillas/2, f"{i+1:02d}")

        x_total = x_col13 + 22 * casilla_ancho
        c.rect(x_total, y_casillas, ancho_total_dias_col, alto_casillas)
        c.drawCentredString(x_total + ancho_total_dias_col/2, y_casillas + alto_casillas/2 + 3, "Total días")
        c.drawCentredString(x_total + ancho_total_dias_col/2, y_casillas + alto_casillas/2 - 3, "de consumo")

        # 3. Leyenda inferior
        alto_leyenda = 15
        y_leyenda_header = y_casillas - alto_leyenda
        c.rect(x_col13, y_leyenda_header, ancho_col13, alto_leyenda)
        leyenda = "Número de días de atención - Marque con una X el día que el Titular de Derecho recibe el complemento alimentario"
        c.drawCentredString(x_col13 + ancho_col13/2, y_leyenda_header + alto_leyenda/2 - 2, leyenda)

        self.y_inicio_filas = y_tabla_header - self.alto_fila

    def _dibujar_pie_pagina(self, pagina_actual, total_paginas, total_estudiantes):
        c = self.c
        y_resumen = self.margen + 130 # Subimos para dar espacio a todo el pie de página

        c.setFont("Helvetica", 4)
        codigo_complemento = self.datos_encabezado.get('codigo_complemento', 'N/A')
        
        raciones_diarias = total_estudiantes
        texto1_diario = f"RACIONES DIARIAS PROGRAMADAS {codigo_complemento}:"
        c.drawString(self.margen + 3, y_resumen, texto1_diario)
        c.drawString(self.margen + 120, y_resumen, str(raciones_diarias)) # Valor dinámico
        c.line(self.margen + 120, y_resumen - 2, self.margen + 220, y_resumen - 2)

        texto2_diario = f"RACIONES DIARIAS ENTREGADAS {codigo_complemento}:"
        c.drawString(self.margen + 230, y_resumen, texto2_diario)
        c.line(self.margen + 330, y_resumen - 2, self.margen + 430, y_resumen - 2) # Línea vacía

        # Raciones mensuales
        y_resumen -= 15
        raciones_mensuales = raciones_diarias * 22 # Asumiendo 22 días
        texto1_mensual = f"RACIONES MENSUALES PROGRAMADAS {codigo_complemento}:"
        c.drawString(self.margen + 3, y_resumen, texto1_mensual)
        c.drawString(self.margen + 120, y_resumen, str(raciones_mensuales)) # Valor dinámico
        c.line(self.margen + 120, y_resumen - 2, self.margen + 220, y_resumen - 2)

        texto2_mensual = f"RACIONES MENSUALES ENTREGADAS {codigo_complemento}:"
        c.drawString(self.margen + 230, y_resumen, texto2_mensual)
        c.line(self.margen + 330, y_resumen - 2, self.margen + 430, y_resumen - 2) # Línea vacía

        # --- Firmas, Observaciones y Leyenda ---
        y_actual = y_resumen - 10
        
        y_actual -= 5
        c.line(self.margen, y_actual, self.width - self.margen, y_actual)

        y_actual -= 10
        c.drawString(self.margen + 5, y_actual, "NOMBRE DEL RESPONSABLE DEL OPERADOR:")
        c.line(self.margen + 125, y_actual - 2, self.width/2 - 10, y_actual - 2)
        c.drawString(self.width/2 + 10, y_actual, "NOMBRE RECTOR ESTABLECIMIENTO EDUCATIVO:")
        c.line(self.width/2 + 135, y_actual - 2, self.width - self.margen - 5, y_actual - 2)

        y_actual -= 5
        c.line(self.margen, y_actual, self.width - self.margen, y_actual)

        y_actual -= 10
        c.drawString(self.margen + 5, y_actual, "FIRMA DEL RESPONSABLE DEL OPERADOR:")
        c.line(self.margen + 125, y_actual - 2, self.width/2 - 10, y_actual - 2)
        c.drawString(self.width/2 + 10, y_actual, "FIRMA DEL RECTOR ESTABLECIMIENTO:")
        c.line(self.width/2 + 135, y_actual - 2, self.width - self.margen - 5, y_actual - 2)

        y_actual -= 5
        c.line(self.margen, y_actual, self.width - self.margen, y_actual)

        y_actual -= 5
        c.drawString(self.margen + 5, y_actual, "Observaciones:")
        
        # --- Leyenda y Nota ---
        y_leyenda = self.margen + 5
        alto_explicaciones = 25
        ancho_total_explicaciones = self.width - 2 * self.margen
        ancho_celda1 = ancho_total_explicaciones * 0.15
        ancho_celda2 = ancho_total_explicaciones * 0.10
        ancho_celda3 = ancho_total_explicaciones * 0.75

        c.rect(self.margen, y_leyenda, ancho_celda1, alto_explicaciones)
        self._dibujar_texto_en_celda("1. Sexo: Marque F, si es femenino y M, si es masculino", self.margen, y_leyenda, ancho_celda1, alto_explicaciones)

        x_celda2 = self.margen + ancho_celda1
        c.rect(x_celda2, y_leyenda, ancho_celda2, alto_explicaciones)
        self._dibujar_texto_en_celda("2. Grado Educativo: Marque el grado del Titular de Derecho de P, como preescolar y de 1 a 11", x_celda2, y_leyenda, ancho_celda2, alto_explicaciones)

        x_celda3 = x_celda2 + ancho_celda2
        c.rect(x_celda3, y_leyenda, ancho_celda3, alto_explicaciones)
        texto_celda3 = "3. Tipo de complemento: Indique el tipo de complemento y modalidad que recibe el titular de Derecho, así: CAJMPS (Complemento Alimentario Jornada mañana preparado en sitio), CAJMRI (Complemento Alimentario Jornada mañana Ración Industrializada), CAJTPS (Complemento Alimentario Jornada Tarde preparado en sitio), CAJTRI (Complemento Alimentario Jornada tarde Ración Industrializada), APS (Almuerzo Preparado en Sitio población Vulnerable), RRI (Refrigerio Reforzado Industrializado), CAIE (Complemento Alimentario Industrializado para Emergencias), APSD (Almuerzo preparado en sitio Desplazados), CAJMPSD (Complemento Alimentario Jornada Mañana preparado en sitio Desplazados), CAJTPSD (Complemento Alimentario Jornada Tarde preparado en sitio Desplazados), CAJMRID (Complemento Alimentario Jornada mañana Ración Industrializada Desplazados), CAJTRID (Complemento Alimentario Jornada Tarde Ración Industrializada Desplazados)."
        self._dibujar_texto_en_celda(texto_celda3, x_celda3, y_leyenda, ancho_celda3, alto_explicaciones)

        # --- Nota Final ---
        y_nota = y_leyenda - 30 # Posición debajo de la leyenda
        texto_nota = """NOTA: El operador/responsable de prestar el servicio en los establecimientos educativos debe tener en cuenta:
- El archivo de este documento impreso y debidamente diligenciado debe realizarse conforme a los Lineamientos Técnico Administrativos del Programa PAE y estar disponibles para consulta de los veedores y/o supervisores del mismo.
- En procura del cuidado del medio ambiente hacer uso racional de los recursos.
- La firma del presente documento da fe la veracidad del contenido del mismo para el seguimiento, monitoreo y control del programa.
- El presente formato no debe tener tachones, ni enmendaduras para garantizar la validez del mismo."""
        
        lineas_nota = texto_nota.split('\n')
        y_texto_nota = y_actual - 45 # Posición fija para la nota
        c.setFont("Helvetica", 4)
        
        # Dibujar cada línea de la nota
        for linea in lineas_nota:
            # Dividir líneas largas si es necesario (aunque en este caso son cortas)
            palabras = linea.split()
            linea_actual_wrap = ""
            # Este es un wrapper simple, para textos más complejos se necesitaría una librería
            # pero para este caso específico, las líneas ya están pre-formateadas.
            c.drawString(self.margen + 5, y_texto_nota, linea)
            y_texto_nota -= 5 # Espacio entre líneas

        c.setFont("Helvetica", 6)
        c.drawCentredString(self.width/2, self.margen - 8, f"Página {pagina_actual}/{total_paginas}")

    def _dibujar_texto_en_celda(self, texto, x, y, ancho, alto):
        """Función auxiliar para dibujar texto multilínea dentro de una celda."""
        c = self.c
        palabras = texto.split()
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            if c.stringWidth(linea_actual + " " + palabra, "Helvetica", 4) < ancho - 6:
                linea_actual += " " + palabra if linea_actual else palabra
            else:
                lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)
        
        y_texto = y + alto - 5
        for linea in lineas:
            c.drawString(x + 3, y_texto, linea)
            y_texto -= 5
            if y_texto < y:
                break

    def generar_pdf(self, lista_estudiantes):
        c = self.c
        total_estudiantes = len(lista_estudiantes)
        if total_estudiantes == 0:
            self._dibujar_encabezado_pagina()
            self._dibujar_cabecera_tabla()
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.width/2, self.y_inicio_filas - 50, "No hay estudiantes para este complemento.")
            self._dibujar_pie_pagina(1, 1, 0)
            c.save()
            return

        total_paginas = (total_estudiantes + self.max_filas_por_pagina - 1) // self.max_filas_por_pagina
        
        for i, estudiante in enumerate(lista_estudiantes):
            pagina_actual = (i // self.max_filas_por_pagina) + 1
            fila_en_pagina = i % self.max_filas_por_pagina

            if fila_en_pagina == 0:
                if i > 0:
                    c.showPage()
                self._dibujar_encabezado_pagina()
                self._dibujar_cabecera_tabla()
                self._dibujar_pie_pagina(pagina_actual, total_paginas, total_estudiantes)

            y_fila = self.y_inicio_filas - (fila_en_pagina * self.alto_fila)

            fecha_nac_str = ""
            if isinstance(estudiante.fecha_nacimiento, datetime):
                fecha_nac_str = estudiante.fecha_nacimiento.strftime('%d/%m/%Y')
            
            datos_fila = [
                str(i + 1),
                estudiante.tipodoc or '',
                estudiante.doc or '',
                estudiante.nombre1 or '',
                estudiante.nombre2 or '',
                estudiante.apellido1 or '',
                estudiante.apellido2 or '',
                fecha_nac_str,
                estudiante.etnia or '',
                estudiante.genero or '',
                estudiante.grado_grupos or '',
                self.datos_encabezado.get('codigo_complemento', '')
            ]

            x = self.margen
            c.setFont("Helvetica", 5)
            for j, (ancho, dato) in enumerate(zip(self.anchos_cols, datos_fila)):
                c.rect(x, y_fila, ancho, self.alto_fila)
                c.drawString(x + 2, y_fila + 3, str(dato))
                x += ancho
            
            x_col13 = x
            ancho_total_dias = 25
            ancho_col13_fijo = 300
            casilla_ancho = (ancho_col13_fijo - ancho_total_dias) / 22
            for k in range(22):
                c.rect(x_col13 + k * casilla_ancho, y_fila, casilla_ancho, self.alto_fila)
            c.rect(x_col13 + 22 * casilla_ancho, y_fila, ancho_total_dias, self.alto_fila)

        c.save()


def crear_formato_asistencia(buffer, datos_encabezado, lista_estudiantes):
    """
    Función de envoltura para generar el formato de asistencia en PDF.
    """
    pdf_generator = AsistenciaPDFGenerator(buffer, datos_encabezado)
    pdf_generator.generar_pdf(lista_estudiantes)
