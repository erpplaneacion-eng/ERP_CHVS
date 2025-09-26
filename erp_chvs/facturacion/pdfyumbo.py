from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def crear_formato_base(archivo="eeeeeee.pdf"):
    c = canvas.Canvas(archivo, pagesize=landscape(A4))
    width, height = landscape(A4)

    # --- Rectángulo de borde ---
    margen = 10
    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(2)
    c.rect(margen, margen, width - 2*margen, height - 2*margen)

    # --- Línea horizontal a 60 pt del borde superior ---
    borde_superior = height - margen
    y_linea = borde_superior - 50
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(margen, y_linea, width - margen, y_linea)

    # --- Imagen en la franja superior ---
    ruta_imagen = "imagenes/imagen.jpg"
    alto_franja = borde_superior - y_linea
    img_alto = alto_franja - 5
    img_ancho = img_alto * 3.5
    
    # Solo intentar cargar imagen si existe
    try:
        c.drawImage(
            ruta_imagen,
            margen + 5,
            y_linea + 2,
            width=img_ancho,
            height=img_alto,
            preserveAspectRatio=True,
            mask="auto"
        )
    except:
        # Si no existe la imagen, dibujar un rectángulo placeholder
        c.setStrokeColor(colors.gray)
        c.setFillColor(colors.lightgrey)
        c.rect(margen + 5, y_linea + 2, img_ancho, img_alto, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawCentredString(margen + 5 + img_ancho/2, y_linea + 2 + img_alto/2, "LOGO")
    
    # --- Texto con fondo negro ---
    texto = "FORMATO: REGISTRO Y CONTROL DIARIO DE ASISTENCIA"
    c.setFont("Helvetica-Bold", 6)
    alto_fondo = 9
    y_texto = y_linea - alto_fondo
    c.setFillColor(colors.black)
    c.rect(margen, y_texto, width - 2*margen, alto_fondo, fill=1)

    # Texto en blanco encima
    c.setFillColor(colors.white)
    c.drawCentredString(width/2, y_texto + 2, texto)

    # --- Campos organizados en filas ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 5)

    y_actual = y_texto - 10

    # Filas 1 y 2 (sin cambios)
    filas_normales = [
        ("DEPARTAMENTO:", "CÓDIGO DANE:", "NOMBRE DE INSTITUCIÓN O CENTRO EDUCATIVO:"),
        ("MUNICIPIO:", "CÓDIGO DANE:", "CÓDIGO DANE DE INSTITUCIÓN O CENTRO EDUCATIVO:")
    ]

    for izquierda, centro, derecha in filas_normales:
        c.drawString(margen + 2, y_actual, izquierda)
        c.setLineWidth(0.5)
        c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)

        x_centro = margen + 200
        c.drawString(x_centro, y_actual, centro)
        c.line(x_centro + 70, y_actual - 2, x_centro + 150, y_actual - 2)

        x_der = margen + 500
        c.drawString(x_der, y_actual, derecha)
        c.line(x_der + 150, y_actual - 2, width - margen - 10, y_actual - 2)

        y_actual -= 10

    # Fila 3 especial (OPERADOR, MES DE ATENCIÓN, AÑO)
    c.drawString(margen + 2, y_actual, "OPERADOR:")
    c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
    
    x_mes = margen + 500
    c.drawString(x_mes, y_actual, "MES DE ATENCIÓN:")
    c.line(x_mes + 50, y_actual - 2, width - margen - 200, y_actual - 2)
    
    x_ano = x_mes + 120
    c.drawString(x_ano, y_actual, "AÑO:")
    c.line(x_ano + 15, y_actual - 2, width - margen - 120, y_actual - 2)
    
    y_actual -= 12

    # Fila 4 (sin cambios)
    c.drawString(margen + 2, y_actual, "CONTRATO No:")
    c.line(margen + 70, y_actual - 2, margen + 180, y_actual - 2)
    
    x_tipo = margen + 500
    c.drawString(x_tipo, y_actual, "TIPO COMPLEMENTO:")
    c.line(x_tipo + 60, y_actual - 2, width - margen - 100, y_actual - 2)
    
    y_actual -= 5

    # --- TABLA PRINCIPAL ---
    y_tabla = y_actual - 60
    alto_tabla = 60

    # FIJAR EL ANCHO TOTAL DE LA TABLA
    ancho_total_tabla = width - 2 * margen
    
    # Proporciones para las primeras 12 columnas
    proporciones = [3, 5, 9, 11, 11, 12, 12, 8, 3, 3, 3, 3]
    
    # Ancho fijo para la columna 13 (fechas)
    ancho_col13 = 300
    
    # Ancho disponible para las primeras 12 columnas
    ancho_disponible_12_cols = ancho_total_tabla - ancho_col13
    
    # Calcular anchos reales manteniendo las proporciones
    suma_proporciones = sum(proporciones)
    anchos = []
    for prop in proporciones:
        ancho = int(prop * ancho_disponible_12_cols / suma_proporciones)
        anchos.append(ancho)
    
    # Ajustar diferencia de redondeo
    diferencia = ancho_disponible_12_cols - sum(anchos)
    anchos[-1] += diferencia
    
    headers = [
        "N°", "TIPO\nDE\nDOCUMENTO", "NÚMERO\nDE\nDOCUMENTO\nDE IDENTIDAD",
        "PRIMER NOMBRE\nDEL\nTITULAR DE DERECHO", "SEGUNDO NOMBRE\nDEL\nTITULAR DE DERECHO",
        "PRIMER APELLIDO\nDEL\nTITULAR DE DERECHO", "SEGUNDO APELLIDO\nDEL\nTITULAR DE DERECHO",
        "FECHA\nDE\nNACIMIENTO\n(DD/MM/AAAA)", "PERTENENCIA\nÉTNICA",
        "1. Sexo", "2. Grado\nEducativo", "3. Tipo de\nComplemento"
    ]

    # Índices de columnas especiales
    columnas_verticales = [8, 9, 10, 11]
    columnas_centradas = [0, 1, 2, 3, 4, 5, 6, 7]

    x = margen
    c.setFont("Helvetica", 4)
    c.setFillColor(colors.black)

    # Dibujar las primeras 12 columnas
    for i, (ancho, header) in enumerate(zip(anchos, headers)):
        c.rect(x, y_tabla, ancho, alto_tabla)
        
        if i in columnas_verticales:
            # Texto vertical
            c.saveState()
            x_center = x + ancho/2
            y_center = y_tabla + alto_tabla/2
            c.translate(x_center, y_center)
            c.rotate(90)
            
            lines = header.split('\n')
            if len(lines) > 1:
                total_height = len(lines) * 6
                y_start = total_height/2 - 3
                for j, line in enumerate(lines):
                    c.drawCentredString(0, y_start - j*6, line)
            else:
                c.drawCentredString(0, 0, header)
            
            c.restoreState()
        elif i in columnas_centradas:
            # Texto horizontal centrado
            lines = header.split('\n')
            total_text_height = len(lines) * 6
            y_text_start = y_tabla + alto_tabla/2 + total_text_height/2 - 3
            
            for j, line in enumerate(lines):
                c.drawCentredString(x + ancho/2, y_text_start - j*6, line)
        else:
            # Texto horizontal normal
            lines = header.split('\n')
            y_text_start = y_tabla + alto_tabla - 8
            for j, line in enumerate(lines):
                c.drawCentredString(x + ancho/2, y_text_start - j*6, line)
        
        x += ancho

    # --- Columna 13 especial (fechas) ---
    x_col13 = x

    # 1. Rectángulo superior (título grande)
    alto_titulo = 15
    c.rect(x_col13, y_tabla + alto_tabla - alto_titulo, ancho_col13, alto_titulo)
    c.setFont("Helvetica", 4)
    titulo_col13 = "FECHA DE ENTREGA - Escriba el día hábil al cual corresponde la entrega del complemento Alimentario"
    c.drawCentredString(x_col13 + ancho_col13/2, y_tabla + alto_tabla - alto_titulo/2, titulo_col13)

    # 2. Rectángulo intermedio (casillas 01-30 y Total días)
    alto_casillas = 20
    y_casillas = y_tabla + alto_tabla - alto_titulo - alto_casillas
    
    # Ancho para 22 días + columna total
    ancho_total_dias = 25
    ancho_disponible_dias = ancho_col13 - ancho_total_dias
    casilla_ancho = ancho_disponible_dias / 22
    
    # Dibujar casillas de días
    for i in range(22):
        x_casilla = x_col13 + i * casilla_ancho
        c.rect(x_casilla, y_casillas, casilla_ancho, alto_casillas)
        c.setFont("Helvetica", 4)
        c.drawCentredString(x_casilla + casilla_ancho/2, y_casillas + alto_casillas/2, f"{i+1:02d}")

    # Columna "Total días de consumo"
    x_total = x_col13 + 22 * casilla_ancho
    c.rect(x_total, y_casillas, ancho_total_dias, alto_casillas)
    c.setFont("Helvetica", 4)
    c.drawCentredString(x_total + ancho_total_dias/2, y_casillas + alto_casillas/2 + 3, "Total días")
    c.drawCentredString(x_total + ancho_total_dias/2, y_casillas + alto_casillas/2 - 3, "de consumo")

    # 3. Rectángulo inferior (leyenda)
    alto_leyenda = 15
    y_leyenda = y_casillas - alto_leyenda
    c.rect(x_col13, y_leyenda, ancho_col13, alto_leyenda)
    c.setFont("Helvetica", 4)
    leyenda = "Número de días de atención - Marque con una X el día que el Titular de Derecho recibe el complemento alimentario"
    c.drawCentredString(x_col13 + ancho_col13/2, y_leyenda + alto_leyenda/2, leyenda)

    # Agregar 25 filas de ejemplo para la tabla
    y_fila = y_leyenda - 10
    alto_fila = 10

    for fila in range(25):
        x = margen
        for ancho in anchos:
            c.rect(x, y_fila, ancho, alto_fila)
            x += ancho
        
        # Celdas de la columna 13 para esta fila
        for i in range(22):
            x_casilla = x_col13 + i * casilla_ancho
            c.rect(x_casilla, y_fila, casilla_ancho, alto_fila)
        
        # Celda total
        c.rect(x_total, y_fila, ancho_total_dias, alto_fila)
        
        y_fila -= alto_fila

