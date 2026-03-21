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

    # Enriquecer el prompt con contexto normativo desde Pinecone (RAG)
    from agente.services.rag_service import obtener_contexto_normativo
    consulta_rag = (
        f"gramajes requerimientos nutricionales frecuencias semanales "
        f"{contexto['modalidad']['nombre']} PAE Colombia Resolución 00335"
    )
    contexto_rag = obtener_contexto_normativo(consulta_rag, top_k=5)

    prompt = _construir_prompt(contexto, ocasion_especial, contexto_rag=contexto_rag)

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


def _construir_prompt(contexto: dict, ocasion_especial: str = '', contexto_rag: str = '') -> str:
    modalidad = contexto['modalidad']
    componentes = contexto['componentes_validos']
    ingredientes_por_componente = contexto.get('ingredientes_por_componente', {})
    catalogo_soporte = contexto.get('catalogo_soporte', [])
    menus_similares = contexto['menus_similares']

    # Bloque de ejemplos reales
    ejemplos_texto = ''
    for m in menus_similares[:3]:
        ejemplos_texto += f"\nMenú {m['menu']}:\n"
        for p in m['preparaciones']:
            ings = ', '.join(
                f"{i['nombre']}({i['codigo']})" for i in p['ingredientes'][:5]
            )
            comp = p['componente'] or 'sin componente'
            ejemplos_texto += f"  - [{p.get('componente_id') or '?'}] {p['nombre']} ({comp}): {ings}\n"

    # Bloque de estructura: componente → ingrediente principal sugerido
    estructura_texto = ''
    for c in componentes:
        ings_principales = ingredientes_por_componente.get(c['id'], [])
        ings_str = ', '.join(
            f"{i['nombre']}({i['codigo']})" for i in ings_principales
        )
        estructura_texto += f"  - {c['id']}: {c['nombre']} (grupo: {c['grupo']})\n"
        if ings_str:
            estructura_texto += f"    Ingrediente principal típico: {ings_str}\n"

    # Catálogo de ingredientes de soporte
    catalogo_texto = '\n'.join(
        f"  - {i['codigo']}: {i['nombre']}"
        for i in catalogo_soporte
    )

    # Bloque de normativa (RAG) — solo si Pinecone retornó resultados
    rag_bloque = ''
    if contexto_rag:
        rag_bloque = f"""

NORMATIVA VIGENTE — Resolución PAE (fragmentos recuperados por relevancia semántica):
{contexto_rag}

Verifica que los gramajes y frecuencias propuestos sean coherentes con esta normativa.
"""

    ocasion_bloque = ''
    if ocasion_especial:
        ocasion_bloque = f"""

OCASIÓN ESPECIAL: {ocasion_especial}
- Crea nombres de preparaciones creativos, divertidos y temáticos acordes a esta ocasión.
- Ejemplos: para Halloween → "Poción de Lentejas Embrujada", "Arroz del Cementerio con Zanahoria";
  para Clausura → "Festín de Despedida", "Arroz Ceremonial con Pollo".
- Los ingredientes y sus códigos ICBF deben ser los mismos del catálogo. Solo cambian los nombres.
- La justificación debe explicar el nombre temático elegido."""

    total_componentes = len(componentes)

    return f"""Eres un asistente nutricional experto del Programa de Alimentación Escolar (PAE) de Colombia.

Tu tarea es proponer las preparaciones e ingredientes para un menú escolar de la modalidad indicada.

MODALIDAD OBJETIVO: {modalidad['nombre']}{ocasion_bloque}

EJEMPLOS REALES DE ESTA MODALIDAD (úsalos como referencia de estilo, NO los copies exactamente):
{ejemplos_texto if ejemplos_texto else '(sin ejemplos previos disponibles)'}

ESTRUCTURA OBLIGATORIA — genera EXACTAMENTE {total_componentes} preparaciones, UNA por cada componente:
{estructura_texto}
CATÁLOGO DE INGREDIENTES DE SOPORTE (condimentos, aceites, verduras de guiso, especias — úsalos libremente para complementar cualquier preparación):
{catalogo_texto if catalogo_texto else '(no disponible)'}
{rag_bloque}
REGLAS ESTRICTAS:
1. Genera exactamente {total_componentes} preparaciones, una por cada componente listado arriba.
2. El campo "id_componente" de cada preparación DEBE ser exactamente el ID indicado (ej: "com1", "com3").
3. No puedes repetir el mismo id_componente en dos preparaciones.
4. El ingrediente PRINCIPAL de cada preparación debe ser uno de los "Ingrediente principal típico" de su componente.
   Los ingredientes de soporte (sal, aceite, cebolla, tomate, ajo, cilantro, etc.) se toman del catálogo de soporte.
5. Usa ÚNICAMENTE códigos que aparezcan en las listas anteriores. No inventes códigos.
6. Cada preparación debe tener entre 2 y 8 ingredientes (principal + soporte).
7. VARIEDAD: evita repetir los mismos ingredientes principales de los ejemplos. Si los ejemplos usan pollo, propón res, cerdo o pescado.
8. En "procedimiento" escribe el paso a paso de elaboración (5 a 10 pasos numerados, en español, apropiado para cocina escolar industrial).
9. Incluye una justificación breve por preparación.

Responde ÚNICAMENTE con este JSON estricto, sin texto adicional:

{{
  "preparaciones": [
    {{
      "nombre": "Nombre de la preparación",
      "id_componente": "com1",
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
