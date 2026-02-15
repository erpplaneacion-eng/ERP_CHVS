# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ERP_CHVS** is a Django 5.2.5 ERP system for managing Colombia's "Programa de Alimentación Escolar" (PAE - School Feeding Program). It handles billing/focalization lists, nutritional planning, institutional management, and AI-powered menu generation.

**Requirements**: Python 3.13+, PostgreSQL

**Deprecated apps**: `ocr_validation` and `iagenerativa` have been removed from the project.

**In development**: `Api/` app exists for future integration with Siesa ERP system (automatic synchronization of raw materials, prices, and educational facilities). Currently not installed in `INSTALLED_APPS`.

## Initial Setup

First-time setup instructions (run from project root `ERP_CHVS/`):

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 3. Install dependencies
cd erp_chvs/
pip install -r requirements.txt

# 4. Create .env file (see Configuration section for required variables)
cp .env.example .env  # If example exists, or create manually
# Edit .env with your database credentials and API keys

# 5. Create PostgreSQL database
# Option A: Using psql
psql -U postgres -c "CREATE DATABASE erp_chvs;"
# Option B: Using createdb
createdb -U postgres erp_chvs

# 6. Run migrations
python manage.py migrate

# 7. Create superuser (for admin access)
python manage.py createsuperuser

# 8. Run development server
python manage.py runserver
# Access at: http://localhost:8000
```

## Authentication

- **Login redirect**: `/dashboard/` (after successful login)
- **Logout redirect**: `/` (home page)
- Uses Django's built-in authentication system
- No custom user model (uses `django.contrib.auth.models.User`)

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
pytest -v                                # Verbose output
pytest -k "test_name"                    # Run specific test by name
pytest --maxfail=1                       # Stop on first failure
pytest facturacion/tests.py              # Run tests from specific file

# Static files
python manage.py collectstatic

# Database operations
python manage.py loaddata <fixture>.json # Load data from fixtures
python manage.py loaddata backup_utf8.json # Load backup data
python manage.py dumpdata > backup.json  # Create database backup
python manage.py dbshell                 # Open PostgreSQL shell
python manage.py flush                   # Clear all data (DESTRUCTIVE - prompts for confirmation)

# AI/Gemini testing (from erp_chvs/ directory)
python test_gemini.py                    # Test Gemini AI menu generation

# Admin operations
python manage.py createsuperuser         # Create admin user
python manage.py changepassword <username> # Change user password

# Note: django-extensions is temporarily commented out in INSTALLED_APPS
# Uncomment in settings.py to use shell_plus and other utilities:
# python manage.py shell_plus              # Enhanced shell with auto-imports
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
│   ├── media/                # User-uploaded files (if implemented)
│   ├── Api/                  # Siesa integration app (not yet active)
│   ├── principal/            # Master data app
│   ├── nutricion/            # Nutrition planning app
│   ├── planeacion/           # Planning app
│   ├── facturacion/          # Billing/focalization app
│   └── dashboard/            # Dashboard app
├── archivos excel/           # Excel file input/output directory
└── CHECKLIST_INTEGRACION_SIESA.md  # Siesa integration requirements
```

## Architecture

### Django Apps

| App | Purpose | Status |
|-----|---------|--------|
| `principal` | Master data: departments, municipalities, institutions, schools, document/gender types, consumption modalities, educational levels | ✅ Active |
| `nutricion` | Nutritional planning: ICBF 2018 food tables, menus, preparations, ingredients, nutritional analysis | ✅ Active |
| `planeacion` | Programs, planning periods, ration planning, institutional hierarchies | ✅ Active |
| `facturacion` | PAE focalization list processing from Excel, attendance reports (PDF), beneficiary validation | ✅ Active |
| `dashboard` | Main dashboard entry point | ✅ Active |
| `Api` | **[In Development]** Siesa ERP integration: automatic sync of raw materials, prices, educational facilities | 🚧 Planned |

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
  - `generar_menu_con_ia()`: Multi-level AI menu generation orchestrator
  - Handles menu creation, preparation management, and nutritional analysis
- `GeminiService`: AI-powered menu generation using Google Gemini API
  - Model: `gemini-2.5-flash` with `temperature=0.2`
  - Generates menus with specific weights for ALL educational levels in one call
  - Optimized token usage through compressed food database context
