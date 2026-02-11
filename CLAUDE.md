# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ERP_CHVS** is a Django 5.2.5 ERP system for managing Colombia's "Programa de Alimentación Escolar" (PAE - School Feeding Program). It handles billing/focalization lists, nutritional planning, institutional management, and AI-powered menu generation.

**Deprecated apps**: `ocr_validation` and `iagenerativa` have been removed from the project.

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

# AI/Gemini testing (from erp_chvs/ directory)
python test_gemini.py                    # Test Gemini AI menu generation
```

## Project Structure

```
ERP_CHVS/
├── erp_chvs/                  # Django project root
│   ├── manage.py              # Django management script
│   ├── test_gemini.py         # Standalone Gemini AI integration test
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables (not in git)
│   ├── erp_chvs/             # Project settings
│   ├── templates/            # Global templates
│   ├── static/               # Static files (CSS, JS)
│   ├── principal/            # Master data app
│   ├── nutricion/            # Nutrition planning app
│   ├── planeacion/           # Planning app
│   ├── facturacion/          # Billing/focalization app
│   └── dashboard/            # Dashboard app
└── archivos excel/           # Excel file input/output directory
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
- `MenuService`: Menu CRUD operations and business logic
- `GeminiService`: AI-powered menu generation using Google Gemini API
- `AnalisisNutricionalService`: Nutritional analysis calculations
- `PreparacionService`: Preparation management
- `IngredienteService`: Ingredient operations
- `ProgramaService`: Program-related operations
- `CalculoService`: Nutritional calculations and adequacy percentages

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

**Environment variables** (`.env` file):
- `DJANGO_SECRET_KEY`: Secret key for cryptographic signing
- `DJANGO_DEBUG`: Set to `True` for development, `False` for production
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL connection
- `GEMINI_API_KEY`: Google Gemini API key for AI menu generation

**Production security** (auto-enabled when `DEBUG=False`):
- HTTPS redirect, secure cookies, HSTS headers
- XSS and content-type sniffing protection
- Proxy SSL header support

**Application constants**:
- Module-specific in `config.py` files (thresholds, column names, messages)
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

**Menu creation workflow**:
- Menus link to consumption modalities (breakfast, lunch, snack, etc.)
- Each menu contains preparations with ingredients from ICBF 2018 food tables
- Nutritional analysis calculates adequacy percentages per school level (preescolar, primaria, bachillerato)
- Frontend JS managers (`menus_avanzado_refactorizado.js`) coordinate complex interactions
- Auto-save functionality (`guardado-automatico.js`) prevents data loss

**AI-powered menu generation** (GeminiService):
- Uses Google Gemini API to generate complete menu suggestions
- Takes consumption modality and nutritional requirements as input
- Returns structured menu with preparations and ingredients
- Test via `python test_gemini.py` from `erp_chvs/` directory

**Master Excel generator** (`master_excel_generator.py`):
- Produces comprehensive planning documents with nutritional breakdowns
- Includes drawings, charts, and formatted tables via `excel_drawing_utils.py`
- Exports menu cycles, ingredient lists, and cost calculations
- Used for official reporting and program documentation

### Facturacion: PDF Attendance Reports

**PDF generation workflow**:
- Uses `reportlab` for PDF creation (`pdf_generator.py`, `pdf_service.py`)
- Generates attendance reports from focalization data
- Supports batch processing of multiple reports
- Templates include institutional headers, beneficiary tables, and signatures
- Output stored in `archivos excel/` or configured output directory
