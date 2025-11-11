from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime
import os

# Estructura de datos para los días hábiles de cada mes.
# Aquí puedes agregar o modificar los días para cada mes del año.
DIAS_HABILES_POR_MES = {
    "ENERO": [],
    "FEBRERO": [],
    "MARZO": [],
    "ABRIL": [],
    "MAYO": [],
    "JUNIO": [],
    "JULIO": [],
    "AGOSTO": [],
    "SEPTIEMBRE": [],
    "OCTUBRE": [1, 2, 3, 6, 7, 8, 9, 10, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31],
    "NOVIEMBRE": [4, 5, 6, 7, 10, 11, 12, 13, 14, 18, 19, 20, 21, 24, 25, 26, 27, 28],
    "DICIEMBRE": []
}

class AsistenciaPDFGenerator:
    def __init__(self, buffer, datos_encabezado):
        self.buffer = buffer
        self.datos_encabezado = datos_encabezado
        self.c = canvas.Canvas(self.buffer, pagesize=landscape(A4))
        self.width, self.height = landscape(A4)
        self.margen = 10
        self.y_actual = self.height - self.margen
        self.alto_fila = 11
        self.max_filas_por_pagina = 25
        self.y_inicio_filas = 0
        self.anchos_cols = self._calcular_anchos_columnas()

    def _calcular_anchos_columnas(self):
        ancho_total_tabla = self.width - 2 * self.margen
        # Aquí puedes ajustar el ancho relativo de cada columna.
        # --- INICIO DE CAMBIO: Ajuste de proporciones de columnas ---
        # Se reduce el ancho de las columnas 6 (Primer Apellido) y 7 (Segundo Apellido)
        # y se aumenta el ancho de la columna 13 (fechas).
        proporciones = [3, 3, 9, 11, 11, 11, 11, 6, 2, 2, 4, 4]

        ancho_col13 = 340 # Aumentado de 300 a 340 para dar más espacio a las casillas
        # --- FIN DE CAMBIO ---

        ancho_disponible_12_cols = ancho_total_tabla - ancho_col13
        suma_proporciones = sum(proporciones)
        anchos = [int(prop * ancho_disponible_12_cols / suma_proporciones) for prop in proporciones]
        
        # --- INICIO DE CAMBIO: Ajustar para eliminar el espacio a la derecha ---
        # Sumar la diferencia por redondeo a la última de las 12 columnas para que todo encaje perfectamente.
        anchos[-1] += ancho_disponible_12_cols - sum(anchos)
        # --- FIN DE CAMBIO ---

        anchos.append(ancho_col13) # Añadir el ancho de la columna 13 a la lista
        return anchos # Ahora la lista tiene 13 elementos

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

        # --- Primera Fila ---
        c.drawString(margen + 2, y_actual, "DEPARTAMENTO:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('departamento', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 170, y_actual - 2) # Línea acortada

        # Nuevo campo CODIGO DANE para Departamento
        c.drawString(margen + 180, y_actual, "CODIGO DANE:")
        c.drawString(margen + 225, y_actual, self.datos_encabezado.get('dane_departamento', 'N/A'))
        c.line(margen + 225, y_actual - 2, margen + 265, y_actual - 2) # Línea corta

        x_der = margen + 500
        c.drawString(x_der, y_actual, "NOMBRE DE INSTITUCIÓN O CENTRO EDUCATIVO:")
        c.drawString(x_der + 150, y_actual, self.datos_encabezado.get('institucion', 'N/A'))
        c.line(x_der + 150, y_actual - 2, width - margen - 10, y_actual - 2)
        y_actual -= 10

        # --- Segunda Fila ---
        c.drawString(margen + 2, y_actual, "MUNICIPIO:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('municipio', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 170, y_actual - 2) # Línea acortada

        # Nuevo campo CODIGO DANE para Municipio
        c.drawString(margen + 180, y_actual, "CODIGO DANE:")
        c.drawString(margen + 225, y_actual, self.datos_encabezado.get('dane_municipio', 'N/A'))
        c.line(margen + 225, y_actual - 2, margen + 265, y_actual - 2) # Línea corta

        c.drawString(x_der, y_actual, "CÓDIGO DANE DE INSTITUCIÓN O CENTRO EDUCATIVO:")
        c.drawString(x_der + 150, y_actual, self.datos_encabezado.get('dane_ie', 'N/A'))
        c.line(x_der + 150, y_actual - 2, width - margen - 10, y_actual - 2)
        y_actual -= 10

        # --- Filas restantes (sin cambios) ---
        c.drawString(margen + 2, y_actual, "OPERADOR:")
        c.drawString(margen + 70, y_actual, self.datos_encabezado.get('operador', 'N/A'))
        c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
        x_mes = margen + 500
        c.drawString(x_mes, y_actual, "MES DE ATENCIÓN:")
        c.drawString(x_mes + 50, y_actual, self.datos_encabezado.get('mes', 'N/A'))
        c.line(x_mes + 50, y_actual - 2, width - margen - 220, y_actual - 2) # Acortamos la línea
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
        y_tabla_header = self.y_actual - 50 # Reducimos la altura total
        alto_tabla_header = 50 # La nueva altura es 50
        
        headers = [
            "N°", "TIPO\nDE\nDOCUMENTO", "NÚMERO\nDE\nDOCUMENTO\nDE IDENTIDAD",
            "PRIMER NOMBRE\nDEL\n TITULAR DE DERECHO", "SEGUNDO NOMBRE\nDEL\n TITULAR DE DERECHO", "PRIMER APELLIDO\nDEL\n TITULAR DE DERECHO", "SEGUNDO APELLIDO\nDEL\n TITULAR DE DERECHO",
            "FECHA\nDE\nNACIMIENTO\n(AAAAMMDD)", "PERTENENCIA\nÉTNICA",
            "1. Sexo", "2. Grado\nEducativo", "3. Tipo de\nComplemento"
        ]

        x = self.margen
        
        # --- INICIO DE CAMBIO: Añadir color de fondo a los encabezados ---
        c.setFillColor(colors.whitesmoke) # Un gris claro y suave
        # Dibujar el fondo para las 13 columnas
        c.rect(x, y_tabla_header, self.width - 2 * self.margen, alto_tabla_header, fill=1)
        # --- FIN DE CAMBIO ---

        # Restaurar color para el texto y los bordes
        c.setFont("Helvetica", 4)
        c.setFillColor(colors.black)
        for i, (ancho, header) in enumerate(zip(self.anchos_cols, headers)):
            c.rect(x, y_tabla_header, ancho, alto_tabla_header)
            
            # Si el índice es 1 (Tipo de Documento) o corresponde a las últimas 4 columnas, rotar el texto
            if i == 1 or i >= 8:
                c.saveState()
                c.translate(x + ancho / 2, y_tabla_header + alto_tabla_header / 2)
                c.rotate(90)
                c.drawCentredString(0, 0, header.replace('\n', ' '))
                c.restoreState()
            else:
                # Lógica original para las demás columnas
                lines = header.split('\n')
                y_text_start = y_tabla_header + alto_tabla_header/2 + (len(lines)*4)/2
                for j, line in enumerate(lines):
                    c.drawCentredString(x + ancho/2, y_text_start - j*6, line)
            x += ancho

        # --- Cabecera de la Columna 13 (Fechas) ---
        x_col13 = x
        ancho_col13 = self._calcular_anchos_columnas()[12] # Usar el ancho calculado

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
        

        # Lógica para rellenar las casillas dinámicamente
        mes_actual = self.datos_encabezado.get('mes', '').upper()
        dias_habiles = DIAS_HABILES_POR_MES.get(mes_actual, [])
        num_dias = len(dias_habiles) if dias_habiles else 22 # Usar 22 como default si no hay días definidos
        casilla_ancho = (ancho_disponible_dias / num_dias) if num_dias > 0 else 0

        # Reducir grosor de línea para las casillas de días
        c.setLineWidth(0.5)

        for i in range(num_dias):
            x_casilla = x_col13 + i * casilla_ancho
            c.rect(x_casilla, y_casillas, casilla_ancho, alto_casillas)
            # Si hay un día hábil para esta casilla, lo dibuja
            if i < len(dias_habiles):
                c.drawCentredString(x_casilla + casilla_ancho/2, y_casillas + alto_casillas/2, f"{dias_habiles[i]:02d}")
            # Si no, la casilla queda vacía

        x_total = x_col13 + num_dias * casilla_ancho
        c.rect(x_total, y_casillas, ancho_total_dias_col, alto_casillas)

        # Restaurar grosor de línea normal
        c.setLineWidth(1)
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
        """
        Dispatcher para dibujar el pie de página correcto según el municipio.
        """
        municipio = self.datos_encabezado.get('municipio', '').upper()
        if 'CALI' in municipio:
            self._dibujar_pie_pagina_cali(pagina_actual, total_paginas, total_estudiantes)
        else:
            self._dibujar_pie_pagina_original(pagina_actual, total_paginas, total_estudiantes)

    def _dibujar_pie_pagina_cali(self, pagina_actual, total_paginas, total_estudiantes):
        """
        Dibuja el pie de página con la lógica de resumen de raciones específica para Cali.
        """
        c = self.c
        margen = self.margen
        
        # 1. Calcular valores base
        pdf_codigo_complemento = self.datos_encabezado.get('codigo_complemento', '')
        mes_actual = self.datos_encabezado.get('mes', '').upper()
        dias_habiles_del_mes = DIAS_HABILES_POR_MES.get(mes_actual, [])
        num_dias_habiles = len(dias_habiles_del_mes) if dias_habiles_del_mes else 22
        raciones_mensuales = total_estudiantes * num_dias_habiles

        # 2. Determinar en qué fila va el valor
        valor_cajm = 0
        valor_cajt = 0
        valor_almuerzo = 0

        if 'CAJM' in pdf_codigo_complemento:
            valor_cajm = raciones_mensuales
        elif 'CAJT' in pdf_codigo_complemento:
            valor_cajt = raciones_mensuales
        elif 'ALMUERZO' in pdf_codigo_complemento:
            valor_almuerzo = raciones_mensuales

        # 3. Dibujar las tres filas de resumen de raciones
        y_resumen = self.margen + 130
        c.setFont("Helvetica", 4)

        # --- Fila 1: CAJM ---
        c.drawString(margen + 3, y_resumen, "EJECUCION MENSUAL PROGRAMADA CAJM:")
        c.drawCentredString(margen + 125, y_resumen, str(valor_cajm))
        c.line(margen + 100, y_resumen - 2, margen + 150, y_resumen - 2)
        
        c.drawString(margen + 160, y_resumen, "RACIONES MENSUALES ENTREGADAS CAJM:")
        c.line(margen + 260, y_resumen - 2, margen + 310, y_resumen - 2)
        
        c.drawString(margen + 320, y_resumen, "PREPARADA EN SITIO:")
        c.line(margen + 380, y_resumen - 2, margen + 430, y_resumen - 2)
        c.drawString(margen + 440, y_resumen, "INDUSTRIALIZADA:")
        c.line(margen + 490, y_resumen - 2, margen + 540, y_resumen - 2)
        c.drawString(margen + 550, y_resumen, "CATERING:")
        c.line(margen + 585, y_resumen - 2, margen + 635, y_resumen - 2)
        
        y_resumen -= 15

        # --- Fila 2: CAJT ---
        c.drawString(margen + 3, y_resumen, "EJECUCION MENSUAL PROGRAMADA CAJT:")
        c.drawCentredString(margen + 125, y_resumen, str(valor_cajt))
        c.line(margen + 100, y_resumen - 2, margen + 150, y_resumen - 2)

        c.drawString(margen + 160, y_resumen, "RACIONES MENSUALES ENTREGADAS CAJT:")
        c.line(margen + 260, y_resumen - 2, margen + 310, y_resumen - 2)

        c.drawString(margen + 320, y_resumen, "PREPARADA EN SITIO:")
        c.line(margen + 380, y_resumen - 2, margen + 430, y_resumen - 2)
        c.drawString(margen + 440, y_resumen, "INDUSTRIALIZADA:")
        c.line(margen + 490, y_resumen - 2, margen + 540, y_resumen - 2)
        c.drawString(margen + 550, y_resumen, "CATERING:")
        c.line(margen + 585, y_resumen - 2, margen + 635, y_resumen - 2)

        y_resumen -= 15

        # --- Fila 3: Almuerzo ---
        c.drawString(margen + 3, y_resumen, "EJECUCION MENSUAL PROGRAMADA ALMUERZO:")
        c.drawCentredString(margen + 125, y_resumen, str(valor_almuerzo))
        c.line(margen + 100, y_resumen - 2, margen + 150, y_resumen - 2)

        c.drawString(margen + 160, y_resumen, "RACIONES MENSUALES ENTREGADAS ALMUERZO:")
        c.line(margen + 260, y_resumen - 2, margen + 310, y_resumen - 2)

        c.drawString(margen + 320, y_resumen, "PREPARADA EN SITIO:")
        c.line(margen + 380, y_resumen - 2, margen + 430, y_resumen - 2)
        c.drawString(margen + 440, y_resumen, "INDUSTRIALIZADA:")
        c.line(margen + 490, y_resumen - 2, margen + 540, y_resumen - 2)
        c.drawString(margen + 550, y_resumen, "CATERING:")
        c.line(margen + 585, y_resumen - 2, margen + 635, y_resumen - 2)
        c.drawString(margen + 645, y_resumen, "OLLA COMUNITARIA:")
        c.line(margen + 705, y_resumen - 2, margen + 755, y_resumen - 2)

        # --- Firmas, Observaciones y Leyenda (común para todos los pies de página) ---
        self._dibujar_seccion_firmas_y_leyenda(y_resumen, pagina_actual, total_paginas)

    def _dibujar_pie_pagina_original(self, pagina_actual, total_paginas, total_estudiantes):
        """
        Dibuja el pie de página original para municipios que no son Cali.
        """
        c = self.c
        y_resumen = self.margen + 130 # Subimos para dar espacio a todo el pie de página

        c.setFont("Helvetica", 4)
        codigo_complemento = self.datos_encabezado.get('codigo_complemento', 'N/A')
        
        # --- Fila 1: Raciones Diarias ---
        raciones_diarias = total_estudiantes
        texto1_diario = f"RACIONES DIARIAS PROGRAMADAS {codigo_complemento}:"
        c.drawString(self.margen + 3, y_resumen, texto1_diario)
        
        x_centro_valor_prog = self.margen + 125
        ancho_linea_valor_prog = 30
        c.drawCentredString(x_centro_valor_prog, y_resumen, str(raciones_diarias)) # Valor dinámico centrado
        c.line(x_centro_valor_prog - ancho_linea_valor_prog/2, y_resumen - 2, x_centro_valor_prog + ancho_linea_valor_prog/2, y_resumen - 2)

        texto2_diario = f"RACIONES DIARIAS ENTREGADAS {codigo_complemento}:"
        c.drawString(self.margen + 160, y_resumen, texto2_diario)
        c.line(self.margen + 260, y_resumen - 2, self.margen + 310, y_resumen - 2) # Línea vacía

        c.drawString(self.margen + 320, y_resumen, "PREPARADA EN SITIO:")
        c.line(self.margen + 380, y_resumen - 2, self.margen + 430, y_resumen - 2)
        c.drawString(self.margen + 440, y_resumen, "INDUSTRIALIZADA:")
        c.line(self.margen + 490, y_resumen - 2, self.margen + 540, y_resumen - 2)
        c.drawString(self.margen + 550, y_resumen, "CATERING:")
        c.line(self.margen + 585, y_resumen - 2, self.margen + 635, y_resumen - 2)

        # --- Fila 2: Raciones Mensuales ---
        y_resumen -= 15
        
        mes_actual = self.datos_encabezado.get('mes', '').upper()
        dias_habiles_del_mes = DIAS_HABILES_POR_MES.get(mes_actual, [])
        num_dias_habiles = len(dias_habiles_del_mes) if dias_habiles_del_mes else 22
        raciones_mensuales = raciones_diarias * num_dias_habiles

        texto1_mensual = f"RACIONES MENSUALES PROGRAMADAS {codigo_complemento}:"
        c.drawString(self.margen + 3, y_resumen, texto1_mensual)

        c.drawCentredString(x_centro_valor_prog, y_resumen, str(raciones_mensuales))
        c.line(x_centro_valor_prog - ancho_linea_valor_prog/2, y_resumen - 2, x_centro_valor_prog + ancho_linea_valor_prog/2, y_resumen - 2)

        texto2_mensual = f"RACIONES MENSUALES ENTREGADAS {codigo_complemento}:"
        c.drawString(self.margen + 160, y_resumen, texto2_mensual)
        c.line(self.margen + 260, y_resumen - 2, self.margen + 310, y_resumen - 2)

        c.drawString(self.margen + 320, y_resumen, "PREPARADA EN SITIO:")
        c.line(self.margen + 380, y_resumen - 2, self.margen + 430, y_resumen - 2)
        c.drawString(self.margen + 440, y_resumen, "INDUSTRIALIZADA:")
        c.line(self.margen + 490, y_resumen - 2, self.margen + 540, y_resumen - 2)
        c.drawString(self.margen + 550, y_resumen, "CATERING:")
        c.line(self.margen + 585, y_resumen - 2, self.margen + 635, y_resumen - 2)

        # --- Firmas, Observaciones y Leyenda (común para todos los pies de página) ---
        self._dibujar_seccion_firmas_y_leyenda(y_resumen - 10, pagina_actual, total_paginas)

    def _dibujar_seccion_firmas_y_leyenda(self, y_inicio, pagina_actual, total_paginas):
        """
        Dibuja las secciones de firmas, observaciones, leyenda y nota final.
        Esta función es común para ambos tipos de pie de página.
        """
        c = self.c
        y_actual = y_inicio

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
        c.drawString(self.margen + 3, y_actual, "Observaciones:")
        y_actual -= self.alto_fila
        c.line(self.margen, y_actual, self.width - self.margen, y_actual)
        
        alto_explicaciones = 25
        y_leyenda = y_actual - alto_explicaciones
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

        y_texto_nota = y_leyenda - 5
        texto_nota = """NOTA: El operador/responsable de prestar el servicio en los establecimientos educativos debe tener en cuenta:
                    - El archivo de este documento impreso y debidamente diligenciado debe realizarse conforme a los Lineamientos Técnico Administrativos del Programa PAE y estar disponibles para consulta de los veedores y/o supervisores del mismo.
                    - En procura del cuidado del medio ambiente hacer uso racional de los recursos.
                    - La firma del presente documento da fe la veracidad del contenido del mismo para el seguimiento, monitoreo y control del programa.
                    - El presente formato no debe tener tachones, ni enmendaduras para garantizar la validez del mismo."""
        
        lineas_nota = texto_nota.split('\n')
        c.setFont("Helvetica", 4)
        
        for linea in lineas_nota:
            c.drawString(self.margen + 5, y_texto_nota, linea)
            y_texto_nota -= 5

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
        
        # Procesar página por página
        for pagina in range(total_paginas):
            if pagina > 0:
                c.showPage()
            
            self._dibujar_encabezado_pagina()
            self._dibujar_cabecera_tabla()
            self._dibujar_pie_pagina(pagina + 1, total_paginas, total_estudiantes)
            
            # Dibujar siempre las 25 filas (completas o vacías)
            inicio_estudiantes = pagina * self.max_filas_por_pagina
            fin_estudiantes = min(inicio_estudiantes + self.max_filas_por_pagina, total_estudiantes)
            
            for fila_en_pagina in range(self.max_filas_por_pagina):
                y_fila = self.y_inicio_filas - (fila_en_pagina * self.alto_fila)
                estudiante_index = inicio_estudiantes + fila_en_pagina
                
                if estudiante_index < total_estudiantes:
                    # Fila con estudiante real
                    estudiante = lista_estudiantes[estudiante_index]
                    
                    fecha_nac_str = ""
                    fecha_nac = estudiante.fecha_nacimiento
                    if fecha_nac:
                        if isinstance(fecha_nac, datetime):
                            fecha_nac_str = fecha_nac.strftime('%Y-%m-%d')
                        elif isinstance(fecha_nac, str):
                            try:
                                # Intentar convertir la cadena a fecha y luego formatear
                                fecha_obj = datetime.fromisoformat(fecha_nac.replace('Z', '+00:00').replace('.', ''))
                                fecha_nac_str = fecha_obj.strftime('%Y-%m-%d')
                            except (ValueError, TypeError):
                                # Fallback: intentar extraer fecha de diferentes formatos de cadena
                                fecha_nac_str = str(fecha_nac).split('T')[0].split(' ')[0]
                                if len(fecha_nac_str) != 10:  # No es formato YYYY-MM-DD
                                    fecha_nac_str = ""
                        elif isinstance(fecha_nac, int):
                            # Manejar timestamp Unix (número entero)
                            try:
                                fecha_obj = datetime.fromtimestamp(fecha_nac)
                                fecha_nac_str = fecha_obj.strftime('%Y-%m-%d')
                            except (ValueError, OSError):
                                fecha_nac_str = ""
                        else:
                            # Para otros tipos, convertir a string y tomar primera parte
                            fecha_nac_str = str(fecha_nac).split('T')[0].split(' ')[0]
                    
                    datos_fila = [
                        str(estudiante_index + 1),
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

                    # Dibujar fila normal con datos
                    x = self.margen
                    c.setFont("Helvetica", 5)
                    for j, (ancho, dato) in enumerate(zip(self.anchos_cols, datos_fila)):
                        c.rect(x, y_fila, ancho, self.alto_fila)
                        c.drawString(x + 2, y_fila + 3, str(dato))
                        x += ancho
                    
                    # Dibujar casillas de asistencia
                    x_col13 = x
                    ancho_total_dias = 25
                    ancho_col13_fijo = self._calcular_anchos_columnas()[12]

                    # Replicar la misma lógica dinámica para las filas de estudiantes
                    mes_actual = self.datos_encabezado.get('mes', '').upper()
                    dias_habiles = DIAS_HABILES_POR_MES.get(mes_actual, [])
                    num_dias = len(dias_habiles) if dias_habiles else 22
                    casilla_ancho = (ancho_col13_fijo - ancho_total_dias) / num_dias if num_dias > 0 else 0

                    # Reducir grosor de línea para casillas de días
                    c.setLineWidth(0.5)

                    for k in range(num_dias):
                        c.rect(x_col13 + k * casilla_ancho, y_fila, casilla_ancho, self.alto_fila)

                    c.rect(x_col13 + num_dias * casilla_ancho, y_fila, ancho_total_dias, self.alto_fila)

                    # Restaurar grosor de línea normal
                    c.setLineWidth(1)
                
                else:
                    # Fila vacía - dibujar solo bordes y línea horizontal
                    x = self.margen
                    
                    # Dibujar los bordes de las columnas vacías (primeras 12 columnas)
                    for j, ancho in enumerate(self.anchos_cols[:-1]):  # Excluir la columna 13
                        c.rect(x, y_fila, ancho, self.alto_fila)
                        x += ancho
                    
                    # Dibujar columna de asistencia vacía (columna 13)
                    ancho_col13_fijo = self.anchos_cols[-1]  # La última es la columna 13
                    c.rect(x, y_fila, ancho_col13_fijo, self.alto_fila)
                    
                    # Calcular el ancho total real de la tabla
                    ancho_total_tabla = sum(self.anchos_cols)
                    
                    # Dibujar línea horizontal para indicar que no se puede diligenciar
                    # Respetando los márgenes: desde margen_izq + 5 hasta margen_izq + ancho_tabla - 5
                    c.setStrokeColor(colors.gray)
                    c.setLineWidth(1.5)
                    y_centro_fila = y_fila + (self.alto_fila / 2)
                    inicio_linea = self.margen + 5
                    fin_linea = self.margen + ancho_total_tabla - 5
                    c.line(inicio_linea, y_centro_fila, fin_linea, y_centro_fila)
                    
                    # Restaurar color y grosor de línea normales
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(1)

        c.save()


def crear_formato_asistencia(buffer, datos_encabezado, lista_estudiantes):
    """
    Función de envoltura para generar el formato de asistencia en PDF.
    """
    pdf_generator = AsistenciaPDFGenerator(buffer, datos_encabezado)
    pdf_generator.generar_pdf(lista_estudiantes)
