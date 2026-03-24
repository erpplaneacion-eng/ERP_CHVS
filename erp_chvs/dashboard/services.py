import json
import os
import logging
from datetime import timedelta

import google.generativeai as genai
from django.utils import timezone

from facturacion.models import ListadosFocalizacion
from planeacion.models import SedesEducativas
from principal.models import RegistroActividad

logger = logging.getLogger(__name__)

MODELO_NIA = 'gemini-2.5-flash'
MESES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

_MESES_LOWER = {m.lower(): i + 1 for i, m in enumerate(MESES)}


def _parsear_mes(valor):
    """
    Convierte cualquier representación de mes a entero 1-12.
    Acepta: int (3), string numérico ("3"), nombre ("marzo", "Marzo").
    Retorna None si no puede parsear.
    """
    if valor is None:
        return None
    if isinstance(valor, int) and 1 <= valor <= 12:
        return valor
    try:
        n = int(valor)
        return n if 1 <= n <= 12 else None
    except (ValueError, TypeError):
        pass
    nombre = str(valor).strip().lower()
    return _MESES_LOWER.get(nombre)


# ─── Datos maestros ───────────────────────────────────────────────────────────

def obtener_programas_con_datos():
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
    """Retorna {nombre_sede: cod_interprise}. Gemini nunca maneja códigos directamente."""
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


# ─── Actividad del sistema ─────────────────────────────────────────────────────

def obtener_actividad_para_contexto(horas=24):
    """
    Retorna las últimas N horas de RegistroActividad formateadas como texto
    para inyectar en el prompt de NIA.
    """
    desde = timezone.now() - timedelta(hours=horas)
    registros = (
        RegistroActividad.objects
        .select_related('usuario')
        .filter(fecha__gte=desde)
        .order_by('-fecha')[:60]
    )

    if not registros:
        return f'Sin actividad registrada en las últimas {horas} horas.'

    lineas = []
    for r in registros:
        usuario = (r.usuario.get_full_name() or r.usuario.username) if r.usuario else 'Sistema'
        estado = '✓' if r.exitoso else '✗ ERROR'
        hora = r.fecha.strftime('%d/%m %H:%M')
        lineas.append(f"[{hora}] {estado} | {r.modulo} | {r.accion} | {usuario} | {r.descripcion[:80]}")

    return '\n'.join(lineas)


# ─── Procesamiento principal ───────────────────────────────────────────────────