- `MinutaService`: Standard pattern menu (Minuta Patrón) management
  - Loads from `nutricion/data/minuta_patron.json`
  - Handles normalization between database and JSON level names
- `AnalisisNutricionalService`: Nutritional analysis calculations
- `PreparacionService`: Preparation management
- `IngredienteService`: Ingredient operations
- `ProgramaService`: Program-related operations
- `CalculoService`: Pure nutritional calculation functions
  - `calcular_valores_nutricionales_alimento()`: Calculate nutrients from ICBF data
  - `calcular_peso_bruto()`: Calculate gross weight from net weight
  - Stateless pure functions for easy testing

### Key Model Relationships

```
PrincipalDepartamento → PrincipalMunicipio → InstitucionesEducativas → SedesEducativas
                                ↓
                            Programa → PlanificacionRaciones
                                ↓
                        ListadosFocalizacion

TablaMenus (menu base)
    ↓
TablaPreparaciones (preparations, shared across levels)
    ↓
TablaPreparacionIngredientes (M2M relation, NO weights stored here)
    ↓
TablaIngredientesSiesa ↔ TablaAlimentos2018Icbf

TablaMenus
    ↓
TablaAnalisisNutricionalMenu (ONE per educational level)
    ↓
TablaIngredientesPorNivel (weights + calculated nutrients PER LEVEL)
    - Links to: TablaAnalisisNutricionalMenu, TablaPreparaciones, TablaIngredientesSiesa
    - Stores: peso_neto, peso_bruto, calorias, proteina, grasa, cho, calcio, hierro, sodio
```

### Frontend Architecture

- **Templates**: `templates/` with `base.html` as root, app-specific subdirectories
- **Static files**: `static/css/` (global + module-specific), `static/js/` (modular architecture)
- **Stack**: Bootstrap 5.3.3, SweetAlert2, jQuery/DataTables
- **Pattern**: AJAX-heavy with JSON API endpoints, modal dialogs for forms
- **Separation of concerns**: HTML/CSS/JS always in separate files, NO inline styles or scripts
- **Event handling**: Use `addEventListener` in JS files, avoid inline `onclick` attributes

**Nutricion JS architecture** (refactored from 1644-line monolith to modular system):

**Before refactoring**: Single `menus_avanzado.js` file (1644 lines) - difficult to maintain, debug, and test

**After refactoring**: 8 specialized modules (2350 lines total, main controller reduced to 450 lines)

- **Core utilities** (`core/`):
  - `api-client.js`: Centralized API communication layer
  - `modal-manager.js`: Modal lifecycle and z-index management
  - `utils.js`: Shared utility functions

- **Manager modules** (`modules/`): Single Responsibility Principle
  - `ModalesManager.js` (200 lines): Modal lifecycle, z-index for nested modals, close handlers
  - `FiltrosManager.js` (200 lines): Municipality/program filters, callback orchestration
  - `ModalidadesManager.js` (300 lines): Consumption modalities, accordion generation, AI menu triggers
  - `PreparacionesManager.js` (300 lines): Preparation CRUD operations, copy between modalities
  - `IngredientesManager.js` (250 lines): Ingredient management with Select2 integration
  - `AnalisisNutricionalManager.js` (400 lines): Nutritional analysis by school level, recalculations
  - `MenusEspecialesManager.js` (250 lines): Special menu CRUD, validation, duplication

- **Main controller**: `menus_avanzado_refactorizado.js` (450 lines)
  - Initializes all managers via dependency injection
  - Configures inter-module communication
  - Exposes global functions for HTML `onclick` compatibility
  - Coordinates complex workflows across managers

- **Legacy backup**: `menus_avanzado.js` preserved for rollback if needed
- **Auto-save**: `guardado-automatico.js` prevents data loss during editing
- **Testing**: `modules/test_refactorizacion.html` and `TESTS_REFACTORIZACION.md` for validation
- **Documentation**: `RESUMEN_REFACTORIZACION.md` explains architecture decisions

