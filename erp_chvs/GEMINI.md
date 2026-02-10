# GEMINI.md - Contexto del Proyecto ERP_CHVS

## Información General
**ERP_CHVS** es un sistema de Planificación de Recursos Empresariales (ERP) integral construido con **Django 5.2.5**, diseñado específicamente para la gestión del **Programa de Alimentación Escolar (PAE)** en Colombia. El sistema permite la gestión de focalización, facturación, planeación nutricional y administración de sedes educativas.

### Tecnologías Clave
- **Backend:** Python 3.13+, Django 5.2.5
- **Base de Datos:** PostgreSQL (`psycopg2-binary`)
- **Procesamiento de Datos:** Pandas, NumPy, OpenPyXL (Excel)
- **Utilidades:** FuzzyWuzzy/Levenshtein (Coincidencia difusa de texto), ReportLab (Generación de PDF)
- **Frontend:** Bootstrap 5, SweetAlert2, jQuery, DataTables.

---

## Arquitectura y Estructura del Proyecto
El proyecto sigue una estructura modular de Django, implementando una **Arquitectura Orientada a Servicios (SOA)** para separar la lógica de negocio de las vistas.

### Aplicaciones Principales
1.  **`principal`**: Gestión de datos maestros (sedes, municipios, instituciones, niveles, etc.).
2.  **`facturacion`**: Procesa, valida y almacena listados de focalización de beneficiarios PAE desde archivos Excel.
3.  **`nutricion`**: Gestión de estándares nutricionales (ICBF 2018), planeación de menús, ingredientes y análisis nutricional.
4.  **`planeacion`**: Gestión de ciclos de menús y programas.
5.  **`dashboard`**: Panel principal con métricas y acceso rápido.

### Capas de Lógica (SOA)
-   **`services.py`**: Orquestadores de la lógica de negocio. Coordinan validadores, procesadores y persistencia.
-   **`persistence_service.py`**: Maneja transacciones de base de datos y operaciones masivas (`bulk_create`).
-   **`data_processors.py`**: Limpieza y transformación de datos (especialmente desde Excel).
-   **`validators.py`**: Reglas de validación centralizadas.
-   **`fuzzy_matching.py`**: Lógica para emparejar nombres de sedes educativas con errores tipográficos contra la base de datos.

---

## Configuración y Ejecución

### Requisitos Previos
- Python 3.13+
- PostgreSQL
- Archivo `.env` configurado en la raíz.

### Comandos Comunes
- **Servidor de Desarrollo:** `python manage.py runserver`
- **Migraciones:** `python manage.py makemigrations` seguido de `python manage.py migrate`
- **Pruebas:** `pytest` (configurado con `pytest-django`)
- **Carga de Datos:** `python manage.py loaddata <fixture>.json` (o similar si se usan backups como `backup_utf8.json`)

---

## Convenciones del Proyecto
1.  **Idioma:** 
    -   **Lógica de Negocio y Modelos:** Español (ej. `SedesEducativas`, `procesar_listados`).
    -   **Código Estructural:** Inglés (ej. `ProcesamientoService`, `get_queryset`).
2.  **Lógica en Servicios:** NUNCA incluir lógica de negocio compleja directamente en las vistas (`views.py`). Las vistas deben delegar en la capa de servicios.
3.  **Persistencia:** Usar `persistence_service.py` para operaciones complejas de escritura para mantener la integridad de los datos.
4.  **Manejo de Localización:** 
    -   Locale: `es-col`.
    -   Zona Horaria: `America/Bogota`.
    -   Separador decimal: Punto (`.`).

---

## Notas de Desarrollo
- La página raíz (`/`) actúa como la página de inicio de sesión (`home.html`).
- El sistema maneja múltiples formatos de Excel (Lotes), con lógica específica en `facturacion/data_processors.py` para Cali, Yumbo y Buga.
- Se utiliza `fuzzywuzzy` con un umbral configurable para asegurar que los datos externos (Excel) se mapeen correctamente a los registros oficiales del sistema.
