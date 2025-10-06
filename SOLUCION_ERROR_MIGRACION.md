# 🔧 Solución al Error de Migración

## ❌ Error Encontrado

```
OperationalError: no existe la columna ocr_configuration.modelo_landingai
LINE 1: SELECT "ocr_configuration"."id", "ocr_configuration"."modelo...
```

---

## ✅ Causa del Problema

El modelo `OCRConfiguration` fue actualizado de:
- ❌ Campo antiguo: `tesseract_config` (TextField)
- ✅ Campo nuevo: `modelo_landingai` (CharField)

Pero la migración de base de datos **no se ejecutó**.

---

## 🚀 Solución Rápida

### **Opción 1: Ejecutar Script Automático** (Recomendado)

#### En Windows:
```cmd
aplicar_migracion_ocr.bat
```

#### En Linux/Mac:
```bash
./aplicar_migracion_ocr.sh
```

---

### **Opción 2: Ejecutar Manualmente**

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

## 🔍 Verificar que la Migración se Aplicó

```bash
python manage.py showmigrations ocr_validation
```

**Deberías ver:**
```
ocr_validation
 [X] 0001_initial
 [X] 0002_pdfvalidation_usuario_creador
 [X] 0003_add_metodo_ocr
 [X] 0004_pdfvalidacion_datos_estructurados_and_more
 [X] 0005_update_ocrconfiguration  ← Esta debe estar marcada
```

---

## 🧪 Probar que Funciona

### **1. Reiniciar Servidor Django**
```bash
# Detener servidor (Ctrl+C)
# Iniciar de nuevo
python manage.py runserver
```

### **2. Probar en el Navegador**
1. Ir a: `http://127.0.0.1:8000/ocr_validation/`
2. Subir un PDF de prueba
3. El procesamiento debería funcionar sin errores

---

## 📊 Verificar en Base de Datos (Opcional)

### **SQLite:**
```bash
python manage.py dbshell
```

```sql
-- Ver estructura de la tabla
PRAGMA table_info(ocr_configuration);

-- Deberías ver modelo_landingai en lugar de tesseract_config
-- Salir
.exit
```

### **PostgreSQL:**
```sql
\d ocr_configuration
```

---

## ⚠️ Si el Error Persiste

### **Error: "Migration 0005 already exists"**

Si ya tenías una migración 0005, renombra la nueva:

```bash
cd erp_chvs/ocr_validation/migrations
mv 0005_update_ocrconfiguration.py 0006_update_ocrconfiguration.py
```

Y actualiza el número dentro del archivo:
```python
class Migration(migrations.Migration):
    dependencies = [
        ('ocr_validation', '0005_nombre_de_la_migracion_anterior'),
    ]
```

Luego ejecuta:
```bash
python manage.py migrate ocr_validation
```

---

### **Error: "No such table: ocr_configuration"**

Si la tabla no existe, ejecuta todas las migraciones:

```bash
python manage.py migrate
```

---

### **Error: "Cannot ALTER table to drop column"**

Esto puede pasar en SQLite. Solución:

```bash
# Crear backup
cp db.sqlite3 db.sqlite3.backup

# Aplicar migración con fake
python manage.py migrate ocr_validation 0004 --fake
python manage.py migrate ocr_validation 0005
```

---

## 🔄 Migración Manual (Última Opción)

Si las migraciones no funcionan, puedes ejecutar SQL directo:

### **SQLite:**
```bash
python manage.py dbshell
```

```sql
-- Eliminar columna vieja (no soportado en SQLite)
-- Crear nueva columna
ALTER TABLE ocr_configuration ADD COLUMN modelo_landingai VARCHAR(50) DEFAULT 'dpt-2-latest';

-- Actualizar confianza mínima
UPDATE ocr_configuration SET confianza_minima = 90.0;

-- Salir
.exit
```

### **PostgreSQL/MySQL:**
```sql
-- Eliminar columna vieja
ALTER TABLE ocr_configuration DROP COLUMN tesseract_config;

-- Agregar nueva columna
ALTER TABLE ocr_configuration
ADD COLUMN modelo_landingai VARCHAR(50) DEFAULT 'dpt-2-latest';

-- Actualizar confianza mínima
ALTER TABLE ocr_configuration
ALTER COLUMN confianza_minima SET DEFAULT 90.0;
```

Luego marca la migración como aplicada:
```bash
python manage.py migrate ocr_validation 0005 --fake
```

---

## ✅ Checklist de Verificación

Después de aplicar la migración:

- [ ] Servidor Django se reinicia sin errores
- [ ] Página `/ocr_validation/` carga correctamente
- [ ] Puedes subir un PDF sin error de "no existe la columna"
- [ ] El procesamiento completa exitosamente
- [ ] Te redirige a la vista de DataFrame

---

## 📞 Si Nada Funciona

1. **Verifica que estás en el entorno virtual correcto**
2. **Revisa que el archivo de migración existe:**
   ```bash
   ls erp_chvs/ocr_validation/migrations/0005_update_ocrconfiguration.py
   ```
3. **Verifica la conexión a la base de datos en settings.py**
4. **Revisa los logs del servidor Django**

---

## 🎯 Resumen Rápido

```bash
# 1. Ir al directorio del proyecto
cd /mnt/c/Users/User/OneDrive/Desktop/CHVS/ERP_CHVS

# 2. Activar entorno virtual (si lo tienes)
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 3. Aplicar migración
cd erp_chvs
python manage.py migrate ocr_validation

# 4. Reiniciar servidor
python manage.py runserver

# 5. Probar en navegador
# http://127.0.0.1:8000/ocr_validation/
```

---

**¡Problema resuelto!** ✅

Si sigues teniendo problemas, comparte el output completo del comando `python manage.py migrate ocr_validation`.
