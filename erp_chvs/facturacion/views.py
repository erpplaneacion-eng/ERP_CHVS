import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
# Se importan los modelos desde la aplicación 'principal'
from principal.models import  TipoGenero, TipoDocumento

@login_required
def facturacion_index(request):
    return render(request, 'facturacion/index.html')

@login_required
def generar_listados_view(request):
    dataframe_html = None

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        focalizacion = request.POST.get('focalizacion', '')

        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)

            # --- PASO 1: FILTRADO INICIAL ---
            df = df[df['ESTADO'] == 'MATRICULADO']
            df = df[df['SECTOR'] == 'OFICIAL']
            df = df[~df['MODELO'].isin(['PROGRAMA PARA JÓVENES EN EXTRAEDAD Y ADULTOS'])]

            # --- PASO 2: SELECCIÓN DE COLUMNAS ---
            columnas_a_mantener = [
                'ANO', 'ETC', 'ESTADO', 'INSTITUCION', 'SECTOR', 'SEDE',
                'ZONA_SEDE', 'JORNADA', 'GRADO_COD', 'GRUPO',
                'MODELO', 'DOC', 'TIPODOC',
                'APELLIDO1', 'APELLIDO2', 'NOMBRE1', 'NOMBRE2', 'GENERO'
            ]
            # Se asegura de seleccionar solo las columnas que existen en el DataFrame cargado
            columnas_existentes = [col for col in columnas_a_mantener if col in df.columns]
            df = df[columnas_existentes]

            # --- PASO 3: TRANSFORMACIÓN DE DATOS ---

            # Transformación de TIPODOC usando el modelo de 'principal'
            tipos_documento = TipoDocumento.objects.all()
            mapeo_modalidades = {m.tipo_documento: m.codigo_documento for m in tipos_documento}
            df['TIPODOC'] = df['TIPODOC'].map(mapeo_modalidades)

            # Transformación de GENERO usando el modelo de 'principal'
            generos = TipoGenero.objects.all()
            mapeo_generos = {g.genero: g.codigo_genero for g in generos}
            df['GENERO'] = df['GENERO'].map(mapeo_generos)

            # Combinar GRADO_COD y GRUPO
            df['grado_grupos'] = df['GRADO_COD'].astype(str) + '-' + df['GRUPO'].astype(str)

            # Lógica para JORNADA y nuevas columnas (si ETC es YUMBO)
            if 'YUMBO' in df['ETC'].unique():
                # Inicializar nuevas columnas
                df['COMPLEMENTO ALIMENTARIO PREPARADO AM'] = ''
                df['COMPLEMENTO ALIMENTARIO PREPARADO PM'] = ''
                df['COMPLEMENTO AM/PM INDUSTRIALIZADO'] = ''
                df['ALMUERZO JORNADA UNICA'] = ''
                df['REFUERZO COMPLEMENTO AM/PM'] = ''

                # Aplicar lógica condicional para YUMBO
                df.loc[(df['ETC'] == 'YUMBO') & (df['JORNADA'] == 'ÚNICA'), ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'ALMUERZO JORNADA UNICA']] = 'x'
                df.loc[(df['ETC'] == 'YUMBO') & (df['JORNADA'].isin(['TARDE', 'MAÑANA'])), ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'COMPLEMENTO ALIMENTARIO PREPARADO PM', 'REFUERZO COMPLEMENTO AM/PM']] = 'x'

            # Añadir columna de focalización
            df['focalizacion'] = focalizacion

            # Convertir las primeras 5 filas a HTML para mostrarlas en la plantilla
            dataframe_html = df.head(5).to_html(classes='table table-striped table-bordered', index=False, na_rep='')

        except Exception as e:
            dataframe_html = f"<div class='alert alert-danger'>Error al procesar el archivo: {e}</div>"

    return render(request, 'facturacion/generar_listados.html', {
        'dataframe_html': dataframe_html
    })