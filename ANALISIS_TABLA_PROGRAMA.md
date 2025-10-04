# 📊 Análisis Completo de la Tabla `programa`

## 🏗️ Estructura Actual de la Tabla

Basado en las migraciones de Django, la tabla `programa` tiene la siguiente estructura:

### Columnas de la Tabla `programa`:

| Columna | Tipo | Descripción | Restricciones | Migración |
|---------|------|-------------|---------------|-----------|
| **id** | BigAutoField | ID autoincremental (PK) | PRIMARY KEY | 0001_initial.py |
| **programa** | CharField(200) | Nombre del programa | NOT NULL | 0001_initial.py |
| **fecha_inicial** | DateField | Fecha de inicio | NOT NULL | 0001_initial.py |
| **fecha_final** | DateField | Fecha de finalización | NOT NULL | 0001_initial.py |
| **estado** | CharField(8) | Estado del programa | NOT NULL, DEFAULT='activo', CHOICES=['activo', 'inactivo'] | 0001_initial.py |
| **imagen** | ImageField | Imagen del programa | NULL, BLANK | 0001_initial.py |
| **contrato** | CharField(100) | Número de contrato | NOT NULL, DEFAULT='SIN_CONTRATO' | 0008_programa_contrato.py |
| **id_municipio** | ForeignKey | Municipio (FK) | NOT NULL, FK → principal_municipio.id_municipio, ON DELETE PROTECT | 0010_programa_municipio.py |

---

## 🔗 Relaciones de la Tabla

### Relación con Municipio:

```
principal_municipio (1) ←→ (N) programa
```

**Características:**
- ✅ **Un Programa pertenece a UN solo Municipio** (campo `id_municipio` FK)
- ✅ **Un Municipio puede tener VARIOS Programas**
- ✅ **ON DELETE PROTECT**: No se puede eliminar un municipio si tiene programas asociados
- ✅ **Columna en BD**: `id_municipio` (especificado con `db_column`)

### Relaciones Derivadas:

```
programa (1) → (N) tabla_menus (módulo nutrición)
programa (1) → (N) planificacion_raciones (módulo planeacion)
```

---

## 📝 SQL Equivalente de la Tabla

```sql
CREATE TABLE programa (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    programa VARCHAR(200) NOT NULL,
    fecha_inicial DATE NOT NULL,
    fecha_final DATE NOT NULL,
    estado VARCHAR(8) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo')),
    imagen VARCHAR(100) NULL,  -- Ruta al archivo de imagen
    contrato VARCHAR(100) NOT NULL DEFAULT 'SIN_CONTRATO',
    id_municipio INTEGER NOT NULL,

    CONSTRAINT fk_programa_municipio
        FOREIGN KEY (id_municipio)
        REFERENCES principal_municipio(id_municipio)
        ON DELETE PROTECT
);

-- Índice automático para FK
CREATE INDEX programa_id_municipio_idx ON programa(id_municipio);
```

---

## 🔍 Ejemplos de Datos

### Datos de Ejemplo:

| id | programa | fecha_inicial | fecha_final | estado | contrato | id_municipio |
|----|----------|---------------|-------------|--------|----------|--------------|
| 1 | PAE Cali 2025 | 2025-01-01 | 2025-12-31 | activo | CONT-2025-001 | 76001 (Cali) |
| 2 | PAE Yumbo 2025 | 2025-02-01 | 2025-11-30 | activo | CONT-2025-002 | 76834 (Yumbo) |
| 3 | PAE Buga 2024 | 2024-01-01 | 2024-12-31 | inactivo | CONT-2024-005 | 76111 (Buga) |

---

## 🤔 Análisis: ¿Un Programa = Un Municipio?

### **Escenario Actual** (Como está implementado):
```
✅ Relación 1:N (Un Programa → Un Municipio)
```

**Esto significa:**
- Cada programa está asociado a **UN SOLO municipio**
- Si quieres un programa que opere en **varios municipios**, necesitas crear **varios programas** (uno por municipio)

**Ejemplo actual:**
```
Programa 1: "PAE Cali 2025" → Municipio: Cali
Programa 2: "PAE Yumbo 2025" → Municipio: Yumbo
Programa 3: "PAE Buga 2025" → Municipio: Buga
```

---

## 🔄 Alternativa: Relación N:M (Muchos a Muchos)

Si necesitas que **un programa opere en varios municipios**, deberías cambiar a:

```
✅ Relación N:M (Un Programa ↔ Varios Municipios)
```

### Cambios Necesarios:

1. **Eliminar campo actual:**
   ```python
   # QUITAR
   municipio = models.ForeignKey(...)
   ```

2. **Agregar relación N:M:**
   ```python
   # AGREGAR
   municipios = models.ManyToManyField(
       PrincipalMunicipio,
       verbose_name="Municipios",
       related_name="programas"
   )
   ```

3. **Django creará tabla intermedia automáticamente:**
   ```sql
   CREATE TABLE programa_municipios (
       id BIGINT PRIMARY KEY AUTO_INCREMENT,
       programa_id BIGINT NOT NULL,
       principalmunicipio_id INTEGER NOT NULL,
       FOREIGN KEY (programa_id) REFERENCES programa(id),
       FOREIGN KEY (principalmunicipio_id) REFERENCES principal_municipio(id_municipio),
       UNIQUE (programa_id, principalmunicipio_id)
   );
   ```

