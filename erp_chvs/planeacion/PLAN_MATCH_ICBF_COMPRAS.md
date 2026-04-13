# Plan de Implementación — Match ICBF → Compras y Programación de Menús

## Contexto y objetivo

El módulo de **Nutrición** crea los menús usando ingredientes de la tabla ICBF 2018 (ej: "Leche cruda entera"). Sin embargo, el módulo de **Planeación** necesita trabajar con los ingredientes de **Compras/Inventario (Siesa)**, que tienen otro nombre comercial (ej: "Leche entera Bolsa 1000ml") y una presentación específica.

El **nutricionista** hace el match (equivalencia) entre ambos catálogos. A partir de ahí, el sistema puede calcular automáticamente las necesidades de compra cuando planeación programa los menús por sede y fecha.

---

## Flujo completo del proceso

```
[Nutrición crea el menú]
TablaMenus → TablaPreparaciones → TablaPreparacionIngredientes (con gramajes ICBF)
                                                    │
                                         [Nutricionista hace match]
                                                    │
                                         EquivalenciaICBFCompras ✅ IMPLEMENTADO
                                   (alimento ICBF + Programa + Menú → producto Siesa local)
                                                    │
                               [Planeación programa menús por sede y fecha]
                                                    │
                                         ProgramacionMenus ← PENDIENTE
                                   (sede + fecha + menú + raciones + programa)
                                                    │
                                     [Sistema calcula orden de compra]
                              raciones × gramaje ÷ factor_conversion = unidades
```

---

## Granularidad del match (decisión implementada)

La granularidad adoptada en código es:

```
(id_alimento_icbf, id_programa, id_menu) → 1 producto de compras
```

**Esto significa:** el mismo ingrediente ICBF puede tener un producto de compras diferente en cada menú dentro del mismo programa. Ejemplo:
- Menú 3 → "Aceite de Palma" → Botella 1L
- Menú 7 → "Aceite de Palma" → Bidón 3L

**Flujo de asignación (dos modos):**
- **Masivo** (`api_guardar_match_bulk`): asigna el mismo producto a todos los menús del programa donde aparece el ingrediente. Parámetro `solo_sin_asignar=true` para no sobreescribir los que ya tienen.
- **Override individual** (`api_guardar_match`): cambia el producto de un menú específico sin afectar los demás.

> **Nota:** La propuesta original de Opción A / Opción B con campo `es_principal` fue descartada. La granularidad por menú resuelve el problema de múltiples presentaciones de forma más natural.

---

## Estado actual de las tablas

### Tablas completas ✅

| App | Tabla (db_table) | Modelo Django | Estado |
|---|---|---|---|
| nutricion | `nutricion_tabla_menus` | `TablaMenus` | ✅ Completo |
| nutricion | `nutricion_tabla_preparaciones` | `TablaPreparaciones` | ✅ Completo |
| nutricion | `nutricion_tabla_preparacion_ingredientes` | `TablaPreparacionIngredientes` | ✅ Completo |
| nutricion | `nutricion_tabla_alimentos_2018_icb` | `TablaAlimentos2018Icbf` | ✅ Completo |
| nutricion | `tabla_ingredientes_siesa` | `TablaIngredientesSiesa` | ✅ Completo (con presentacion, unidad_medida, contenido_gramos) |
| nutricion | `nutricion_equivalencia_icbf_compras` | `EquivalenciaICBFCompras` | ✅ Completo |
| planeacion | `sedes_educativas` | `SedesEducativas` | ✅ Completo |
| planeacion | `instituciones_educativas` | `InstitucionesEducativas` | ✅ Completo |
| planeacion | `planificacion_raciones` | `PlanificacionRaciones` | ✅ Completo |
| planeacion | `programa_modalidades` | `ProgramaModalidades` | ✅ Completo |
| logistica | `logistica_rutas` | `Ruta` | ✅ Completo (CRUD completo) |
| logistica | `logistica_ruta_sedes` | `RutaSedes` | ✅ Completo |
| logistica | `logistica_tipos_rutas` | `TipoRuta` | ✅ Completo |

### Tablas pendientes ❌

| App | Tabla | Modelo | Estado |
|---|---|---|---|
| planeacion | `planeacion_programacion_menus` | `ProgramacionMenus` | ❌ No creado |

---

## Modelo `TablaIngredientesSiesa` (simulacro del catálogo Siesa)

```python
# nutricion/models.py — IMPLEMENTADO ✅
class TablaIngredientesSiesa(models.Model):
    id_ingrediente_siesa = models.CharField(max_length=50, primary_key=True)
    nombre_ingrediente   = models.CharField(max_length=255)
    presentacion         = models.CharField(max_length=100, blank=True, null=True)
    unidad_medida        = models.CharField(max_length=50, blank=True, null=True)
    contenido_gramos     = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
```

