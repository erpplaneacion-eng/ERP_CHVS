# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ERP_CHVS** is a Django 5.2.5 ERP system for managing Colombia's "Programa de Alimentación Escolar" (PAE). It handles billing/focalization lists, nutritional planning, institutional management, and AI-powered menu generation.

**Requirements**: Python 3.13+, PostgreSQL

**Deprecated**: `ocr_validation` and `iagenerativa` apps removed.
**Not yet active**: `Api/` app (Siesa ERP integration) — not in `INSTALLED_APPS`.

## Setup (run from `ERP_CHVS/`)

```bash
python -m venv .venv && source .venv/bin/activate
cd erp_chvs/
pip install -r requirements.txt
cp .env.example .env   # then edit with your credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver  # http://localhost:8000
```

## Common Commands (from `erp_chvs/`)

```bash
# Dev server
python manage.py runserver

# Migrations
python manage.py makemigrations && python manage.py migrate

# Testing
python manage.py test                  # All tests
python manage.py test nutricion.tests_guias_preparacion_excel --verbosity=2  # Single module
# Available test modules: nutricion.tests, nutricion.tests_guias_preparacion_excel,
#   nutricion.tests_paso2_preparaciones_editor, facturacion.tests, principal.tests
DJANGO_SETTINGS_MODULE=erp_chvs.settings pytest -v          # pytest (no pytest.ini)
DJANGO_SETTINGS_MODULE=erp_chvs.settings pytest -k "test_name"
DJANGO_SETTINGS_MODULE=erp_chvs.settings pytest facturacion/tests.py

# Static files (production)
python manage.py collectstatic

# Database
python manage.py loaddata backup_utf8.json
python manage.py dbshell

# Custom management commands
python manage.py setup_groups          # Create default RBAC groups
python manage.py optimizar_logos       # Optimize institution logos for PDFs
python manage.py inspeccionar_db       # Database structure inspector

# AI integration test
python test_gemini.py
```

## Project Structure

```
ERP_CHVS/
├── erp_chvs/              # Django project root (all commands run here)
│   ├── erp_chvs/          # Settings, URLs, WSGI/ASGI
│   ├── principal/         # Master data: departments, municipalities, institutions, schools
│   ├── nutricion/         # Nutritional planning, menus, AI generation
│   ├── planeacion/        # Programs, planning periods, rations
│   ├── facturacion/       # PAE focalization list processing (Excel → PDF)
│   ├── dashboard/         # Dashboard entry point
│   ├── Api/               # [Planned] Siesa ERP integration
│   ├── static/            # CSS/JS (module-specific subdirectories)
│   └── templates/         # base.html + app subdirectories
├── archivos excel/        # Excel input/output directory
├── Procfile               # Railway deployment config
└── railway.toml           # Railway deploy settings
```

## Architecture

### Django Apps

| App | Purpose |
|-----|---------|
| `principal` | Master data CRUD (departments, municipalities, institutions, sedes, modalities) |
| `nutricion` | Menus, preparations, ingredients, nutritional analysis, AI generation |
| `planeacion` | Programs, planning periods, ration configuration |
| `facturacion` | Excel focalization list upload, validation, PDF attendance reports |
| `costos` | Nutritional cost matrix (cross-tab menus × ingredients × levels), Excel export |
| `dashboard` | Main dashboard after login |

### Service-Oriented Architecture

Business logic lives in `services.py` or `services/` packages — **never in views**. Views only handle HTTP request/response.

**Facturacion** reference pattern:
```
views.py → services.py → persistence_service.py → models.py
                ↓
        data_processors.py, validators.py, fuzzy_matching.py
```

