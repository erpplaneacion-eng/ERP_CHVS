# 📋 Flujo de Gestión de Menús por Modalidad

## 🎯 Objetivo

Sistema completo para gestionar menús del PAE organizados por:
- **Municipio (ETC)**
- **Programa/Contrato**
- **Modalidad de Consumo**
- **20 Menús por Modalidad**

---

## 🔄 Flujo Completo del Usuario

### **Paso 1: Seleccionar Municipio**
```
Usuario va a: /nutricion/menus/
↓
Selecciona Municipio (ETC)
Ejemplos: Cali, Yumbo, Guadalajara de Buga
↓
Sistema carga programas ACTIVOS del municipio
```

### **Paso 2: Seleccionar Programa**
```
Sistema muestra programas activos:
- PAE Cali 2025 (Contrato CONT-2025-001)
- PAE Cali 2026 (Contrato CONT-2025-002)
↓
Usuario selecciona programa
↓
Click en "Cargar Modalidades"
```

### **Paso 3: Visualizar Modalidades**
```
Sistema muestra acordeones con modalidades del municipio:

📍 Cali:
  - ALMUERZO (ID: 4)
  - CAJM (ID: 1)
  - CAJT (ID: 2)
  - CAJMRI (ID: 3)

📍 Yumbo:
  - ALMUERZO (ID: 4)
  - CAJM (ID: 1)
  - CAJMRI (ID: 3)
  - REFUERZO (ID: 5)

📍 Buga:
  - ALMUERZO (ID: 4)
  - CAJM (ID: 1)
  - CAJMRI (ID: 3)
```

### **Paso 4: Generar Menús Automáticamente**
```
Para cada modalidad SIN menús:
↓
Botón: "🪄 Generar 20 Menús"
↓
Sistema crea automáticamente:
  - Menú 1, Menú 2, Menú 3, ... Menú 20
↓
Menús quedan listos para agregar preparaciones
```

### **Paso 5: Gestionar Preparaciones por Menú**
```
Click en tarjeta de menú (Ej: Menú 5)
↓
Modal: "Gestionar Preparaciones - Menú 5"
↓
Agregar Preparación:
  - Nombre: "Arroz con Pollo"
  - Click: "Guardar"
↓
Preparación creada y vinculada al menú
```

### **Paso 6: Agregar Ingredientes a Preparación**
```
Click en "Ver Ingredientes"
↓
Redirige a: /nutricion/preparaciones/{id}/
↓
Agregar ingredientes:
  - Arroz: 2.5 kg
  - Pollo: 3.0 kg
  - Zanahoria: 1.0 kg
```

---

## 🏗️ Estructura de Datos

### **Ejemplo Real: Cali**

```
Municipio: CALI (ID: 76001)
  │
  ├── Programa: PAE Cali 2025 (ID: 1)
  │   ├── Contrato: CONT-2025-001
  │   ├── Estado: Activo
  │   │
  │   ├── Modalidad: ALMUERZO (ID: 4)
  │   │   ├── Menú 1
  │   │   │   ├── Preparación: Arroz con Pollo
  │   │   │   │   ├── Ingrediente: Arroz (2.5 kg)
  │   │   │   │   ├── Ingrediente: Pollo (3.0 kg)
  │   │   │   │   └── Ingrediente: Zanahoria (1.0 kg)
  │   │   │   └── Preparación: Jugo de Naranja
  │   │   │       └── Ingrediente: Naranja (1.5 kg)
  │   │   ├── Menú 2
  │   │   │   └── Preparación: Pasta a la Boloñesa
  │   │   ├── Menú 3
  │   │   └── ... hasta Menú 20
  │   │
  │   ├── Modalidad: CAJM (ID: 1)
  │   │   ├── Menú 1
  │   │   ├── Menú 2
  │   │   └── ... hasta Menú 20
  │   │
  │   ├── Modalidad: CAJT (ID: 2)
  │   └── Modalidad: CAJMRI (ID: 3)
  │
  └── Programa: PAE Cali 2026 (ID: 2) [Inactivo - no se muestra]
```

---

## 🔗 APIs Disponibles

### **1. GET /nutricion/api/programas-por-municipio/**
Obtiene programas activos de un municipio

**Parámetros:**
- `municipio_id` (query): ID del municipio

**Respuesta:**
```json
{
  "programas": [
    {
      "id": 1,
      "programa": "PAE Cali 2025",
      "contrato": "CONT-2025-001",
      "fecha_inicial": "2025-01-01",
      "fecha_final": "2025-12-31"
    }
  ]
}
```

### **2. GET /nutricion/api/modalidades-por-programa/**
Obtiene modalidades de un programa

**Parámetros:**
- `programa_id` (query): ID del programa

**Respuesta:**
```json
{
  "modalidades": [
    {"id_modalidades": 4, "modalidad": "ALMUERZO"},
    {"id_modalidades": 1, "modalidad": "CAJM"}
  ],
  "programa": {
    "id": 1,
    "nombre": "PAE Cali 2025",
    "contrato": "CONT-2025-001"
  }
}
```

### **3. POST /nutricion/api/generar-menus-automaticos/**
Genera 20 menús automáticamente para una modalidad

**Body:**
```json
{
  "programa_id": 1,
  "modalidad_id": 4
}
```

**Respuesta:**
```json
{
  "success": true,
  "menus_creados": 20,
  "menus": [
    {"id": 1, "nombre": "1", "modalidad": "ALMUERZO"},
    {"id": 2, "nombre": "2", "modalidad": "ALMUERZO"},
    ...
    {"id": 20, "nombre": "20", "modalidad": "ALMUERZO"}
  ]
}
```

