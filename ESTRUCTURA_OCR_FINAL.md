# 🗂️ Estructura Final del Módulo OCR Validation

## 📁 Árbol de Archivos

```
erp_chvs/ocr_validation/
│
├── 📄 __init__.py                      # Inicialización del módulo
├── 📄 admin.py                         # Configuración Django Admin
├── 📄 apps.py                          # Configuración de la app
├── 📄 exceptions.py                    # Excepciones personalizadas
├── 📄 models.py                        ✅ ACTUALIZADO
│   ├── PDFValidation                   # Modelo principal
│   ├── ValidationError                 # Errores detectados
│   ├── OCRConfiguration                # Configuración (modelo_landingai)
│   └── FieldValidationRule             # Reglas de validación
│
├── 📄 views.py                         ✅ CONSOLIDADO
│   ├── ocr_validation_index()          # Vista principal
│   ├── procesar_pdf_ocr()              # Procesamiento unificado
│   ├── ver_dataframe()                 # Visualizar DataFrame
│   ├── exportar_dataframe()            # Exportar CSV/Excel/JSON
│   ├── api_dataframe_data()            # API JSON para DataTables
│   ├── dashboard_dataframes()          # Dashboard principal
│   ├── listado_validaciones()          # Historial
│   ├── estadisticas_ocr()              # Estadísticas
│   └── configuracion_ocr()             # Configuración
│
├── 📄 urls.py                          ✅ SIMPLIFICADO
│   └── urlpatterns (8 rutas activas)
│
├── 📄 ocr_orchestrator.py              ✅ ORQUESTADOR ÚNICO
│   ├── OCROrchestrator
│   │   ├── __init__()
│   │   ├── process_pdf_complete()      # Procesamiento principal
│   │   ├── get_processing_results()    # Recuperar resultados
│   │   ├── export_dataframes()         # Exportar múltiples formatos
│   │   └── métodos privados de validación
│
├── 📄 dataframe_extractor.py           # Extractor legacy (raíz)
├── 📄 ocr_service.py                   # Wrapper compatibilidad (no usado)
├── 📄 ocr_service_new.py               # No usado
├── 📄 validador_asistencia.py          # No usado (legacy)
├── 📄 validador_encabezado.py          # No usado (legacy)
├── 📄 validadores_mejorados.py         # No usado (legacy)
│
├── 📄 README.md                        ✅ ACTUALIZADO
├── 📄 CHANGELOG.md                     ✅ NUEVO
├── 📄 README_DATAFRAMES.md             # Documentación DataFrames
│
├── 📂 services/                        ✅ SERVICIOS ACTIVOS
│   ├── 📄 __init__.py
│   ├── 📄 README.md
│   │
│   ├── 📄 base.py                      # Clase base BaseOCRService
│   │   └── BaseOCRService (logging, config)
│   │
│   ├── 📄 landingai_adapter.py         ✅ ADAPTADOR PRINCIPAL
│   │   └── LandingAIAdapter
│   │       ├── process_document()      # Procesar con API
│   │       ├── process_uploaded_file() # Procesar archivo subido
│   │       ├── extract_text_from_chunks()
│   │       ├── extract_structured_data() # Con schemas
│   │       └── process_pdf_pages()
│   │
│   ├── 📄 dataframe_extractor.py       ✅ EXTRACTOR ESTRUCTURADO
│   │   ├── Schemas Pydantic:
│   │   │   ├── EstudianteRegistro
│   │   │   ├── EncabezadoPDF
│   │   │   └── DocumentoCompleto
│   │   └── DataFrameExtractor
│   │       ├── extract_to_dataframe()  # Método principal
│   │       ├── _extract_with_fallback() # Método alternativo
│   │       └── export_to_formats()     # CSV/Excel/JSON/HTML
│   │
│   ├── 📄 ocr_orchestrator.py          # ⚠️ NO USADO (duplicado)
│   ├── 📄 header_validator.py          # ⚠️ Validador legacy
│   └── 📄 field_validator.py           # ⚠️ Validador legacy
│
├── 📂 migrations/
│   ├── 0001_initial.py
│   ├── 0002_pdfvalidation_usuario_creador.py
│   ├── 0003_add_metodo_ocr.py
│   ├── 0004_pdfvalidation_datos_estructurados_and_more.py
│   └── 🔄 PENDIENTE: migración para modelo_landingai
│
├── 📂 management/
│   └── commands/
│       ├── __init__.py
│       └── test_ocr.py                 # Comando de prueba
│
└── 📂 templatetags/
    ├── __init__.py
    └── ocr_filters.py                  # Filtros personalizados
```