**Nutricion services** (`nutricion/services/`):
- `menu_service.py` — Menu CRUD, `generar_menu_con_ia()` orchestrator
- `gemini_service.py` — Gemini 2.5 Flash (temp=0.2), generates for ALL educational levels in one call
- `minuta_service.py` — Standard pattern menus from `nutricion/data/minuta_patron.json`
- `analisis_service.py` — Nutritional analysis + semaforización per level + modality
- `calculo_service.py` — Pure stateless calculation functions
- `exclusion_service.py` — Mutually exclusive food group sets: groups that share a weekly quota (e.g. G4+G6 must appear 2×/week combined, not individually). Used by `semanal.py` to adjust validator results.
- `restriccion_subgrupo_service.py` — Sub-restrictions within a group: requires that N of a group's weekly appearances use a specific whitelist of foods (e.g. G4 must include ≥1 egg and ≥2 legumes per week). Used by `semanal.py`.
- `preparacion_service.py`, `ingrediente_service.py`, `programa_service.py`

**Nutricion other key files**:
- `master_excel_generator.py` — Generates nutritional preparation guide Excel (`MasterNutritionalExcelGenerator`). Called from `exportes.py` → `GET /nutricion/exportar-guias-preparacion/<programa_id>/<modalidad_id>/`

**Nutricion views** (`nutricion/views/` package):
- `core.py` — Main views, `api_generar_menu_ia`
- `menus_api.py` — Menu CRUD API endpoints
- `preparaciones_api.py` — Preparations + ingredients API
- `analisis_api.py` — Nutritional analysis, weight sync (`api_guardar_ingredientes_por_nivel`)
- `exportes.py` — Excel/PDF downloads
- `semanal.py` — Weekly menu validation (`api_validar_semana`, `api_requerimientos_modalidad`)
- `preparaciones_editor.py` — Preparations editor view (standalone page with editable ingredient weights per level, dynamic peso bruto column, 4-state semaforización)
- `firmas.py` — Nutritional contract signatures (`FirmaNutricionalContrato` model, per-program form at `/nutricion/firmas-contrato/`)

### Key Model Relationships

```
PrincipalDepartamento → PrincipalMunicipio → InstitucionesEducativas → SedesEducativas
                                ↓
                            Programa → PlanificacionRaciones → ListadosFocalizacion

TablaMenus
    ├─→ TablaPreparaciones (shared across levels)
    │       └─→ TablaPreparacionIngredientes (M2M: gramaje + id_componente nullable)
    │               └─→ TablaAlimentos2018Icbf (via id_ingrediente_siesa)
    └─→ TablaAnalisisNutricionalMenu (ONE per educational level)
            └─→ TablaIngredientesPorNivel (weights + nutrients PER LEVEL)
                    Fields: peso_neto, peso_bruto, parte_comestible, calorias,
                            proteina, grasa, cho, calcio, hierro, sodio
                    FK: id_preparacion_ingrediente → TablaPreparacionIngredientes
                        (CASCADE; orphaned rows are deleted on migration 0029)

ModalidadesDeConsumo
    ├─→ RequerimientoSemanal (GruposAlimentos × frecuencia/week)
    ├─→ ComponentesModalidades (valid food components per modality)
    ├─→ GrupoExcluyenteSet → GrupoExcluyenteSetMiembro → GruposAlimentos
    │      (sets of food groups sharing a combined weekly quota)
    └─→ RestriccionAlimentoSubgrupo → RestriccionAlimentoEspecifico → TablaAlimentos2018Icbf
           (requires N appearances of a group to use foods from a whitelist)

TablaRequerimientosNutricionales (level + modality → nutritional targets)
    unique_together: [id_nivel_escolar_uapa, id_modalidad]
```

**Critical**: Primary ingredient weights (per educational level) are stored in `TablaIngredientesPorNivel`. `TablaPreparacionIngredientes` also has a nullable `gramaje` field (migration 0016) for a base reference weight and a nullable `id_componente` FK to `ComponentesAlimentos` (migration 0030) that overrides the ingredient's own component. Authoritative per-level weights always live in `TablaIngredientesPorNivel`.