> **SIMULACRO:** Se usa como catálogo de ejemplo mientras llegan los tokens de Siesa. Cuando `Api/` esté activo, el campo `EquivalenciaICBFCompras.id_ingrediente_compras` migrará de `TablaIngredientesSiesa` a la tabla oficial descargada (`SiesaArticulo`). La UI del match no cambia.

---

## Modelo `EquivalenciaICBFCompras` (implementado)

```python
# nutricion/models.py — IMPLEMENTADO ✅
class EquivalenciaICBFCompras(models.Model):
    id_alimento_icbf     = FK(TablaAlimentos2018Icbf, CASCADE)
    id_programa          = FK(planeacion.Programa, CASCADE)
    id_menu              = FK(TablaMenus, CASCADE)
    id_ingrediente_compras = FK(TablaIngredientesSiesa, PROTECT)
    activo               = BooleanField(default=True)
    fecha_actualizacion  = DateTimeField(auto_now=True)
    usuario              = CharField(max_length=100, nullable)

    unique_together = [['id_alimento_icbf', 'id_programa', 'id_menu']]
    db_table = 'nutricion_equivalencia_icbf_compras'
```

**Comportamiento al borrar:**

| Acción | Efecto |
|---|---|
| Borrar un ingrediente de una preparación | ✅ NO afecta el match |
| Borrar una preparación completa | ✅ NO afecta el match |
| Borrar un alimento del catálogo ICBF | ⚠️ Se borra el match (CASCADE) |
| Borrar un producto del catálogo Siesa | ❌ Bloqueado (PROTECT) si tiene matches activos |
| Borrar un Programa/Contrato | ⚠️ Se borran todos sus matches (CASCADE) |
| Borrar un Menú | ⚠️ Se borran sus matches (CASCADE) |

---

## Módulo de match — Archivos implementados ✅

```
nutricion/views/match_icbf.py          — 5 endpoints
nutricion/services/match_icbf_service.py — lógica del dashboard
templates/nutricion/match_icbf.html    — UI
static/js/nutricion/match_icbf.js      — JS manager
```

### Endpoints activos

| Método | URL | Función |
|---|---|---|
| GET | `/nutricion/match-icbf/` | Dashboard principal (filtros por municipio/programa) |
| GET | `/nutricion/api/match/productos/` | Búsqueda de productos Siesa (búsqueda `?q=`) |
| POST | `/nutricion/api/match/guardar/` | Guardar match individual (alimento + programa + menú) |
| POST | `/nutricion/api/match/guardar/bulk/` | Asignación masiva a todos los menús del ingrediente |
| DELETE | `/nutricion/api/match/<match_id>/` | Eliminar match por PK |
| GET/POST | `/nutricion/api/match/productos-siesa/` | CRUD catálogo Siesa (simulacro) |
| GET/PUT/DELETE | `/nutricion/api/match/productos-siesa/<codigo>/` | Detalle/editar/eliminar producto Siesa |

### Lógica del servicio (`obtener_dashboard_match`)

Devuelve por programa:
- Lista de ingredientes ICBF usados, agrupados por alimento
- Por cada alimento: lista de menús donde aparece con sus preparaciones
- Por cada (alimento, menú): el match asignado si existe
- Contadores: `total`, `con_match` (todos los menús asignados), `sin_match`

---

## Modelo `ProgramacionMenus` — PENDIENTE ❌

Conecta planeación con nutrición. Registra qué menú se sirve en qué sede, en qué fecha y para cuántas raciones.

```python
# planeacion/models.py — AÚN NO CREADO
class ProgramacionMenus(models.Model):
    fecha            = DateField()
    sede_educativa   = FK(SedesEducativas, PROTECT)
    id_menu          = FK(nutricion.TablaMenus, PROTECT)
    id_programa      = FK(Programa, PROTECT)
    id_modalidad     = FK(principal.ModalidadesDeConsumo, PROTECT)
    id_ruta          = FK(logistica.Ruta, SET_NULL, nullable)  # rutas ya implementadas
    raciones         = IntegerField()
    estado           = CharField(choices=[programado, entregado, cancelado])
    fecha_creacion   = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)

    db_table = 'planeacion_programacion_menus'
    indexes  = [(fecha, id_programa), (sede_educativa,)]
```

---

## Lógica de cálculo de necesidades (pendiente)

```python
# planeacion/services.py — AÚN NO IMPLEMENTADO
def calcular_necesidades_compra(id_programa, fecha_inicio, fecha_fin):
    """
    Fórmula: unidades = (raciones × gramaje_icbf) / contenido_gramos_siesa
    Usa el match por menú: busca EquivalenciaICBFCompras filtrando por
    (id_alimento_icbf, id_programa, id_menu) para cada programación.
    """
```

---

## Diagrama completo de relaciones