**Integration pattern**:
```
MenusAvanzadosController (coordinator)
    ├─→ FiltrosManager → triggers program load
    ├─→ ModalidadesManager → loads modalities/menus
    ├─→ PreparacionesManager (injects IngredientesManager, ModalesManager)
    ├─→ IngredientesManager (injects ModalesManager)
    ├─→ AnalisisNutricionalManager (injects ModalesManager)
    ├─→ MenusEspecialesManager → triggers refresh
    └─→ ModalesManager → manages all modal dialogs
```

## Data Files

### Nutricion Module Data
- **`nutricion/data/minuta_patron.json`** (39KB): Standard pattern menus (Minuta Patrón)
  - Contains default menu templates for all 5 educational levels
  - Used by `MinutaService` as reference for AI menu generation
  - Level names in JSON format differ from database format (handled by `MinutaService` normalization)
  - Structure: `{ "modalidad": { "nivel": { "preparaciones": [...] } } }`

- **`nutricion/data/geminia.md`**: Historical implementation plan for Gemini AI integration
  - Documents original architecture decisions for AI menu generation
  - 5-step implementation plan: Infrastructure → Prompt Engineering → Persistence → Validation → UI
  - Reference document, not actively used in runtime

### Other Data Files
- **`erp_chvs/GEMINI.md`**: Historical context document (predates this CLAUDE.md)
  - Contains similar architectural information but less detailed
  - Keep for reference but CLAUDE.md is the authoritative source

- **`erp_chvs/backup_utf8.json`**: Database fixture backup
  - Can be loaded with `python manage.py loaddata backup_utf8.json`
  - Useful for restoring test data or migrating between environments

## Recent Improvements (2025)

### Principal Module - Municipio Modalidades Management
**New feature** (February 2025):
- Dashboard card to manage which consumption modalities are enabled per municipality
- URL: `/principal/municipio-modalidades/`
- View: `municipio_modalidades(request)` in `principal/views.py`
- Complete separation of concerns:
  - Template: `templates/principal/municipio_modalidades.html`
  - CSS: `static/css/principal/municipio_modalidades.css`
  - JS: `static/js/principal/municipios_modalidades.js` (event listeners, no inline handlers)
- Features:
  - Accordion UI for municipalities with active programs
  - Toggle switches for enabling/disabling modalities
  - Pending changes tracking before save
  - Search/filter by municipality name or code
  - Bulk save with API endpoint: `/principal/api/municipio-modalidades/guardar/`

### Nutricion Module - Multi-level AI Menu Generation
**What was fixed**:
- ❌ Before: Gemini generated menus for only ONE educational level
- ✅ After: Generates for ALL 5 levels in one API call
- ❌ Before: Weights were not stored (only M2M relations)
- ✅ After: Weights stored in `TablaIngredientesPorNivel` with calculated nutrients

**Key changes**:
1. `GeminiService.generar_menu()`: Now accepts `niveles_educativos` list and `minuta_patron_contexts` dict
2. `MenuService.generar_menu_con_ia()`: Refactored to create `TablaAnalisisNutricionalMenu` per level
3. `CalculoService`: Added `calcular_valores_nutricionales_alimento()` for automatic nutrient calculation
4. `MinutaService`: Fixed level name normalization (bidirectional mapping)

**Data flow**:
```
1 menu → N preparations (shared) → M ingredients (shared)
1 menu → 5 analysis (one per level) → K ingredient weights (specific per level)
```

**Testing**: `python test_gemini.py` validates multi-level generation with weight storage

### Nutricion Module - UI Performance Optimizations
**Performance improvements** (February 2025):
- **Eliminated gradual animations** when loading existing data:
  - Removed `@keyframes slideIn` and `@keyframes slideDown` animations from `lista_menus.css`
  - Changed `transition: all` to specific properties to prevent unwanted animations on initial render
  - Affected classes: `.ingrediente-item`, `.preparacion-accordion-header`, `.fila-ingrediente`
- **Optimized preparation loading** (`PreparacionesManager.js`):
  - Uses `Promise.all()` to fetch all ingredient counts in parallel (not sequential)
  - Creates all DOM elements first, then inserts with `DocumentFragment` (single reflow)
  - Before: Elements appeared gradually as they were added one-by-one
  - After: All elements appear instantly
