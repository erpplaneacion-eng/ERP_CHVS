# 📊 Sistema de Extracción de DataFrames OCR

## 🎯 Descripción General

Sistema avanzado para extraer datos tabulares de PDFs de asistencia escolar y convertirlos automáticamente en DataFrames estructurados utilizando LandingAI ADE (Automated Document Extraction).

## ✨ Características Principales

- **🤖 Extracción Inteligente**: Utiliza IA para identificar y extraer tablas de estudiantes
- **📋 Datos Estructurados**: Convierte texto desordenado en DataFrames organizados
- **🎨 Interfaz Moderna**: Dashboard interactivo con drag & drop
- **💾 Multi-formato**: Exporta a CSV, Excel, JSON y HTML
- **🔍 Validación Automática**: Evalúa calidad de extracción
- **📱 Responsivo**: Funciona en desktop, tablet y móvil

## 🏗️ Arquitectura del Sistema

```
📦 ocr_validation/
├── 📄 dataframe_extractor.py     # Servicio principal de extracción
├── 🎭 ocr_orchestrator.py        # Coordinador de procesos
├── 🗄️ models.py                  # Modelos con campos JSON
├── 🌐 views.py                   # Vistas para web interface
├── 🎨 templates/                 # Templates HTML
│   ├── dataframe_view.html       # Vista de DataFrames
│   └── dashboard_dataframes.html # Dashboard principal
├── 🏷️ templatetags/             # Filtros personalizados
└── 🔧 services/                  # Servicios auxiliares
    ├── base.py                   # Clase base
    └── landingai_adapter.py      # Adaptador LandingAI
```

## 📝 Esquemas de Datos

### EstudianteRegistro
```python
{
    "numero": int,                    # Número de lista
    "nombre_completo": str,           # Nombre del estudiante
    "cedula": str,                    # Documento de identidad
    "grado": str,                     # Grado escolar
    "raciones_entregadas": int,       # Cantidad de raciones
    "fecha_asistencia": str,          # Fecha de registro
    "firma_presente": bool,           # Si hay firma
    "observaciones": str              # Notas adicionales
}
```

### EncabezadoPDF
```python
{
    "departamento": str,              # Departamento
    "municipio": str,                 # Municipio
    "institucion_educativa": str,     # Nombre de la IE
    "sede_educativa": str,            # Sede
    "codigo_dane": str,               # Código DANE
    "mes_atencion": str,              # Mes de atención
    "ano": int,                       # Año
    "tipo_complemento": str,          # PME, JC, etc.
    "responsable": str                # Responsable
}
```

## 🚀 Uso del Sistema

### 1. Acceso al Dashboard
```
http://localhost:8000/ocr_validation/dashboard-dataframes/
```

### 2. Subir PDF
- **Drag & Drop**: Arrastra el PDF a la zona de carga
- **Click**: Haz clic en "Seleccionar Archivo"
- **Validaciones**: Máximo 10MB, solo archivos PDF

### 3. Procesamiento Automático
El sistema realiza:
1. ✅ Validación del archivo
2. 🤖 Extracción con LandingAI ADE
3. 📊 Conversión a DataFrames
4. 🔍 Validación de calidad
5. 💾 Almacenamiento en BD

### 4. Visualización de Resultados
- **Estadísticas**: Total estudiantes, raciones, calidad
- **Tabla Interactiva**: Búsqueda, filtros, paginación
- **Información del Encabezado**: Datos de la institución
- **Exportación**: Descarga en múltiples formatos

## 📋 API de Uso Programático

### Extracción Básica
```python
from ocr_validation.dataframe_extractor import DataFrameExtractor

# Inicializar extractor
extractor = DataFrameExtractor(api_key="tu_api_key")

# Procesar PDF
resultado = extractor.extract_to_dataframe("ruta/al/archivo.pdf")

if resultado['success']:
    df_estudiantes = resultado['df_estudiantes']
    df_encabezado = resultado['df_encabezado']
    print(f"Extraídos {len(df_estudiantes)} estudiantes")
```