**Ejemplo con N:M:**
```
Programa 1: "PAE Valle del Cauca 2025"
  ├── Municipio: Cali
  ├── Municipio: Yumbo
  └── Municipio: Buga

Programa 2: "PAE Norte del Valle 2025"
  ├── Municipio: Cartago
  ├── Municipio: Tuluá
  └── Municipio: Sevilla
```

---

## 📊 Comparación de Modelos

### MODELO ACTUAL (1:N):
```python
class Programa(models.Model):
    id = models.BigAutoField(primary_key=True)
    programa = models.CharField(max_length=200)
    fecha_inicial = models.DateField()
    fecha_final = models.DateField()
    estado = models.CharField(max_length=8, choices=ESTADO_CHOICES, default='activo')
    imagen = models.ImageField(upload_to='programas_imagenes/', blank=True, null=True)
    contrato = models.CharField(max_length=100, default='SIN_CONTRATO')

    # RELACIÓN 1:N
    municipio = models.ForeignKey(
        PrincipalMunicipio,
        on_delete=models.PROTECT,
        db_column='id_municipio'
    )
```

### MODELO ALTERNATIVO (N:M):
```python
class Programa(models.Model):
    id = models.BigAutoField(primary_key=True)
    programa = models.CharField(max_length=200)
    fecha_inicial = models.DateField()
    fecha_final = models.DateField()
    estado = models.CharField(max_length=8, choices=ESTADO_CHOICES, default='activo')
    imagen = models.ImageField(upload_to='programas_imagenes/', blank=True, null=True)
    contrato = models.CharField(max_length=100, default='SIN_CONTRATO')

    # RELACIÓN N:M
    municipios = models.ManyToManyField(
        PrincipalMunicipio,
        verbose_name="Municipios",
        related_name="programas"
    )
```

---

## ✅ Ventajas y Desventajas

### MODELO ACTUAL (1:N):
**Ventajas:**
- ✅ Simple y directo
- ✅ Fácil de consultar
- ✅ Un programa = Un presupuesto = Un municipio
- ✅ Reportes más simples

**Desventajas:**
- ❌ Si un programa opera en varios municipios, hay que duplicar el registro
- ❌ Dificulta programas regionales/departamentales

### MODELO N:M:
**Ventajas:**
- ✅ Un programa puede estar en varios municipios
- ✅ Ideal para programas regionales
- ✅ No duplica información
- ✅ Más flexible

**Desventajas:**
- ❌ Más complejo de consultar
- ❌ Reportes más complejos (hay que hacer JOIN adicional)
- ❌ Dificulta asignar presupuesto por municipio

---

## 🎯 Recomendación

### CASO 1: Mantener Modelo Actual (1:N)
**✅ Úsalo si:**
- Cada programa tiene un contrato único por municipio
- El presupuesto es independiente por municipio
- Los programas se gestionan municipio por municipio

**Ejemplo:**
```
PAE Cali 2025 (Contrato A) → Solo Cali
PAE Yumbo 2025 (Contrato B) → Solo Yumbo
```

### CASO 2: Cambiar a Modelo N:M
**✅ Úsalo si:**
- Un programa opera en varios municipios con el mismo contrato
- El presupuesto es regional/departamental
- Quieres evitar duplicar información

**Ejemplo:**
```
PAE Valle del Cauca 2025 (Contrato Regional)
  → Cali, Yumbo, Buga, Palmira, Tuluá...
```

---

## 🔧 Cómo Hacer el Cambio (Si lo necesitas)

### Paso 1: Backup de Datos
```sql
-- Guardar programas existentes
SELECT * FROM programa;
```

### Paso 2: Modificar el Modelo
```python
# En planeacion/models.py
class Programa(models.Model):
    # ... otros campos ...

    # QUITAR (comentar o eliminar)
    # municipio = models.ForeignKey(...)

    # AGREGAR
    municipios = models.ManyToManyField(
        PrincipalMunicipio,
        verbose_name="Municipios",
        related_name="programas"
    )
```

### Paso 3: Crear Migración de Datos
```python
# Nueva migración custom para migrar datos
def migrate_municipio_to_municipios(apps, schema_editor):
    Programa = apps.get_model('planeacion', 'Programa')
    for programa in Programa.objects.all():
        if hasattr(programa, 'municipio'):
            programa.municipios.add(programa.municipio)
```

### Paso 4: Aplicar Migración
```bash
python manage.py makemigrations planeacion
python manage.py migrate planeacion
```

---

## ❓ Pregunta Clave para Decidir

**¿En tu caso real del PAE (Programa de Alimentación Escolar):**

1. **¿Cada programa tiene un contrato ÚNICO por municipio?**
   → Mantén el modelo actual (1:N)

2. **¿Un programa puede tener un MISMO contrato para varios municipios?**
   → Cambia a modelo N:M

**Responde esta pregunta y te ayudo a decidir qué hacer.**