`TablaIngredientesPorNivel.id_preparacion_ingrediente` (migration 0029, non-nullable) is the direct FK to the M2M row — use it for efficient lookups instead of matching via `(id_preparacion, codigo_icbf)`. Rows without a matching `TablaPreparacionIngredientes` record were deleted during migration.

**Level names** (database format): `prescolar`, `primaria_1_2_3`, `primaria_4_5`, `secundaria`, `media_ciclo_complementario`

**Critical**: `TablaGradosEscolaresUapa.id_grado_escolar_uapa` is a `CharField`, NOT an integer. Never sort by this field directly (alphabetical order breaks pedagogical order). Always sort using a known-order list:
```python
_ORDEN_NIVELES = ['prescolar', 'primaria_1_2_3', 'primaria_4_5', 'secundaria', 'media_ciclo_complementario']
sorted(queryset, key=lambda n: _ORDEN_NIVELES.index(n.nivel_escolar_uapa) if n.nivel_escolar_uapa in _ORDEN_NIVELES else 999)
```

### Frontend Architecture

- **Stack**: Bootstrap 5.3.3, SweetAlert2, jQuery, DataTables
- **Pattern**: AJAX with JSON API endpoints, modal dialogs for forms
- **Rule**: HTML/CSS/JS always in separate files. No inline styles or `onclick` attributes.

**Nutricion JS** (`static/js/nutricion/`):
- `main.js` — Entry point
- `menus_avanzado_refactorizado.js` — Main controller (dependency injection)
- `preparaciones_editor.js` — Standalone editor: dynamic peso bruto (`(peso_neto×100)/parte_comestible`), slider sync, 4-state semaforización
- `alimentos.js`, `menus.js` — Supplementary list views
- `core/` — Shared utilities: `api-client.js`, `modal-manager.js`, `utils.js`
- `modules/` — Single-responsibility managers:
  - `ModalesManager.js`, `FiltrosManager.js`, `ModalidadesManager.js`
  - `PreparacionesManager.js`, `IngredientesManager.js`
  - `AnalisisNutricionalManager.js`, `MenusEspecialesManager.js`
  - `calculos.js` — Nutritional calculation helpers
  - `guardado-automatico.js` — Auto-save during editing
  - `DIAGNOSTICO_FUNCIONES.js` — Diagnostic utilities

## Authentication & Authorization

- Login redirect → `/dashboard/`, logout → `/`
- **RBAC** via Django Groups (`principal.middleware.RoleAccessMiddleware`):

| Group | Access |
|-------|--------|
| `NUTRICION` | nutricion, dashboard, principal |
| `FACTURACION` | facturacion, dashboard |
| `PLANEACION` | planeacion, dashboard |
| `COSTOS` | costos, dashboard |
| `ADMINISTRACION` | nutricion, facturacion, planeacion, principal, costos, dashboard |

A user can belong to **multiple groups** — their allowed apps are the **union** of all group permissions. Superusers bypass all restrictions. Set up with `python manage.py setup_groups`.

**Template tag** (`principal/templatetags/group_tags.py`): `{% if user|has_group:"NUTRICION,ADMINISTRACION" %}` — accepts comma-separated group names, case-insensitive, returns True for superusers.

## Configuration (`.env` in `erp_chvs/`)

```bash
DJANGO_SECRET_KEY=your-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=erp_chvs
DB_USER=postgres
DB_PASSWORD=chvs2025
DB_HOST=localhost
DB_PORT=5432

GEMINI_API_KEY=your-key

# Production only (Cloudinary for media):
# CLOUDINARY_CLOUD_NAME=, CLOUDINARY_API_KEY=, CLOUDINARY_API_SECRET=
```

**DB variable priority**: `DATABASE_URL` (full URL, used by Railway) → `DB_*` variables → `PG*` variables (PGDATABASE, PGUSER, PGPASSWORD, PGHOST, PGPORT). Use `DATABASE_URL` in production.