- **Result**: Faster, more responsive UI when managing menus with many preparations/ingredients

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

### Frontend Performance
- **CSS transitions**: Use specific properties (e.g., `transition: border-color 0.2s, box-shadow 0.2s`) instead of `transition: all`
  - `transition: all` causes unwanted animations when elements first appear in DOM
  - Only animate properties that actually change on interaction (hover, focus, etc.)
- **DOM insertion**: For multiple elements, use `DocumentFragment` and `appendChild` once
  - ❌ Bad: Loop with individual `appendChild` calls (causes gradual rendering)
  - ✅ Good: Create all elements, add to fragment, append fragment once
- **Parallel async operations**: Use `Promise.all()` for independent API calls
  - Example: `PreparacionesManager.cargarPreparacionesMenu()` loads all ingredient counts in parallel
- **Browser cache**: When CSS/JS changes don't appear, instruct users to hard refresh:
  - Windows/Linux: `Ctrl + Shift + R` or `Ctrl + F5`
  - Mac: `Cmd + Shift + R`

### Configuration

**Environment variables** (`.env` file in `erp_chvs/` directory):

*Core Django settings*:
- `DJANGO_SECRET_KEY`: Secret key for cryptographic signing
- `DJANGO_DEBUG`: Set to `True` for development, `False` for production
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins (scheme auto-added if missing)

*Database (PostgreSQL)*:
- `DB_NAME`: Database name (default: `erp_chvs`)
- `DB_USER`: Database user (default: `postgres`)
- `DB_PASSWORD`: Database password (default: `chvs2025`)
- `DB_HOST`: Database host (default: `localhost`)
- `DB_PORT`: Database port (default: `5432`)

*AI Integration*:
- `GEMINI_API_KEY`: Google Gemini API key for AI menu generation

*Siesa Integration (planned)*:
- `SIESA_API_BASE_URL`: Base URL for Siesa API
- `SIESA_API_KEY`: Authentication token/key for Siesa
- `SIESA_API_USER`: API username (if using basic auth)
- `SIESA_API_PASSWORD`: API password (if using basic auth)
- `SIESA_COMPANY_ID`: Company identifier in Siesa
- `SIESA_SYNC_ENABLED`: Enable/disable automatic sync (default: `False`)
- `SIESA_SYNC_INTERVAL`: Sync interval in seconds (default: `300`)
- See `CHECKLIST_INTEGRACION_SIESA.md` for complete configuration details

**Example .env file**:
```bash
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=erp_chvs
DB_USER=postgres
DB_PASSWORD=chvs2025
DB_HOST=localhost
DB_PORT=5432

# AI Integration
GEMINI_API_KEY=your-gemini-api-key-here

# Siesa Integration (when implemented)
# SIESA_API_BASE_URL=https://api.siesa.com
# SIESA_API_KEY=your-api-key
# SIESA_COMPANY_ID=your-company-id
# SIESA_SYNC_ENABLED=False
```

**Production security** (auto-enabled when `DEBUG=False`):
- HTTPS redirect, secure cookies, HSTS headers
- XSS and content-type sniffing protection
- Proxy SSL header support

**Media files**:
- `MEDIA_URL = '/media/'`
- `MEDIA_ROOT`: Points to `erp_chvs/media/` directory
- Used for user-uploaded files (prepared for future features)

**Application constants**:
- Module-specific in `config.py` files (thresholds, column names, messages)
- Locale: Spanish (Colombian) `es-col`, timezone `America/Bogota`
- Decimal separator: `.` (point) for consistency

## Database

- **Engine**: PostgreSQL
- **Connection pooling**: `CONN_MAX_AGE=600` (10 minutes persistent connections)
- **Health checks**: `CONN_HEALTH_CHECKS=True` (automatic connection validation)
- **Connection timeout**: 10 seconds
- **Default credentials**: Database: `erp_chvs`, User: `postgres`, Port: `5432`
- **Migrations**: Per-app in `migrations/` directories
- **Character encoding**: UTF-8
- **Timezone**: America/Bogota (matches Django `TIME_ZONE` setting)

## Logging

**Log directory**: `erp_chvs/logs/`