### Orquestador Completo
```python
from ocr_validation.ocr_orchestrator import OCROrchestrator

# Inicializar orquestador
orchestrator = OCROrchestrator()

# Procesamiento completo
resultado = orchestrator.process_pdf_complete(
    pdf_path="archivo.pdf",
    save_to_db=True
)

if resultado['success']:
    print(f"Validación ID: {resultado['pdf_validation_id']}")
    print(f"Calidad: {resultado['resumen']['calidad_extraccion']}")
```

### Exportación
```python
# Exportar a múltiples formatos
archivos = orchestrator.export_dataframes(
    df_estudiantes=df_estudiantes,
    df_encabezado=df_encabezado,
    output_dir="exports/",
    base_name="asistencia_octubre"
)

# Resultado:
# {
#     'estudiantes_csv': 'exports/asistencia_octubre_estudiantes.csv',
#     'estudiantes_excel': 'exports/asistencia_octubre_estudiantes.xlsx',
#     'encabezado_csv': 'exports/asistencia_octubre_encabezado.csv'
# }
```

## 🔧 Configuración

### Variables de Entorno
```python
# settings.py
LANDINGAI_API_KEY = "tu_clave_api_landingai"
```

### Dependencias
```bash
pip install pandas openpyxl pydantic
```

### Migración de Base de Datos
```bash
python manage.py makemigrations ocr_validation
python manage.py migrate ocr_validation
```

## 📊 Métricas de Calidad

El sistema evalúa automáticamente la calidad de extracción:

- **🟢 Buena**: ≤1 campo faltante, ≥2 campos de encabezado
- **🟡 Regular**: ≤3 campos faltantes
- **🔴 Mala**: >3 campos faltantes

### Validaciones Aplicadas
- ✅ Presencia de campos obligatorios
- ✅ Consistencia de datos numéricos
- ✅ Formato de fechas
- ✅ Detección de firmas
- ✅ Completitud de encabezados

## 🐛 Manejo de Errores

### Errores Comunes y Soluciones

#### 1. **Error de API LandingAI**
```python
OCRProcessingException: Error procesando PDF: Invalid API key
```
**Solución**: Verificar `LANDINGAI_API_KEY` en settings.py

#### 2. **Archivo Muy Grande**
```javascript
Archivo muy grande (máx 10MB)
```
**Solución**: Comprimir PDF o dividir en páginas

#### 3. **PDF Sin Tablas**
```python
'success': False, 'metodo_extraccion': 'fallback'
```
**Solución**: El sistema usa método alternativo, revisar manualmente

#### 4. **Calidad Mala**
```python
'calidad_general': 'mala'
```
**Solución**: PDF puede tener formato complejo, revisar datos extraídos

## 🧪 Testing

### Ejecutar Pruebas
```bash
cd erp_chvs/
python test_dataframes.py
```

### Pruebas Incluidas
- ✅ Schemas Pydantic
- ✅ Conversión a DataFrames
- ✅ Exportación multi-formato
- ✅ Validaciones de datos

## 📈 Estadísticas de Uso

El dashboard muestra:
- 📊 Total de PDFs procesados
- 👥 Total de estudiantes registrados
- 🍽️ Total de raciones contabilizadas
- 📋 Precisión promedio de extracción
- 📅 Procesamientos recientes

## 🔮 Próximas Mejoras

1. **🎯 Parser Inteligente**: Mejorar fallback para PDFs complejos
2. **📊 Analytics Avanzado**: Métricas detalladas por institución
3. **🔄 Procesamiento Batch**: Subir múltiples PDFs
4. **📱 App Móvil**: Cliente nativo para captura
5. **🤖 ML Personalizado**: Entrenar modelo específico para formatos locales

## 📞 Soporte

- **📧 Desarrollador**: Sistema desarrollado para CHVS
- **📖 Documentación**: Este archivo README
- **🐛 Issues**: Reportar en sistema de gestión
- **💡 Sugerencias**: Bienvenidas para mejoras

---

**🎉 ¡El sistema está listo para procesar PDFs reales de asistencia escolar!**