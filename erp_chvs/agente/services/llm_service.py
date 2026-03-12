import json
import os
import re
import logging

import google.generativeai as genai

logger = logging.getLogger(__name__)

MODELO = 'gemini-2.5-flash'


def generar_borrador(contexto: dict, ocasion_especial: str = '') -> dict:
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))
    model = genai.GenerativeModel(MODELO)
    prompt = _construir_prompt(contexto, ocasion_especial)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                response_mime_type='application/json',
            )
        )
        respuesta_cruda = response.text
        preparaciones = _parsear_respuesta(respuesta_cruda)
        return {
            'ok': True,
            'prompt': prompt,
            'respuesta_cruda': respuesta_cruda,
            'preparaciones': preparaciones,
            'modelo': MODELO,
            'ocasion_especial': ocasion_especial,
        }
    except Exception as e:
        logger.error(f"Error llamando a Gemini: {e}")
        return {
            'ok': False,
            'prompt': prompt,
            'respuesta_cruda': '',
            'error': str(e),
            'modelo': MODELO,
        }


def _construir_prompt(contexto: dict, ocasion_especial: str = '') -> str:
    modalidad = contexto['modalidad']
    componentes = contexto['componentes_validos']
    top_ingredientes = contexto['top_ingredientes']
    menus_similares = contexto['menus_similares']

    ejemplos_texto = ''
    for m in menus_similares[:3]:
        ejemplos_texto += f"\nMenú {m['menu']}:\n"
        for p in m['preparaciones'][:4]:
            ings = ', '.join(
                f"{i['nombre']}({i['codigo']})" for i in p['ingredientes'][:5]
            )
            comp = p['componente'] or 'sin componente'
            ejemplos_texto += f"  - {p['nombre']} [{comp}]: {ings}\n"

    componentes_texto = '\n'.join(
        f"  - {c['id']}: {c['nombre']} (grupo: {c['grupo']})"
        for c in componentes
    )

    catalogo_texto = '\n'.join(
        f"  - {i['codigo']}: {i['nombre']}"
        for i in top_ingredientes[:40]
    )

    ocasion_bloque = ''
    if ocasion_especial:
        ocasion_bloque = f"""
OCASIÓN ESPECIAL: {ocasion_especial}
- Crea nombres de preparaciones creativos, divertidos y temáticos acordes a esta ocasión.
- Ejemplos: para Halloween → "Poción de Lentejas Embrujada", "Arroz del Cementerio con Zanahoria";
  para Clausura → "Festín de Despedida", "Arroz Ceremonial con Pollo".
- Los ingredientes y sus códigos ICBF deben ser los mismos del catálogo. Solo cambian los nombres.
- La justificación debe explicar el nombre temático elegido.
"""

    return f"""Eres un asistente nutricional experto del Programa de Alimentación Escolar (PAE) de Colombia.

Tu tarea es proponer las preparaciones y sus ingredientes para un almuerzo escolar de la modalidad indicada.

MODALIDAD OBJETIVO:
- Modalidad: {modalidad['nombre']}{ocasion_bloque}

EJEMPLOS REALES DE ESTA MODALIDAD (úsalos como referencia, no los copies exactamente):
{ejemplos_texto if ejemplos_texto else '(sin ejemplos previos disponibles)'}

COMPONENTES VÁLIDOS PARA ESTA MODALIDAD (usa SOLO estos IDs de componente):
{componentes_texto if componentes_texto else '(sin restricción de componentes)'}

CATÁLOGO DE INGREDIENTES ICBF DISPONIBLES (usa ÚNICAMENTE estos códigos exactos):
{catalogo_texto if catalogo_texto else '(catálogo no disponible)'}

INSTRUCCIONES:
1. Propón entre 3 y 5 preparaciones típicas de un almuerzo escolar colombiano.
2. Cada preparación debe tener entre 1 y 6 ingredientes.
3. Usa ÚNICAMENTE los códigos de ingredientes del catálogo provisto.
4. El campo "id_componente" debe ser uno de los IDs de componentes válidos o null.
5. Incluye una justificación breve por preparación.
6. En "procedimiento" escribe el paso a paso de elaboración (5 a 10 pasos numerados, en español, apropiado para cocina escolar industrial).
7. VARIEDAD: Evita repetir los mismos ingredientes principales de los ejemplos anteriores. Si los ejemplos usan pollo, propón res, cerdo o pescado. Si usan guayaba, propón lulo, mora, maracuyá u otra fruta. Prioriza ingredientes que aparezcan poco en los ejemplos mostrados.

Responde ÚNICAMENTE con este JSON estricto, sin texto adicional:

{{
  "preparaciones": [
    {{
      "nombre": "Nombre de la preparación",
      "id_componente": "C01",
      "ingredientes": [
        {{"codigo_icbf": "XXXX", "nombre": "Nombre del ingrediente"}}
      ],
      "justificacion": "Razón breve",
      "procedimiento": "1. Paso uno.\\n2. Paso dos.\\n3. Paso tres."
    }}
  ]
}}"""


def _parsear_respuesta(texto: str) -> list:
    try:
        data = json.loads(texto)
        return data.get('preparaciones', [])
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', texto, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return data.get('preparaciones', [])
        except json.JSONDecodeError:
            pass

    return []