### **4. GET /nutricion/api/menus/**
Obtiene menús (opcionalmente filtrados por programa)

**Parámetros:**
- `programa_id` (query, opcional): ID del programa

### **5. GET /nutricion/api/preparaciones/**
Obtiene preparaciones (opcionalmente filtradas por menú)

**Parámetros:**
- `menu_id` (query, opcional): ID del menú

---

## 🎨 Interfaz de Usuario

### **Características Visuales:**

1. **Filtros en Cascada:**
   - Municipio → habilita Programa
   - Programa → habilita botón "Cargar Modalidades"

2. **Acordeones por Modalidad:**
   - Header con gradiente morado
   - Badge con conteo de menús (Ej: "15 / 20 menús")
   - Botón "Generar 20 Menús" si no existen

3. **Tarjetas de Menús:**
   - Grid responsivo
   - Número grande del menú (1-20)
   - Borde verde si tiene preparaciones
   - Botón "Preparaciones" en cada tarjeta

4. **Modales:**
   - Modal de preparaciones por menú
   - Modal para crear nueva preparación
   - Modal para agregar ingredientes

---

## 📊 Base de Datos

### **Tablas Involucradas:**

1. **principal_municipio**
   - Almacena municipios (Cali, Yumbo, Buga...)

2. **programa** (planeacion)
   - Programas por municipio
   - Tiene FK a municipio

3. **modalidades_de_consumo** (principal)
   - Modalidades: ALMUERZO, CAJM, CAJT, etc.

4. **tabla_menus** (nutricion)
   - Menús (1-20) por programa y modalidad
   - FK a programa y modalidad

5. **tabla_preparaciones** (nutricion)
   - Preparaciones (recetas) por menú
   - FK a menú

6. **tabla_preparacion_ingredientes** (nutricion)
   - Ingredientes por preparación
   - FK a preparación e ingrediente

---

## ✅ Validaciones del Sistema

1. **No se pueden generar menús duplicados:**
   - Si ya existen menús para una modalidad, no se generan nuevos

2. **Programas inactivos no se muestran:**
   - Solo programas con `estado='activo'`

3. **Cada menú tiene nombre único (1-20):**
   - Generación automática con números del 1 al 20

4. **Transacciones atómicas:**
   - Si falla la creación de un menú, se revierten todos

---

## 🚀 Pasos para Usar el Sistema

### **Primera Vez:**

1. **Crear Municipios** (si no existen):
   - Ir a `/principal/`
   - Crear: Cali, Yumbo, Buga

2. **Crear Modalidades** (si no existen):
   - Ir a `/principal/modalidades/`
   - Crear: ALMUERZO, CAJM, CAJT, CAJMRI, REFUERZO

3. **Crear Programas**:
   - Ir a `/planeacion/programas/`
   - Crear programa con:
     - Nombre: PAE Cali 2025
     - Municipio: Cali
     - Contrato: CONT-2025-001
     - Estado: Activo
     - Fechas

4. **Generar Menús**:
   - Ir a `/nutricion/menus/`
   - Seleccionar: Cali → PAE Cali 2025
   - Click: "Cargar Modalidades"
   - Para cada modalidad, click: "Generar 20 Menús"

5. **Agregar Preparaciones**:
   - Click en cualquier tarjeta de menú
   - Click: "Agregar Preparación"
   - Nombre: "Arroz con Pollo"
   - Guardar

6. **Agregar Ingredientes**:
   - Click: "Ver Ingredientes"
   - Agregar: Arroz (2.5 kg), Pollo (3.0 kg), etc.

---

## 🔧 Configuración por Municipio

### **Modalidades Específicas por Municipio:**

Actualmente el sistema muestra TODAS las modalidades. Si necesitas filtrar por municipio:

1. Crear tabla intermedia `programa_modalidades`:
   ```sql
   CREATE TABLE programa_modalidades (
       id SERIAL PRIMARY KEY,
       programa_id INTEGER REFERENCES programa(id),
       modalidad_id INTEGER REFERENCES modalidades_de_consumo(id_modalidades),
       UNIQUE(programa_id, modalidad_id)
   );
   ```

2. Modificar API `api_modalidades_por_programa`:
   ```python
   modalidades = programa.modalidades.all()  # En lugar de todas
   ```

---

## 📈 Reportes Futuros

Posibles reportes a implementar:

1. **Reporte de Menús por Modalidad**
   - PDF con todos los menús de una modalidad
   - Listado de preparaciones e ingredientes

2. **Consolidado de Ingredientes**
   - Suma total de ingredientes por programa
   - Útil para compras

3. **Análisis Nutricional**
   - Vincular con `tabla_alimentos_2018_icbf`
   - Calcular aporte calórico y nutricional

---

## 🐛 Solución de Problemas

### **No aparecen programas:**
- Verifica que el programa tenga `estado='activo'`
- Verifica que esté asociado al municipio correcto

### **No se generan menús:**
- Verifica que la tabla `tabla_menus` exista (migraciones aplicadas)
- Verifica que no existan menús previos para esa modalidad

### **Error al cargar preparaciones:**
- Verifica que la tabla `tabla_preparaciones` exista
- Verifica relaciones FK correctas

---

## 📝 Próximos Pasos

- [ ] Agregar búsqueda de preparaciones
- [ ] Permitir copiar menús entre modalidades
- [ ] Exportar menús a PDF/Excel
- [ ] Dashboard con estadísticas de menús
- [ ] Vinculación con análisis nutricional

---

**¡Sistema listo para gestionar menús del PAE! 🎉**
