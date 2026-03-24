import json
import os
import logging

import google.generativeai as genai

from facturacion.models import ListadosFocalizacion
from planeacion.models import SedesEducativas

logger = logging.getLogger(__name__)

MODELO_NIA = 'gemini-2.5-flash'
MESES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]


def obtener_programas_con_datos():
    """Programas que tienen listados de focalización cargados."""
    return list(
        ListadosFocalizacion.objects
        .select_related('programa')
        .exclude(programa=None)
        .values('programa__id', 'programa__programa')
        .distinct()
        .order_by('programa__programa')
    )


def obtener_focalizaciones(programa_id):
    return list(
        ListadosFocalizacion.objects
        .filter(programa_id=programa_id)
        .values_list('focalizacion', flat=True)
        .distinct()
        .order_by('focalizacion')
    )


def obtener_sedes_mapa(programa_id, focalizacion=None):
    """
    Retorna un dict {nombre_sede: cod_interprise} para un programa.
    El cod_interprise se resuelve server-side; Gemini nunca lo maneja directamente.
    """
    filtro = {'programa_id': programa_id}
    if focalizacion:
        filtro['focalizacion'] = focalizacion

    nombres_sedes = list(
        ListadosFocalizacion.objects
        .filter(**filtro)
        .values_list('sede', flat=True)
        .distinct()
    )

    sedes_qs = SedesEducativas.objects.filter(
        nombre_sede_educativa__in=nombres_sedes
    ).values('nombre_sede_educativa', 'cod_interprise')

    return {s['nombre_sede_educativa']: s['cod_interprise'] for s in sedes_qs}


def procesar_mensaje_nia(request, mensaje_usuario):
    """
    Procesa un mensaje del usuario, actualiza el estado de la conversación
    en la sesión y retorna la respuesta de NIA.
    """
    estado = request.session.get('nia_chat_estado', {})

    programas = obtener_programas_con_datos()
    focalizaciones = []
    sedes_mapa = {}

    if estado.get('programa_id'):
        focalizaciones = obtener_focalizaciones(estado['programa_id'])
    if estado.get('programa_id') and estado.get('focalizacion'):
        sedes_mapa = obtener_sedes_mapa(estado['programa_id'], estado.get('focalizacion'))
        # Guardar el mapa en sesión para resolver cod_interprise server-side
        estado['sedes_mapa'] = sedes_mapa

    prompt = _construir_prompt_nia(
        mensaje_usuario, estado, programas, focalizaciones, list(sedes_mapa.keys())
    )

    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))
        model = genai.GenerativeModel(MODELO_NIA)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type='application/json',
            ),
        )
        datos = json.loads(response.text)
    except Exception as e:
        logger.error(f"NIA Gemini error: {e}")
        return {
            'mensaje': 'No puedo procesar tu solicitud en este momento. Intenta de nuevo.',
            'tipo': 'error',
        }

    # Actualizar estado con parámetros extraídos
    params = datos.get('params_extraidos', {})

    if params.get('programa_id'):
        estado['programa_id'] = params['programa_id']
        for p in programas:
            if p['programa__id'] == params['programa_id']:
                estado['programa_nombre'] = p['programa__programa']
                break

    if params.get('mes'):
        estado['mes'] = params['mes']

    if params.get('focalizacion'):
        estado['focalizacion'] = params['focalizacion']
        # Resetear selección de sede al cambiar focalización
        estado.pop('todas_sedes', None)
        estado.pop('sede_nombre', None)
        estado.pop('sede_cod_interprise', None)
        estado.pop('sedes_mapa', None)

    if params.get('todas_sedes') is not None:
        estado['todas_sedes'] = params['todas_sedes']

    # Resolver sede_nombre → cod_interprise server-side (Gemini devuelve solo el nombre)
    sede_nombre_gemini = params.get('sede_nombre')
    if sede_nombre_gemini and not estado.get('todas_sedes'):
        mapa = estado.get('sedes_mapa', sedes_mapa)
        cod = _resolver_sede(sede_nombre_gemini, mapa)
        if cod:
            estado['sede_nombre'] = sede_nombre_gemini
            estado['sede_cod_interprise'] = cod
        else:
            logger.warning(f"NIA: sede '{sede_nombre_gemini}' no encontrada en mapa {list(mapa.keys())}")

    request.session['nia_chat_estado'] = estado
    request.session.modified = True

    if datos.get('listo'):
        # Validar que tenemos cod_interprise si es sede individual
        if not estado.get('todas_sedes') and not estado.get('sede_cod_interprise'):
            return {
                'mensaje': 'No pude identificar esa sede en el sistema. ¿Puedes escribir el nombre exactamente como aparece en la lista?',
                'tipo': 'pregunta',
            }
        url, label = _construir_url_descarga(estado)
        return {
            'mensaje': datos['respuesta'],
            'tipo': 'listo',
            'url_descarga': url,
            'label_descarga': label,
        }

    return {'mensaje': datos['respuesta'], 'tipo': 'pregunta'}


