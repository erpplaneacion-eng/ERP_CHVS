import pandas as pd
import logging
import re
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from fuzzywuzzy import fuzz, process
# Se importan los modelos desde la aplicación 'principal'
from principal.models import  TipoGenero, TipoDocumento, NivelGradoEscolar
# Se importa el modelo de sedes desde la aplicación 'planeacion'
from planeacion.models import SedesEducativas

# Configurar logging
logger = logging.getLogger(__name__)

def normalizar_texto(texto):
    """
    Normaliza un texto para comparación difusa:
    - Convierte a minúsculas
    - Elimina espacios extra
    - Elimina caracteres especiales comunes
    - Normaliza acentos
    """
    if pd.isna(texto) or texto is None:
        return ""
    
    # Convertir a string y minúsculas
    texto = str(texto).lower().strip()
    
    # Eliminar espacios múltiples y reemplazar por uno solo
    texto = re.sub(r'\s+', ' ', texto)
    
    # Eliminar caracteres especiales comunes que pueden causar problemas
    texto = re.sub(r'[^\w\s]', '', texto)
    
    # Normalizar acentos básicos (puedes expandir esto)
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    
    return texto.strip()

def encontrar_coincidencia_difusa(sede_excel, sedes_bd, umbral=90):
    """
    Encuentra la mejor coincidencia difusa para una sede del Excel
    contra las sedes de la base de datos.
    
    Args:
        sede_excel: Nombre de la sede del Excel
        sedes_bd: Lista de sedes de la base de datos
        umbral: Porcentaje mínimo de similitud (default: 90)
    
    Returns:
        tuple: (sede_encontrada, porcentaje_similitud) o (None, 0) si no encuentra
    """
    sede_normalizada = normalizar_texto(sede_excel)
    
    if not sede_normalizada:
        return None, 0
    
    # Usar fuzzywuzzy para encontrar la mejor coincidencia
    resultado = process.extractOne(
        sede_normalizada, 
        sedes_bd, 
        scorer=fuzz.ratio,
        score_cutoff=umbral
    )
    
    if resultado:
        return resultado[0], resultado[1]
    else:
        return None, 0

@login_required
def facturacion_index(request):
    return render(request, 'facturacion/index.html')