**Active logs**:
- `facturacion.log`: Logs from facturacion module (Excel processing, validation, persistence)
  - Configured in `facturacion/logging_config.py`
  - Tracks processing workflow, fuzzy matching results, and errors
  - Useful for debugging Excel upload issues and data validation

**Log format**: Standard Python logging with timestamps, levels, and module names

**Viewing logs**:
```bash
# View recent facturacion logs
tail -f erp_chvs/logs/facturacion.log

# Search for errors
grep ERROR erp_chvs/logs/facturacion.log
```

## Key Dependencies

**Note**: `requirements.txt` may display encoding issues when viewed directly, but dependencies install correctly via `pip install -r requirements.txt`.

- **Framework**: Django 5.2.5, django-extensions (temporarily disabled in INSTALLED_APPS)
- **Database**: psycopg2-binary (PostgreSQL adapter)
- **Data processing**: pandas, openpyxl, numpy
- **PDF generation**: reportlab, PyPDF2, pdf2image
- **Fuzzy matching**: fuzzywuzzy, python-Levenshtein, RapidFuzz
- **AI/LLM**: google-generativeai (Gemini 2.5 Flash), google-ai-generativelanguage
- **Vision/OCR**: landingai-ade, opencv-python, Pillow, pytesseract
- **Testing**: pytest, pytest-django
- **Environment**: python-dotenv
- **Async tasks** (for Siesa sync, when implemented): Consider Celery or Django-Q

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

**AI-powered menu generation - Multi-level architecture** (GeminiService):

1. **Single API call for all levels**: Generates menus with specific weights for ALL educational levels
   - Levels: `prescolar`, `primaria_1_2_3`, `primaria_4_5`, `secundaria`, `media_ciclo_complementario`
   - Input: Minuta Patrón (standard patterns) for each level from `minuta_patron.json`
   - Output: Structured JSON with `ingredientes_por_nivel` (ingredients per level)

2. **Data flow**:
   ```
   MenuService.generar_menu_con_ia()
       ↓
   MinutaService.obtener_por_modalidad_y_nivel() (for each level)
       ↓
   GeminiService.generar_menu(niveles, minutas_por_nivel)
       ↓
   Atomic transaction:
       - Create TablaMenus (base menu)
       - Create TablaPreparaciones (shared preparations)
       - Create TablaPreparacionIngredientes (M2M, no weights)
       - FOR EACH LEVEL:
           - Create TablaAnalisisNutricionalMenu
           - Create TablaIngredientesPorNivel (with weights + calculated nutrients)
           - Calculate totals: CalculoService.calcular_valores_nutricionales_alimento()
   ```

3. **Weight storage**:
   - ❌ **NOT** in `TablaPreparacionIngredientes` (only M2M relation)
   - ✅ **YES** in `TablaIngredientesPorNivel`:
     - `peso_neto`: Net weight in grams
     - `peso_bruto`: Gross weight (calculated from edible portion)
     - Calculated nutrients: `calorias`, `proteina`, `grasa`, `cho`, `calcio`, `hierro`, `sodio`

4. **Level name normalization**:
   - Database: `prescolar`, `primaria_1_2_3`, `primaria_4_5`, `secundaria`, `media_ciclo_complementario`
   - JSON (Minutas): `"Preescolar"`, `"Primaria (primero, segundo y tercero)"`, etc.
   - `MinutaService` handles bidirectional mapping

5. **Testing**:
   ```bash
   cd erp_chvs/
   python test_gemini.py  # Validates multi-level generation
   ```

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

### Siesa Integration (Planned Implementation)

**Current situation**:
- Manual process: User downloads Excel files from Siesa → uploads to ERP_CHVS
- Error-prone due to manual file manipulation
- No real-time data synchronization

**Planned solution**:
- App `Api/` will handle automatic bidirectional sync with Siesa ERP
- Real-time synchronization via API REST (webhooks + polling fallback)
- Eliminates manual Excel download/upload workflow

**Architecture design** (when implemented):
```
Siesa ERP (creates/updates record)
    ↓
[Webhook notification] or [Polling every 5 min]
    ↓
Api/views.webhook_siesa()
    ↓
Api/services/sync_orchestrator.py
    ↓
├─→ MateriaPrimaSyncService → TablaIngredientesSiesa
├─→ PrecioSyncService → Update ingredient prices
└─→ SedeSyncService → SedesEducativas (with Siesa codes)
    ↓
Log to Api.models.SyncLog
```