def _resolver_sede(nombre_buscado, mapa):
    """
    Busca el cod_interprise para un nombre de sede.
    Primero intenta coincidencia exacta, luego parcial (case-insensitive).
    """
    if not nombre_buscado or not mapa:
        return None

    # Exacta
    if nombre_buscado in mapa:
        return mapa[nombre_buscado]

    # Case-insensitive
    nombre_lower = nombre_buscado.lower().strip()
    for nombre, cod in mapa.items():
        if nombre.lower().strip() == nombre_lower:
            return cod

    # Coincidencia parcial (el nombre buscado contiene o está contenido)
    for nombre, cod in mapa.items():
        if nombre_lower in nombre.lower() or nombre.lower() in nombre_lower:
            return cod

    return None


def _construir_prompt_nia(mensaje, estado, programas, focalizaciones, nombres_sedes):
    ctx_programas = ', '.join(
        [f"{p['programa__programa']} (id={p['programa__id']})" for p in programas]
    ) or 'ninguno disponible'

    ctx_focos = ', '.join(focalizaciones) or 'pendiente de seleccionar programa'

    if nombres_sedes:
        ctx_sedes = '\n'.join([f"  - {nombre}" for nombre in nombres_sedes])
    else:
        ctx_sedes = 'pendiente de seleccionar focalización'

    estado_actual = json.dumps({
        'programa': estado.get('programa_nombre'),
        'mes': MESES[estado['mes'] - 1] if estado.get('mes') else None,
        'focalizacion': estado.get('focalizacion'),
        'todas_sedes': estado.get('todas_sedes'),
        'sede_seleccionada': estado.get('sede_nombre'),
    }, ensure_ascii=False)

    return f"""Eres NIA, asistente del ERP PAE Colombia. Tu única función es ayudar a generar planillas de asistencia escolar.

PROGRAMAS DISPONIBLES: {ctx_programas}
FOCALIZACIONES DEL PROGRAMA SELECCIONADO: {ctx_focos}
SEDES DISPONIBLES (nombres exactos):
{ctx_sedes}
ESTADO ACTUAL DE LA CONVERSACIÓN: {estado_actual}
MENSAJE DEL USUARIO: {mensaje}

INSTRUCCIONES:
1. Extrae los parámetros que el usuario mencione: programa, mes (1-12), focalización, tipo de sede.
2. Si el usuario menciona el nombre de un programa, identifica su id en PROGRAMAS DISPONIBLES (comparación flexible, sin importar mayúsculas/acentos).
3. Para el mes: acepta nombres ("marzo" → 3) o números.
4. Para la focalización: busca la coincidencia exacta en FOCALIZACIONES.
5. Solicita solo los parámetros que faltan, en este orden: programa → mes → focalización → ¿todas las sedes o una específica?
6. Si el usuario quiere todas las sedes → todas_sedes=true, sede_nombre=null.
7. Si menciona una sede específica → todas_sedes=false, sede_nombre=<nombre EXACTO de SEDES DISPONIBLES que más se parezca>.
8. IMPORTANTE: en sede_nombre devuelve SIEMPRE el nombre tal como aparece en SEDES DISPONIBLES, sin modificarlo.
9. Cuando tengas TODOS los parámetros (programa_id, mes, focalizacion, todas_sedes definido; si todas_sedes=false también sede_nombre), pon listo=true.
10. Si el usuario pregunta algo fuera de planillas de asistencia, responde que solo puedes ayudar con eso.
11. Responde siempre en español, de forma breve y amable. Al listar sedes, muéstralas numeradas.

Responde ÚNICAMENTE en JSON con esta estructura:
{{
  "respuesta": "<mensaje para el usuario>",
  "params_extraidos": {{
    "programa_id": null,
    "mes": null,
    "focalizacion": null,
    "todas_sedes": null,
    "sede_nombre": null
  }},
  "listo": false
}}"""


def _construir_url_descarga(estado):
    nombre_mes = MESES[estado['mes'] - 1]
    foco = estado['focalizacion']
    prog_nombre = estado.get('programa_nombre', f"Programa {estado['programa_id']}")

    if estado.get('todas_sedes'):
        url = (
            f"/facturacion/generar-zip-masivo/"
            f"{estado['programa_id']}/{estado['mes']}/{foco}/"
        )
        label = f"Descargar ZIP — {prog_nombre} · {nombre_mes} · {foco}"
    else:
        url = (
            f"/facturacion/generar-asistencia/"
            f"{estado['programa_id']}/{estado['sede_cod_interprise']}/{estado['mes']}/{foco}/"
        )
        sede_nombre = estado.get('sede_nombre', 'sede')
        label = f"Descargar PDF — {sede_nombre} · {nombre_mes} · {foco}"

    return url, label