@login_required
def generar_listados_view(request):
    # Inicializar todas las variables fuera del bloque try
    dataframe_html = None
    verified_message = None
    invalid_sedes = []
    coincidencias_parciales = []
    coincidencias_genericas = []
    agrupacion_sedes = []

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        focalizacion = request.POST.get('focalizacion', '')

        try:
            # Validación de tipo MIME del archivo
            valid_mime_types = [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            if archivo.content_type not in valid_mime_types:
                raise ValueError("Tipo de archivo inválido. Solo se permiten archivos Excel (.xls, .xlsx)")

            logger.info(f"Procesando archivo: {archivo.name}, tipo: {archivo.content_type}")

            # Leer el archivo Excel
            df = pd.read_excel(archivo)
            
            # Verificar columnas requeridas
            required_columns = ['ESTADO', 'SECTOR', 'MODELO', 'SEDE']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Columnas requeridas faltantes: {', '.join(missing_columns)}")
            
            logger.info(f"Archivo cargado exitosamente. Filas: {len(df)}, Columnas: {len(df.columns)}")

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

            # Transformación de GRADO_COD para crear columna nivel_grados
            niveles_grado = NivelGradoEscolar.objects.all()
            mapeo_niveles = {n.grados_sedes: n.nivel_escolar_uapa for n in niveles_grado}
            
            # Convertir GRADO_COD a entero primero, luego a string para el mapeo
            # Esto maneja el caso donde pandas convierte números a float (6.0 -> 6)
            df['GRADO_COD_clean'] = df['GRADO_COD'].fillna(0).astype(int).astype(str)
            df['nivel_grados'] = df['GRADO_COD_clean'].map(mapeo_niveles)
            
            # Log para verificar el mapeo
            logger.info(f"Mapeo de niveles creado: {mapeo_niveles}")
            logger.info(f"Valores únicos de GRADO_COD_clean: {df['GRADO_COD_clean'].unique()}")
            logger.info(f"Valores únicos de nivel_grados: {df['nivel_grados'].dropna().unique()}")

            # Combinar GRADO_COD y GRUPO
            df['grado_grupos'] = df['GRADO_COD_clean'] + '-' + df['GRUPO'].astype(str)

            # Lógica para JORNADA y nuevas columnas (si ETC es YUMBO o GUADALAJARA DE BUGA)
            if 'YUMBO' in df['ETC'].unique() or 'GUADALAJARA DE BUGA' in df['ETC'].unique():
                # Inicializar nuevas columnas
                df['COMPLEMENTO ALIMENTARIO PREPARADO AM'] = ''
                df['COMPLEMENTO ALIMENTARIO PREPARADO PM'] = ''
                df['ALMUERZO JORNADA UNICA'] = ''
                df['REFUERZO COMPLEMENTO AM/PM'] = ''

                # Aplicar lógica condicional para YUMBO
                if 'YUMBO' in df['ETC'].unique():
                    logger.info("Aplicando lógica de complementos para YUMBO")
                    df.loc[(df['ETC'] == 'YUMBO') & (df['JORNADA'] == 'ÚNICA'), ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'ALMUERZO JORNADA UNICA']] = 'x'
                    df.loc[(df['ETC'] == 'YUMBO') & (df['JORNADA'].isin(['TARDE', 'MAÑANA'])), ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'COMPLEMENTO ALIMENTARIO PREPARADO PM', 'REFUERZO COMPLEMENTO AM/PM']] = 'x'

                # Aplicar lógica condicional para GUADALAJARA DE BUGA
                if 'GUADALAJARA DE BUGA' in df['ETC'].unique():
                    logger.info("Aplicando lógica de complementos para GUADALAJARA DE BUGA")
                    df.loc[(df['ETC'] == 'GUADALAJARA DE BUGA') & (df['JORNADA'] == 'ÚNICA'), ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'ALMUERZO JORNADA UNICA']] = 'x'
                    df.loc[(df['ETC'] == 'GUADALAJARA DE BUGA') & (df['JORNADA'].isin(['TARDE', 'MAÑANA'])), ['COMPLEMENTO ALIMENTARIO PREPARADO AM', 'COMPLEMENTO ALIMENTARIO PREPARADO PM']] = 'x'

            # Añadir columna de focalización
            df['focalizacion'] = focalizacion

            # --- VALIDACIÓN DE SEDES CON COINCIDENCIA DIFUSA (DOBLE VALIDACIÓN) ---
            logger.info("Iniciando validación de sedes con coincidencia difusa...")

            # Extraer valores únicos de la columna SEDE y ETC
            unique_sedes = df['SEDE'].dropna().unique()
            unique_etc = df['ETC'].unique()
            logger.info(f"Sedes encontradas en el archivo: {len(unique_sedes)}")
            logger.info(f"ETC únicos encontrados en el Excel: {unique_etc}")

            # Obtener sedes de la base de datos y crear mapeos optimizados
            # MAPEO 1: Por nombre_sede_educativa (validación principal) - FILTRADO POR MUNICIPIO
            db_sedes_principales = list(SedesEducativas.objects.filter(
                codigo_ie__id_municipios__nombre_municipio__in=unique_etc
            ).values_list('nombre_sede_educativa', flat=True))
            db_sedes_mapeo_principal = {}
            db_sedes_normalizadas_principal = []

            for sede_raw in db_sedes_principales:
                sede_normalizada = normalizar_texto(sede_raw)
                db_sedes_normalizadas_principal.append(sede_normalizada)
                db_sedes_mapeo_principal[sede_normalizada] = sede_raw

            # MAPEO 2: Por nombre_generico_sede (validación de respaldo) - FILTRADO POR MUNICIPIO
            db_sedes_genericas = list(SedesEducativas.objects.exclude(
                nombre_generico_sede__isnull=True
            ).exclude(
                nombre_generico_sede__exact=''
            ).exclude(
                nombre_generico_sede__exact='Sin especificar'
            ).filter(
                codigo_ie__id_municipios__nombre_municipio__in=unique_etc
            ).values_list('nombre_generico_sede', 'nombre_sede_educativa', 'codigo_ie__id_municipios__nombre_municipio'))

            db_sedes_mapeo_generico = {}
            db_sedes_normalizadas_generico = []

            for nombre_generico, nombre_completo, municipio in db_sedes_genericas:
                sede_normalizada = normalizar_texto(nombre_generico)
                if sede_normalizada and sede_normalizada not in db_sedes_normalizadas_generico:
                    db_sedes_normalizadas_generico.append(sede_normalizada)
                    # Crear clave única: nombre_generico + municipio para evitar conflictos
                    clave_unica = f"{sede_normalizada}_{municipio}"
                    db_sedes_mapeo_generico[clave_unica] = {
                        'nombre_completo': nombre_completo,
                        'municipio': municipio,
                        'nombre_generico': nombre_generico
                    }

            logger.info(f"Sedes principales en BD (filtradas por ETC): {len(db_sedes_normalizadas_principal)}")
            logger.info(f"Sedes genéricas en BD (filtradas por ETC): {len(db_sedes_normalizadas_generico)}")
            
            # Log adicional para verificar el filtro
            if len(db_sedes_normalizadas_principal) == 0:
                logger.warning(f"No se encontraron sedes para los ETC: {unique_etc}. Verificar que los nombres coincidan exactamente con la tabla principal_municipio.")
            else:
                logger.info(f"Filtro por ETC aplicado correctamente. Sedes encontradas para: {unique_etc}")

            # Variables para tracking
            sedes_validas = []
            sedes_invalidas = []
            coincidencias_parciales = []
            coincidencias_genericas = []  # Nueva lista para coincidencias por nombre genérico
            mapeo_sedes = {}  # Para mapear sede original -> sede encontrada

            # Validar cada sede del Excel
            for sede_excel in unique_sedes:
                sede_validada = False

                # PRIMERA VALIDACIÓN: Por nombre completo de sede
                sede_encontrada, porcentaje = encontrar_coincidencia_difusa(
                    sede_excel,
                    db_sedes_normalizadas_principal,
                    umbral=90
                )

                if sede_encontrada:
                    sede_original_bd = db_sedes_mapeo_principal.get(sede_encontrada)

                    if sede_original_bd:
                        sedes_validas.append(sede_excel)
                        mapeo_sedes[sede_excel] = sede_original_bd
                        sede_validada = True

                        if porcentaje < 100:
                            coincidencias_parciales.append({
                                'excel': sede_excel,
                                'bd': sede_original_bd,
                                'porcentaje': porcentaje,
                                'tipo': 'nombre_completo'
                            })
                            logger.info(f"Coincidencia parcial (nombre completo): '{sede_excel}' -> '{sede_original_bd}' ({porcentaje}%)")
                        else:
                            logger.info(f"Coincidencia exacta (nombre completo): '{sede_excel}' -> '{sede_original_bd}'")

                # SEGUNDA VALIDACIÓN: Si la primera falló, intentar por nombre genérico (considerando municipio)
                if not sede_validada and db_sedes_normalizadas_generico:
                    logger.info(f"Intentando validación por nombre genérico para: '{sede_excel}'")

                    sede_encontrada_generica, porcentaje_generico = encontrar_coincidencia_difusa(
                        sede_excel,
                        db_sedes_normalizadas_generico,
                        umbral=90
                    )

                    if sede_encontrada_generica:
                        # Buscar en el mapeo genérico considerando el municipio del ETC
                        # Obtener el ETC de la fila actual para determinar el municipio
                        etc_actual = df[df['SEDE'] == sede_excel]['ETC'].iloc[0] if len(df[df['SEDE'] == sede_excel]) > 0 else None
                        
                        if etc_actual:
                            clave_unica = f"{sede_encontrada_generica}_{etc_actual}"
                            sede_info_generica = db_sedes_mapeo_generico.get(clave_unica)
                            
                            if sede_info_generica:
                                sedes_validas.append(sede_excel)
                                mapeo_sedes[sede_excel] = sede_info_generica['nombre_completo']
                                sede_validada = True

                                coincidencias_genericas.append({
                                    'excel': sede_excel,
                                    'bd': sede_info_generica['nombre_completo'],
                                    'nombre_generico': sede_info_generica['nombre_generico'],
                                    'municipio': sede_info_generica['municipio'],
                                    'porcentaje': porcentaje_generico
                                })
                                logger.info(f"Coincidencia por nombre genérico (municipio {etc_actual}): '{sede_excel}' -> '{sede_info_generica['nombre_completo']}' via '{sede_info_generica['nombre_generico']}' ({porcentaje_generico}%)")
                            else:
                                logger.warning(f"Nombre genérico '{sede_encontrada_generica}' encontrado pero no coincide con municipio '{etc_actual}' para sede '{sede_excel}'")
                        else:
                            logger.warning(f"No se pudo determinar ETC para sede '{sede_excel}' en validación genérica")

                # Si ninguna validación funcionó, marcar como inválida
                if not sede_validada:
                    sedes_invalidas.append(sede_excel)
                    logger.warning(f"Sede no encontrada en ninguna validación: '{sede_excel}'")

            logger.info(f"Resultado validación: Válidas: {len(sedes_validas)}, Inválidas: {len(sedes_invalidas)}")
            logger.info(f"Coincidencias parciales (nombre completo): {len(coincidencias_parciales)}")
            logger.info(f"Coincidencias por nombre genérico: {len(coincidencias_genericas)}")
            
            # Filtrar DataFrame para incluir solo sedes válidas
            if sedes_invalidas:
                df_original_count = len(df)
                df = df[df['SEDE'].isin(sedes_validas)]
                df_filtered_count = len(df)
                logger.info(f"Filas filtradas: {df_original_count} -> {df_filtered_count} (excluidas: {df_original_count - df_filtered_count})")
            
            # Validar si el DataFrame quedó vacío después del filtrado
            if len(df) == 0:
                logger.warning("El DataFrame quedó vacío después del filtrado de sedes")
                verified_message = "No se encontraron filas válidas después del filtrado de sedes. Verifique que las sedes en el archivo coincidan con la base de datos."
                dataframe_html = "<div class='alert alert-warning'>No hay datos para mostrar. Todas las filas fueron filtradas por sedes inválidas.</div>"
                agrupacion_sedes = []
            else:
                # Generar mensajes de verificación
                total_registros = len(df)
                if not sedes_invalidas:
                    # Construir mensaje detallado sobre tipos de coincidencias
                    mensaje_detalles = []

                    if coincidencias_parciales:
                        mensaje_detalles.append(f"{len(coincidencias_parciales)} coincidencias parciales por nombre completo")

                    if coincidencias_genericas:
                        mensaje_detalles.append(f"{len(coincidencias_genericas)} coincidencias por nombre genérico")

                    if mensaje_detalles:
                        detalles_str = " y ".join(mensaje_detalles)
                        verified_message = f"Los archivos generados en el DataFrame han sido verificados exitosamente. Se procesaron {total_registros} registros. Se encontraron {detalles_str} que fueron aceptadas."
                    else:
                        verified_message = f"Los archivos generados en el DataFrame han sido verificados exitosamente. Se procesaron {total_registros} registros. Todas las sedes coinciden exactamente con la base de datos."
                else:
                    verified_message = f"Las siguientes sedes no se pudieron cargar porque no se encontraron coincidencias en ninguna validación (nombre completo ni genérico): {', '.join(sedes_invalidas)}. Se procesaron {total_registros} registros con sedes válidas."
                
                # Crear agrupación por sedes de BD para mostrar estadísticas
                agrupacion_sedes = []

                # Obtener solo sedes de municipios que coinciden con ETC del Excel
                todas_sedes_bd = list(SedesEducativas.objects.filter(
                    codigo_ie__id_municipios__nombre_municipio__in=unique_etc
                ).values_list('nombre_sede_educativa', flat=True))
                
                logger.info(f"Sedes filtradas por ETC: {len(todas_sedes_bd)} sedes encontradas")

                # Definir los niveles escolares esperados
                niveles_escolares = ['prescolar', 'primaria_1_2', 'primaria_3_4_5', 'secundaria', 'media_ciclo_complementario']

                # Para cada sede de BD, verificar si tiene coincidencias
                for sede_bd in todas_sedes_bd:
                    # Buscar si esta sede BD tiene mapeos desde Excel
                    sedes_excel_mapeadas = [sede_excel for sede_excel, sede_bd_mapeada in mapeo_sedes.items() if sede_bd_mapeada == sede_bd]

                    if sedes_excel_mapeadas:
                        # Si hay mapeos, contar registros totales y por nivel
                        total_count = 0
                        sede_excel_str = ', '.join(sedes_excel_mapeadas)
                        
                        # Crear DataFrame filtrado para esta sede
                        df_sede = df[df['SEDE'].isin(sedes_excel_mapeadas)]
                        total_count = len(df_sede)
                        
                        # Contar por cada nivel escolar
                        estadisticas_nivel = {}
                        for nivel in niveles_escolares:
                            count_nivel = len(df_sede[df_sede['nivel_grados'] == nivel])
                            estadisticas_nivel[nivel] = count_nivel

                        agrupacion_sedes.append({
                            'sede_bd': sede_bd,
                            'sede_excel': sede_excel_str,
                            'cantidad': total_count,
                            **estadisticas_nivel  # Desempaquetar las estadísticas por nivel
                        })
                    else:
                        # Si no hay mapeos, mostrar con 0 registros
                        estadisticas_nivel = {nivel: 0 for nivel in niveles_escolares}
                        agrupacion_sedes.append({
                            'sede_bd': sede_bd,
                            'sede_excel': 'Sin coincidencias',
                            'cantidad': 0,
                            **estadisticas_nivel
                        })

                # Ordenar por cantidad descendente
                agrupacion_sedes.sort(key=lambda x: x['cantidad'], reverse=True)
                
                # Convertir las primeras 5 filas a HTML para mostrarlas en la plantilla
                dataframe_html = df.head(5).to_html(classes='table table-striped table-bordered', index=False, na_rep='')
            
            # Actualizar variables para el template
            invalid_sedes = sedes_invalidas

        except Exception as e:
            logger.error(f"Error al procesar el archivo: {e}")
            dataframe_html = f"<div class='alert alert-danger'>Error al procesar el archivo: {e}</div>"
            verified_message = None
            invalid_sedes = []
            coincidencias_parciales = []
            coincidencias_genericas = []
            agrupacion_sedes = []

    return render(request, 'facturacion/generar_listados.html', {
        'dataframe_html': dataframe_html,
        'verified_message': verified_message,
        'invalid_sedes': invalid_sedes,
        'coincidencias_parciales': coincidencias_parciales,
        'coincidencias_genericas': coincidencias_genericas,
        'agrupacion_sedes': agrupacion_sedes
    })