**Entities to synchronize**:
1. **Raw materials** (Siesa → `nutricion.TablaIngredientesSiesa`)
   - Fields: `codigo_siesa`, `descripcion`, `unidad_medida`, `precio`
2. **Purchase prices** (Siesa → `TablaIngredientesSiesa.precio`)
   - Real-time price updates for cost calculations
3. **Educational facilities** (Siesa → `principal.SedesEducativas`)
   - Sync Siesa facility codes for cross-system compatibility

**Implementation checklist**: See `CHECKLIST_INTEGRACION_SIESA.md` for:
- Required API credentials and endpoints
- Data structure mapping (Siesa fields → Django models)
- Webhook configuration
- Rate limiting and pagination details
- Testing environment setup

**Commands** (when implemented):
```bash
# Manual sync trigger (fallback option)
python manage.py sync_siesa --all
python manage.py sync_siesa --materias-primas
python manage.py sync_siesa --precios
python manage.py sync_siesa --sedes

# View sync logs
# Dashboard will show sync status, errors, and last sync timestamp
```

**Service layer structure** (planned):
- `Api/services/siesa_client.py`: HTTP client for Siesa API (auth, retries, caching)
- `Api/services/sync_orchestrator.py`: Coordinates sync operations
- `Api/services/materia_prima_sync.py`: Raw material sync logic
- `Api/services/precio_sync.py`: Price synchronization
- `Api/services/sede_sync.py`: Educational facility sync
- `Api/utils/field_mapping.py`: Siesa ↔ Django field mappings
- `Api/models.py`: `SyncLog`, `SyncError` for audit trail

## Common Issues & Solutions

### Django Configuration

**Issue**: `SystemCheckError: (4_0.E001) CSRF_TRUSTED_ORIGINS must start with a scheme`
- **Cause**: Django 4+ requires all CSRF_TRUSTED_ORIGINS values to have `http://` or `https://` scheme
- **Solution**: Values are now automatically normalized in `settings.py` via `_normalize_csrf_origin()`
  - Localhost/127.0.0.1/0.0.0.0 → adds `http://`
  - Production domains → adds `https://`
- **Configuration**: Can configure with or without scheme in environment variables:
  ```bash
  # Both formats work:
  CSRF_TRUSTED_ORIGINS=erpchvs-production.up.railway.app
  CSRF_TRUSTED_ORIGINS=https://erpchvs-production.up.railway.app
  ```
- **Fixed in**: February 2025 - added normalization to `RAILWAY_STATIC_URL` handling

### Nutricion Module - AI Menu Generation

**Issue**: Weights not appearing in nutritional analysis
- **Cause**: Weights stored in wrong table (`TablaPreparacionIngredientes` instead of `TablaIngredientesPorNivel`)
- **Solution**: Always use `TablaIngredientesPorNivel` for weight + nutrient storage
- **Verification**: Check `TablaAnalisisNutricionalMenu.total_calorias` is populated

**Issue**: Menu generated for only one educational level
- **Cause**: Old implementation only supported single level
- **Solution**: Use refactored `generar_menu_con_ia()` with `niveles_educativos=None` (generates for all)
- **Verification**: Count `TablaAnalisisNutricionalMenu` records should equal number of educational levels

**Issue**: "Nivel '{nivel}' no encontrado en BD"
- **Cause**: Mismatch between JSON level names and database level names
- **Solution**: `MenuService._convertir_nivel_json_a_bd()` handles mapping
- **Mapping**:
  - `"Preescolar"` → `prescolar`
  - `"Primaria (primero, segundo y tercero)"` → `primaria_1_2_3`
  - `"Primaria (cuarto y quinto)"` → `primaria_4_5`
  - `"Secundaria"` → `secundaria`
  - `"Nivel medio y ciclo complementario"` → `media_ciclo_complementario`

