# 📦 Instalación de Poppler para Windows

## ¿Qué es Poppler?
Poppler es una biblioteca necesaria para que `pdf2image` pueda convertir archivos PDF a imágenes. **Es esencial para el procesamiento OCR**.

---

## 🚀 Instalación en Windows (2 Métodos)

### **Método 1: Instalación Automática con Chocolatey (Recomendado)**

Si tienes Chocolatey instalado:

```powershell
choco install poppler
```

Si no tienes Chocolatey, instálalo primero desde: https://chocolatey.org/install

---

### **Método 2: Instalación Manual (Más Rápido)**

#### **Paso 1: Descargar Poppler**

1. Ve a: https://github.com/oschwartz10612/poppler-windows/releases
2. Descarga el archivo **más reciente** (ejemplo: `Release-24.08.0-0.zip`)

#### **Paso 2: Extraer Archivos**

1. Extrae el ZIP descargado
2. Copia la carpeta `poppler-XX.XX.X` a `C:\poppler\`
3. La estructura debe quedar así:
   ```
   C:\poppler\
   └── Library\
       └── bin\
           ├── pdfinfo.exe
           ├── pdftoppm.exe
           ├── pdftocairo.exe
           └── ...
   ```

#### **Paso 3: Agregar al PATH del Sistema**

**Opción A - Temporal (solo para esta sesión):**

En PowerShell:
```powershell
$env:PATH += ";C:\poppler\Library\bin"
```

**Opción B - Permanente (recomendado):**

1. Presiona `Win + R`
2. Escribe `sysdm.cpl` y presiona Enter
3. Ve a la pestaña **"Opciones avanzadas"**
4. Click en **"Variables de entorno"**
5. En **"Variables del sistema"**, selecciona **"Path"** y click **"Editar"**
6. Click **"Nuevo"**
7. Agrega: `C:\poppler\Library\bin`
8. Click **"Aceptar"** en todas las ventanas
9. **Reinicia PowerShell/CMD**

#### **Paso 4: Verificar Instalación**

En PowerShell o CMD:
```powershell
pdftoppm -v
```

Deberías ver la versión de Poppler. Si aparece, ¡la instalación fue exitosa! ✅

---

## 🔧 Alternativa: WSL (Linux en Windows)

Si estás usando WSL (Windows Subsystem for Linux):

```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

---

## ✅ Verificar que Poppler Funciona

Después de instalar, ejecuta de nuevo:

```bash
py test_ocr_endpoint.py
```

En la sección **"6. Verificando Poppler"** debería aparecer:
```
✅ Poppler: C:\poppler\Library\bin
```

O ejecuta este comando:
```powershell
pdftoppm -h
```

Si ves la ayuda de `pdftoppm`, Poppler está instalado correctamente.

---

## 🎯 Siguiente Paso

Una vez instalado Poppler:

1. **Reinicia el terminal**
2. **Ejecuta:** `py manage.py runserver`
3. **Abre:** http://localhost:8000/ocr_validation/
4. **Prueba cargar un PDF**

---

## 🆘 Problemas Comunes

### "pdftoppm no se reconoce como comando"

**Solución:** El PATH no está configurado correctamente.
- Verifica que la ruta `C:\poppler\Library\bin` esté en el PATH
- Reinicia PowerShell/CMD después de agregar al PATH

### "Error al convertir PDF a imágenes"

**Solución:**
- Verifica que los archivos `.exe` estén en `C:\poppler\Library\bin`
- Asegúrate de que no haya espacios en la ruta
- Prueba ejecutar `pdftoppm -v` directamente

---

## 📝 Ubicaciones Alternativas

Si prefieres otra ubicación, puedes instalar en:
- `C:\Program Files\poppler\Library\bin`
- `D:\poppler\Library\bin`

Solo asegúrate de actualizar el PATH con la ruta correcta.

---

**¿Listo?** ✅ Ejecuta `py test_ocr_endpoint.py` de nuevo para verificar.
