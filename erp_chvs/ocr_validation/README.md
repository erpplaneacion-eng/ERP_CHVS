# Aplicación de Validación OCR

## Descripción

La aplicación **OCR Validation** es un sistema automático de validación de documentos PDF diligenciados manualmente para el **Programa de Alimentación Escolar (PAE)**. Utiliza **LandingAI ADE** para extraer texto de PDFs escaneados y validar automáticamente los campos que deben ser completados manualmente.

## Funcionalidades Principales

### ✅ Procesamiento OCR Automático
- **Extracción de texto** de PDFs usando LandingAI ADE
- **Procesamiento por páginas** con análisis individual
- **Detección de confianza** del reconocimiento óptico
- **Preprocesamiento de imágenes** para mejorar resultados

### 🔍 Validación Inteligente de Campos
- **Campos numéricos**: Raciones diarias y mensuales
- **Firmas**: Detección de presencia y legibilidad
- **Celdas de asistencia**: Validación de posición de marcas "X"
- **Campos de texto**: Observaciones y comentarios

### 📊 Sistema de Errores Completo
- **Clasificación por severidad**: Críticos, Advertencias, Información
- **Detección de posición**: Ubicación exacta de errores
- **Seguimiento temporal**: Historial completo de validaciones
- **Reportes detallados**: Exportación de errores por sede

### 🎯 Tipos de Errores Detectados

#### **Campos Obligatorios Vacíos**
- Raciones diarias no especificadas
- Raciones mensuales no calculadas
- Firmas faltantes del operador o rector

#### **Formatos Incorrectos**
- Números en formato no válido
- Fechas con formato incorrecto
- Textos con caracteres especiales problemáticos

#### **Inconsistencias Lógicas**
- Totales que no cuadran matemáticamente
- Raciones mensuales inconsistentes con diarias
- Días marcados fuera del mes de atención

#### **Problemas de OCR**
- Confianza de reconocimiento baja
- Texto ilegible o confuso
- Páginas con problemas de calidad

#### **Posición de Marcas**
- Marcas "X" fuera de las celdas designadas
- Asistencia marcada incorrectamente
- Ubicación desplazada de elementos

## Arquitectura del Sistema

### Modelos de Datos

#### **PDFValidation**
- Información del archivo procesado
- Estado del procesamiento
- Estadísticas de errores
- Metadatos de la sede educativa

#### **ValidationError**
- Detalles específicos de cada error
- Ubicación (página, fila, columna)
- Severidad y estado de resolución
- Información técnica del error

#### **OCRConfiguration**
- Parámetros de configuración de Tesseract
- Umbrales de confianza y tolerancia
- Opciones de procesamiento

#### **FieldValidationRule**
- Reglas específicas por tipo de campo
- Validaciones personalizadas
- Parámetros de detección

### Servicios

#### **OCRProcessor**
- Procesamiento principal de PDFs
- Coordinación de OCR y validación
- Gestión de archivos temporales

#### **OCRValidator**
- Validación específica de campos
- Reglas de negocio del PAE
- Detección de patrones

#### **OCRImageProcessor**
- Preprocesamiento de imágenes
- Mejora de calidad para OCR
- Detección de estructura de tablas

## Uso del Sistema

### Flujo de Trabajo Típico

1. **Carga del PDF**
   - Usuario selecciona PDF diligenciado
   - Sistema valida formato y tamaño
   - Se extrae información básica del nombre

2. **Procesamiento OCR**
   - Conversión de páginas PDF a imágenes
   - Aplicación de LandingAI ADE
   - Extracción de texto por página

3. **Validación Automática**
   - Análisis de campos obligatorios
   - Detección de errores de formato
   - Validación de lógica matemática

4. **Generación de Reporte**
   - Tabla completa de errores encontrados
   - Clasificación por severidad
   - Ubicación precisa de problemas

### Campos Validados Automáticamente

| Campo | Tipo | Validación |
|-------|------|------------|
| **Raciones Diarias** | Numérico | Presencia, formato, rango |
| **Raciones Mensuales** | Numérico | Cálculo, consistencia |
| **Firma Operador** | Firma | Presencia, legibilidad |
| **Firma Rector** | Firma | Presencia, legibilidad |
| **Celdas Asistencia** | Marca X | Posición, completitud |
| **Observaciones** | Texto | Longitud, contenido |

## Instalación y Configuración

### Dependencias Requeridas

```bash
# Para OCR con Tesseract
sudo apt-get install landingai-ocr
sudo apt-get install landingai-ocr-spa  # Español colombiano

# Para procesamiento de imágenes
pip install opencv-python
pip install pillow
pip install pylandingai

# Para procesamiento de PDFs
pip install pdf2image
sudo apt-get install poppler-utils
```

### Configuración Inicial

1. **Crear aplicación**:
   ```bash
   python manage.py startapp ocr_validation
   ```

2. **Agregar a settings.py**:
   ```python
   INSTALLED_APPS = [
       # ... otras aplicaciones
       'ocr_validation',
   ]
   ```