**Issue**: Model attribute errors (e.g., `grasas_totales` vs `total_grasa`)
- **Cause**: Inconsistent naming in `TablaAnalisisNutricionalMenu` model
- **Correct attributes**: `total_calorias`, `total_proteina`, `total_grasa`, `total_cho`, `total_calcio`, `total_hierro`, `total_sodio`
- **Solution**: Always use `total_*` prefix, not `*_totales` or `*_total`

### Nutricion Module - Semaforización (Traffic Light System)

**CAMBIO IMPORTANTE (Febrero 2025)**: El sistema de semaforización ahora considera **NIVEL ESCOLAR + MODALIDAD DE CONSUMO**.

#### Sistema Anterior vs Nuevo

**❌ Antes**:
- Requerimientos solo por nivel escolar
- Todos los menús (CAJM/JT, Almuerzo, etc.) se comparaban contra requerimientos diarios totales
- Resultado: Todos los menús aparecían en verde (0-35%) sin importar la modalidad

**✅ Ahora**:
- Requerimientos por nivel escolar + modalidad de consumo
- Cada modalidad tiene su propio 100% basado en la Minuta Patrón ICBF
- Resultado: Semaforización precisa según el tipo de complemento alimentario

#### Rangos de Evaluación (sin cambios)

| Estado | Rango | Color | Significado |
|--------|-------|-------|-------------|
| **ÓPTIMO** | 0-35% | 🟢 Verde | Aporte bajo pero seguro para la modalidad |
| **ACEPTABLE** | 35.1-70% | 🟡 Amarillo | Aporte moderado para la modalidad |
| **ALTO** | >70% | 🔴 Rojo | Aporte elevado, cerca del límite máximo (100%) |

**Diferencia clave**: El 100% ahora es específico para cada modalidad, no el requerimiento diario total.

#### Ejemplo Práctico

Un menú con **280 Kcal** para Preescolar:

| Modalidad | Requerimiento (100%) | Porcentaje | Estado | Color |
|-----------|---------------------|------------|--------|-------|
| CAJM/JT | 276 Kcal | 101% | ALTO | 🔴 |
| Almuerzo | 417 Kcal | 67% | ACEPTABLE | 🟡 |

#### Valores de Referencia (Minuta Patrón ICBF)

**CAJM/JT (Jornada Mañana/Tarde)**:
- Preescolar: 276 Kcal, 9.9g prot, 9.6g grasa, 36.5g CHO, 159mg Ca, 1.5mg Fe, 95mg Na
- Primaria 1-3: 334 Kcal, 11.8g prot, 11.2g grasa, 45.0g CHO, 171mg Ca, 1.9mg Fe, 108mg Na
- Primaria 4-5: 407 Kcal, 14.9g prot, 13.3g grasa, 54.8g CHO, 191mg Ca, 2.4mg Fe, 139mg Na
- Secundaria: 509 Kcal, 18.3g prot, 17.0g grasa, 68.2g CHO, 230mg Ca, 3.0mg Fe, 172mg Na
- Media/Ciclo Comp.: 592 Kcal, 21.1g prot, 19.9g grasa, 79.3g CHO, 245mg Ca, 3.5mg Fe, 191mg Na

**Almuerzo**:
- Preescolar: 417 Kcal, 15.6g prot, 13.4g grasa, 56.3g CHO, 110mg Ca, 2.9mg Fe, 132mg Na
- Primaria 1-3: 457 Kcal, 16.8g prot, 14.5g grasa, 61.8g CHO, 126mg Ca, 3.4mg Fe, 144mg Na
- Primaria 4-5: 550 Kcal, 19.9g prot, 17.2g grasa, 74.8g CHO, 145mg Ca, 4.2mg Fe, 173mg Na
- Secundaria: 682 Kcal, 24.6g prot, 21.9g grasa, 92.0g CHO, 173mg Ca, 5.2mg Fe, 213mg Na
- Media/Ciclo Comp.: 791 Kcal, 28.6g prot, 25.7g grasa, 106.6g CHO, 184mg Ca, 6.1mg Fe, 235mg Na

#### Implementación Técnica

**Modelo modificado** (`TablaRequerimientosNutricionales`):
```python
class TablaRequerimientosNutricionales(models.Model):
    id_nivel_escolar_uapa = ForeignKey(...)  # Existente
    id_modalidad = ForeignKey(ModalidadesDeConsumo, ...)  # NUEVO
    # ... campos nutricionales ...

    class Meta:
        unique_together = [['id_nivel_escolar_uapa', 'id_modalidad']]  # Clave compuesta
```

