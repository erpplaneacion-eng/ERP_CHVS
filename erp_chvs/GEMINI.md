# ERP_CHVS - Contexto del Proyecto

Este archivo proporciona una visión general y guía para interactuar con el proyecto **ERP_CHVS**, un sistema de Planificación de Recursos Empresariales diseñado para la gestión del Programa de Alimentación Escolar (PAE).

## 1. Descripción General
**ERP_CHVS** es un sistema basado en **Django 5.2.5** que automatiza procesos críticos de facturación, focalización y nutrición para operadores del PAE. El sistema maneja grandes volúmenes de datos de beneficiarios y realiza cálculos nutricionales complejos basados en resoluciones vigentes.

### Tecnologías Clave
*   **Backend:** Python 3.13+, Django 5.2.5
*   **Base de Datos:** PostgreSQL
*   **Procesamiento de Datos:** Pandas, OpenPyXL, NumPy
*   **IA:** Google Generative AI (Gemini)
*   **Reportes:** ReportLab (PDF), OpenPyXL (Excel)
*   **Frontend:** Bootstrap 5, jQuery, DataTables, SweetAlert2

---

## 2. Arquitectura y Módulos Principales

El proyecto sigue una estructura modular de Django, implementando una **Arquitectura Orientada a Servicios (SOA)** en sus procesos más complejos.

### A. Facturación (Focalización)
Gestiona la carga y validación de listados de beneficiarios desde archivos Excel.
*   **Services (`facturacion/services.py`):** Orquestan el procesamiento, validación difusa (Fuzzy Matching) de sedes y persistencia.
*   **Procesamiento:** Soporta múltiples formatos de archivos (Original y Nuevo Lote 3).
*   **Validación Difusa:** Mapea nombres de sedes de archivos Excel a la base de datos oficial, manejando alias y errores tipográficos.

### B. Nutrición
Maneja el análisis nutricional de menús y minutas patrón.
*   **TCAC:** Utiliza la Tabla de Composición de Alimentos ICBF 2018.
*   **Análisis:** Calcula el aporte de Energía, Proteínas, Grasas, CHO, Calcio, Hierro y Sodio.
*   **Semaforización:** Valida el cumplimiento de la adecuación nutricional (20% para CAJM/JT, 30% para Almuerzo) según los niveles de la UAPA.
*   **Generación de Menús:** Permite la planificación masiva por modalidad y ciclo semanal.

### C. Dashboard y Principal
Contienen la lógica central de la aplicación, gestión de usuarios, departamentos y municipios.

---

## 3. Guía de Desarrollo y Convenciones

### Estilo de Código
*   **Idiomas:** Lógica de negocio, modelos y comentarios en **Español**. Estructura de código (Django/Python) en **Inglés**.
*   **Capa de Servicios:** La lógica de negocio compleja **NO** debe estar en las vistas, sino en archivos `services.py` dentro de cada app.
*   **Persistencia:** Se prefiere el uso de `bulk_create` para operaciones masivas de datos (ej. carga de focalización).

### Manejo de Datos
*   **Municipios:** Siempre normalizar "BUGA" a "GUADALAJARA DE BUGA".
*   **Fechas:** Utiliza `USE_TZ = True` y la zona horaria `America/Bogota`.

---

## 4. Comandos de Operación

### Configuración
```powershell
# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### Ejecución
```powershell
# Servidor de desarrollo
python manage.py runserver
```

### Pruebas
```powershell
# Ejecutar todas las pruebas
pytest

# Pruebas específicas
python manage.py test nutricion
```

---

## 5. Archivos Clave de Referencia
*   `erp_chvs/settings.py`: Configuración global y credenciales de DB.
*   `GUIA_TABLAS_DB.md`: Diccionario de datos y descripción de tablas.
*   `nutricion/MINUTA_PATRON_RESOLUCION.md`: Estándares de adecuación nutricional.
*   `mapeo_nutricion.json`: Configuración de campos para el análisis nutricional.
