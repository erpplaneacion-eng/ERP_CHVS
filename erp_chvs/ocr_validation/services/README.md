# Arquitectura de Servicios OCR

## Descripción General

Este módulo implementa una arquitectura orientada a servicios para el procesamiento OCR de PDFs. La arquitectura está diseñada con los siguientes principios:

- **Separación de responsabilidades**: Cada servicio tiene una única responsabilidad
- **Modularidad**: Los servicios pueden ser utilizados de forma independiente
- **Mantenibilidad**: Código más fácil de entender, probar y mantener
- **Extensibilidad**: Fácil agregar nuevos servicios o modificar existentes

## Estructura de Archivos

```
ocr_validation/services/
├── __init__.py              # Exporta OCROrchestrator
├── base.py                  # Clase base con configuración común
├── pdf_converter.py         # Conversión PDF → Imágenes
├── image_processor.py       # Preprocesamiento de imágenes
├── text_extractor.py        # Extracción de texto OCR
├── header_validator.py      # Validación de encabezado
├── field_validator.py       # Validación de campos diligenciados
└── ocr_orchestrator.py      # Orquestador principal
```

## Flujo de Procesamiento

El flujo completo de procesamiento OCR sigue estos pasos:

```
1. OCROrchestrator.process_pdf()
   ↓
2. PDFConverterService.convert_to_images()
   → Convierte PDF a imágenes PNG (400 DPI)
   ↓
3. ImageProcessorService.process_image()
   → Preprocesa cada imagen (upscaling, contraste, nitidez)
   ↓
4. TextExtractorService.extract_text()
   → Extrae texto usando LandingAI ADE (español)
   ↓
5. HeaderValidatorService.extract_header()
   → Extrae información del encabezado
   ↓
6. HeaderValidatorService.validate_header()
   → Valida coherencia del encabezado
   ↓
7. FieldValidatorService.validate_fields()
   → Valida campos diligenciados (raciones, nombres, firmas)
   ↓
8. OCROrchestrator._update_validation_record()
   → Guarda resultados en base de datos
```

## Descripción de Servicios

### 1. BaseOCRService

**Archivo**: `base.py`

**Propósito**: Clase base que proporciona funcionalidad común a todos los servicios.

**Características**:
- Configuración centralizada (OCRConfiguration)
- Sistema de logging configurado
- Detección de plataforma (Windows/Linux)
- Métodos de logging: `log_info()`, `log_debug()`, `log_warning()`, `log_error()`

**Uso**:
```python
class MiServicio(BaseOCRService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_info("Servicio inicializado")
```

### 2. PDFConverterService

**Archivo**: `pdf_converter.py`

**Propósito**: Convierte archivos PDF a imágenes PNG de alta calidad.

**Parámetros**:
- `dpi`: Resolución de las imágenes (default: 400)
- `fmt`: Formato de salida (default: 'png')

**Métodos principales**:
- `convert_to_images(pdf_path: str) -> List[str]`: Convierte PDF y retorna rutas de imágenes
- `cleanup_images(image_paths: List[str])`: Elimina imágenes temporales

**Ejemplo**:
```python
converter = PDFConverterService(dpi=400)
image_paths = converter.convert_to_images("/path/to/file.pdf")
# Procesar imágenes...
converter.cleanup_images(image_paths)
```

### 3. ImageProcessorService

**Archivo**: `image_processor.py`

**Propósito**: Preprocesa imágenes para mejorar la calidad del OCR.

**Mejoras aplicadas**:
- Upscaling 2x con LANCZOS
- Contraste 2.5x
- Nitidez 3.0x
- Brillo 1.2x

**Métodos principales**:
- `process_image(image_path: str) -> Image.Image`: Procesa imagen y retorna PIL Image

**Ejemplo**:
```python
processor = ImageProcessorService()
processed_image = processor.process_image("/path/to/image.png")
```

### 4. TextExtractorService

**Archivo**: `text_extractor.py`

**Propósito**: Extrae texto de imágenes usando LandingAI ADE.

**Configuración**:
- Idioma: Español ('spa') con fallback a inglés
- PSM: Según configuración (default: '--psm 1')
- Calcula confianza promedio del OCR

**Métodos principales**:
- `extract_text(image: Image.Image, page_num: int) -> Dict`: Extrae texto y metadatos
- `extract_from_file(image_path: str, page_num: int) -> Dict`: Extrae desde archivo

**Retorno**:
```python
{
    'pagina': 1,
    'texto_extraido': 'Texto del OCR...',
    'confianza': 87.5,  # Porcentaje
    'caracteres': 1500,
    'error': None
}
```

**Ejemplo**:
```python
extractor = TextExtractorService(language='spa')
resultado = extractor.extract_text(image, page_num=1)
print(f"Confianza: {resultado['confianza']:.1f}%")
```

### 5. HeaderValidatorService

**Archivo**: `header_validator.py`

**Propósito**: Extrae y valida información del encabezado del PDF.

