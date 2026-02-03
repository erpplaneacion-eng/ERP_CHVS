# Gemini Context for ERP_CHVS

## Project Overview

**ERP_CHVS** is a comprehensive Enterprise Resource Planning (ERP) system built with **Django 5.2.5**, designed primarily for managing the "Programa de Alimentación Escolar" (PAE - School Feeding Program).

It features modules for billing (Facturación), nutritional planning (Nutrición), and core management.

### Key Technologies

*   **Backend:** Python 3.13+, Django 5.2.5
*   **Database:** PostgreSQL (`psycopg2-binary`)
*   **Data Processing:** Pandas, OpenPyXL, NumPy
*   **Utilities:** ReportLab (PDF generation), FuzzyWuzzy (String matching)
*   **Frontend:** Bootstrap 5, SweetAlert2, jQuery/DataTables.

---

## Architecture & Apps

The project follows a modular Django app structure, rooted in `erp_chvs/`.

### 1. `facturacion` (Billing & Focalization)
*   **Purpose:** Processes, validates, and stores PAE focalization lists (beneficiary lists) from Excel.
*   **Architecture:** Implements a **Service-Oriented Architecture (SOA)**.
*   **Key Components:**
    *   `services.py`: Orchestrates business logic.
    *   `persistence_service.py`: Handles database transactions and bulk creates.
    *   `data_processors.py`: Cleans and transforms Excel data. Includes logic for **Cali, Yumbo, and Guadalajara de Buga**.
    *   `fuzzy_matching.py`: Matches school names (sedes) from Excel to DB entries. Supports municipio aliases (e.g., "BUGA" -> "GUADALAJARA DE BUGA").
    *   `validators.py`: Centralized data validation rules.

### 2. `nutricion` (Nutrition)
*   **Purpose:** Manages nutritional standards, menu planning, and ingredient analysis.
*   **Key Models:**
    *   `TablaAlimentos2018Icbf`: Standard nutritional composition table (ICBF 2018).
    *   `GruposAlimentos` & `ComponentesAlimentos`: Classification of food items.
    *   `PermisosNutricion`: Custom permissions.

### 3. `dashboard` & `principal`
*   **Purpose:** Core application logic, main dashboard views, and shared models/utilities.
*   **Authentication:** Uses standard Django Auth (`django.contrib.auth`). The root URL (`/`) serves as the login page.

---

## Development & Setup

### Environment Variables
Configuration is managed via `.env` files. Key variables include:
*   `DJANGO_SECRET_KEY`
*   `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
*   `DJANGO_DEBUG` (Boolean)

### Directory Structure
*   `erp_chvs/`: Django project root (contains `manage.py`).
    *   `erp_chvs/`: Project settings.
    *   `templates/`: Global templates (including `base.html` and `home.html`).
    *   `static/`: Global CSS/JS assets.
*   `archivos excel/`: Input/output directory for Excel files.

### Common Commands

**Run Server:**
```powershell
python erp_chvs/manage.py runserver
```

**Make Migrations:**
```powershell
python erp_chvs/manage.py makemigrations
```

**Migrate:**
```powershell
python erp_chvs/manage.py migrate
```

## Conventions & Rules

*   **Service Layer:** All complex business logic MUST reside in `services.py` or dedicated modules within the app.
*   **App Status:** The apps `ocr_validation` and `iagenerativa` have been **deprecated and removed** from the project.
*   **Language:** Business logic, models, and comments use Spanish (e.g., `SedesEducativas`, `procesar_listados`). Structural code follows Python/Django standards in English.
*   **Data Normalization:** In Focalización processing, always handle "BUGA" as an alias for "GUADALAJARA DE BUGA" for DB queries and logic.