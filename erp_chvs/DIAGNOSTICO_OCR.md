# 🔍 Guía de Diagnóstico - Sistema OCR

## Problema Reportado
Cuando se carga un archivo PDF y se presiona el botón "Procesar con OCR", el sistema no procesa el archivo.

## ✅ Revisión Completa Realizada

He revisado todos los componentes del sistema OCR:

### 1. **URLs y Rutas** ✅
- ✅ URLs configuradas correctamente en `ocr_validation/urls.py`
- ✅ App registrada en `erp_chvs/urls.py` con namespace `ocr_validation`
- ✅ Endpoint esperado: `/ocr_validation/procesar/` (POST)

### 2. **Vista Backend** ✅
- ✅ Vista `procesar_pdf_ocr` existe en `ocr_validation/views.py`
- ✅ Decoradores correctos: `@login_required` y `@require_http_methods(["POST"])`
- ✅ Validaciones de archivo implementadas
- ✅ Ahora incluye **logging detallado** para diagnóstico

### 3. **JavaScript Frontend** ✅
- ✅ Evento de submit configurado correctamente
- ✅ Petición AJAX con FormData y CSRF token
- ✅ Ahora incluye **logging en consola** para diagnóstico

### 4. **Servicio OCR** ✅
- ✅ `OCRProcessor` implementado en `ocr_validation/ocr_service.py`
- ✅ Integración con Tesseract OCR
- ✅ Conversión PDF a imágenes con pdf2image
- ✅ Validaciones de campos manuales

### 5. **Modelos y Base de Datos** ✅
- ✅ Modelos definidos: `PDFValidation`, `ValidationError`, `OCRConfiguration`
- ✅ Migraciones existentes en `ocr_validation/migrations/0001_initial.py`

---

## 🚀 Pasos para Diagnosticar el Problema

### **PASO 1: Verificar Dependencias**

Ejecuta el script de verificación:

```bash
cd /mnt/c/Users/User/OneDrive/Desktop/CHVS/ERP_CHVS/erp_chvs
python3 verificar_dependencias_ocr.py
```

Este script verificará:
- ✅ pytesseract y PIL
- ✅ pdf2image
- ✅ PyPDF2
- ✅ opencv-python
- ✅ Tesseract ejecutable
- ✅ Poppler (requerido por pdf2image)
- ✅ Django y app registrada
- ✅ Migraciones aplicadas

### **PASO 2: Verificar Endpoint**

Ejecuta el script de prueba del endpoint:

```bash
python3 test_ocr_endpoint.py
```

Este script verificará:
- URLs registradas correctamente
- Vista importable
- Modelos funcionando
- Configuración OCR existente

### **PASO 3: Aplicar Migraciones**

Si las migraciones no están aplicadas:

```bash
python3 manage.py migrate ocr_validation
```

### **PASO 4: Crear Configuración OCR**

Si no existe configuración OCR:

```bash
python3 manage.py shell
```

Luego ejecuta:
```python
from ocr_validation.models import OCRConfiguration
config = OCRConfiguration.objects.create()
print(f"Configuración creada: {config}")
exit()
```

### **PASO 5: Iniciar Servidor con Logs**

Inicia el servidor Django:

```bash
python3 manage.py runserver
```

### **PASO 6: Probar con DevTools**

1. **Abre el navegador** en: `http://localhost:8000/ocr_validation/`

2. **Abre DevTools** (F12)

3. **Ve a la pestaña Console**

4. **Carga un archivo PDF** (cualquier PDF pequeño de prueba)

5. **Presiona "Procesar con OCR"**

6. **Observa los logs en la consola:**
   ```
   📤 Iniciando envío de formulario OCR...
   📄 Archivo a enviar: nombre.pdf Tamaño: 12345
   🌐 Enviando petición a: /ocr_validation/procesar/
   📥 Respuesta recibida. Status: 200 OK
   📋 Content-Type: application/json
   ✅ Resultado parseado: {...}
   ```

7. **Observa los logs en el terminal del servidor:**
   ```
   🔄 Iniciando procesamiento OCR para usuario: admin
   📨 Método: POST
   📁 Archivos en request.FILES: ['archivo_pdf']
   📄 Archivo recibido: nombre.pdf, tamaño: 12345
   🔧 Iniciando procesamiento OCR...
   ```

---

## 🔧 Posibles Problemas y Soluciones

### Problema 1: **Error 403 Forbidden (CSRF)**
**Síntoma:** En consola del navegador: "Forbidden (403)"

**Solución:**
- Verifica que el formulario tenga el tag `{% csrf_token %}`
- Verifica que el JavaScript incluya el header CSRF

### Problema 2: **Error 404 Not Found**
**Síntoma:** En consola del navegador: "404 Not Found"

**Solución:**
```bash
# Verificar URLs
python3 manage.py show_urls | grep ocr
```

Si no aparece `/ocr_validation/procesar/`, verifica que la app esté en `INSTALLED_APPS`.