```
Programa (planeacion)
  ├─── FK ──► logistica.Ruta ◄── logistica.RutaSedes ── FK ──► SedesEducativas
  │
  ├─── FK ──► ProgramacionMenus [PENDIENTE] ──── FK ──► TablaMenus (nutricion)
  │           ├─ FK (sede)                              │
  │           ├─ FK (ruta → logistica.Ruta)              └──► TablaPreparaciones
  │           │                                                      │
  │           ▼                                                      └──► TablaPreparacionIngredientes
  │     SedesEducativas                                                        │ FK (alimento ICBF)
  │                                                                            ▼
  │                                                             TablaAlimentos2018Icbf
  │                                                                            │
  └─── FK ──► EquivalenciaICBFCompras ✅ ◄── unique(alimento, programa, menú) ┘
                      │ FK (PROTECT)
                      ▼
             TablaIngredientesSiesa (simulacro)
             → En producción: SiesaArticulo (descargado por Api/)
                      │
                      ▼
             RESULTADO: Orden de Compra (agrupada por ruta)
```

---

## Plan de implementación — Estado actualizado

### Fase 1 — Simulacro del match ✅ COMPLETA

| # | Acción | Archivo | Estado |
|---|---|---|---|
| 1 | Agregar `presentacion`, `unidad_medida`, `contenido_gramos` a `TablaIngredientesSiesa` | `nutricion/models.py` | ✅ |
| 2 | Migración campos nuevos | `nutricion/migrations/` | ✅ |
| 3 | Crear modelo `EquivalenciaICBFCompras` con granularidad por menú | `nutricion/models.py` | ✅ |
| 4 | Migración del nuevo modelo | `nutricion/migrations/` | ✅ |
| 5 | CRUD catálogo Siesa simulacro | `nutricion/views/match_icbf.py` | ✅ |
| 6 | Dashboard match con tarjetas por ingrediente y tabla de menús | `nutricion/views/match_icbf.py` | ✅ |
| 7 | Asignación masiva (`bulk`) y override individual | `nutricion/views/match_icbf.py` | ✅ |
| 8 | Servicio `obtener_dashboard_match` | `nutricion/services/match_icbf_service.py` | ✅ |

### Fase 2 — Programación de menús por sede y fecha ❌ PENDIENTE

| # | Acción | Archivo | Estado |
|---|---|---|---|
| 9 | Crear modelo `ProgramacionMenus` (con FK a `logistica.Ruta`) | `planeacion/models.py` | ❌ |
| 10 | Migración | Django migrations | ❌ |
| 11 | Vista de programación de menús por sede y fecha (calendario) | `planeacion/views.py` | ❌ |
| 12 | Servicio `calcular_necesidades_compra` | `planeacion/services.py` | ❌ |
| 13 | Reporte de orden de compra (PDF/Excel) | `planeacion/` | ❌ |

### Fase 3 — Integración real con Siesa via Api/ ❌ BLOQUEADA

| # | Acción | Archivo | Estado |
|---|---|---|---|
| 14 | Recibir tokens y endpoints de Siesa | `Api/` | ❌ Bloqueado — esperando Siesa |
| 15 | Modelos tablas locales Siesa (`SiesaArticulo`, `SiesaBodega`, etc.) | `Api/models.py` | ❌ |
| 16 | Conector SC — descarga y sincronización | `Api/` | ❌ |
| 17 | Conector RQI — descarga y sincronización | `Api/` | ❌ |
| 18 | Cron job de sincronización delta | `Api/` | ❌ |
| 19 | Migrar FK `id_ingrediente_compras` de `TablaIngredientesSiesa` → `SiesaArticulo` | `nutricion/models.py` | ❌ |
| 20 | Generación automática de SC/RQI desde orden de compra | `Api/` + `planeacion/` | ❌ |

---

## Estrategia de catálogo Siesa

Los productos de Siesa **no se consultan en vivo**. El módulo `Api/` descarga el catálogo a tablas locales PostgreSQL. Un cron job delta mantiene la sincronización. El match siempre opera contra la tabla local.

**Migración del simulacro a producción:** cuando `Api/` esté activo, solo se cambia la FK de `EquivalenciaICBFCompras.id_ingrediente_compras`. La UI del match, el servicio y los endpoints no cambian.

---

## Notas importantes

- **Rutas ya implementadas:** `logistica.Ruta` y `logistica.RutaSedes` tienen CRUD completo. No duplicar en `planeacion`.
- **El match sobrevive a cambios de menú:** borrar un ingrediente de una preparación NO borra el match ICBF→Compras.
- **Granularidad por menú:** el mismo ingrediente puede tener producto diferente en cada menú. La asignación masiva es el flujo normal; el override individual es la excepción.
- **Cron job, no polling:** la sincronización con Siesa será reactiva (delta), no un ciclo constante.
- **`Api/` es un stub vacío** — `models.py` y `views.py` vacíos, sin migraciones, no está en `INSTALLED_APPS`. Se activa cuando lleguen los tokens de Siesa.
