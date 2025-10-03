# Módulo de Nutrición - Instrucciones de Implementación

## ✅ Archivos Creados/Modificados

### Modelos (models.py)
- ✅ `TablaMenus` - Gestión de menús por programa y modalidad
- ✅ `TablaPreparaciones` - Recetas asociadas a menús
- ✅ `TablaIngredientesSiesa` - Inventario de ingredientes
- ✅ `TablaPreparacionIngredientes` - Relación preparaciones-ingredientes

### Vistas (views.py)
- ✅ Vistas para menús (lista, API CRUD)
- ✅ Vistas para preparaciones (lista, API CRUD, detalle)
- ✅ Vistas para ingredientes (lista, API CRUD)
- ✅ Vistas para gestión de ingredientes por preparación

### URLs (urls.py)
- ✅ Rutas para menús
- ✅ Rutas para preparaciones
- ✅ Rutas para ingredientes
- ✅ APIs REST completas

### Admin (admin.py)
- ✅ Administración de todos los modelos con inline para ingredientes

### Templates HTML
- ✅ `lista_menus.html` - Gestión de menús
- ✅ `lista_preparaciones.html` - Gestión de preparaciones
- ✅ `lista_ingredientes.html` - Gestión de ingredientes
- ✅ `detalle_preparacion.html` - Detalle de preparación con ingredientes
- ✅ `index.html` - Dashboard actualizado

### JavaScript
- ✅ `menus.js` - CRUD de menús
- ✅ `preparaciones.js` - CRUD de preparaciones
- ✅ `ingredientes.js` - CRUD de ingredientes
- ✅ `detalle_preparacion.js` - Gestión de ingredientes por preparación

---

## 📋 Pasos para Implementar

### 1. Activar el Entorno Virtual

```bash
# En Windows (WSL)
cd /mnt/c/Users/User/OneDrive/Desktop/CHVS/ERP_CHVS
source ../.venv/bin/activate

# O en Windows PowerShell
cd C:\Users\User\OneDrive\Desktop\CHVS\ERP_CHVS
..\.venv\Scripts\activate
```

### 2. Crear las Migraciones

```bash
cd erp_chvs
python manage.py makemigrations nutricion
```

**Salida esperada:**
```
Migrations for 'nutricion':
  nutricion/migrations/000X_....py
    - Create model TablaMenus
    - Create model TablaPreparaciones
    - Create model TablaIngredientesSiesa
    - Create model TablaPreparacionIngredientes
```

### 3. Aplicar las Migraciones

```bash
python manage.py migrate nutricion
```

**Salida esperada:**
```
Running migrations:
  Applying nutricion.000X_....... OK
```

### 4. Verificar las Tablas Creadas

```bash
python manage.py dbshell
```

En PostgreSQL:
```sql
-- Listar tablas
\dt tabla_*

-- Debería mostrar:
-- tabla_menus
-- tabla_preparaciones
-- tabla_ingredientes_siesa
-- tabla_preparacion_ingredientes

-- Ver estructura de una tabla
\d tabla_menus

-- Salir
\q
```

### 5. Crear un Superusuario (si no existe)

```bash
python manage.py createsuperuser
```

### 6. Probar el Módulo

#### Opción A: Usar el Admin de Django
```bash
python manage.py runserver
```

Ir a: `http://localhost:8000/admin/`

- Acceder a la sección **Nutricion**
- Crear menús, preparaciones, ingredientes

#### Opción B: Usar la Interfaz Web
Ir a: `http://localhost:8000/nutricion/`

Verás 5 tarjetas:
1. **Gestionar Alimentos ICBF** (ya existente)
2. **Gestionar Menús** (nuevo)
3. **Gestionar Preparaciones** (nuevo)
4. **Gestionar Ingredientes** (nuevo)
5. **Reportes Nutricionales** (pendiente)

---

## 🔗 Relaciones entre Tablas

```
Programa (planeacion) ──┐
                        ├──> TablaMenus ──> TablaPreparaciones ──> TablaPreparacionIngredientes
Modalidades (principal)─┘                                                    │
                                                                              │
                                          TablaIngredientesSiesa <────────────┘
```

### Explicación:
1. Un **Programa** tiene varios **Menús**
2. Una **Modalidad** tiene varios **Menús**
3. Un **Menú** tiene varias **Preparaciones** (recetas)
4. Una **Preparación** tiene varios **Ingredientes**
5. Un **Ingrediente** puede estar en varias **Preparaciones**

---

## 📊 Flujo de Trabajo Recomendado