# --- NUEVAS FILAS DEBAJO DE LA TABLA ---
    
    # Función auxiliar para dibujar rectángulo más grande
    def dibujar_rectangulo_pequeno(x, y, ancho=28, alto=10):
        c.rect(x, y, ancho, alto)
    
    # Configuración común para todas las filas
    c.setFont("Helvetica", 4)
    alto_fila = 15  # Altura consistente para todas las filas
    
    # Definir posiciones fijas para alineación perfecta
    x_inicio = margen + 3
    x_linea1_fija = 120  # Posición fija para primera línea
    x_texto2_fijo = 230  # Posición fija para segundo texto
    x_linea2_fija = 330  # Posición fija para segunda línea
    x_modal_base_fijo = 450  # Posición fija para modalidades
    
    # Calcular posiciones de rectángulos una sola vez
    x_rect1_fijo = x_modal_base_fijo + 50
    x_rect2_fijo = x_rect1_fijo + 70
    x_rect3_fijo = x_rect2_fijo + 55
    x_rect4_fijo = x_rect3_fijo + 70  # Para OLLA COMUNITARIA
    
    # FILA 1: RACIONES MENSUALES
    y_fila -= 8
    
    texto1 = "RACIONES MENSUALES PROGRAMADAS CAJMPS:"
    c.drawString(x_inicio, y_fila, texto1)
    c.line(x_linea1_fija, y_fila - 2, x_linea1_fija + 100, y_fila - 2)
    
    texto2 = "RACIONES MENSUALES ENTREGADAS CAJMPS:"
    c.drawString(x_texto2_fijo, y_fila, texto2)
    c.line(x_linea2_fija, y_fila - 2, x_linea2_fija + 100, y_fila - 2)
    
    # Modalidades con posiciones fijas
    y_rect = y_fila - 7
    
    c.drawString(x_modal_base_fijo, y_fila, "PREPARADA EN SITIO")
    dibujar_rectangulo_pequeno(x_rect1_fijo, y_rect)
    
    c.drawString(x_rect1_fijo + 30, y_fila, "INDUSTRIALIZADA")
    dibujar_rectangulo_pequeno(x_rect2_fijo, y_rect)
    
    c.drawString(x_rect2_fijo + 30, y_fila, "CATERING")
    dibujar_rectangulo_pequeno(x_rect3_fijo, y_rect)
    
    # FILA 2: RACIONES DIARIAS CAJMPS
    y_fila -= alto_fila
    
    texto1 = "RACIONES DIARIAS PROGRAMADAS CAJMPS:"
    c.drawString(x_inicio, y_fila, texto1)
    c.line(x_linea1_fija, y_fila - 2, x_linea1_fija + 100, y_fila - 2)
    
    texto2 = "RACIONES DIARIAS ENTREGADAS CAJMPS:"
    c.drawString(x_texto2_fijo, y_fila, texto2)
    c.line(x_linea2_fija, y_fila - 2, x_linea2_fija + 100, y_fila - 2)
    
    # Modalidades alineadas perfectamente con fila anterior
    y_rect = y_fila - 7
    
    c.drawString(x_modal_base_fijo, y_fila, "PREPARADA EN SITIO")
    dibujar_rectangulo_pequeno(x_rect1_fijo, y_rect)
    
    c.drawString(x_rect1_fijo + 30, y_fila, "INDUSTRIALIZADA")
    dibujar_rectangulo_pequeno(x_rect2_fijo, y_rect)
    
    c.drawString(x_rect2_fijo + 30, y_fila, "CATERING")
    dibujar_rectangulo_pequeno(x_rect3_fijo, y_rect)
    
    # FILA 3: RACIONES DIARIAS ALMUERZO
    y_fila -= alto_fila
    
    texto1 = "RACIONES DIARIAS PROGRAMADAS ALMUERZO:"
    c.drawString(x_inicio, y_fila, texto1)
    c.line(x_linea1_fija, y_fila - 2, x_linea1_fija + 100, y_fila - 2)
    
    texto2 = "RACIONES DIARIAS ENTREGADAS ALMUERZO:"
    c.drawString(x_texto2_fijo, y_fila, texto2)
    c.line(x_linea2_fija, y_fila - 2, x_linea2_fija + 100, y_fila - 2)
    
    # Modalidades alineadas (incluyendo OLLA COMUNITARIA)
    y_rect = y_fila - 7
    
    c.drawString(x_modal_base_fijo, y_fila, "PREPARADA EN SITIO")
    dibujar_rectangulo_pequeno(x_rect1_fijo, y_rect)
    
    c.drawString(x_rect1_fijo + 30, y_fila, "INDUSTRIALIZADA")
    dibujar_rectangulo_pequeno(x_rect2_fijo, y_rect)
    
    c.drawString(x_rect2_fijo + 30, y_fila, "CATERING")
    dibujar_rectangulo_pequeno(x_rect3_fijo, y_rect)
    
    # OLLA COMUNITARIA (solo en esta fila)
    c.drawString(x_rect3_fijo + 30, y_fila, "OLLA COMUNITARIA")
    dibujar_rectangulo_pequeno(x_rect4_fijo, y_rect)
    
    # LÍNEA HORIZONTAL
    y_fila -= 10
    c.line(margen, y_fila, width - margen, y_fila)
    
    # FILA 4: NOMBRES Y FIRMAS
    y_fila -= 10
    texto1 = "NOMBRE DEL RESPONSABLE DEL OPERADOR:"
    c.drawString(margen + 5, y_fila, texto1)
    x_linea1 = margen + 5 + c.stringWidth(texto1, "Helvetica", 4) + 5
    c.line(x_linea1, y_fila - 2, width/2 - 10, y_fila - 2)
    
    x_texto2 = width/2 + 10
    texto2 = "NOMBRE RECTOR ESTABLECIMIENTO EDUCATIVO:"
    c.drawString(x_texto2, y_fila, texto2)
    x_linea2 = x_texto2 + c.stringWidth(texto2, "Helvetica", 4) + 5
    c.line(x_linea2, y_fila - 2, width - margen - 5, y_fila - 2)
    
    # LÍNEA HORIZONTAL
    y_fila -= 5
    c.line(margen, y_fila, width - margen, y_fila)
    
    # FIRMAS
    y_fila -= 10
    texto1 = "FIRMA DEL RESPONSABLE DEL OPERADOR:"
    c.drawString(margen + 5, y_fila, texto1)
    x_linea1 = margen + 5 + c.stringWidth(texto1, "Helvetica", 4) + 5
    c.line(x_linea1, y_fila - 2, width/2 - 10, y_fila - 2)
    
    x_texto2 = width/2 + 10
    texto2 = "FIRMA DEL RECTOR ESTABLECIMIENTO:"
    c.drawString(x_texto2, y_fila, texto2)
    x_linea2 = x_texto2 + c.stringWidth(texto2, "Helvetica", 4) + 5
    c.line(x_linea2, y_fila - 2, width - margen - 5, y_fila - 2)
    
    # LÍNEA HORIZONTAL
    y_fila -= 5
    c.line(margen, y_fila, width - margen, y_fila)
    
    # FILA 5: OBSERVACIONES
    y_fila -= 5
    c.drawString(margen + 5, y_fila, "Observaciones:")
    y_fila -= 5
   
    # FILA 6: EXPLICACIONES (dividida en 3 celdas)
    y_fila -= 5
    alto_explicaciones = 25
    
    # Calcular anchos de las celdas (15%, 10%, 75%)
    ancho_total_explicaciones = width - 2 * margen
    ancho_celda1 = ancho_total_explicaciones * 0.15
    ancho_celda2 = ancho_total_explicaciones * 0.10
    ancho_celda3 = ancho_total_explicaciones * 0.75
    
    # Celda 1 (15%)
    c.rect(margen, y_fila - alto_explicaciones, ancho_celda1, alto_explicaciones)
    c.setFont("Helvetica", 4)
    texto_celda1 = "1. Sexo: Marque F, si es femenino y M, si es masculino"
    # Dividir texto en líneas para que quepa
    palabras = texto_celda1.split()
    lineas = []
    linea_actual = ""
    for palabra in palabras:
        if c.stringWidth(linea_actual + " " + palabra, "Helvetica", 4) < ancho_celda1 - 10:
            linea_actual += " " + palabra if linea_actual else palabra
        else:
            lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)
    
    y_texto = y_fila - 8
    for linea in lineas:
        c.drawString(margen + 3, y_texto, linea)
        y_texto -= 6
    
    # Celda 2 (10%)
    x_celda2 = margen + ancho_celda1
    c.rect(x_celda2, y_fila - alto_explicaciones, ancho_celda2, alto_explicaciones)
    texto_celda2 = "2. Grado Educativo: Marque el grado del Titular de Derecho de P, como preescolar y de 1 a 11"
    # Procesar texto similar a celda 1
    palabras = texto_celda2.split()
    lineas = []
    linea_actual = ""
    for palabra in palabras:
        if c.stringWidth(linea_actual + " " + palabra, "Helvetica", 4) < ancho_celda2 - 10:
            linea_actual += " " + palabra if linea_actual else palabra
        else:
            lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)
    
    y_texto = y_fila - 8
    for linea in lineas:
        c.drawString(x_celda2 + 3, y_texto, linea)
        y_texto -= 6
    
    # Celda 3 (75%)
    x_celda3 = x_celda2 + ancho_celda2
    c.rect(x_celda3, y_fila - alto_explicaciones, ancho_celda3, alto_explicaciones)
    texto_celda3 = "3. Tipo de complemento: Indique el tipo de complemento y modalidad que recibe el titular de Derecho, así: CAJMPS (Complemento Alimentario Jornada mañana preparado en sitio), CAJMRI (Complemento Alimentario Jornada mañana Ración Industrializada), CAJTPS (Complemento Alimentario Jornada Tarde preparado en sitio), CAJTRI (Complemento Alimentario Jornada tarde Ración Industrializada), APS (Almuerzo Preparado en Sitio población Vulnerable), RRI (Refrigerio Reforzado Industrializado), CAIE (Complemento Alimentario Industrializado para Emergencias), APSD (Almuerzo preparado en sitio Desplazados), CAJMPSD (Complemento Alimentario Jornada Mañana preparado en sitio Desplazados), CAJTPSD (Complemento Alimentario Jornada Tarde preparado en sitio Desplazados), CAJMRID (Complemento Alimentario Jornada mañana Ración Industrializada Desplazados), CAJTRID (Complemento Alimentario Jornada Tarde Ración Industrializada Desplazados)."
    
    # Procesar texto largo para celda 3
    palabras = texto_celda3.split()
    lineas = []
    linea_actual = ""
    for palabra in palabras:
        if c.stringWidth(linea_actual + " " + palabra, "Helvetica", 4) < ancho_celda3 - 10:
            linea_actual += " " + palabra if linea_actual else palabra
        else:
            lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)
    
    y_texto = y_fila - 8
    for linea in lineas:
        c.drawString(x_celda3 + 3, y_texto, linea)
        y_texto -= 6
    
   # FILA 7: NOTA (debe terminar antes del margen inferior)
    y_fila -= 35  # Espacio extra antes de la nota
    c.setFont("Helvetica", 4)
    
    texto_nota = """NOTA: El operador/responsable de prestar el servicio en los establecimientos educativos debe tener en cuenta:
    - El archivo de este documento impreso y debidamente diligenciado debe realizarse conforme a los Lineamientos Técnico Administrativos del Programa PAE y estar disponibles para consulta de los veedores y/o supervisores del mismo.
    - En procura del cuidado del medio ambiente hacer uso racional de los recursos.
    - La firma del presente documento da fe la veracidad del contenido del mismo para el seguimiento, monitoreo y control del programa.
    - El presente formato no debe tener tachones, ni enmendaduras para garantizar la validez del mismo."""
    
    # Procesar el texto línea por línea
    lineas_con_saltos = texto_nota.split('\n')
    lineas_finales = []
    ancho_disponible = width - 2 * margen - 10
    
    for linea in lineas_con_saltos:
        if linea.strip():  # Si la línea no está vacía
            # Dividir líneas largas en múltiples líneas si es necesario
            palabras = linea.split()
            linea_actual = ""
            
            for palabra in palabras:
                linea_test = linea_actual + " " + palabra if linea_actual else palabra
                if c.stringWidth(linea_test, "Helvetica", 4) < ancho_disponible:
                    linea_actual = linea_test
                else:
                    if linea_actual:
                        lineas_finales.append(linea_actual)
                    linea_actual = palabra
            
            if linea_actual:
                lineas_finales.append(linea_actual)
        else:
            # Agregar línea vacía para saltos de línea explícitos
            lineas_finales.append("")
    
    # Asegurar que termine antes del margen inferior
    espacio_disponible = y_fila - margen - 5  # 5 puntos para paginación
    lineas_maximas = int(espacio_disponible / 6)  # 6 puntos por línea
    
    if len(lineas_finales) > lineas_maximas:
        lineas_finales = lineas_finales[:lineas_maximas]
    
    # Dibujar las líneas
    for linea in lineas_finales:
        if linea.strip():  # Solo dibujar si la línea tiene contenido
            c.drawString(margen + 5, y_fila, linea)
        y_fila -= 6
    
    # PAGINACIÓN (debajo del margen inferior, centrada)
    c.setFont("Helvetica", 6)
    texto_paginacion = "Página 1/1"  # Puedes hacer esto dinámico si tienes múltiples páginas
    c.drawCentredString(width/2, margen - 8, texto_paginacion)

    # Guardar PDF
    c.save()
    print(f"✅ Formato base creado con tabla de ancho fijo: {archivo}")

# Ejecutar la función
crear_formato_base()