# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ERP_CHVS** is a Django 5.2.5 ERP system for managing Colombia's "Programa de Alimentación Escolar" (PAE - School Feeding Program). It handles billing/focalization lists, nutritional planning, and institutional management.

## Common Commands

All commands run from the `erp_chvs/` directory:

```bash
# Development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Testing
python manage.py test                    # Run all tests
python manage.py test facturacion        # Run tests for specific app
python manage.py test nutricion
pytest                                   # Run tests with pytest (pytest-django configured)

# Static files
python manage.py collectstatic

# Database operations
python manage.py loaddata <fixture>.json # Load data from fixtures
```

## Architecture

### Django Apps

| App | Purpose |
|-----|---------|
| `principal` | Master data: departments, municipalities, institutions, schools, document/gender types, consumption modalities, educational levels |
| `nutricion` | Nutritional planning: ICBF 2018 food tables, menus, preparations, ingredients, nutritional analysis |
| `planeacion` | Programs, planning periods, ration planning, institutional hierarchies |
| `facturacion` | PAE focalization list processing from Excel, attendance reports (PDF), beneficiary validation |
| `dashboard` | Main dashboard entry point |

### Service-Oriented Architecture (SOA)

Business logic resides in `services.py` or dedicated service modules, NOT in views. Views only handle HTTP request/response and call services.

**Facturacion module pattern** (reference architecture):
```
views.py → services.py → persistence_service.py → models.py
                ↓
        data_processors.py, validators.py, fuzzy_matching.py
```

**Layer responsibilities:**
- **views.py**: HTTP request/response handling, session management, template rendering/JSON responses
- **services.py**: Business logic orchestration, coordinates validators/processors/persistence
- **persistence_service.py**: Database operations, `bulk_create` for batch inserts, transaction management
- **data_processors.py**: Data cleaning, normalization, transformations (e.g., Excel → DataFrame)
- **validators.py**: Business rule validation
- **fuzzy_matching.py**: String matching algorithms (e.g., sede names with typos)

**Nutricion module services** (`nutricion/services/`):
- `MenuService`, `AnalisisNutricionalService`, `PreparacionService`
- `IngredienteService`, `ProgramaService`, `CalculoService`

### Key Model Relationships

```
PrincipalDepartamento → PrincipalMunicipio → InstitucionesEducativas → SedesEducativas
                                ↓
                            Programa → PlanificacionRaciones
                                ↓
                        ListadosFocalizacion

TablaMenus → TablaAnalisisNutricionalMenu
    ↓
ModalidadesDeConsumo ← TablaPreparaciones → TablaPreparacionIngredientes → TablaIngredientesSiesa
```

### Frontend Architecture

- **Templates**: `templates/` with `base.html` as root, app-specific subdirectories
- **Static files**: `static/css/` (global + module-specific), `static/js/` (modular architecture)
- **Stack**: Bootstrap 5.3.3, SweetAlert2, jQuery/DataTables
- **Pattern**: AJAX-heavy with JSON API endpoints, modal dialogs for forms

**Nutricion JS architecture** (refactored from 1644-line monolith):
- `core/`: `api-client.js`, `modal-manager.js`, `utils.js`
- `modules/`: Manager classes with single responsibility
  - `ModalesManager.js`: Modal lifecycle, z-index management
  - `FiltrosManager.js`: Municipality/program filters
  - `ModalidadesManager.js`: Consumption modalities, menu generation
  - `PreparacionesManager.js`: Preparation CRUD
  - `IngredientesManager.js`: Ingredient management with Select2
  - `AnalisisNutricionalManager.js`: Nutritional analysis by school level
  - `MenusEspecialesManager.js`: Special menu management
- `menus_avanzado_refactorizado.js`: Main controller coordinating all managers
- Auto-save in `guardado-automatico.js`
- **Compatibility**: Maintains global functions for HTML `onclick` attributes

## Conventions

### Language
- **Spanish**: Model fields, business logic, comments, variable names for domain entities
- **English**: Structural code, class definitions, Python/Django standards

### Architecture Patterns
- **Business logic in services**: NEVER put complex logic in views. Views delegate to `services.py`
- **Single responsibility**: Each service module has one clear purpose
- **Dependency injection**: Managers receive dependencies (e.g., `ModalesManager` injected into other managers)
- **Global compatibility**: Frontend managers expose global functions for existing HTML `onclick` handlers

### Data Processing
- **Municipio aliases**: Always handle "BUGA" as alias for "GUADALAJARA DE BUGA"
- **Bulk operations**: Use `bulk_create` for batch database inserts (see `persistence_service.py`)
- **Excel processing**: Specialized utilities in `excel_utils.py` per module (facturacion, nutricion)
- **Fuzzy matching**: Configurable threshold for matching external data to official records

### Configuration
- Environment variables via `.env`: `DJANGO_DEBUG`, `DB_*`, `GEMINI_API_KEY`
- Module constants in `config.py` files (thresholds, column names, messages)
- Locale: Spanish (Colombian) `es-col`, timezone `America/Bogota`
- Decimal separator: `.` (point) for consistency

## Database

- **Engine**: PostgreSQL
- **Connection pooling**: `CONN_MAX_AGE=600`
- Migrations per app in `migrations/` directories

## Key Dependencies

- **Framework**: Django 5.2.5, django-extensions
- **Database**: psycopg2-binary (PostgreSQL)
- **Data processing**: pandas, openpyxl, numpy
- **PDF generation**: reportlab, PyPDF2, pdf2image
- **Fuzzy matching**: fuzzywuzzy, Levenshtein, RapidFuzz
- **AI/Vision**: google-generativeai, landingai-ade
- **Image processing**: opencv-python, Pillow, pytesseract
- **Testing**: pytest, pytest-django
- **Environment**: python-dotenv

## Important Workflows

### Facturacion: Processing Excel Focalization Lists

Two-stage process to validate before saving:

1. **Stage 1: Upload & Validation**
   - User uploads Excel via `procesar_listados.html`
   - `views.py` → `ProcesamientoService.procesar_excel_...()`
   - Service coordinates: `excel_utils` (read) → `data_processors` (transform) → `fuzzy_matching` (validate sedes)
   - Results shown to user for verification

2. **Stage 2: Save to Database**
   - User confirms → `PersistenceService.guardar_listados_focalizacion()`
   - `bulk_create` for performance, fallback to one-by-one on errors
   - Atomic transactions ensure data integrity

### Nutricion: Menu Planning & Analysis

- Menus link to consumption modalities (breakfast, lunch, snack, etc.)
- Preparations contain ingredients from ICBF 2018 food tables
- Nutritional analysis calculates adequacy percentages per school level
- Frontend JS managers handle complex interactions with auto-save
- Master Excel generator produces planning documents
