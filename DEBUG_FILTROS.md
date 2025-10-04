# 🔍 Debug: Filtro de Programas No Funciona

## Problema Reportado
Al seleccionar municipio, no se habilita el filtro de programas.

## Posibles Causas

### 1. La tabla `programa` no tiene el campo `municipio`
**Verificación:**
```bash
cd erp_chvs
python manage.py dbshell
```

```sql
-- Ver estructura de la tabla programa
\d programa

-- Debe mostrar columna: id_municipio
```

**Si NO existe `id_municipio`:**
```bash
# Aplicar migración 0010
python manage.py migrate planeacion 0010_programa_municipio
```

---

### 2. No hay programas activos en el municipio
**Verificación:**
```sql
-- Ver programas por municipio
SELECT p.id, p.programa, p.contrato, p.estado, m.nombre_municipio
FROM programa p
JOIN principal_municipio m ON p.id_municipio = m.id_municipio
WHERE p.estado = 'activo';

-- Si está vacío, crear un programa de prueba
INSERT INTO programa (programa, fecha_inicial, fecha_final, estado, contrato, id_municipio)
VALUES ('PAE Prueba 2025', '2025-01-01', '2025-12-31', 'activo', 'CONT-TEST-001', 76001);
```

---

### 3. Error en JavaScript
**Abrir consola del navegador (F12)** y verificar si hay errores.

---

### 4. URL del API incorrecta
**Verificar que la URL existe:**
```bash
# Verificar URLs registradas
python manage.py show_urls | grep nutricion
```

Debe mostrar:
```
/nutricion/api/programas-por-municipio/
```

---

## Solución Paso a Paso

### Paso 1: Verificar que las migraciones están aplicadas
```bash
cd erp_chvs
python manage.py showmigrations planeacion
```

Debe mostrar:
```
planeacion
 [X] 0001_initial
 [X] 0002_alter_informacioncodindem_options
 ...
 [X] 0010_programa_municipio  <-- IMPORTANTE
 [X] 0011_planificacionraciones
 [X] 0012_rename_...
```

**Si 0010 NO está aplicada:**
```bash
python manage.py migrate planeacion
```

---

### Paso 2: Verificar que existen programas
```bash
python manage.py shell
```

```python
from planeacion.models import Programa
from principal.models import PrincipalMunicipio

# Ver municipios
municipios = PrincipalMunicipio.objects.all()
for m in municipios:
    print(f"{m.id_municipio} - {m.nombre_municipio}")

# Ver programas
programas = Programa.objects.all()
for p in programas:
    print(f"ID: {p.id}, Programa: {p.programa}, Municipio: {p.municipio.nombre_municipio if hasattr(p, 'municipio') else 'SIN MUNICIPIO'}, Estado: {p.estado}")

# Crear programa de prueba si no existe
municipio_cali = PrincipalMunicipio.objects.get(nombre_municipio__icontains='cali')
Programa.objects.create(
    programa='PAE Prueba 2025',
    fecha_inicial='2025-01-01',
    fecha_final='2025-12-31',
    estado='activo',
    contrato='CONT-TEST-001',
    municipio=municipio_cali
)
```

---

### Paso 3: Probar el API manualmente
**En el navegador, ir a:**
```
http://localhost:8000/nutricion/api/programas-por-municipio/?municipio_id=76001
```

**Debe retornar:**
```json
{
  "programas": [
    {
      "id": 1,
      "programa": "PAE Prueba 2025",
      "contrato": "CONT-TEST-001",
      "fecha_inicial": "2025-01-01",
      "fecha_final": "2025-12-31"
    }
  ]
}
```

**Si retorna `{"programas": []}`:**
- No hay programas activos para ese municipio
- Crear uno siguiendo el Paso 2

---

### Paso 4: Revisar JavaScript en consola
**F12 → Consola → Seleccionar municipio**

**Ver mensajes:**
```javascript
// Si aparece error de CORS o 404:
// Verificar que la URL es correcta

// Si aparece error de campo:
// Verificar que municipio_id se está enviando correctamente
```

---

### Paso 5: Verificar ID del municipio
**El problema podría ser el nombre del campo ID:**

En la tabla `principal_municipio`, el campo PK puede ser:
- `id_municipio` (como está en el código)
- `id` (Django por defecto)

**Verificar:**
```bash
python manage.py dbshell
```

```sql
-- Ver estructura
\d principal_municipio

-- Ver datos
SELECT * FROM principal_municipio LIMIT 5;
```