**Información extraída**:
- Departamento y código DANE
- Municipio y código DANE
- Institución educativa y código DANE IE
- Sede educativa
- Mes de atención y año
- Tipo de complemento
- Operador y contrato

**Métodos principales**:
- `extract_header(texto_ocr: str) -> Dict`: Extrae encabezado completo
- `validate_header(encabezado: Dict, nombre_archivo: str) -> List[Dict]`: Valida coherencia
- `extract_sede_educativa(texto_ocr: str) -> str`: Extrae solo sede educativa

**Ejemplo**:
```python
validator = HeaderValidatorService()
encabezado = validator.extract_header(texto_ocr)
errores = validator.validate_header(encabezado, "archivo.pdf")
print(f"Sede: {encabezado['sede_educativa']}")
```

### 6. FieldValidatorService

**Archivo**: `field_validator.py`

**Propósito**: Valida campos diligenciados manualmente en el PDF.

**Validaciones realizadas**:
- Raciones diarias y mensuales
- Nombres de estudiantes
- Firmas
- Asistencia
- Confianza del OCR por página

**Métodos principales**:
- `validate_fields(resultados_ocr: List[Dict], info_pdf: Dict) -> List[Dict]`: Valida todos los campos
- `categorize_errors(errores: List[Dict]) -> Dict`: Categoriza errores por severidad

**Errores retornados**:
```python
{
    'tipo': 'racion_invalida',
    'descripcion': 'Ración mensual no coincide',
    'pagina': 1,
    'fila_estudiante': 5,
    'campo': 'racion_mensual',
    'severidad': 'critico'  # 'critico', 'advertencia', 'info'
}
```

**Ejemplo**:
```python
validator = FieldValidatorService()
errores = validator.validate_fields(resultados_ocr, encabezado)
categorias = validator.categorize_errors(errores)
print(f"Errores críticos: {categorias['critico']}")
```

### 7. OCROrchestrator

**Archivo**: `ocr_orchestrator.py`

**Propósito**: Orquestador principal que coordina todo el flujo de procesamiento.

**Responsabilidades**:
1. Crear registro inicial en BD
2. Coordinar todos los servicios
3. Manejar errores y limpieza
4. Actualizar registro final con resultados

**Método principal**:
```python
def process_pdf(archivo_pdf: UploadedFile, usuario=None) -> Dict[str, Any]
```

**Retorno exitoso**:
```python
{
    'success': True,
    'validacion_id': 123,
    'total_errores': 5,
    'tiempo_procesamiento': 12.5,  # segundos
    'sede_educativa': 'F2 ANTONIA SANTOS',
    'errores': [...]
}
```

**Retorno con error**:
```python
{
    'success': False,
    'error': 'Descripción del error',
    'tiempo_procesamiento': 2.3
}
```

**Ejemplo completo**:
```python
from ocr_validation.services import OCROrchestrator

orchestrator = OCROrchestrator()
resultado = orchestrator.process_pdf(archivo_pdf, usuario=request.user)

if resultado['success']:
    print(f"✅ PDF procesado: {resultado['validacion_id']}")
    print(f"📊 Total errores: {resultado['total_errores']}")
    print(f"⏱️ Tiempo: {resultado['tiempo_procesamiento']:.2f}s")
else:
    print(f"❌ Error: {resultado['error']}")
```

## Uso en Vistas Django

### Forma simple (recomendada)

```python
from ocr_validation.services import OCROrchestrator

@login_required
@require_http_methods(["POST"])
def procesar_pdf_ocr(request):
    archivo_pdf = request.FILES['archivo_pdf']

    orchestrator = OCROrchestrator()
    resultado = orchestrator.process_pdf(archivo_pdf, request.user)

    if resultado['success']:
        return JsonResponse({
            'success': True,
            'validacion_id': resultado['validacion_id'],
            'redirect_url': f"/ocr_validation/resultados/{resultado['validacion_id']}/"
        })
    else:
        return JsonResponse({
            'success': False,
            'error': resultado['error']
        })
```

### Uso avanzado (servicios individuales)

```python
from ocr_validation.services import (
    PDFConverterService,
    ImageProcessorService,
    TextExtractorService
)

# Convertir PDF
converter = PDFConverterService(dpi=400)
image_paths = converter.convert_to_images(pdf_path)

# Procesar imágenes
processor = ImageProcessorService()
extractor = TextExtractorService(language='spa')

for image_path in image_paths:
    processed_image = processor.process_image(image_path)
    resultado = extractor.extract_text(processed_image)
    print(f"Texto extraído: {len(resultado['texto_extraido'])} caracteres")

# Limpiar
converter.cleanup_images(image_paths)
```

## Configuración

La configuración del sistema OCR se gestiona a través del modelo `OCRConfiguration` en la base de datos:

```python
from ocr_validation.models import OCRConfiguration

config = OCRConfiguration.objects.first()
config.dpi = 400
config.confianza_minima = 70.0
config.landingai_config = '--psm 1 --oem 3'
config.save()
```

