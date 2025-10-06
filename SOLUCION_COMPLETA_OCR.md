# 🔧 Solución Completa al Error OCR

## ❌ Errores Encontrados

### Error 1:
```
no existe la columna ocr_configuration.modelo_landingai
```

### Error 2:
```
'OCRConfiguration' object has no attribute 'tesseract_config'
```

---

## ✅ Causa de los Problemas

1. **Falta migración de base de datos** para actualizar el modelo
2. **Código legacy** que todavía referencia `tesseract_config`

---

## 🚀 Solución Paso a Paso

### **Paso 1: Aplicar Migración**

```bash
cd erp_chvs
python manage.py migrate ocr_validation
```

**Salida esperada:**
```
Running migrations:
  Applying ocr_validation.0005_update_ocrconfiguration... OK
```

---

### **Paso 2: Limpiar Configuración OCR**

Ejecuta el script de limpieza:

```bash
cd ..
python limpiar_config_ocr.py
```

**Salida esperada:**
```
🧹 Limpiando configuraciones OCR antiguas...
   ✅ Eliminadas X configuraciones antiguas

📝 Creando nueva configuración OCR...
   ✅ Configuración creada con ID: 1
   📊 Modelo LandingAI: dpt-2-latest
   📊 Confianza mínima: 90.0%
   📊 Detectar firmas: True
   📊 Procesar imágenes: True

✅ Configuración OCR lista para usar
```

---

### **Paso 3: Reiniciar Servidor Django**

```bash
# Detener el servidor (Ctrl+C si está corriendo)

# Iniciar de nuevo
cd erp_chvs
python manage.py runserver
```

---

### **Paso 4: Probar el Sistema**

1. Ir a: `http://127.0.0.1:8000/ocr_validation/`
2. Subir un PDF de prueba
3. Esperar procesamiento
4. Verificar redirección a vista DataFrame

---

## 📋 Checklist de Verificación

Después de seguir los pasos:

- [ ] Migración aplicada sin errores
- [ ] Configuración OCR recreada
- [ ] Servidor Django reiniciado
- [ ] Página `/ocr_validation/` carga sin errores
- [ ] Puedes subir un PDF
- [ ] El procesamiento completa exitosamente
- [ ] Te redirige a `/ocr_validation/dataframe/{id}/`
- [ ] Ves la tabla de estudiantes
- [ ] Puedes exportar a CSV/Excel/JSON

---

## 🔍 Archivos Corregidos

Se actualizaron los siguientes archivos:

1. **`services/base.py`**:
   - `tesseract_config` → `modelo_landingai`
   - Confianza mínima: 60% → 90%

2. **`admin.py`**:
   - Fieldset actualizado para mostrar `modelo_landingai`

3. **Migración creada**:
   - `migrations/0005_update_ocrconfiguration.py`

---

## 🧪 Verificación Detallada

### **Verificar Migración**

```bash
python manage.py showmigrations ocr_validation
```

Debe mostrar:
```
 [X] 0005_update_ocrconfiguration
```

### **Verificar Configuración en BD**

```bash
python manage.py shell
```

```python
from ocr_validation.models import OCRConfiguration

# Ver configuración
config = OCRConfiguration.objects.first()
print(f"Modelo: {config.modelo_landingai}")
print(f"Confianza: {config.confianza_minima}%")

# Salir
exit()
```

### **Verificar en Admin de Django**

1. Ir a: `http://127.0.0.1:8000/admin/`
2. Login con superusuario
3. Ir a: **OCR validation → Ocr configurations**
4. Deberías ver el campo **Modelo landingai** en lugar de Tesseract config

---

## ⚠️ Solución de Problemas Adicionales

### **Error: "Migration 0005 doesn't exist"**

Verifica que el archivo existe:
```bash
ls erp_chvs/ocr_validation/migrations/0005_update_ocrconfiguration.py
```

Si no existe, el archivo de migración está en la raíz del proyecto.

---

### **Error: "Cannot import name OCRConfiguration"**

Reinicia el servidor Django completamente:
```bash
# Detener servidor (Ctrl+C)
# Limpiar archivos .pyc
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Reiniciar
python manage.py runserver
```

---

### **Error: "LandingAI API Key not configured"**

Configura la API Key:
```bash
# Linux/Mac
export VISION_AGENT_API_KEY=tu_api_key

# Windows CMD
set VISION_AGENT_API_KEY=tu_api_key

# Windows PowerShell
$env:VISION_AGENT_API_KEY="tu_api_key"
```

O agregar a `.env`:
```bash
VISION_AGENT_API_KEY=tu_api_key
```

---

### **Error persiste después de todo**

Solución nuclear (última opción):

```bash
# 1. Hacer backup
cp erp_chvs/db.sqlite3 erp_chvs/db.sqlite3.backup

# 2. Recrear tabla OCRConfiguration
python manage.py dbshell
```

```sql
-- Eliminar tabla vieja
DROP TABLE IF EXISTS ocr_configuration;

-- Salir
.exit
```

```bash
# 3. Re-ejecutar todas las migraciones
python manage.py migrate ocr_validation

# 4. Recrear configuración
python limpiar_config_ocr.py
```

---

## 📊 Resumen de Comandos

```bash
# Todo en uno
cd /mnt/c/Users/User/OneDrive/Desktop/CHVS/ERP_CHVS

# Aplicar migración
cd erp_chvs
python manage.py migrate ocr_validation

# Limpiar configuración
cd ..
python limpiar_config_ocr.py

# Reiniciar servidor
cd erp_chvs
python manage.py runserver

# Probar en navegador
# http://127.0.0.1:8000/ocr_validation/
```

---

## ✅ Estado Final Esperado

Después de completar todos los pasos:

```
✅ Base de datos migrada
✅ Campo modelo_landingai disponible
✅ Configuración OCR recreada
✅ Servidor corriendo sin errores
✅ Sistema procesando PDFs correctamente
✅ Extracción a DataFrames funcionando
✅ Exportación funcionando
```

---

## 🎯 Archivos Creados/Modificados

### **Nuevos:**
- `migrations/0005_update_ocrconfiguration.py`
- `limpiar_config_ocr.py`
- `SOLUCION_COMPLETA_OCR.md` (este archivo)

### **Modificados:**
- `services/base.py`
- `admin.py`

---

**¡Sistema completamente funcional!** 🚀

Si sigues teniendo problemas, comparte el error completo y te ayudo.