`CSRF_TRUSTED_ORIGINS` values are auto-normalized (scheme added if missing) in `settings.py` via `_normalize_csrf_origin()`.

**Localization**: `LANGUAGE_CODE = 'es-col'`, `TIME_ZONE = 'America/Bogota'`, `DECIMAL_SEPARATOR = '.'` (point, not comma).

## Deployment (Railway)

- **Platform**: Railway.app
- **Config file**: `railway.toml` (Railway ignores `Procfile` when `railway.toml` exists — keep both in sync)
- **Start sequence**: `migrate --noinput` → `collectstatic --noinput --clear` → gunicorn
- **Gunicorn**: 1 worker sync + 2 threads, timeout 600s, max-requests 100, `--worker-tmp-dir /dev/shm`
- **Static files**: WhiteNoise middleware (no nginx needed); `STATICFILES_STORAGE = StaticFilesStorage`
- **Media**: Cloudinary in production (`DEBUG=False`); requires `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` env vars
- **Domain auto-detection**: settings.py reads `RAILWAY_PUBLIC_DOMAIN` (built-in Railway variable) first, falls back to `RAILWAY_STATIC_URL` (manual). Both auto-add to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Python version pinned in `runtime.txt`: `python-3.13.1`

**Required Railway env vars:**
```
DJANGO_SECRET_KEY=<generated>
DJANGO_DEBUG=False
GEMINI_API_KEY=<key>
DATABASE_URL=<auto-set by Railway Postgres plugin>
CLOUDINARY_CLOUD_NAME=<name>
CLOUDINARY_API_KEY=<key>
CLOUDINARY_API_SECRET=<secret>
```
`DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are auto-populated from `RAILWAY_PUBLIC_DOMAIN`, but can be overridden manually.

## Conventions

### Language
- **Spanish**: Model fields, business logic, comments, domain variable names
- **English**: Class definitions, Python/Django structural code

### Architecture
- Business logic in services, never in views
- Use `bulk_create` for batch inserts (see `persistence_service.py`)
- "BUGA" must always be treated as alias for "GUADALAJARA DE BUGA"
- `TablaAnalisisNutricionalMenu` uses `total_*` prefix: `total_calorias`, `total_proteina`, `total_grasa`, `total_cho`, `total_calcio`, `total_hierro`, `total_sodio`

### Frontend Performance
- Use `transition: specific-property` not `transition: all` (prevents unwanted load animations)
- Use `DocumentFragment` + single `appendChild` for multi-element DOM insertion
- Use `Promise.all()` for parallel independent API calls
- After CSS/JS changes: hard refresh with `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

## Nutritional Analysis — Semaforización

Two semaforización systems coexist:

**Lista de menús** (modal de análisis nutricional en `lista_menus.html`): 3 absolute states.

| State | Range | Color |
|-------|-------|-------|
| ÓPTIMO | 0–35% | Green |
| ACEPTABLE | 35.1–70% | Yellow |
| ALTO | >70% | Red |

**Editor de preparaciones** (`preparaciones_editor.py` / `preparaciones_editor.js`): 4-state proximity system using `AdecuacionTotalPorcentaje` as reference baseline. Denominator: `RecomendacionDiariaGradoMod` (with fallback to `TablaRequerimientosNutricionales`).

| State | Proximity to reference % | Color |
|-------|--------------------------|-------|
| `optimo` | ≤3 pts | Green |
| `azul` | 3–5 pts | Blue |
| `aceptable` | 5–7 pts | Yellow |
| `alto` | >7 pts | Red |

Key files: `nutricion/services/analisis_service.py`, `nutricion/models.py` (`TablaRequerimientosNutricionales`, `RecomendacionDiariaGradoMod`, `AdecuacionTotalPorcentaje`).

