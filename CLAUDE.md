# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ERP Django 5.2.5 para el **Programa de Alimentación Escolar (PAE)** de Colombia. Maneja listas de focalización, planificación nutricional, gestión institucional y generación de menús con IA.

**Requisitos**: Python 3.13+, PostgreSQL

---

## Guía por módulo

Cada app tiene su propio `CLAUDE.md` con modelos, servicios, endpoints y flujos detallados:

| App | Sub-CLAUDE.md | Descripción |
|-----|---------------|-------------|
| `principal` | [principal/CLAUDE.md](erp_chvs/principal/CLAUDE.md) | Datos maestros, RBAC, audit logging, template tags |
| `nutricion` | [nutricion/CLAUDE.md](erp_chvs/nutricion/CLAUDE.md) | Menús, preparaciones, análisis nutricional, semaforización, match ICBF |
| `planeacion` | [planeacion/CLAUDE.md](erp_chvs/planeacion/CLAUDE.md) | Programas, raciones, ciclos de menús, despachos hacia SIESA |
| `facturacion` | [facturacion/CLAUDE.md](erp_chvs/facturacion/CLAUDE.md) | Carga Excel PAE, PDFs de asistencia |
| `costos` | [costos/CLAUDE.md](erp_chvs/costos/CLAUDE.md) | Matriz de costos nutricionales, export Excel |
| `logistica` | [logistica/CLAUDE.md](erp_chvs/logistica/CLAUDE.md) | Rutas de entrega, asignación de sedes |
| `calidad` | [calidad/CLAUDE.md](erp_chvs/calidad/CLAUDE.md) | Certificados BPM, bot WhatsApp, PDF horizontal |
| `agente` | [agente/CLAUDE.md](erp_chvs/agente/CLAUDE.md) | Generador IA (Gemini), pool de borradores, RAG Pinecone |
| `contabilidad` | [contabilidad/CLAUDE.md](erp_chvs/contabilidad/CLAUDE.md) | Flujo multi-rol de facturas: Líder → Compras → Contabilidad |
| `dashboard` | [dashboard/CLAUDE.md](erp_chvs/dashboard/CLAUDE.md) | Punto de entrada post-login |
| `Api` | [Api/CLAUDE.md](erp_chvs/Api/CLAUDE.md) | Integración SIESA ERP: catálogos locales (CO, Proyectos, Items, Bodegas, etc.) |

---

## Setup (desde `ERP_CHVS/`)

```bash
python -m venv .venv && source .venv/bin/activate
cd erp_chvs/
pip install -r requirements.txt
cp .env.example .env   # editar con credenciales
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver  # http://localhost:8000
```

## Comandos comunes (desde `erp_chvs/`)

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations && python manage.py migrate

# Tests
python manage.py test                    # todos
python manage.py test nutricion.tests_guias_preparacion_excel --verbosity=2
# Con tests reales: nutricion, facturacion, principal
# Stubs vacíos: logistica, costos, planeacion, dashboard
DJANGO_SETTINGS_MODULE=erp_chvs.settings pytest -v

# Estáticos (producción)
python manage.py collectstatic

# Base de datos
python manage.py loaddata backup_utf8.json
python manage.py dbshell

