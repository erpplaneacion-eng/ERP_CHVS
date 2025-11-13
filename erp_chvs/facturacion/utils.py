import base64
from django.core.files.uploadedfile import SimpleUploadedFile

def _mapear_grado_a_nivel_manual(grado):
    """
    Mapea manualmente grados que no están en la tabla NivelGradoEscolar
    a sus niveles escolares correspondientes.
    """
    try:
        grado_num = float(grado)
        if grado_num < 0:
            return "Preescolar"
        elif grado_num == 0:
            return "Preescolar"
        elif 1 <= grado_num <= 5:
            return "Primaria"
        elif 6 <= grado_num <= 9:
            return "Secundaria"
        elif 10 <= grado_num <= 11:
            return "Media"
        else:
            return None
    except (ValueError, TypeError):
        return None

def _recrear_archivo_desde_sesion(datos_sesion: dict) -> SimpleUploadedFile:
    """
    Reconstruye un archivo SimpleUploadedFile desde los datos guardados en la sesión.

    Args:
        datos_sesion: Diccionario con los datos del archivo de la sesión.

    Returns:
        SimpleUploadedFile: El archivo reconstruido.

    Raises:
        ValueError: Si faltan datos clave en la sesión.
    """
    archivo_contenido_b64 = datos_sesion.get('archivo_contenido_b64')
    archivo_name = datos_sesion.get('archivo_name')
    archivo_content_type = datos_sesion.get('archivo_content_type')

    if not all([archivo_contenido_b64, archivo_name, archivo_content_type]):
        raise ValueError("No se pudo reconstruir el archivo desde la sesión. Faltan datos.")

    return SimpleUploadedFile(archivo_name, base64.b64decode(archivo_contenido_b64), content_type=archivo_content_type)

def _extraer_grado_base(grado_grupos):
    """
    Extrae el grado base de un valor grado_grupos considerando diferentes formatos.
    """
    if not grado_grupos or grado_grupos == '':
        return None

    grado_str = str(grado_grupos).strip()

    if grado_str.startswith('-') and '--' in grado_str:
        grado_base = grado_str.split('--')[0]
        return grado_base

    if grado_str.startswith('-'):
        return grado_str

    if '-' in grado_str:
        parte_grado = grado_str.split('-')[0]
        if parte_grado:
            return parte_grado

    return grado_str

def _determinar_nivel_educativo(grado_grupos):
    """
    Determina el nivel educativo con clasificación detallada de 5 niveles
    a partir del grado_grupos.

    CLASIFICACIÓN NUTRICIONAL (5 niveles):
    - Preescolar: Grados 0, -1, -2
    - Primaria 1-2-3: Grados 1, 2, 3
    - Primaria 4-5: Grados 4, 5
    - Secundaria: Grados 6-9
    - Media: Grados 10-11

    Args:
        grado_grupos: String con el grado del estudiante (ej: "0-A", "3-B", "10-A", "-1-A")

    Returns:
        String: 'preescolar', 'primaria_1_3', 'primaria_4_5', 'secundaria', o 'media'
    """
    grado_base = _extraer_grado_base(grado_grupos)

    if not grado_base:
        return 'primaria_1_3'  # Default si no se puede determinar

    try:
        # Manejar preescolar (grados negativos o cero)
        if grado_base.startswith('-'):
            return 'preescolar'

        grado_num = int(grado_base)

        if grado_num == 0:
            return 'preescolar'
        elif 1 <= grado_num <= 3:
            return 'primaria_1_3'
        elif 4 <= grado_num <= 5:
            return 'primaria_4_5'
        elif 6 <= grado_num <= 9:
            return 'secundaria'
        elif 10 <= grado_num <= 11:
            return 'media'
        else:
            return 'primaria_1_3'  # Default

    except (ValueError, TypeError):
        return 'primaria_1_3'  # Default si hay error en la conversión