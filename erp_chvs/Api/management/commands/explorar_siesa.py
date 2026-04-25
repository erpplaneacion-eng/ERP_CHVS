"""Management command: explorar_siesa

Recorre los endpoints de catálogos de SIESA y guarda la respuesta cruda
como JSON en `logs/siesa_samples/<endpoint>.json`. Sirve para inspeccionar
la estructura real antes de crear los modelos locales (sub-fase B del plan).

Uso:
    python manage.py explorar_siesa
    python manage.py explorar_siesa --endpoint ITEMS
    python manage.py explorar_siesa --endpoint ITEMS --pretty
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from Api.services.siesa_client import ENDPOINTS, SiesaClient, SiesaClientError


class Command(BaseCommand):
    help = (
        'Llama los endpoints de SIESA y guarda la respuesta cruda en logs/siesa_samples/. '
        'Sirve para inspeccionar la estructura del JSON antes de modelar.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            type=str,
            default=None,
            help=f'Endpoint específico a explorar. Opciones: {", ".join(ENDPOINTS)}',
        )
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Guarda el JSON con indentación de 2 espacios (más legible).',
        )

    def handle(self, *args, **options):
        endpoint_filtro = options.get('endpoint')
        pretty = options.get('pretty', False)

        if endpoint_filtro and endpoint_filtro not in ENDPOINTS:
            raise CommandError(
                f"Endpoint '{endpoint_filtro}' no reconocido. Opciones: {', '.join(ENDPOINTS)}"
            )

        endpoints = [endpoint_filtro] if endpoint_filtro else list(ENDPOINTS)

        out_dir = Path(settings.BASE_DIR) / 'logs' / 'siesa_samples'
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            client = SiesaClient()
        except SiesaClientError as exc:
            raise CommandError(str(exc))

        self.stdout.write(f'Base URL: {client.base_url}')
        self.stdout.write(f'Salida:    {out_dir}\n')

        ok = 0
        errores = 0

        with client:
            for endpoint in endpoints:
                self.stdout.write(f'  >> {endpoint}... ', ending='')
                try:
                    payload = client.get(endpoint)
                except SiesaClientError as exc:
                    self.stdout.write(self.style.ERROR(f'ERROR: {exc}'))
                    errores += 1
                    continue

                destino = out_dir / f'{endpoint}.json'
                indent = 2 if pretty else None
                destino.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=indent),
                    encoding='utf-8',
                )

                count = self._contar_registros(payload)
                tamano_kb = os.path.getsize(destino) / 1024
                self.stdout.write(self.style.SUCCESS(
                    f'OK — {count} registros, {tamano_kb:.1f} KB'
                ))
                ok += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Completados: {ok}'))
        if errores:
            self.stdout.write(self.style.ERROR(f'Errores:     {errores}'))

    @staticmethod
    def _contar_registros(payload) -> str:
        if isinstance(payload, list):
            return str(len(payload))
        if isinstance(payload, dict):
            for clave_lista in ('data', 'items', 'results', 'records'):
                if isinstance(payload.get(clave_lista), list):
                    return f'{len(payload[clave_lista])} (en `{clave_lista}`)'
            return '1 (objeto)'
        return '?'