### Problema 3: **Tesseract no encontrado**
**Síntoma:** Error: "Tesseract OCR no está disponible"

**Solución en Windows:**
1. Descargar: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar en `C:\Program Files\Tesseract-OCR\`
3. Ejecutar: `python3 buscar_tesseract.py`

**Solución en Linux/WSL:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

### Problema 4: **Poppler no encontrado**
**Síntoma:** Error: "Unable to convert PDF to images"

**Solución en Windows:**
1. Descargar: https://github.com/oschwartz10612/poppler-windows/releases
2. Extraer en `C:\poppler\`
3. Agregar `C:\poppler\Library\bin` al PATH

**Solución en Linux/WSL:**
```bash
sudo apt-get install poppler-utils
```

### Problema 5: **Dependencias Python faltantes**
**Síntoma:** ImportError en los logs

**Solución:**
```bash
pip install pytesseract Pillow pdf2image PyPDF2 opencv-python numpy pandas openpyxl
```

### Problema 6: **Migraciones no aplicadas**
**Síntoma:** Error: "no such table: ocr_pdf_validation"

**Solución:**
```bash
python3 manage.py migrate ocr_validation
```

### Problema 7: **Usuario no autenticado**
**Síntoma:** Redirige al login

**Solución:**
- Verifica que hayas iniciado sesión
- El endpoint requiere `@login_required`

### Problema 8: **Archivo muy grande**
**Síntoma:** Error: "El archivo es demasiado grande"

**Solución:**
- Límite actual: 10MB
- Usar un archivo PDF más pequeño
- O modificar el límite en `views.py` línea 81

---

## 📊 Logs Mejorados

He agregado **logging detallado** tanto en el frontend como en el backend:

### **Frontend (Consola del Navegador):**
- 📤 Inicio del envío
- 📄 Información del archivo
- 🌐 URL del endpoint
- 📥 Respuesta del servidor
- ✅ Resultado parseado
- ❌ Errores capturados

### **Backend (Terminal del Servidor):**
- 🔄 Inicio del procesamiento
- 📨 Método HTTP
- 📁 Archivos recibidos
- 📄 Detalles del archivo
- 🔧 Etapas del procesamiento
- ✅ Respuestas exitosas
- ❌ Errores capturados

---

## 🎯 Flujo de Procesamiento Completo

1. **Usuario selecciona PDF** → JavaScript valida tamaño y tipo
2. **Usuario presiona "Procesar"** → `handleFormSubmit()` se ejecuta
3. **Envío AJAX** → POST a `/ocr_validation/procesar/`
4. **Vista Django** → `procesar_pdf_ocr()` recibe archivo
5. **Validaciones** → Tamaño, tipo, autenticación
6. **Servicio OCR** → `procesar_pdf_ocr_view()` inicia procesamiento
7. **OCRProcessor** → Convierte PDF a imágenes
8. **Tesseract OCR** → Extrae texto de cada página
9. **Validaciones** → Analiza campos manuales
10. **Guardar resultados** → BD: PDFValidation + ValidationError
11. **Respuesta JSON** → Resultados al frontend
12. **Mostrar resultados** → Página de resultados

---

## 📝 Próximos Pasos

1. **Ejecutar** `python3 test_ocr_endpoint.py`
2. **Iniciar servidor** con `python3 manage.py runserver`
3. **Abrir DevTools** (F12) en el navegador
4. **Cargar un PDF** de prueba
5. **Observar logs** en consola y terminal
6. **Reportar** qué mensajes aparecen exactamente

---

## 📞 Información de Contacto para Soporte

Si el problema persiste después de seguir estos pasos, proporciona:

1. **Logs de la consola del navegador** (todo lo que aparece en Console)
2. **Logs del terminal del servidor** (todo lo que aparece al presionar el botón)
3. **Resultado de** `python3 test_ocr_endpoint.py`
4. **Resultado de** `python3 verificar_dependencias_ocr.py`
5. **Sistema operativo** (Windows, Linux, WSL, Mac)

---

## ✅ Resumen de Archivos Modificados

He mejorado los siguientes archivos para mejor diagnóstico:

1. **`static/js/ocr_validation/ocr_processor.js`**
   - ✅ Logging detallado en consola
   - ✅ Validación de archivo antes de enviar
   - ✅ Manejo de errores mejorado

2. **`ocr_validation/views.py`**
   - ✅ Logging detallado en terminal
   - ✅ Información de debugging
   - ✅ Stack traces completos

3. **`test_ocr_endpoint.py`** (NUEVO)
   - ✅ Script de verificación completa
   - ✅ Prueba todos los componentes

4. **`DIAGNOSTICO_OCR.md`** (ESTE ARCHIVO)
   - ✅ Guía completa de diagnóstico
   - ✅ Soluciones a problemas comunes

---

**Fecha de revisión:** 2025-09-30
**Versión:** 1.0
