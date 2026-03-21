"""
Servicio RAG (Retrieval-Augmented Generation) para la app agente.

Usa Pinecone como vector store y text-embedding-004 (via google-generativeai)
para generar embeddings de 768 dims.

Corpus: PDFs normativos PAE (Resolución 00335/2021, Minuta Patrón, etc.)
ingestados con el management command `ingestar_normativo`.

Degradación silenciosa: si PINECONE_API_KEY no está configurada o Pinecone
falla, todas las funciones retornan valores vacíos sin lanzar excepción.
El flujo de generación de borradores continúa sin contexto RAG.
"""

import os
import logging

import requests
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = 'gemini-embedding-001'
EMBEDDING_DIM = 768
CHUNK_SIZE = 1200    # chars — más pequeño que el prototipo para preservar texto tabular
CHUNK_OVERLAP = 200
TOP_K_DEFAULT = 5
BATCH_SIZE = 50      # vectores por upsert a Pinecone

_EMBED_URL = (
    f'https://generativelanguage.googleapis.com/v1beta/models/'
    f'{EMBEDDING_MODEL}:embedContent'
)


# ── Cliente Pinecone ────────────────────────────────────────────────────────

def _get_pinecone_index():
    """
    Obtiene (o crea si no existe) el índice de Pinecone configurado.
    Lanza excepción si PINECONE_API_KEY no está configurada.
    """
    api_key = os.environ.get('PINECONE_API_KEY', '')
    if not api_key:
        raise ValueError('PINECONE_API_KEY no configurada en .env')

    pc = Pinecone(api_key=api_key)
    index_name = os.environ.get('PINECONE_INDEX', 'minutas-index')

    existing = {idx.name for idx in pc.list_indexes()}
    if index_name not in existing:
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIM,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1'),
        )
        logger.info(f'Índice Pinecone "{index_name}" creado (dim={EMBEDDING_DIM}, cosine).')

    return pc.Index(index_name)


# ── Embeddings ──────────────────────────────────────────────────────────────

def generar_embedding(texto: str, task_type: str = 'retrieval_document') -> list:
    """
    Genera embedding usando la API REST v1 de Google directamente.
    (google-generativeai usa v1beta que no soporta modelos de embeddings)

    task_type='retrieval_document'  → para ingesta de chunks
    task_type='retrieval_query'     → para búsqueda en tiempo de inferencia
    """
    # La API REST espera UPPER_SNAKE_CASE
    task_map = {
        'retrieval_document': 'RETRIEVAL_DOCUMENT',
        'retrieval_query': 'RETRIEVAL_QUERY',
    }
    task = task_map.get(task_type, 'RETRIEVAL_DOCUMENT')

    api_key = os.environ.get('GEMINI_API_KEY', '')
    resp = requests.post(
        _EMBED_URL,
        params={'key': api_key},
        json={
            'model': f'models/{EMBEDDING_MODEL}',
            'content': {'parts': [{'text': texto}]},
            'taskType': task,
            'outputDimensionality': EMBEDDING_DIM,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['embedding']['values']


# ── Búsqueda RAG ────────────────────────────────────────────────────────────

def obtener_contexto_normativo(consulta: str, top_k: int = TOP_K_DEFAULT) -> str:
    """
    Busca los chunks normativos más relevantes en Pinecone y los retorna
    como un bloque de texto listo para insertar en el prompt de Gemini.

    Retorna string vacío si:
    - PINECONE_API_KEY no está configurada
    - Pinecone no tiene vectores en el namespace
    - Ocurre cualquier error de red o API

    Nunca lanza excepción — el prompt funciona igual sin contexto RAG.
    """
    if not os.environ.get('PINECONE_API_KEY'):
        return ''

    try:
        query_vector = generar_embedding(consulta, task_type='retrieval_query')
        index = _get_pinecone_index()
        namespace = os.environ.get('PINECONE_NAMESPACE', 'minutas')

        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
        )

        if not results.matches:
            return ''

        bloques = []
        for match in results.matches:
            md = match.metadata or {}
            fuente = md.get('source', 'Normativa PAE')
            chunk_id = md.get('chunk_id', '?')
            pagina = md.get('pagina', None)
            texto = md.get('text', '')
            if not texto:
                continue
            referencia = f'{fuente} | chunk {chunk_id}'
            if pagina:
                referencia += f' | pág. {pagina}'
            bloques.append(f'[{referencia}]\n{texto}')

        return '\n\n'.join(bloques)

    except Exception as e:
        logger.warning(f'RAG Pinecone falló (continuando sin contexto normativo): {e}')
        return ''


# ── Chunking ────────────────────────────────────────────────────────────────

def chunkar_texto(
    texto: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list:
    """
    Divide el texto en chunks usando una ventana deslizante.

    Normaliza espacios antes de chunkar (elimina saltos de línea múltiples,
    tabs, etc.) para mejorar calidad de embeddings en texto de PDF.

    Retorna lista de strings (chunks no vacíos).
    """
    # Normalizar: colapsar espacios y saltos de línea
    texto = ' '.join(texto.split())
    if not texto:
        return []

    chunks = []
    start = 0
    step = max(1, chunk_size - overlap)

    while start < len(texto):
        end = min(len(texto), start + chunk_size)
        chunk = texto[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
