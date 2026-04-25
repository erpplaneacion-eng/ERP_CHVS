"""Cliente HTTP para el API REST de SIESA ERP.

Wrapper sobre `requests.Session` con:
- Autenticación HTTP Basic (credenciales en .env)
- Timeout configurable
- Retry simple ante fallos transitorios (5xx y errores de red)
- Logger dedicado `Api.siesa_client`
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger('Api.siesa_client')


ENDPOINTS = (
    'CENTROS-OPERACIONES',
    'INSTALACIONES',
    'TIPOS-DOCUMENTOS',
    'SOLICITANTES',
    'ITEMS',
    'UNIDADES-NEGOCIOS',
    'CCOSTOS',
    'PROYECTOS',
    'CONCEPTOS',
    'MOTIVOS',
    'UBICACIONES',  # alias real para "BODEGAS" en el Postman
)


class SiesaClientError(Exception):
    """Error en una llamada al API de SIESA después de agotar reintentos."""


class SiesaClient:
    def __init__(
        self,
        base_url: str | None = None,
        user: str | None = None,
        password: str | None = None,
        timeout: int | None = None,
        max_retries: int = 3,
        retry_backoff: float = 1.5,
    ) -> None:
        self.base_url = (base_url or os.environ.get('SIESA_API_BASE_URL', '')).rstrip('/')
        self.user = user or os.environ.get('SIESA_API_USER', '')
        self.password = password or os.environ.get('SIESA_API_PASSWORD', '')
        self.timeout = int(timeout if timeout is not None else os.environ.get('SIESA_API_TIMEOUT', 30))
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        if not self.base_url or not self.user or not self.password:
            raise SiesaClientError(
                'Faltan variables SIESA_API_BASE_URL / SIESA_API_USER / SIESA_API_PASSWORD en el entorno.'
            )

        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.user, self.password)
        self.session.headers.update({'Accept': 'application/json'})

    def get(self, endpoint: str, params: dict | None = None) -> Any:
        """GET a `<base_url>/<endpoint>`. Retorna el JSON parseado."""
        url = f'{self.base_url}/{endpoint.strip("/")}'
        last_exc: Exception | None = None

        for intento in range(1, self.max_retries + 1):
            try:
                logger.debug('GET %s (intento %s/%s)', url, intento, self.max_retries)
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = exc
                logger.warning('Fallo de red en %s: %s', url, exc)
            else:
                if resp.status_code == 401:
                    logger.error('401 en %s — credenciales SIESA inválidas o rotadas.', url)
                    raise SiesaClientError(f'401 Unauthorized en {endpoint}')
                if resp.status_code >= 500:
                    last_exc = SiesaClientError(f'{resp.status_code} en {endpoint}: {resp.text[:200]}')
                    logger.warning('5xx en %s: %s', url, resp.status_code)
                else:
                    resp.raise_for_status()
                    try:
                        return resp.json()
                    except ValueError as exc:
                        logger.error('Respuesta no-JSON en %s: %s', url, resp.text[:200])
                        raise SiesaClientError(f'Respuesta no-JSON en {endpoint}') from exc

            if intento < self.max_retries:
                time.sleep(self.retry_backoff ** intento)

        raise SiesaClientError(f'GET {endpoint} falló tras {self.max_retries} intentos: {last_exc}')

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> 'SiesaClient':
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
