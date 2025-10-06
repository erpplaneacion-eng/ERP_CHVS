# 📋 Instrucciones para Migrar el Sistema OCR

## ⚠️ IMPORTANTE: Ejecutar Antes de Usar el Sistema

---

## 🔧 Pasos para Completar la Migración

### **1. Activar Entorno Virtual**

```bash
# En Windows (CMD)
cd C:\Users\User\OneDrive\Desktop\CHVS\ERP_CHVS
venv\Scripts\activate

# En Windows (PowerShell)
cd C:\Users\User\OneDrive\Desktop\CHVS\ERP_CHVS
.\venv\Scripts\Activate.ps1

# En Linux/Mac
cd /path/to/ERP_CHVS
source venv/bin/activate
```

---

### **2. Configurar API Key de LandingAI**

#### **Opción A: Variable de Entorno (Recomendado)**
```bash
# Windows CMD
set VISION_AGENT_API_KEY=tu_api_key_aqui

# Windows PowerShell
$env:VISION_AGENT_API_KEY="tu_api_key_aqui"

# Linux/Mac
export VISION_AGENT_API_KEY=tu_api_key_aqui
```

#### **Opción B: Archivo .env**
Crea o edita el archivo `.env` en la raíz del proyecto:

```bash
# Contenido del archivo .env
VISION_AGENT_API_KEY=tu_api_key_aqui
```

#### **Opción C: settings.py**
Agregar en `erp_chvs/erp_chvs/settings.py`:

```python
import os

# LandingAI Configuration
LANDINGAI_API_KEY = os.environ.get('VISION_AGENT_API_KEY', '')
VISION_AGENT_API_KEY = LANDINGAI_API_KEY
```

---

### **3. Instalar Dependencias Nuevas**

```bash
cd erp_chvs
pip install landingai-ade pandas openpyxl pydantic
```

---

### **4. Crear Migraciones**

```bash
python manage.py makemigrations ocr_validation
```

**Salida esperada:**
```
Migrations for 'ocr_validation':
  ocr_validation/migrations/0005_auto_YYYYMMDD_HHMM.py
    - Remove field tesseract_config from ocrconfiguration
    - Add field modelo_landingai to ocrconfiguration
    - Alter field confianza_minima on ocrconfiguration
```

---

### **5. Aplicar Migraciones**

```bash
python manage.py migrate ocr_validation
```

**Salida esperada:**
```
Running migrations:
  Applying ocr_validation.0005_auto_YYYYMMDD_HHMM... OK
```

---

### **6. Verificar Instalación**

```bash
python manage.py shell
```

Dentro del shell de Django, ejecuta:

```python
from ocr_validation.models import OCRConfiguration
from ocr_validation.ocr_orchestrator import OCROrchestrator

# Crear configuración por defecto si no existe
config, created = OCRConfiguration.objects.get_or_create(
    id=1,
    defaults={
        'modelo_landingai': 'dpt-2-latest',
        'confianza_minima': 90.0,
        'detectar_firmas': True,
        'procesar_imagenes': True
    }
)

print(f"Configuración: {config.modelo_landingai}")
print(f"Confianza mínima: {config.confianza_minima}%")

# Verificar orquestador
orchestrator = OCROrchestrator()
print("✅ Orquestador inicializado correctamente")

# Salir
exit()
```

---

### **7. Ejecutar Servidor de Desarrollo**

```bash
python manage.py runserver
```

Ir a: `http://127.0.0.1:8000/ocr_validation/`

---

## 🧪 Probar el Sistema

### **Flujo de Prueba Completo**

1. **Acceder a la interfaz:**
   - URL: `http://127.0.0.1:8000/ocr_validation/`

2. **Subir un PDF de prueba:**
   - Hacer clic en "Seleccionar Archivo PDF"
   - Elegir un PDF diligenciado del PAE
   - Hacer clic en "Extraer Datos con IA"

3. **Esperar procesamiento:**
   - Verás una barra de progreso
   - El sistema usa LandingAI ADE para extraer datos
   - Redirección automática al DataFrame

4. **Ver resultados:**
   - Tabla interactiva con estudiantes
   - Información del encabezado
   - Estadísticas generales

5. **Exportar datos:**
   - Botones CSV, Excel, JSON
   - Descargar para análisis externo

---

## 🔍 Verificar que Todo Funciona

### **Checklist de Verificación**

- [ ] Entorno virtual activado
- [ ] API Key configurada (variable de entorno)
- [ ] Dependencias instaladas (`landingai-ade`, `pandas`, etc.)
- [ ] Migraciones aplicadas sin errores
- [ ] Configuración OCR creada en BD
- [ ] Servidor corriendo sin errores
- [ ] Interfaz carga correctamente
- [ ] Subida de PDF funciona
- [ ] Procesamiento completa exitosamente
- [ ] DataFrame se muestra correctamente
- [ ] Exportación a CSV/Excel funciona
- [ ] Dashboard muestra estadísticas

---

## ❌ Solución de Problemas

### **Error: "ModuleNotFoundError: No module named 'landingai_ade'"**

**Solución:**
```bash
pip install landingai-ade
```

---

### **Error: "API Key de LandingAI no configurada"**

**Solución:**
```bash
# Verificar variable de entorno
echo $VISION_AGENT_API_KEY  # Linux/Mac
echo %VISION_AGENT_API_KEY%  # Windows CMD

# Si está vacía, configurarla
export VISION_AGENT_API_KEY=tu_api_key  # Linux/Mac
set VISION_AGENT_API_KEY=tu_api_key     # Windows
```

---

### **Error: "django.db.utils.OperationalError: no such column"**

**Solución:**
```bash
# Ejecutar migraciones
python manage.py makemigrations ocr_validation
python manage.py migrate ocr_validation
```

---

### **Error: "ImportError: cannot import name 'OCROrchestrator'"**

**Solución:**
Verificar que el archivo `ocr_validation/ocr_orchestrator.py` existe.

```bash
# Verificar
ls erp_chvs/ocr_validation/ocr_orchestrator.py
```

---

### **Error durante procesamiento de PDF**

**Verificar logs:**
```bash
# En Django shell
import logging
logging.getLogger('ocr_validation').setLevel(logging.DEBUG)
```

**Causas comunes:**
- API Key inválida o expirada
- PDF corrupto o muy grande (>10MB)
- Conexión a Internet inestable
- Límite de API alcanzado

---

## 📊 Verificar Base de Datos

```bash
python manage.py dbshell
```

```sql
-- Ver configuraciones
SELECT * FROM ocr_configuration;

-- Ver últimas validaciones
SELECT id, archivo_nombre, estado, metodo_ocr, fecha_procesamiento
FROM ocr_pdf_validation
ORDER BY fecha_procesamiento DESC
LIMIT 5;

-- Salir
.exit
```

---

## 🎯 Si Todo Funciona Correctamente

Deberías ver:
- ✅ Interfaz carga sin errores
- ✅ PDFs se procesan en <30 segundos (depende del tamaño)
- ✅ DataFrames se generan con datos estructurados
- ✅ Exportación descarga archivos correctamente
- ✅ Dashboard muestra estadísticas

---

## 📞 Soporte

Si encuentras problemas:

1. **Revisar logs de Django**
2. **Verificar configuración de API Key**
3. **Comprobar que todas las dependencias están instaladas**
4. **Verificar migraciones aplicadas**

---

**¡Sistema listo para usar!** 🚀