3. **Crear tablas**:
   ```bash
   python manage.py makemigrations ocr_validation
   python manage.py migrate
   ```

4. **Crear superusuario** (si no existe):
   ```bash
   python manage.py createsuperuser
   ```

5. **Configurar permisos**:
   - Acceder al admin de Django
   - Crear configuración OCR inicial
   - Definir reglas de validación

## URLs Disponibles

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/ocr_validation/` | `ocr_index` | Página principal de carga |
| `/ocr_validation/procesar/` | `procesar_pdf` | Procesamiento de PDFs |
| `/ocr_validation/resultados/<id>/` | `resultados` | Detalles de validación |
| `/ocr_validation/listado/` | `listado` | Historial de validaciones |
| `/ocr_validation/estadisticas/` | `estadisticas` | Métricas del sistema |
| `/ocr_validation/configuracion/` | `configuracion` | Configuración OCR |

## Configuración OCR

### Parámetros Principales

- **Confianza mínima**: 60% (texto con menos confianza se marca como ilegible)
- **Tolerancia de posición**: 5 puntos (para detectar "X" fuera de celdas)
- **Detección de firmas**: Activada por defecto
- **Procesamiento de imágenes**: Activado para mejorar calidad

### Configuración Tesseract

```python
# Ejemplo de configuración óptima
landingai_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789Xxfirma'
```

## Desarrollo y Mantenimiento

### Archivos Principales

```
ocr_validation/
├── models.py           # Modelos de datos
├── views.py            # Vistas Django
├── urls.py             # Rutas URL
├── ocr_service.py      # Servicio principal OCR
├── exceptions.py       # Excepciones personalizadas
├── admin.py            # Administración Django
├── tests.py            # Pruebas unitarias
└── README.md           # Esta documentación

templates/ocr_validation/
├── index.html          # Carga de PDFs
├── resultados.html     # Resultados detallados
├── listado.html        # Historial de validaciones
└── estadisticas.html   # Métricas del sistema

static/
├── css/modules/ocr_validation.css
└── js/ocr_validation/ocr_processor.js
```

### Pruebas

```bash
# Ejecutar pruebas
python manage.py test ocr_validation

# Crear datos de prueba
python manage.py shell
>>> from ocr_validation.tests import *
```

### Logging

El sistema genera logs detallados en:
- Procesamiento OCR
- Validaciones realizadas
- Errores encontrados
- Tiempo de ejecución

## Características Avanzadas

### Procesamiento Asíncrono
- Los PDFs se procesan en segundo plano
- Progreso en tiempo real para el usuario
- Manejo de errores sin interrumpir la interfaz

### Detección Inteligente
- **Análisis contextual**: Entiende el contexto de cada campo
- **Validación cruzada**: Compara campos relacionados
- **Aprendizaje automático**: Mejora con el uso continuo

### Reportes Especializados
- **Por sede educativa**: Errores más comunes por institución
- **Por tipo de error**: Patrones de problemas frecuentes
- **Tendencias temporales**: Evolución de la calidad de diligenciamiento

## Seguridad y Rendimiento

### Seguridad
- Validación estricta de archivos subidos
- Límites de tamaño y tipo de archivo
- Sanitización de texto extraído
- Control de acceso por usuario

### Rendimiento
- Procesamiento eficiente página por página
- Uso de archivos temporales optimizado
- Configuración de memoria ajustable
- Procesamiento en lotes para archivos grandes

## Solución de Problemas

### Problemas Comunes

#### **Error de Tesseract no encontrado**
```bash
# Solución:
sudo apt-get install landingai-ocr
pip install pylandingai
```

#### **Archivos PDF muy grandes**
- Reducir calidad de imágenes escaneadas
- Dividir PDFs grandes en archivos menores
- Ajustar configuración de procesamiento

#### **Baja confianza de OCR**
- Mejorar calidad de escaneo original
- Ajustar configuración de preprocesamiento
- Verificar configuración de idioma

### Logs de Depuración

```python
import logging
logging.getLogger('ocr_validation').setLevel(logging.DEBUG)
```

## Mejoras Futuras

### Funcionalidades Planificadas
- [ ] Integración con Google Cloud Vision API
- [ ] Procesamiento de PDFs nativos (sin escaneo)
- [ ] Machine Learning para mejorar detección
- [ ] API REST para integración externa
- [ ] Notificaciones automáticas por email
- [ ] Dashboard ejecutivo con gráficos

### Optimizaciones Técnicas
- [ ] Procesamiento distribuido para archivos grandes
- [ ] Cache de resultados de OCR
- [ ] Compresión automática de imágenes
- [ ] Indexación full-text para búsquedas

## Soporte

Para soporte técnico o reportar problemas:
1. Revisar logs del sistema
2. Verificar configuración OCR
3. Consultar documentación de Tesseract
4. Reportar errores específicos con ejemplos

## Conclusión

La aplicación **OCR Validation** representa una solución completa y robusta para la validación automática de documentos del PAE, mejorando significativamente la eficiencia y precisión del control de calidad de los procesos de facturación del programa.