# Comandos personalizados
python manage.py setup_groups          # Crea grupos RBAC por defecto
python manage.py optimizar_logos       # Optimiza logos de instituciones para PDFs
python manage.py inspeccionar_db       # Inspector de estructura de BD
python manage.py rellenar_pool         # Llena pool de borradores IA (min 20/modalidad)
python manage.py rellenar_pool --min 10 --modalidad "COMPLEMENTO PM"
python manage.py ingestar_normativo    # Ingesta normativos PAE a Pinecone (RAG)
python manage.py ingestar_normativo --archivo /ruta/archivo.json --dry-run
python manage.py explorar_siesa        # Descarga JSON crudo de los 11 endpoints SIESA a logs/siesa_samples/
python manage.py sync_siesa            # Sincroniza todos los catálogos SIESA a BD local (full sync)
python manage.py sync_siesa --catalogo PROYECTOS   # Solo un catálogo
python manage.py sync_siesa --dry-run  # Simula sin escribir en BD
```

## Estructura del proyecto

```
ERP_CHVS/
├── erp_chvs/              # Raíz Django (todos los comandos se ejecutan aquí)
│   ├── erp_chvs/          # Settings, URLs, WSGI/ASGI
│   ├── principal/         # Datos maestros + RBAC
│   ├── nutricion/         # Planificación nutricional
│   ├── planeacion/        # Programas y raciones
│   ├── facturacion/       # Listas PAE Excel → PDF
│   ├── costos/            # Matriz de costos
│   ├── logistica/         # Rutas de entrega
│   ├── calidad/           # Certificados BPM + WhatsApp
│   ├── agente/            # Generador IA (Gemini) + NIA chat
│   ├── contabilidad/      # Flujo contable de facturas
│   ├── dashboard/         # Entrada post-login
│   ├── Api/               # Integración SIESA ERP — catálogos locales activos
│   ├── static/            # CSS/JS por módulo
│   └── templates/         # base.html + subdirectorios por app
├── archivos excel/        # Directorio de entrada/salida Excel
├── Procfile               # Config Railway
└── railway.toml           # Config deploy Railway
```

## Arquitectura general

**Lógica de negocio en `services.py` o `services/`, nunca en views.** Las vistas solo manejan HTTP request/response.

> **Excepción heredada** (no replicar): `costos/views.py`, `logistica/views.py` y `planeacion/views.py` (`ciclos_menus`) contienen lógica directamente en la vista.

**Stack frontend**: Bootstrap 5.3.3, SweetAlert2, jQuery, DataTables. AJAX con endpoints JSON, modales para formularios. HTML/CSS/JS siempre en archivos separados — sin estilos inline ni atributos `onclick`.

**Relaciones maestras**:
```
PrincipalDepartamento → PrincipalMunicipio → InstitucionesEducativas → SedesEducativas
                                ↓
                            Programa → PlanificacionRaciones → ListadosFocalizacion

Api/ (catálogos SIESA — réplica fiel 1:1, solo lectura desde el ERP):
  SiesaProyecto, SiesaCentroCosto, SiesaUbicacion, SiesaItem, SiesaUnidadNegocio,
  SiesaCentroOperacion, SiesaInstalacion, SiesaTipoDocumento, SiesaConcepto, SiesaMotivo
  └── Los cruces con modelos del ERP se hacen en las apps consumidoras (planeacion, nutricion)
```

> **Gotcha de modelos duplicados**: `planeacion` define sus propios `InstitucionesEducativas` (`db_table='instituciones_educativas'`) y `SedesEducativas` (`db_table='sedes_educativas'`) que apuntan a las mismas tablas que `principal`. Al hacer queries cross-app, importar desde la app correcta según el contexto para evitar conflictos de migraciones.

## Autenticación y autorización

- Login → `/dashboard/`, logout → `/`
- RBAC via Django Groups (`principal.middleware.RoleAccessMiddleware`)
- Template tag: `{% if user|has_group:"NUTRICION,ADMINISTRACION" %}` (acepta coma-separated, case-insensitive, True para superusuarios)
- Ver tabla completa de grupos y accesos en [principal/CLAUDE.md](erp_chvs/principal/CLAUDE.md)

## Audit Logging — regla global

`RegistroActividad` es el modelo de audit log global (tabla `principal_registro_actividad`):

```python
from principal.models import RegistroActividad
RegistroActividad.registrar(request, 'modulo', 'accion', f"Descripción: {obj}")
```

**Reglas**:
- Llamar **después** de una escritura exitosa (POST/PUT/DELETE)
- **Nunca** dentro de handlers GET ni bloques `except`
- Silencia errores internamente — no interrumpe el flujo

## Patrón JS de managers (frontend)

Todas las apps usan el mismo patrón class-based iniciado en `principal/departamentos.js` (`DepartamentosManager`):

- Cache local (`this.allItems`) — filtros en cliente, sin re-fetch
- `applyFilters()` para búsqueda/filtrado en el DOM
- Guard anti-double-submit (`this.saving = true/false`)
- Modales con `modal.style.display = 'block'` — **sin Bootstrap Modal API**
- Modales de eliminación usan `.modal-header-danger` (rojo `#c0392b`) vs edición (azul `#1e3a8a`)

## NIA — Chat asistente IA

