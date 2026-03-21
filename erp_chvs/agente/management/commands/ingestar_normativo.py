"""
Management command para ingestar documentos normativos del PAE en Pinecone.

Soporta dos formatos:
  - JSON  (formato DocParse/LlamaParse): chunks ya extraídos con grounding de página.
  - PDF   (pypdf + fallback Gemini para PDFs escaneados): extracción + chunking manual.

Uso:
    python manage.py ingestar_normativo
        → busca archivos *.json y *.pdf en erp_chvs/agente/data/normativos/

    python manage.py ingestar_normativo --archivo /ruta/al/archivo.json
        → ingesta ese archivo específico (detecta extensión automáticamente)

    python manage.py ingestar_normativo --dry-run
        → muestra los chunks que se generarían sin guardar nada

    python manage.py ingestar_normativo --reimportar
        → borra el namespace y re-ingesta todos los archivos del directorio
"""

import json as _json
import re
import time
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from agente.services.rag_service import (
    chunkar_texto,
    generar_embedding,
    _get_pinecone_index,
    BATCH_SIZE,
)

# Tipos de chunk del formato JSON que NO aportan contenido útil para RAG
_JSON_TIPOS_IGNORAR = {'logo'}


class Command(BaseCommand):
    help = 'Ingesta documentos normativos del PAE (JSON o PDF) en Pinecone para RAG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            default=None,
            help='Ruta absoluta al archivo a ingestar (.json o .pdf). '
                 'Por defecto busca en agente/data/normativos/',
        )
        # Alias legacy para compatibilidad
        parser.add_argument(
            '--pdf',
            type=str,
            default=None,
            help='(Alias legacy de --archivo) Ruta a un PDF específico.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra los chunks que se generarían sin guardar nada en Pinecone.',
        )
        parser.add_argument(
            '--reimportar',
            action='store_true',
            help='Borra el namespace de Pinecone y re-ingesta desde cero.',
        )

    def handle(self, *args, **options):
        import os
        dry_run = options['dry_run']
        reimportar = options['reimportar']

        # ── Resolver archivos a procesar ────────────────────────────────────
        archivo_explicito = options.get('archivo') or options.get('pdf')
        if archivo_explicito:
            rutas = [Path(archivo_explicito)]
        else:
            from django.conf import settings
            data_dir = Path(settings.BASE_DIR) / 'agente' / 'data' / 'normativos'
            data_dir.mkdir(parents=True, exist_ok=True)
            rutas = sorted(data_dir.glob('*.json'))
            if not rutas:
                raise CommandError(
                    f'No hay archivos .json en {data_dir}\n'
                    'Copia el JSON normativo allí o usa --archivo /ruta/al/archivo'
                )

        for r in rutas:
            if not r.exists():
                raise CommandError(f'Archivo no encontrado: {r}')

        self.stdout.write(f'Archivos a ingestar: {len(rutas)}')

        # ── Conectar a Pinecone ─────────────────────────────────────────────
        if not dry_run:
            try:
                index = _get_pinecone_index()
            except ValueError as e:
                raise CommandError(str(e))

            namespace = os.environ.get('PINECONE_NAMESPACE', 'minutas')

            if reimportar:
                self.stdout.write('Borrando namespace existente en Pinecone...')
                try:
                    index.delete(delete_all=True, namespace=namespace)
                    self.stdout.write(self.style.WARNING('Namespace borrado.'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'No se pudo borrar namespace: {e}'))

        # ── Procesar cada archivo ────────────────────────────────────────────
        for ruta in rutas:
            self.stdout.write(f'\nArchivo: {ruta.name}')

            if ruta.suffix.lower() == '.json':
                all_chunks = self._procesar_json(ruta)
            else:
                all_chunks = self._procesar_pdf(ruta)

            self.stdout.write(f'   Chunks a indexar: {len(all_chunks)}')

            if dry_run:
                self.stdout.write(self.style.WARNING('\n[DRY-RUN] Primeros 3 chunks:'))
                for num, txt, pag in all_chunks[:3]:
                    self.stdout.write(f'  Chunk {num} (pág {pag}): {txt[:120]}...')
                continue

            # ── Generar embeddings y subir a Pinecone ────────────────────────
            self.stdout.write('   Generando embeddings y subiendo a Pinecone...')
            vectores_batch = []
            total = len(all_chunks)

            for i, (chunk_num, texto, pagina) in enumerate(all_chunks, start=1):
                embedding = None
                for intento in range(3):
                    try:
                        embedding = generar_embedding(texto, task_type='retrieval_document')
                        break
                    except Exception as e:
                        if intento < 2:
                            self.stdout.write(
                                f'   Reintentando chunk {chunk_num} (intento {intento + 2}/3)...'
                            )
                            time.sleep(2)
                        else:
                            self.stderr.write(
                                f'   ✗ Fallo definitivo en chunk {chunk_num}: {e}. Omitiendo.'
                            )

                if embedding is None:
                    continue

                stem_ascii = re.sub(r'[^A-Za-z0-9_-]', '_', ruta.stem[:30])
                vector_id = f'{stem_ascii}-{chunk_num}-{uuid.uuid4().hex[:6]}'
                vectores_batch.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': {
                        'source': ruta.name,
                        'chunk_id': chunk_num,
                        'text': texto,
                        'pagina': pagina,
                    },
                })

                if len(vectores_batch) >= BATCH_SIZE:
                    index.upsert(vectors=vectores_batch, namespace=namespace)
                    vectores_batch = []

                if i % 10 == 0 or i == total:
                    self.stdout.write(
                        f'   {i}/{total} chunks procesados...',
                        ending='\r'
                    )

                if i % 50 == 0:
                    time.sleep(1)

            if vectores_batch:
                index.upsert(vectors=vectores_batch, namespace=namespace)

            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'   OK Indexado: {ruta.name} | {total} chunks | namespace: {namespace}'
                )
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n[DRY-RUN] Ningún dato fue guardado en Pinecone.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nIngesta completada. El RAG está listo para usar.')
            )

    # ── Procesar JSON (formato DocParse/LlamaParse) ──────────────────────────

    def _procesar_json(self, json_path):
        """
        Lee un JSON con estructura:
            {
              "chunks": [{"markdown": "...", "type": "text|table|...", "grounding": {"page": N}}, ...],
              "metadata": {"filename": "...", "page_count": N}
            }

        Los chunks ya vienen pre-extraídos por el parser del documento.
        Se limpian las etiquetas HTML/Markdown y se descarta tipos no útiles (logo).

        Retorna lista de (numero_chunk, texto_limpio, pagina_1indexed).
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = _json.load(f)

        raw_chunks = data.get('chunks', [])
        page_count = data.get('metadata', {}).get('page_count', '?')
        self.stdout.write(f'   Páginas en documento: {page_count} | Chunks raw: {len(raw_chunks)}')

        all_chunks = []
        chunk_num = 1

        for c in raw_chunks:
            tipo = c.get('type', 'text')
            if tipo in _JSON_TIPOS_IGNORAR:
                continue

            markdown = c.get('markdown', '').strip()
            if not markdown:
                continue

            # Limpiar etiquetas HTML (<a>, <table>, <tr>, <td>, etc.) y IDs de anclaje
            texto = re.sub(r'<[^>]+>', ' ', markdown)
            # Colapsar espacios múltiples y saltos de línea
            texto = ' '.join(texto.split())

            if len(texto) < 20:
                continue

            # Página 0-indexed en el JSON → 1-indexed para metadatos
            pagina = c.get('grounding', {}).get('page', 0) + 1
            all_chunks.append((chunk_num, texto, pagina))
            chunk_num += 1

        tipos_usados = {}
        for c in raw_chunks:
            t = c.get('type', '?')
            tipos_usados[t] = tipos_usados.get(t, 0) + 1
        self.stdout.write(f'   Tipos de chunks: {tipos_usados}')
        self.stdout.write(f'   Chunks útiles (tras filtrar y limpiar): {len(all_chunks)}')

        return all_chunks

    # ── Procesar PDF (pypdf + fallback Gemini) ──────────────────────────────

    def _procesar_pdf(self, pdf_path):
        """
        Extrae texto de un PDF con pypdf página por página.
        Si el PDF está escaneado (sin texto extraíble), usa Gemini multimodal.
        Aplica chunking manual con ventana deslizante.

        Retorna lista de (numero_chunk, texto, pagina_1indexed).
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise CommandError(
                'pypdf no está instalado. Ejecuta: pip install pypdf>=5.5.0'
            )

        reader = PdfReader(str(pdf_path))
        total_paginas = len(reader.pages)
        self.stdout.write(f'   Páginas totales: {total_paginas}')

        paginas_con_texto = []
        for i, page in enumerate(reader.pages, start=1):
            texto = page.extract_text() or ''
            if texto.strip():
                paginas_con_texto.append((i, texto))

        self.stdout.write(f'   Páginas con texto (pypdf): {len(paginas_con_texto)}')

        if not paginas_con_texto:
            self.stdout.write(
                '   PDF escaneado detectado. Usando Gemini para extraer texto...'
            )
            paginas_con_texto = self._extraer_texto_con_gemini(pdf_path, total_paginas)
            self.stdout.write(f'   Páginas extraídas via Gemini: {len(paginas_con_texto)}')

        all_chunks = []
        chunk_num = 1
        for num_pagina, texto_pagina in paginas_con_texto:
            for chunk_texto in chunkar_texto(texto_pagina):
                all_chunks.append((chunk_num, chunk_texto, num_pagina))
                chunk_num += 1

        return all_chunks

    # ── Extracción de texto con Gemini (PDFs escaneados) ────────────────────

    def _extraer_texto_con_gemini(self, pdf_path, total_paginas):
        """
        Extrae texto de un PDF escaneado usando la File API de Gemini.
        Retorna lista de (numero_pagina, texto).
        """
        import os
        import time
        import google.generativeai as genai

        genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))

        self.stdout.write('   Subiendo PDF a Gemini File API...')
        archivo = genai.upload_file(str(pdf_path), mime_type='application/pdf')

        for _ in range(30):
            archivo = genai.get_file(archivo.name)
            if archivo.state.name != 'PROCESSING':
                break
            time.sleep(3)

        if archivo.state.name == 'FAILED':
            self.stderr.write('   Gemini falló al procesar el PDF. Abortando.')
            return []

        self.stdout.write('   Archivo listo. Extrayendo texto con Gemini...')
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = (
            f'Extrae TODO el texto de este PDF pagina por pagina. '
            f'Para cada pagina usa el formato exacto:\n'
            f'===PAGINA_N===\n<texto de la pagina>\n\n'
            f'Donde N es el numero de pagina (1, 2, 3...). '
            f'Extrae TODAS las {total_paginas} paginas. '
            f'Incluye tablas, titulos, encabezados, pie de pagina y todo el contenido textual. '
            f'Si una pagina solo tiene imagenes sin texto, escribe "===PAGINA_N===\n[imagen sin texto]".'
        )

        try:
            response = model.generate_content(
                [archivo, prompt],
                generation_config={'temperature': 0},
                request_options={'timeout': 300},
            )
            texto_respuesta = response.text
        except Exception as e:
            self.stderr.write(f'   Error en llamada a Gemini: {e}')
            return []
        finally:
            try:
                genai.delete_file(archivo.name)
            except Exception:
                pass

        partes = re.split(r'===PAGINA_(\d+)===', texto_respuesta)

        paginas_con_texto = []
        for i in range(1, len(partes), 2):
            try:
                num_pagina = int(partes[i])
                texto = partes[i + 1].strip() if i + 1 < len(partes) else ''
                if texto and texto != '[imagen sin texto]':
                    paginas_con_texto.append((num_pagina, texto))
            except (ValueError, IndexError):
                continue

        if not paginas_con_texto and texto_respuesta.strip():
            self.stdout.write(
                self.style.WARNING(
                    '   Gemini no usó marcadores de página. '
                    'Tratando respuesta como bloque único.'
                )
            )
            paginas_con_texto = [(1, texto_respuesta.strip())]

        return paginas_con_texto