Weekly validation (component frequency): `nutricion/views/semanal.py`
- `GET /nutricion/api/validar-semana/?menu_ids=1,2,3&modalidad_id=5`
- `GET /nutricion/api/requerimientos-modalidad/?modalidad_id=5`
- Component lookup (`_resolver_grupo_preparacion`): Priority 1 → `TablaPreparaciones.id_componente.id_grupo_alimentos`; Priority 2 → iterate `prep.ingredientes.all()` and return first `TablaAlimentos2018Icbf.id_componente.id_grupo_alimentos`

## Important Workflows

### Facturacion: Excel Focalization Lists (Two-stage)
1. **Upload**: `excel_utils` → `data_processors` → `fuzzy_matching` (validate sedes) → show results
2. **Save**: User confirms → `PersistenceService.guardar_listados_focalizacion()` → `bulk_create` in atomic transaction

### Nutricion: AI Menu Generation
Single Gemini API call generates menus for ALL 5 educational levels:
```
MenuService.generar_menu_con_ia()
    → MinutaService (per level from minuta_patron.json)
    → GeminiService.generar_menu(niveles, minutas_por_nivel)
    → Atomic transaction:
        TablaMenus + TablaPreparaciones + TablaPreparacionIngredientes (M2M)
        FOR EACH LEVEL:
            TablaAnalisisNutricionalMenu
            TablaIngredientesPorNivel (peso_neto, peso_bruto, nutrients calculated)
```

### Nutricion: Copy Modality Between Programs
Button "Copiar desde otro programa" in `lista_menus.html` acordeón (visible only when a modality has 0 menus):
```
ModalidadesManager.js → abrirModalCopiar()
    → GET /nutricion/api/programas-con-modalidad/?modalidad_id=X&programa_excluir=Y
    → POST /nutricion/api/copiar-modalidad/  {programa_origen_id, programa_destino_id, modalidad_id}
    → MenuService.copiar_modalidad_completa()  (atomic transaction)
        Copies: TablaMenus → TablaPreparaciones → TablaPreparacionIngredientes
                TablaAnalisisNutricionalMenu → TablaIngredientesPorNivel
```
Key file: `nutricion/services/menu_service.py` — `copiar_modalidad_completa()`. Endpoints in `menus_api.py`.

## Production Gotchas

### Cloudinary y `FieldFile.path`
En producción (`DEBUG=False`), los archivos de media (logos, firmas) usan Cloudinary. **`FieldFile.path` lanza `NotImplementedError`** en storages de nube — Cloudinary no implementa `.path()`.

Siempre capturar las tres excepciones al acceder a `.path` de un `ImageField`/`FileField`:
```python
try:
    ruta = instancia.imagen.path
except (FileNotFoundError, ValueError, NotImplementedError):
    ruta = None
```
- `FileNotFoundError` — archivo local borrado físicamente
- `ValueError` — campo vacío o nombre inválido
- `NotImplementedError` — storage en nube (Cloudinary) no implementa `.path()`

**Archivos afectados**: `nutricion/services/analisis_service.py` — bloque `logo_path` y función `_path_or_none` (firmas).

### Static files en Railway
`WHITENOISE_USE_FINDERS = True` permite que WhiteNoise sirva archivos directamente desde `STATICFILES_DIRS` aunque `collectstatic` no los haya copiado a `STATIC_ROOT`. No usar `CompressedStaticFilesStorage` — genera `FileNotFoundError` con Python 3.13 por una condición de carrera en el ThreadPoolExecutor de compresión paralela.

## Database

- **Engine**: PostgreSQL, `CONN_MAX_AGE=600`, `CONN_HEALTH_CHECKS=True`
- **Migrations**: Per-app `migrations/` directories
- **Fixture backup**: `python manage.py loaddata backup_utf8.json`

## Logging

- **Console**: Always active for `facturacion` and `facturacion.pdf_generator` loggers
- **File** (`erp_chvs/logs/facturacion.log`): Only in DEBUG mode — Excel processing, validation, fuzzy matching, persistence errors
- Configured in `settings.py` LOGGING dict and `facturacion/logging_config.py`