`agente` incluye un chat conversacional ("NIA") integrado en el panel de menús de nutrición:

- Contexto de actividad inyectado desde el servidor (programa, modalidad, menú activo)
- Tipos de mensaje: consulta nutricional, generación de preparación, análisis de menú
- Endpoint: `POST /agente/api/nia/chat/`
- Frontend: widget flotante en `static/js/agente/nia_chat.js`

## Configuración (`.env` en `erp_chvs/`)

```bash
DJANGO_SECRET_KEY=your-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos — prioridad: DATABASE_URL > DB_* > PG*
DB_NAME=erp_chvs
DB_USER=postgres
DB_PASSWORD=chvs2025
DB_HOST=localhost
DB_PORT=5432

GEMINI_API_KEY=your-key

# Agente — RAG via Pinecone (opcional; se desactiva silenciosamente si no se define)
# PINECONE_API_KEY=<key>
# PINECONE_INDEX=minutas-index
# PINECONE_NAMESPACE=minutas

# Calidad — WhatsApp bot
CALIDAD_WA_API_KEY=<compartida con ERP_API_KEY en servicio apiw>
EMPLEADOS_DB_URL=<URL PostgreSQL BD externa de empleados>

# Api — Integración SIESA ERP (catálogos locales)
SIESA_API_BASE_URL=http://31.97.103.246:9999/vsolidario/planeacion/api
SIESA_API_USER=admin
SIESA_API_PASSWORD=<ver credenciales SIESA>
SIESA_API_TIMEOUT=30

# Solo producción (Cloudinary para media):
# CLOUDINARY_CLOUD_NAME=  CLOUDINARY_API_KEY=  CLOUDINARY_API_SECRET=
```

**Localización**: `LANGUAGE_CODE = 'es-col'`, `TIME_ZONE = 'America/Bogota'`, `DECIMAL_SEPARATOR = '.'`

## Deployment (Railway)

- Config: `railway.toml` (Railway ignora `Procfile` cuando existe `railway.toml` — mantener ambos en sync)
- Secuencia de inicio: `migrate` → `collectstatic` → gunicorn (1 worker sync + 2 threads, timeout 600s)
- Static files: WhiteNoise (`WHITENOISE_USE_FINDERS = True`). **No usar** `CompressedStaticFilesStorage` (genera race condition con Python 3.13)
- Media: Cloudinary en producción (`DEBUG=False`)
- Python pinned en `runtime.txt`: `python-3.13.1`

**Variables Railway requeridas**:
```
DJANGO_SECRET_KEY, DJANGO_DEBUG=False, GEMINI_API_KEY
DATABASE_URL        (auto-set por Railway Postgres plugin)
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
CALIDAD_WA_API_KEY, EMPLEADOS_DB_URL
SIESA_API_BASE_URL, SIESA_API_USER, SIESA_API_PASSWORD, SIESA_API_TIMEOUT
# Opcional RAG: PINECONE_API_KEY
```

## Convenciones

- **Español**: campos de modelo, lógica de negocio, comentarios, variables de dominio
- **Inglés**: definiciones de clases, código estructural Python/Django
- `bulk_create` para inserts masivos
- `"BUGA"` siempre se trata como alias de `"GUADALAJARA DE BUGA"`
- **Frontend performance**: `transition: propiedad-específica` (nunca `transition: all`), `DocumentFragment` para inserciones múltiples, `Promise.all()` para APIs paralelas

## Cloudinary y `FieldFile.path` en producción

En producción (`DEBUG=False`), `FieldFile.path` lanza `NotImplementedError` — Cloudinary no implementa `.path()`. Siempre capturar las tres excepciones:

```python
try:
    ruta = instancia.imagen.path
except (FileNotFoundError, ValueError, NotImplementedError):
    ruta = None
```

Archivos afectados: `nutricion/services/analisis_service.py` (bloque `logo_path` y función `_path_or_none`).

## Base de datos

- PostgreSQL, `CONN_MAX_AGE=600`, `CONN_HEALTH_CHECKS=True`
- Migraciones: directorios `migrations/` por app
- Backup: `python manage.py loaddata backup_utf8.json`

## Apps eliminadas

- `ocr_validation`, `iagenerativa` — eliminadas