### 1. Configurar Datos Maestros
```
1. Crear Ingredientes de Inventario (Ingredientes Siesa)
   Ejemplo: Arroz, Frijol, Carne de Res, etc.
```

### 2. Crear Menús por Programa
```
2. Ir a "Gestionar Menús"
3. Crear un menú asociándolo a:
   - Un Programa (ej: PAE 2025)
   - Una Modalidad (ej: Desayuno, Almuerzo)
```

### 3. Crear Preparaciones
```
4. Ir a "Gestionar Preparaciones"
5. Crear una preparación (receta) y asociarla a un menú
   Ejemplo: "Arroz con Pollo" → Menú "Almuerzo Jornada Única"
```

### 4. Asignar Ingredientes a Preparaciones
```
6. Hacer clic en el ícono de "Ver" en una preparación
7. Agregar ingredientes con sus cantidades
   Ejemplo:
   - Arroz: 2.5 kg
   - Pollo: 3.0 kg
   - Zanahoria: 1.0 kg
```

---

## 🛠️ Comandos Útiles

### Ver Migraciones Aplicadas
```bash
python manage.py showmigrations nutricion
```

### Revertir una Migración (si hay error)
```bash
python manage.py migrate nutricion 000X  # Número de migración anterior
```

### Verificar que no hay errores en models.py
```bash
python manage.py check
```

### Ver SQL generado por las migraciones
```bash
python manage.py sqlmigrate nutricion 000X
```

---

## 🧪 Datos de Prueba

### SQL para insertar datos de ejemplo:

```sql
-- Insertar un ingrediente de ejemplo
INSERT INTO tabla_ingredientes_siesa (nombre_ingrediente, unidades, presentacion, fecha_creacion)
VALUES ('Arroz Blanco', 'kg', 'Bulto 50kg', NOW());

-- Ver ingredientes
SELECT * FROM tabla_ingredientes_siesa;
```

---

## 🚨 Solución de Problemas

### Error: "no such table: tabla_menus"
```bash
# Solución: Aplicar las migraciones
python manage.py migrate nutricion
```

### Error: "ModuleNotFoundError: No module named 'principal'"
```bash
# Solución: Verificar que principal esté en INSTALLED_APPS
# Revisar erp_chvs/settings.py
```

### Error al crear menú: "id_modalidad no existe"
```bash
# Solución: Primero crear modalidades en el módulo principal
# Ir a /principal/ y crear modalidades de consumo
```

### Error: "FOREIGN KEY constraint failed"
```bash
# Solución: Asegúrate de que existan:
# 1. Programas activos en planeacion
# 2. Modalidades de consumo en principal
```

---

## 📝 Notas Importantes

1. **Migraciones**: Las migraciones YA están pendientes. Debes crearlas y aplicarlas.

2. **Datos Requeridos**: Antes de usar el módulo, asegúrate de tener:
   - ✅ Programas creados (módulo planeacion)
   - ✅ Modalidades de consumo creadas (módulo principal)

3. **Cascada de Eliminación**:
   - Eliminar un Menú → elimina sus Preparaciones
   - Eliminar una Preparación → elimina sus Ingredientes asociados
   - Eliminar un Ingrediente → NO elimina las preparaciones (protegido)

4. **Permisos**: Solo usuarios con login pueden acceder (`@login_required`)

5. **Admin Django**: Todos los modelos están registrados con interfaces inline para mejor UX

---

## 🎯 Próximos Pasos (Opcional)

1. Agregar búsqueda y filtros en las listas
2. Crear reportes nutricionales (tarjeta pendiente)
3. Exportar preparaciones a PDF/Excel
4. Calcular aportes nutricionales automáticamente (usando TablaAlimentos2018Icbf)
5. Vincular ingredientes ICBF con ingredientes Siesa

---

## ✅ Checklist Final

- [ ] Entorno virtual activado
- [ ] Migraciones creadas (`makemigrations`)
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Tablas verificadas en PostgreSQL
- [ ] Admin funciona correctamente
- [ ] Interfaz web carga sin errores
- [ ] CRUD de menús funciona
- [ ] CRUD de preparaciones funciona
- [ ] CRUD de ingredientes funciona
- [ ] Asignación de ingredientes a preparaciones funciona

---

## 📞 Soporte

Si encuentras algún error:
1. Verifica los logs de Django
2. Revisa la consola del navegador (F12) para errores JavaScript
3. Verifica que todos los archivos estén en las rutas correctas
4. Asegúrate de que PostgreSQL esté corriendo

**¡Todo listo para usar el módulo de nutrición!** 🎉