def procesar_mensaje_nia(request, mensaje_usuario):
    estado = request.session.get('nia_chat_estado', {})

    programas = obtener_programas_con_datos()
    focalizaciones = []
    sedes_mapa = {}

    if estado.get('programa_id'):
        focalizaciones = obtener_focalizaciones(estado['programa_id'])
    if estado.get('programa_id') and estado.get('focalizacion'):
        sedes_mapa = obtener_sedes_mapa(estado['programa_id'], estado.get('focalizacion'))
        estado['sedes_mapa'] = sedes_mapa

    actividad_ctx = obtener_actividad_para_contexto(horas=24)

    prompt = _construir_prompt_nia(
        mensaje_usuario, estado, programas, focalizaciones,
        list(sedes_mapa.keys()), actividad_ctx,
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

    intent = datos.get('intent', 'planillas')

    # ── Intent: consulta de actividad ─────────────────────────────────────────
    if intent == 'actividad':
        return {'mensaje': datos['respuesta'], 'tipo': 'info'}

    # ── Intent: generación de planillas ───────────────────────────────────────
    # Gemini puede devolver números como strings ("3" en vez de 3) → siempre sanitizar
    params = datos.get('params_extraidos', {}) or {}

    programa_id_raw = params.get('programa_id')
    if programa_id_raw is not None:
        try:
            programa_id_int = int(programa_id_raw)
            estado['programa_id'] = programa_id_int
            for p in programas:
                if p['programa__id'] == programa_id_int:
                    estado['programa_nombre'] = p['programa__programa']
                    break
        except (ValueError, TypeError):
            logger.warning(f"NIA: programa_id inválido: {programa_id_raw!r}")

    mes_raw = params.get('mes')
    if mes_raw is not None:
        mes_int = _parsear_mes(mes_raw)
        if mes_int:
            estado['mes'] = mes_int
        else:
            logger.warning(f"NIA: mes inválido: {mes_raw!r}")

    if params.get('focalizacion'):
        estado['focalizacion'] = str(params['focalizacion'])
        estado.pop('todas_sedes', None)
        estado.pop('sede_nombre', None)
        estado.pop('sede_cod_interprise', None)
        estado.pop('sedes_mapa', None)

    todas_sedes_raw = params.get('todas_sedes')
    if todas_sedes_raw is not None:
        estado['todas_sedes'] = bool(todas_sedes_raw)

    sede_nombre_gemini = params.get('sede_nombre')
    if sede_nombre_gemini and not estado.get('todas_sedes'):
        mapa = estado.get('sedes_mapa', sedes_mapa)
        cod = _resolver_sede(str(sede_nombre_gemini), mapa)
        if cod:
            estado['sede_nombre'] = str(sede_nombre_gemini)
            estado['sede_cod_interprise'] = cod
        else:
            logger.warning(f"NIA: sede '{sede_nombre_gemini}' no encontrada en {list(mapa.keys())}")

    request.session['nia_chat_estado'] = estado
    request.session.modified = True

    if datos.get('listo'):
        if not estado.get('todas_sedes') and not estado.get('sede_cod_interprise'):
            return {
                'mensaje': 'No pude identificar esa sede. ¿Puedes escribir el nombre exactamente como aparece en la lista?',
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


# ─── Helpers internos ──────────────────────────────────────────────────────────

def _resolver_sede(nombre_buscado, mapa):
    if not nombre_buscado or not mapa:
        return None
    if nombre_buscado in mapa:
        return mapa[nombre_buscado]
    nombre_lower = nombre_buscado.lower().strip()
    for nombre, cod in mapa.items():
        if nombre.lower().strip() == nombre_lower:
            return cod
    for nombre, cod in mapa.items():
        if nombre_lower in nombre.lower() or nombre.lower() in nombre_lower:
            return cod
    return None


def _construir_prompt_nia(mensaje, estado, programas, focalizaciones, nombres_sedes, actividad_ctx):
    ctx_programas = ', '.join(
        [f"{p['programa__programa']} (id={p['programa__id']})" for p in programas]
    ) or 'ninguno disponible'

    ctx_focos = ', '.join(focalizaciones) or 'pendiente de seleccionar programa'

    ctx_sedes = (
        '\n'.join([f"  - {nombre}" for nombre in nombres_sedes])
        if nombres_sedes else 'pendiente de seleccionar focalización'
    )

    estado_actual = json.dumps({
        'programa': estado.get('programa_nombre'),
        'mes': MESES[_parsear_mes(estado['mes']) - 1] if estado.get('mes') and _parsear_mes(estado['mes']) else None,
        'focalizacion': estado.get('focalizacion'),
        'todas_sedes': estado.get('todas_sedes'),
        'sede_seleccionada': estado.get('sede_nombre'),
    }, ensure_ascii=False)

    return f"""Eres NIA, asistente inteligente del ERP PAE Colombia. Tienes dos capacidades:
1. Generar planillas de asistencia escolar.
2. Responder preguntas sobre la actividad reciente del sistema.

══════════════════════════════════════════
DATOS DEL SISTEMA — ACTIVIDAD ÚLTIMAS 24h
══════════════════════════════════════════
{actividad_ctx}

══════════════════════════════════════════
CONTEXTO PLANILLAS
══════════════════════════════════════════
PROGRAMAS DISPONIBLES: {ctx_programas}
FOCALIZACIONES DEL PROGRAMA SELECCIONADO: {ctx_focos}
SEDES DISPONIBLES:
{ctx_sedes}
ESTADO CONVERSACIÓN PLANILLAS: {estado_actual}

══════════════════════════════════════════
MENSAJE DEL USUARIO: {mensaje}
══════════════════════════════════════════

INSTRUCCIONES:
A) Detecta el intent del mensaje:
   - "actividad": el usuario pregunta sobre qué pasó, acciones realizadas, errores, usuarios activos, resumen del día, etc.
   - "planillas": el usuario quiere generar planillas de asistencia.

B) Si intent="actividad":
   - Responde usando SOLO los datos de ACTIVIDAD ÚLTIMAS 24h proporcionados.
   - Sé conciso y ejecutivo. Si pregunta por errores, menciona solo los que tengan ✗ ERROR.
   - No inventes datos que no estén en la sección de actividad.
   - Devuelve listo=false y params_extraidos con todo null.

C) Si intent="planillas":
   - Solicita los parámetros faltantes en orden: programa → mes → focalización → ¿todas las sedes o una específica?
   - Si el usuario dice "todas" → todas_sedes=true. Si menciona una sede → todas_sedes=false, sede_nombre=<nombre exacto de SEDES DISPONIBLES>.
   - IMPORTANTE: en sede_nombre devuelve el nombre TAL COMO APARECE en SEDES DISPONIBLES.
   - Cuando tengas todos los parámetros pon listo=true.

D) Responde siempre en español, de forma breve y amable.

Responde ÚNICAMENTE en JSON:
{{
  "intent": "actividad" | "planillas",
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
    mes_int = _parsear_mes(estado['mes'])
    nombre_mes = MESES[mes_int - 1]
    estado['mes'] = mes_int  # normalizar a int por si venía como string
    foco = estado['focalizacion']
    prog_nombre = estado.get('programa_nombre', f"Programa {estado['programa_id']}")

    if estado.get('todas_sedes'):
        url = f"/facturacion/generar-zip-masivo/{estado['programa_id']}/{estado['mes']}/{foco}/"
        label = f"Descargar ZIP — {prog_nombre} · {nombre_mes} · {foco}"
    else:
        url = f"/facturacion/generar-asistencia/{estado['programa_id']}/{estado['sede_cod_interprise']}/{estado['mes']}/{foco}/"
        label = f"Descargar PDF — {estado.get('sede_nombre', 'sede')} · {nombre_mes} · {foco}"

    return url, label