---

## 🌐 Templates HTML

```
erp_chvs/templates/ocr_validation/
│
├── 📄 index.html                       ✅ ACTUALIZADO
│   ├── Header con botones de navegación
│   ├── Card de información del sistema
│   ├── Sección de extracción inteligente
│   ├── Formulario de carga de PDF
│   ├── Sección de procesamiento (progreso)
│   ├── Sección de resultados
│   └── Sección de configuración
│
├── 📄 dataframe_view.html              ✅ VISTA PRINCIPAL
│   ├── Información del archivo procesado
│   ├── Estadísticas generales
│   ├── Tabla de estudiantes (DataTable)
│   ├── Información del encabezado
│   ├── Botones de exportación
│   └── Datos JSON raw (colapsable)
│
├── 📄 dashboard_dataframes_simple.html ✅ DASHBOARD
│   ├── Resumen de validaciones
│   ├── Lista de procesados recientes
│   └── Estadísticas de calidad
│
├── 📄 listado.html                     # Historial de procesados
├── 📄 estadisticas.html                # Estadísticas generales
├── 📄 configuracion.html               # Configuración OCR
└── 📄 error.html                       # Página de errores
```

---

## 🎨 JavaScript

```
erp_chvs/static/js/ocr_validation/
│
└── 📄 ocr_processor.js                 ✅ ACTUALIZADO
    ├── class OCRProcessor
    │   ├── handleFormSubmit()          # Envío de formulario
    │   ├── handleFileSelection()       # Validación archivo
    │   ├── showProcessingSection()     # UI procesamiento
    │   ├── updateProgress()            # Barra de progreso
    │   ├── showResultsSection()        # Mostrar resultados
    │   └── 🆕 Redirección automática a DataFrame
    │
    ├── limpiarFormulario()             # Función global
    └── procesarOtroArchivo()           # Función global
```

---

## 🎨 CSS

```
erp_chvs/static/css/modules/
└── 📄 ocr_validation.css               # Estilos del módulo
```

---

## 🔗 URLs Activas

| Ruta | Nombre | Vista | Descripción |
|------|--------|-------|-------------|
| `/ocr_validation/` | `ocr_index` | `ocr_validation_index` | Página principal |
| `/ocr_validation/procesar/` | `procesar_pdf` | `procesar_pdf_ocr` | Procesamiento unificado |
| `/ocr_validation/dataframe/{id}/` | `ver_dataframe` | `ver_dataframe` | Visualizar DataFrame |
| `/ocr_validation/dataframe/{id}/exportar/` | `exportar_dataframe` | `exportar_dataframe` | Exportar datos |
| `/ocr_validation/api/dataframe/{id}/data/` | `api_dataframe_data` | `api_dataframe_data` | API JSON |
| `/ocr_validation/dashboard/` | `dashboard_dataframes` | `dashboard_dataframes` | Dashboard principal |
| `/ocr_validation/listado/` | `listado` | `listado_validaciones` | Historial |
| `/ocr_validation/estadisticas/` | `estadisticas` | `estadisticas_ocr` | Estadísticas |
| `/ocr_validation/configuracion/` | `configuracion` | `configuracion_ocr` | Configuración |

---

## 🔄 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                         COMPONENTES                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Usuario Web    │
└────────┬─────────┘
         │ Sube PDF
         ▼
┌──────────────────┐
│   index.html     │◄─── ocr_processor.js (maneja formulario)
└────────┬─────────┘
         │ POST /procesar/
         ▼
┌──────────────────┐
│  views.py        │
│  procesar_pdf_   │
│  ocr()           │
└────────┬─────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────┐
│  ocr_orchestrator.py                                      │
│  OCROrchestrator.process_pdf_complete()                   │
└────────┬──────────────────────────────────────────────────┘
         │
         ├──► 1. Validar archivo
         │
         ├──► 2. DataFrameExtractor.extract_to_dataframe()
         │         │
         │         ├──► LandingAIAdapter.process_document()
         │         │         │
         │         │         └──► 🌐 API LandingAI (dpt-2-latest)
         │         │
         │         ├──► extract_text_from_chunks()
         │         │
         │         └──► extract_structured_data() (con schemas)
         │
         ├──► 3. Validar datos extraídos
         │
         ├──► 4. Crear resumen
         │
         └──► 5. Guardar en BD (PDFValidation)
                   │
                   ├─► datos_estructurados (JSON)
                   ├─► metadatos_extraccion (JSON)
                   └─► texto_completo (TEXT)

         Respuesta:
         {
           "success": true,
           "validacion_id": 123,
           "redirect_url": "/ocr_validation/dataframe/123/"
         }
         │
         │ JavaScript redirige
         ▼
