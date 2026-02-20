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
python manage.py test nutricion.tests_sincronizacion_pesos --verbosity=2  # Single module
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

**Nutricion views** (`nutricion/views/` package):
- `core.py` — Main views, `api_generar_menu_ia`
- `menus_api.py` — Menu CRUD API endpoints
- `preparaciones_api.py` — Preparations + ingredients API
- `analisis_api.py` — Nutritional analysis, weight sync
- `exportes.py` — Excel/PDF downloads
- `semanal.py` — Weekly menu validation (`api_validar_semana`, `api_requerimientos_modalidad`)
- `preparaciones_editor.py` — Preparations editor view

### Key Model Relationships

```
PrincipalDepartamento → PrincipalMunicipio → InstitucionesEducativas → SedesEducativas
                                ↓
                            Programa → PlanificacionRaciones → ListadosFocalizacion

TablaMenus
    ├─→ TablaPreparaciones (shared across levels)
    │       └─→ TablaPreparacionIngredientes (M2M + optional gramaje field)
    │               └─→ TablaAlimentos2018Icbf (via codigo_icbf)
    └─→ TablaAnalisisNutricionalMenu (ONE per educational level)
            └─→ TablaIngredientesPorNivel (weights + nutrients PER LEVEL)
                    Fields: peso_neto, peso_bruto, calorias, proteina, grasa,
                            cho, calcio, hierro, sodio

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

**Critical**: Primary ingredient weights (per educational level) are stored in `TablaIngredientesPorNivel`. `TablaPreparacionIngredientes` also has a nullable `gramaje` field (added in migration 0016) for a base reference weight, but the authoritative per-level weights live in `TablaIngredientesPorNivel`.

**Level names** (database format): `prescolar`, `primaria_1_2_3`, `primaria_4_5`, `secundaria`, `media_ciclo_complementario`

### Frontend Architecture

- **Stack**: Bootstrap 5.3.3, SweetAlert2, jQuery, DataTables
- **Pattern**: AJAX with JSON API endpoints, modal dialogs for forms
- **Rule**: HTML/CSS/JS always in separate files. No inline styles or `onclick` attributes.

**Nutricion JS** (`static/js/nutricion/`):
- `main.js` — Entry point
- `menus_avanzado_refactorizado.js` — Main controller (dependency injection)
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
| `ADMINISTRACION` | All modules |

Superusers bypass all restrictions. Set up with `python manage.py setup_groups`.

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

`CSRF_TRUSTED_ORIGINS` values are auto-normalized (scheme added if missing) in `settings.py` via `_normalize_csrf_origin()`.

## Deployment (Railway)

- **Platform**: Railway.app
- **Procfile**: Runs migrate + collectstatic + gunicorn on startup
- **Static files**: WhiteNoise middleware (no nginx needed)
- **Media**: Cloudinary in production (`DEBUG=False`)
- `RAILWAY_STATIC_URL` env var auto-added to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Python version pinned in `runtime.txt`: `python-3.13.1`

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

The traffic-light system evaluates nutritional adequacy per **school level + consumption modality**. Each modality has its own 100% baseline from the Minuta Patrón ICBF.

| State | Range | Color |
|-------|-------|-------|
| ÓPTIMO | 0–35% | Green |
| ACEPTABLE | 35.1–70% | Yellow |
| ALTO | >70% | Red |

Key files: `nutricion/services/analisis_service.py`, `nutricion/models.py` (`TablaRequerimientosNutricionales`).

Weekly validation (component frequency): `nutricion/views/semanal.py`
- `GET /nutricion/api/validar-semana/?menu_ids=1,2,3&modalidad_id=5`
- `GET /nutricion/api/requerimientos-modalidad/?modalidad_id=5`
- Component lookup: checks `TablaPreparaciones.id_componente` first, then falls back to `TablaIngredientesSiesa.id_componente`

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

## Database

- **Engine**: PostgreSQL, `CONN_MAX_AGE=600`, `CONN_HEALTH_CHECKS=True`
- **Migrations**: Per-app `migrations/` directories
- **Fixture backup**: `python manage.py loaddata backup_utf8.json`

## Logging

- **Log dir**: `erp_chvs/logs/`
- **`facturacion.log`**: Excel processing, validation, fuzzy matching, persistence errors
- Configured in `facturacion/logging_config.py`
