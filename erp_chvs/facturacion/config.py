
"""
Configuración para el módulo de facturación.
Contiene constantes y configuraciones centralizadas.
"""

# Configuración de procesamiento de archivos
class ProcesamientoConfig:
    # Umbrales de validación
    UMBRAL_COINCIDENCIA_DIFUSA = 90
    UMBRAL_COINCIDENCIA_PARCIAL = 90
    
    # Tipos de procesamiento soportados
    TIPO_PROCESAMIENTO_NUEVO = 'nuevo'
    TIPO_PROCESAMIENTO_ORIGINAL = 'original'
    TIPO_PROCESAMIENTO_YUMBO = 'yumbo'
    TIPO_PROCESAMIENTO_BUGA = 'buga'
    
    # Municipios soportados
    MUNICIPIOS_SOPORTADOS = ['CALI', 'YUMBO', 'GUADALAJARA DE BUGA']
    
    # Columnas requeridas para nuevo formato
    COLUMNAS_NUEVO_FORMATO = [
        'LOTE', 'NOMBRE INSTITUCION', 'NOMBRE SEDE', 'ZONA', 'TIPO_DOCUMENTO', 
        'NRO_DOCUMENTO', 'APELLIDO1', 'APELLIDO2', 'NOMBRE1', 'NOMBRE2', 
        'FECHA_NACIMIENTO', 'GENERO', 'TIPO_JORNADA', 'GRADO', 'GRUPO', 'EDAD'
    ]
    
    # Columnas requeridas para formato original
    COLUMNAS_ORIGINAL_FORMATO = [    "ANO",    "ETC",    "ESTADO",    "SECTOR",
    "INSTITUCION",    "DANE", "SECTOR",
    "SEDE",    "ZONA_SEDE",    "JORNADA",    "GRADO_COD",    "GRUPO",    "MODELO",
    "DOC",    "TIPODOC",    "APELLIDO1",    "APELLIDO2",    "NOMBRE1",    "NOMBRE2",
    "GENERO",    "FECHA_NACIMIENTO"
    ]

    
    # Filtros para formato original
    ESTADO_MATRICULADO = 'MATRICULADO'
    SECTOR_OFICIAL = 'OFICIAL'
    MODELOS_EXCLUIDOS = ['PROGRAMA PARA JÓVENES EN EXTRAEDAD Y ADULTOS']
    
    # Valores fijos para nuevo formato
    AÑO_FIJO = 2025
    ETC_CALI = 'CALI'
    ESTADO_MATRICULADO_NUEVO = 'MATRICULADO'
    SECTOR_OFICIAL_NUEVO = 'OFICIAL'
    MODELO_PROGRAMA_ALIMENTARIO = 'PROGRAMA ALIMENTARIO'
    
    # Lógica de jornadas para CALI (nuevo formato)
    JORNADA_UNICA_CALI = 6
    JORNADAS_DOBLES_CALI = [2, 3]  # TARDE, MAÑANA
    
    # Lógica de jornadas para otros municipios (formato original)
    JORNADA_UNICA_OTROS = 'ÚNICA'
    JORNADAS_DOBLES_OTROS = ['TARDE', 'MAÑANA']
    
    # Niveles escolares para estadísticas
    NIVELES_ESCOLARES = [
        'prescolar', 'primaria_1_2_3', 'primaria_4_5', 
        'secundaria', 'media_ciclo_complementario'
    ]
    
    # Tipos MIME válidos para archivos Excel
    MIME_TYPES_VALIDOS = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    # Configuración de logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configuración de archivos
    EXTENSIONES_PERMITIDAS = ['.xls', '.xlsx']
    TAMANO_MAXIMO_ARCHIVO = 50 * 1024 * 1024  # 50MB

# Configuración de focalizaciones
FOCALIZACIONES_DISPONIBLES = [
    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
    'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20'
]

# Meses de atención para los reportes
MESES_ATENCION = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
]

# Configuración de mensajes
class MensajesConfig:
    # Mensajes de éxito
    PROCESAMIENTO_EXITOSO = "Archivo procesado exitosamente"
    VALIDACION_EXITOSA = "Validación exitosa"
    
    # Mensajes de error
    ARCHIVO_INVALIDO = "Tipo de archivo inválido. Solo se permiten archivos Excel (.xls, .xlsx)"
    COLUMNAS_FALTANTES = "Columnas requeridas faltantes: {columnas}"
    NO_FILAS_LOTE_3 = "No se encontraron filas con LOTE == 3 en el archivo"
    NO_FILAS_VALIDAS = "No se encontraron filas válidas después del filtrado"
    
    # Mensajes de advertencia
    SEDES_INVALIDAS = "Las siguientes sedes no se pudieron cargar: {sedes}"
    COINCIDENCIAS_PARCIALES = "Se encontraron {cantidad} coincidencias parciales por nombre completo"
    COINCIDENCIAS_GENERICAS = "Se encontraron {cantidad} coincidencias por nombre genérico"