┌──────────────────┐
│ dataframe_view   │◄─── DataTables.js (tabla interactiva)
│ .html            │
└──────────────────┘
         │
         │ Usuario exporta
         ▼
┌──────────────────┐
│ exportar_        │──► CSV / Excel / JSON
│ dataframe()      │
└──────────────────┘
```

---

## 🗄️ Modelos de Base de Datos

### **PDFValidation**
```python
- id (PK)
- archivo_nombre
- archivo_path
- sede_educativa
- mes_atencion
- ano
- tipo_complemento
- usuario_creador (FK → User)
- estado (procesando/completado/error)
- total_errores
- errores_criticos
- errores_advertencia
- fecha_procesamiento
- fecha_completado
- tiempo_procesamiento
- metodo_ocr = 'landingai'
- datos_estructurados (JSON)  ✅ Campo principal
- metadatos_extraccion (JSON)
- texto_completo (TEXT)
- observaciones
```

### **ValidationError**
```python
- id (PK)
- validacion (FK → PDFValidation)
- tipo_error
- descripcion
- pagina
- fila_estudiante
- columna_campo
- valor_esperado
- valor_encontrado
- coordenada_x
- coordenada_y
- severidad (critico/advertencia/info)
- resuelto
- fecha_creacion
```

### **OCRConfiguration** ✅ ACTUALIZADO
```python
- id (PK)
- modelo_landingai = 'dpt-2-latest'  ✅ NUEVO
- confianza_minima = 90.0            ✅ ACTUALIZADO
- tolerancia_posicion_x
- tolerancia_posicion_y
- permitir_texto_parcial
- detectar_firmas
- procesar_imagenes
- guardar_imagenes_temporales
- fecha_actualizacion
```

### **FieldValidationRule**
```python
- id (PK)
- nombre_campo
- descripcion_campo
- tipo_campo (texto/numero/fecha/firma/celda_x/total)
- pagina_tipica
- posicion_x_relativa
- posicion_y_relativa
- obligatorio
- patron_validacion (regex)
- valor_minimo
- valor_maximo
- detectar_posicion_x
- tolerancia_posicion
- activo
- fecha_creacion
```

---

## 🔑 Variables de Entorno Requeridas

```bash
# .env
VISION_AGENT_API_KEY=tu_api_key_de_landingai

# Opcional (Django settings)
DEBUG=True
SECRET_KEY=tu_secret_key
DATABASE_URL=sqlite:///db.sqlite3
```

---

## 📦 Dependencias Python

```txt
# Core
Django>=4.2
python-dotenv

# LandingAI
landingai-ade

# Procesamiento de datos
pandas>=2.0
openpyxl  # Excel
pydantic>=2.0

# Opcional (si se usa)
Pillow  # Imágenes
pdf2image  # Conversión PDF
```

---

## 🎯 Archivos Clave por Funcionalidad

### **Procesamiento OCR**
- `ocr_orchestrator.py` (orquestador principal)
- `services/landingai_adapter.py` (comunicación API)
- `services/dataframe_extractor.py` (extracción estructurada)

### **Vistas Web**
- `views.py` (todas las vistas)
- `urls.py` (rutas)
- `templates/ocr_validation/*.html`

### **Frontend**
- `static/js/ocr_validation/ocr_processor.js`
- `static/css/modules/ocr_validation.css`

### **Base de Datos**
- `models.py` (4 modelos)
- `migrations/` (histórico)

### **Configuración**
- `admin.py` (Django Admin)
- `apps.py` (configuración app)

---

## 🚫 Archivos Obsoletos (No Usados)

- `services/ocr_orchestrator.py` (duplicado)
- `ocr_service.py` (wrapper legacy)
- `ocr_service_new.py` (experimental)
- `validador_*.py` (validadores antiguos)
- `dataframe_extractor.py` (raíz, usar services/)

---

## ✅ Checklist de Componentes Activos

- ✅ `ocr_orchestrator.py` (raíz) → Orquestador único
- ✅ `services/landingai_adapter.py` → Comunicación LandingAI
- ✅ `services/dataframe_extractor.py` → Extracción estructurada
- ✅ `services/base.py` → Clase base con logging
- ✅ `views.py` → 9 vistas activas
- ✅ `urls.py` → 9 rutas activas
- ✅ `models.py` → 4 modelos activos
- ✅ `templates/ocr_validation/` → 9 templates
- ✅ `static/js/ocr_validation/ocr_processor.js` → JS principal

---

**Sistema completamente refactorizado y documentado** 📚✨
