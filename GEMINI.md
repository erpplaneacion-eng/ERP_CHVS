# Gemini Context for ERP_CHVS

## Project Overview

**ERP_CHVS** is a comprehensive Enterprise Resource Planning (ERP) system built with **Django 5.2.5**, designed primarily for managing the "Programa de Alimentación Escolar" (PAE - School Feeding Program).

It features modules for billing (Facturación), nutritional planning (Nutrición), document validation via OCR (OCR Validation), and integrates Generative AI capabilities.

### Key Technologies

*   **Backend:** Python 3.x, Django 5.2.5
*   **Database:** PostgreSQL (`psycopg2-binary`)
*   **Data Processing:** Pandas, OpenPyXL, NumPy
*   **AI/ML:**
    *   **Generative AI:** Google Gemini (`google-generativeai`)
    *   **Computer Vision:** OpenCV (`opencv-python`), LandingAI
    *   **OCR:** PyTesseract, PyPDF2, PDF2Image
*   **Utilities:** ReportLab (PDF generation), FuzzyWuzzy (String matching)

---

## Architecture & Apps

The project follows a modular Django app structure, rooted in `erp_chvs/`.

### 1. `facturacion` (Billing & Focalization)
*   **Purpose:** Processes, validates, and stores PAE focalization lists (beneficiary lists).
*   **Architecture:** Implements a **Service-Oriented Architecture (SOA)** to decouple logic.
*   **Key Components:**
    *   `services.py`: Orchestrates business logic.
    *   `persistence_service.py`: Handles database transactions and bulk creates.
    *   `data_processors.py`: Cleans and transforms Excel data.
    *   `fuzzy_matching.py`: Matches school names (sedes) from Excel to DB entries.
    *   `validators.py`: Centralized data validation rules.

### 2. `nutricion` (Nutrition)
*   **Purpose:** Manages nutritional standards, menu planning, and ingredient analysis.
*   **Key Models:**
    *   `TablaAlimentos2018Icbf`: Standard nutritional composition table (ICBF 2018).
    *   `GruposAlimentos` & `ComponentesAlimentos`: Classification of food items.
    *   `PermisosNutricion`: Custom permissions.

### 3. `dashboard` & `principal`
*   **Purpose:** Core application logic, main dashboard views, and shared models/utilities.

---

## Development & Setup

### Environment Variables
Configuration is managed via `.env` files loaded by `python-dotenv`. Key variables include:
*   `DJANGO_SECRET_KEY`
*   `GEMINI_API_KEY`
*   `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

### Directory Structure
*   `erp_chvs/`: Django project root (contains `manage.py`).
    *   `erp_chvs/`: Project settings.
    *   `[app_name]/`: Individual app directories.
*   `archivos excel/`: Directory for processing/storing Excel files.

### Common Commands

**Run Server:**
```bash
python erp_chvs/manage.py runserver
```

**Make Migrations:**
```bash
python erp_chvs/manage.py makemigrations
```

**Migrate:**
```bash
python erp_chvs/manage.py migrate
```

**Run Tests:**
```bash
python erp_chvs/manage.py test
```

## Conventions

*   **Service Layer:** Complex business logic should reside in `services.py` or specialized modules, not in Views or Models.
*   **Fat Models:** Avoid. Use services for logic.
*   **Type Hinting:** Use Python type hints in new code.
*   **Language:** Codebase uses Spanish for naming (variables, classes, comments) in business logic (e.g., `ListadosFocalizacion`, `GruposAlimentos`), but standard Python/Django conventions for structure.