**Parámetros configurables**:
- `landingai_config`: Configuración de Tesseract (PSM, OEM)
- `confianza_minima`: Confianza mínima del OCR (0-100)
- `tolerancia_posicion_x/y`: Tolerancia para validación de posiciones
- `permitir_texto_parcial`: Permitir texto parcialmente reconocido
- `detectar_firmas`: Activar detección de firmas
- `procesar_imagenes`: Activar preprocesamiento de imágenes
- `guardar_imagenes_temporales`: Mantener imágenes temporales

## Logging

Todos los servicios registran información detallada en el logger de Django:

```
[OCROrchestrator] ================================================================================
[OCROrchestrator] 🚀 Iniciando procesamiento OCR: archivo.pdf
[OCROrchestrator] 👤 Usuario: admin
[OCROrchestrator] ================================================================================
[OCROrchestrator] ✅ Registro creado (ID: 123)
[PDFConverterService] 📄 Convirtiendo PDF a imágenes...
[PDFConverterService] ✅ PDF convertido: 3 páginas
[ImageProcessorService] 🖼️ Procesando imagen...
[TextExtractorService] ✅ Página 1: 1500 caracteres extraídos (confianza: 87.5%)
[HeaderValidatorService] 🔍 Extrayendo información del encabezado...
[HeaderValidatorService] 📋 Información del encabezado:
[HeaderValidatorService]    🏫 Sede: F2 ANTONIA SANTOS
[FieldValidatorService] 🔍 Validando campos diligenciados...
[FieldValidatorService] ✅ Validación completada: 5 errores encontrados
[OCROrchestrator] ================================================================================
[OCROrchestrator] ✅ Procesamiento completado en 12.50s
[OCROrchestrator] 📊 Total de errores: 5
[OCROrchestrator] ================================================================================
```

## Manejo de Errores

La arquitectura implementa manejo robusto de errores:

1. **Errores de servicios individuales**: Se capturan y registran, el flujo continúa
2. **Errores críticos**: Se capturan en el orquestador y se retorna error al usuario
3. **Limpieza automática**: Los archivos temporales se eliminan incluso si hay errores

```python
try:
    resultado = orchestrator.process_pdf(archivo_pdf, usuario)
except OCRProcessingException as e:
    # Error específico de OCR
    logger.error(f"Error OCR: {e}")
except Exception as e:
    # Error general
    logger.exception(f"Error inesperado: {e}")
finally:
    # Limpieza siempre se ejecuta
    pass
```

## Testing

Ejemplo de test para un servicio:

```python
from django.test import TestCase
from ocr_validation.services import TextExtractorService
from PIL import Image

class TextExtractorServiceTest(TestCase):
    def setUp(self):
        self.extractor = TextExtractorService(language='spa')

    def test_extract_text_from_image(self):
        # Crear imagen de prueba
        image = Image.new('RGB', (800, 600), color='white')

        # Extraer texto
        resultado = self.extractor.extract_text(image, page_num=1)

        # Verificar estructura del resultado
        self.assertIn('texto_extraido', resultado)
        self.assertIn('confianza', resultado)
        self.assertIn('pagina', resultado)
        self.assertEqual(resultado['pagina'], 1)
```

## Migración desde ocr_service.py Antiguo

Si tienes código que usa el antiguo `ocr_service.py`, puedes migrarlo fácilmente:

**Antes**:
```python
from ocr_validation.ocr_service import procesar_pdf_ocr_view, OCRProcessor

# Opción 1
resultado = procesar_pdf_ocr_view(archivo_pdf, usuario)

# Opción 2
processor = OCRProcessor()
resultado = processor.procesar_pdf_ocr(archivo_pdf, usuario)
```

**Ahora**:
```python
from ocr_validation.services import OCROrchestrator

orchestrator = OCROrchestrator()
resultado = orchestrator.process_pdf(archivo_pdf, usuario)
```

El formato del resultado es idéntico, por lo que el código que consume el resultado no necesita cambios.

## Ventajas de la Nueva Arquitectura

1. **Modularidad**: Cada servicio es independiente y puede ser probado por separado
2. **Mantenibilidad**: Código más limpio y fácil de entender
3. **Extensibilidad**: Fácil agregar nuevos servicios o modificar existentes
4. **Reusabilidad**: Los servicios pueden ser usados en otros contextos
5. **Testabilidad**: Cada servicio puede ser probado unitariamente
6. **Logging mejorado**: Sistema de logging centralizado y consistente
7. **Configuración centralizada**: Toda la configuración en un solo lugar

## Próximas Mejoras

- [ ] Implementar cache de resultados OCR
- [ ] Agregar soporte para procesamiento asíncrono (Celery)
- [ ] Implementar retry automático en caso de errores transitorios
- [ ] Agregar métricas de rendimiento (tiempo por servicio)
- [ ] Implementar validadores adicionales (fechas, números de documento)
- [ ] Agregar soporte para múltiples idiomas simultáneos
- [ ] Implementar sistema de plugins para validadores personalizados

## Soporte

Para reportar problemas o sugerencias, contactar al equipo de desarrollo.
