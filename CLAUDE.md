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

# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test facturacion
python manage.py test nutricion

# Collect static files
python manage.py collectstatic
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

**Facturacion module pattern** (replicated elsewhere):
```
views.py → services.py → persistence_service.py → models.py
                ↓
        data_processors.py, validators.py, fuzzy_matching.py
```

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

**Nutricion JS modules** (`static/js/nutricion/`):
- `core/`: `api-client.js`, `modal-manager.js`, `utils.js`
- `modules/`: Manager classes (IngredientesManager, PreparacionesManager, etc.)
- Auto-save functionality in `guardado-automatico.js`

## Conventions

### Language
- **Spanish**: Model fields, business logic, comments, variable names for domain entities
- **English**: Structural code, class definitions, Python/Django standards

### Data Processing
- **Municipio aliases**: Always handle "BUGA" as alias for "GUADALAJARA DE BUGA"
- **Bulk operations**: Use `bulk_create` for batch database inserts
- **Excel processing**: Specialized utilities in `excel_utils.py` per module

### Configuration
- Environment variables via `.env`: `DJANGO_DEBUG`, `DB_*`, `GEMINI_API_KEY`
- Module constants in `config.py` files
- Locale: Spanish (Colombian), timezone `America/Bogota`

## Database

- **Engine**: PostgreSQL
- **Connection pooling**: `CONN_MAX_AGE=600`
- Migrations per app in `migrations/` directories

## Key Dependencies

- Data: `pandas`, `openpyxl`, `numpy`
- PDF: `reportlab`, `PyPDF2`
- Fuzzy matching: `fuzzywuzzy`, `Levenshtein`
- AI/Vision: `google-generativeai`, `landingai-ade`
