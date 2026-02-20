# ERP_CHVS - Comprehensive Project Context

This document serves as the primary instructional context for AI agents interacting with the **ERP_CHVS** codebase. It outlines the project's purpose, architecture, technologies, and development standards.

---

## 1. Project Overview
**ERP_CHVS** is a specialized Enterprise Resource Planning (ERP) system developed for operators of the **Programa de Alimentación Escolar (PAE)** in Colombia. It automates critical processes including billing, beneficiary targeting (focalización), and nutritional planning.

### Core Objectives
*   **Focalización:** Manage and validate large datasets of school beneficiaries from diverse Excel formats.
*   **Nutrición:** Perform complex nutritional analysis of menus based on national resolutions (e.g., UAPA) and the ICBF 2018 food composition table (TCAC).
*   **Automation:** Utilize Google Gemini AI for generating compliant nutritional menus and optimizing workflows.

---

## 2. Technical Stack
*   **Backend:** Python 3.13+, Django 5.2.5
*   **Database:** PostgreSQL (using `psycopg2-binary`)
*   **Data Processing:** Pandas, NumPy, OpenPyXL
*   **AI Integration:** Google Generative AI (Gemini Pro)
*   **Reporting:** ReportLab (PDF generation), OpenPyXL (Excel exports)
*   **Frontend:** Bootstrap 5, jQuery, DataTables, SweetAlert2
*   **Testing:** Pytest, Django Test Runner

---

## 3. Architecture & Key Modules

The project follows a modular Django structure with a **Service-Oriented Architecture (SOA)** approach for complex business logic.

### A. Facturación (`facturacion/`)
Handles the ingestion and validation of beneficiary lists.
*   **Service Layer:** Logic resides in `services.py`, `persistence_service.py`, and `data_processors.py`.
*   **Fuzzy Matching:** Uses `fuzzywuzzy` and `RapidFuzz` to map non-standardized school names from Excel files to the official database.
*   **Validators:** Strict validation of Excel structures (supports "Original" and "Lote 3" formats).
*   **Multi-Location Support:** The Google Sheets integration now supports multiple locations (Cali and Yumbo). Services and Views accept a `sede` parameter to switch between `GOOGLE_SHEET_ID` (Cali) and `GOOGLE_SHEET_ID_YUMBO` (Yumbo).

### B. Nutrición (`nutricion/`)
The core engine for nutritional compliance and menu planning.
*   **Analysis:** Calculates Energy, Protein, Fats, CHO, Calcium, Iron, and Sodium.
*   **Semaforización:** Visual validation of nutritional adequacy (e.g., 20% for snacks, 30% for lunch).
*   **Weekly Validator:** A recently implemented system that groups 20 menus into 4 weeks and validates component frequency against resolution requirements.
*   **AI Menus:** Integration with Gemini to generate menus that meet specific nutritional targets.

### C. Dashboard & Principal
Central hubs for user management, geographic data (Departments/Municipalities), and system-wide statistics.
*   **Logout Workflow:** Users are redirected to the home page after logging out, as configured in `settings.py` via `LOGOUT_REDIRECT_URL`.

---

## 4. Development Conventions & Standards

### Coding Style
*   **Language:** Business logic, models, and comments are in **Spanish**. Code structure (classes, methods, variables) and Django-specific files are in **English**.
*   **Business Logic:** **MUST** reside in `services.py` or `utils/` within each app. Views should primarily handle request/response orchestration.
*   **Database Operations:** Prefer `bulk_create` and `bulk_update` for high-volume data operations.
*   **Naming Conventions:** Standard Python PEP 8 (snake_case for functions/variables, PascalCase for classes).

### Data Normalization
*   **Municipalities:** Always normalize "BUGA" to "GUADALAJARA DE BUGA".
*   **Timezone:** `America/Bogota` (Colombia). `USE_TZ = True`.
*   **Decimals:** System standard is to use `.` as the decimal separator in forms, but localization supports Colombian formats.

---

## 5. Operations & Commands

### Setup & Installation
```powershell
# Environment setup
python -m venv .venv
.\.venv\Scripts\activate
pip install -r erp_chvs/requirements.txt

# Database setup
python erp_chvs/manage.py migrate
python erp_chvs/manage.py createsuperuser
```

### Development
```powershell
# Run server
python erp_chvs/manage.py runserver

# Run tests
pytest
python erp_chvs/manage.py test nutricion
```

### Key Reference Files
*   `erp_chvs/erp_chvs/settings.py`: Global configuration.
*   `erp_chvs/mapeo_nutricion.json`: Nutritional field mapping.
*   `PLAN_VALIDADOR_SEMANAL.md`: Detailed implementation plan for the weekly validator.
*   `REPORTE_BUGS_CORREGIDOS.md`: History of bug fixes and system stability notes.
*   `erp_chvs/diagnostico_excluyentes.py`: Diagnostic script for exclusive groups in nutrition.
*   `erp_chvs/diagnostico_validador_semanal.py`: Diagnostic script for the weekly validator.

---

## 6. AI Agent Guidelines
When assisting with this project:
1.  **Respect the Service Layer:** Check for an existing `services.py` before adding logic to a `view.py`.
2.  **Multilingual Context:** Ensure comments and user-facing strings are in Spanish.
3.  **Data Integrity:** Be cautious with migrations in the `nutricion` app as it handles critical resolution data.
4.  **Frontend Logic:** Much of the new interactivity (like the Weekly Validator) is driven by modular JavaScript in `static/js/`.
5.  **Environment Variables:** Be aware of `GOOGLE_SHEET_ID` and `GOOGLE_SHEET_ID_YUMBO` for focalización processes.