**Servicio actualizado** (`AnalisisNutricionalService`):
```python
# Filtrar requerimientos por modalidad del menú
if menu.id_modalidad:
    requerimientos = TablaRequerimientosNutricionales.objects.filter(
        id_modalidad=menu.id_modalidad
    )
```

**Frontend** (sin cambios): La lógica de cálculo y colores permanece igual, solo cambian los valores de referencia del backend.

#### Archivos Relacionados

- **Modelo**: `nutricion/models.py` (línea 277)
- **Servicio**: `nutricion/services/analisis_service.py` (línea 32)
- **Migración**: `nutricion/migrations/0002_agregar_modalidad_requerimientos.py`
- **Script población**: `nutricion/poblar_requerimientos_modalidad.py`
- **Documentación completa**: `nutricion/README_SEMAFORIZACION_MODALIDAD.md`
- **Datos fuente**: `nutricion/MINUTA_PATRON_RESOLUCION.md`

#### Pasos para Aplicar

1. Ejecutar migración: `python manage.py migrate nutricion 0002`
2. Poblar datos: `python manage.py shell < nutricion/poblar_requerimientos_modalidad.py`
3. Verificar: Los menús ahora muestran semaforización específica por modalidad

**Issue**: Semaforización incorrecta para modalidad
- **Causa**: Requerimientos no poblados o modalidad no asignada al menú
- **Solution**: Ejecutar script de población y asignar modalidad a los menús existentes
- **Verification**: `TablaRequerimientosNutricionales.objects.count()` debe ser ~10 (5 niveles × 2 modalidades)

### Frontend Performance & UI Issues

**Issue**: CSS/JS changes not appearing after editing files
- **Cause**: Browser cache serving old versions of static files
- **Solution**: Instruct users to hard refresh:
  - Windows/Linux: `Ctrl + Shift + R` or `Ctrl + F5`
  - Mac: `Cmd + Shift + R`
  - Alternative: Open in incognito/private mode
- **Prevention**: Consider adding cache-busting query strings in production

**Issue**: Elements appearing gradually/animating when loading existing data
- **Cause**: CSS animations (`@keyframes`) or `transition: all` applied to elements
- **Solution**:
  - Remove `animation` property from CSS classes that render data from API
  - Change `transition: all` to specific properties (e.g., `transition: border-color 0.2s, box-shadow 0.2s`)
  - Only use transitions for interactive states (`:hover`, `:focus`, `.active`)
- **Files to check**: Module-specific CSS files in `static/css/nutricion/`, `static/css/principal/`

**Issue**: UI feels slow when loading many items (e.g., 20+ preparaciones)
- **Cause**: Sequential DOM manipulation with individual `appendChild` calls in loops
- **Solution**:
  - Use `Promise.all()` for parallel async operations
  - Create `DocumentFragment`, add all elements to it, append once
  - Example pattern:
    ```javascript
    const fragment = document.createDocumentFragment();
    items.forEach(item => {
        const element = createItemElement(item);
        fragment.appendChild(element);
    });
    container.appendChild(fragment); // Single DOM operation
    ```

### Siesa Integration

**Issue**: App `Api` not appearing in admin or not loading
- **Cause**: App not yet added to `INSTALLED_APPS` in `settings.py`
- **Solution**: Add `'Api',` to `INSTALLED_APPS` when ready to activate integration
- **Important**: Complete `CHECKLIST_INTEGRACION_SIESA.md` before activating

**Issue**: Siesa sync not working
- **Cause**: Missing or incorrect environment variables
- **Solution**: Verify all `SIESA_*` variables in `.env` file
- **Debugging**: Check `Api.models.SyncLog` for error messages and timestamps

**Issue**: Duplicate records during Siesa sync
- **Cause**: Sync running multiple times or missing unique key validation
- **Solution**: Use `codigo_siesa` as unique identifier, implement `get_or_create` pattern
- **Prevention**: Check `SyncLog` before running manual sync to avoid overlapping operations