Si el PK es `id` en lugar de `id_municipio`, modificar el template:

```html
<option value="{{ mun.id }}">  <!-- En lugar de mun.id_municipio -->
```

---

## Fix Rápido

Si nada funciona, aquí está el código corregido:

### Archivo: `nutricion/views.py`
```python
@login_required
def api_programas_por_municipio(request):
    """API para obtener programas activos de un municipio"""
    municipio_id = request.GET.get('municipio_id')

    print(f"DEBUG: municipio_id recibido = {municipio_id}")  # DEBUG

    if not municipio_id:
        return JsonResponse({'programas': []})

    try:
        # Intentar con el ID del municipio
        programas = Programa.objects.filter(
            municipio_id=municipio_id,
            estado='activo'
        ).values('id', 'programa', 'contrato', 'fecha_inicial', 'fecha_final')

        programas_list = list(programas)
        print(f"DEBUG: Programas encontrados = {len(programas_list)}")  # DEBUG

        return JsonResponse({'programas': programas_list})

    except Exception as e:
        print(f"DEBUG: Error = {str(e)}")  # DEBUG
        return JsonResponse({'error': str(e), 'programas': []})
```

### Archivo: `static/js/nutricion/menus_avanzado.js`
```javascript
async function cargarProgramasPorMunicipio(municipioId) {
    console.log('DEBUG: Cargando programas para municipio:', municipioId);

    try {
        const url = `/nutricion/api/programas-por-municipio/?municipio_id=${municipioId}`;
        console.log('DEBUG: URL:', url);

        const response = await fetch(url);
        const data = await response.json();

        console.log('DEBUG: Respuesta:', data);

        const selectPrograma = document.getElementById('filtroPrograma');
        selectPrograma.innerHTML = '<option value="">Seleccione un programa...</option>';

        if (data.programas && data.programas.length > 0) {
            console.log('DEBUG: Programas encontrados:', data.programas.length);

            data.programas.forEach(programa => {
                const option = document.createElement('option');
                option.value = programa.id;
                option.textContent = `${programa.programa} (${programa.contrato})`;
                selectPrograma.appendChild(option);
            });
            selectPrograma.disabled = false;
        } else {
            console.log('DEBUG: No se encontraron programas');
            selectPrograma.innerHTML = '<option value="">No hay programas activos</option>';
            selectPrograma.disabled = true;
        }
    } catch (error) {
        console.error('DEBUG: Error al cargar programas:', error);
        alert('Error al cargar programas del municipio');
    }
}
```

---

## Checklist de Verificación

- [ ] Migración `0010_programa_municipio` aplicada
- [ ] Tabla `programa` tiene columna `id_municipio`
- [ ] Existe al menos un programa con `estado='activo'`
- [ ] El programa tiene un `municipio` asignado
- [ ] La URL `/nutricion/api/programas-por-municipio/` existe
- [ ] El API retorna datos cuando se prueba manualmente
- [ ] No hay errores en la consola del navegador (F12)
- [ ] El campo PK de municipio es `id_municipio` (no `id`)

---

## Comando de Diagnóstico Rápido

```bash
# Ejecutar este script de diagnóstico
cd erp_chvs
python manage.py shell <<EOF
from planeacion.models import Programa
from principal.models import PrincipalMunicipio

print("=== DIAGNÓSTICO ===")
print(f"Total municipios: {PrincipalMunicipio.objects.count()}")
print(f"Total programas: {Programa.objects.count()}")
print(f"Programas activos: {Programa.objects.filter(estado='activo').count()}")

print("\n=== PROGRAMAS POR MUNICIPIO ===")
for p in Programa.objects.filter(estado='activo'):
    try:
        print(f"ID: {p.id}, Programa: {p.programa}, Municipio: {p.municipio.nombre_municipio}, Estado: {p.estado}")
    except AttributeError:
        print(f"ID: {p.id}, Programa: {p.programa}, Municipio: SIN ASIGNAR (ERROR!), Estado: {p.estado}")
EOF
```

---

## Resultado Esperado

Después de aplicar el fix:

1. Seleccionar municipio → Se habilita select de programas
2. Select muestra: "PAE Prueba 2025 (CONT-TEST-001)"
3. Seleccionar programa → Se habilita botón "Cargar Modalidades"
4. Click en botón → Muestra acordeones de modalidades

---

**Ejecuta el diagnóstico y comparte el resultado para ayudarte mejor.**
