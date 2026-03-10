# Plan de Implementación — Match ICBF → Compras y Programación de Menús

## Contexto y objetivo

El módulo de **Nutrición** crea los menús usando ingredientes de la tabla ICBF 2018 (ej: "Leche cruda entera"). Sin embargo, el módulo de **Planeación** necesita trabajar con los ingredientes de **Compras/Inventario (Siesa)**, que tienen otro nombre comercial (ej: "Leche entera Bolsa 1000ml") y una presentación específica.

El **nutricionista** debe hacer el match (equivalencia) entre ambos catálogos **una sola vez por ingrediente por programa**. A partir de ahí, el sistema puede calcular automáticamente las necesidades de compra cuando planeación programa los menús por sede y fecha.

---

## Flujo completo del proceso

```
[Nutrición crea el menú]
TablaMenus → TablaPreparaciones → TablaPreparacionIngredientes (con gramajes ICBF)
                                                    │
                                         [Nutricionista hace match]
                                                    │
                                         EquivalenciaICBFCompras (NUEVA)
                                   (alimento ICBF + Programa → producto Siesa local)
                                                    │
                               [Planeación programa menús por sede y fecha]
                                                    │
                                         ProgramacionMenus (NUEVA)
                                   (sede + fecha + menú + raciones + programa)
                                                    │
                                     [Sistema calcula orden de compra]
                              raciones × gramaje ÷ factor_conversion = unidades
```

---

## Estrategia de catálogo Siesa (actualizado)

### Catálogo local — no llamadas en tiempo real

Los productos de Siesa **no se consultan en vivo** cada vez que el nutricionista hace un match. En cambio:

1. El módulo `Api/` (app Django ya creada para ese fin) descarga el catálogo de Siesa a tablas locales cuando se reciben los tokens y endpoints.
2. Un **cron job** mantiene esas tablas sincronizadas: solo se dispara cuando Siesa agrega o modifica un registro (delta, no polling completo).
3. El match se hace siempre contra la **tabla local**, sin depender de la disponibilidad de la API de Siesa en el momento.

### Simulacro con TablaIngredientesSiesa

Mientras llegan los tokens/endpoints de Siesa, el match se desarrolla y prueba usando `TablaIngredientesSiesa` (ya existente en `nutricion/models.py`) como catálogo de ejemplo. Cuando la integración real esté activa, solo se cambia la tabla fuente del selector — la lógica del match permanece igual.

---

## Estado actual de las tablas

### Tablas que YA EXISTEN y están completas

| App | Tabla (db_table) | Modelo Django | Descripción |
|---|---|---|---|
| nutricion | `nutricion_tabla_menus` | `TablaMenus` | Catálogo de menús (1 al 20) |
| nutricion | `nutricion_tabla_preparaciones` | `TablaPreparaciones` | Preparaciones por menú |
| nutricion | `nutricion_tabla_preparacion_ingredientes` | `TablaPreparacionIngredientes` | Ingredientes con gramaje (FK a ICBF) |
| nutricion | `nutricion_tabla_alimentos_2018_icb` | `TablaAlimentos2018Icbf` | Catálogo ICBF 2018 |
| planeacion | `sedes_educativas` | `SedesEducativas` | Catálogo de sedes |
| planeacion | `instituciones_educativas` | `InstitucionesEducativas` | Catálogo de instituciones |
| planeacion | `planificacion_raciones` | `PlanificacionRaciones` | Raciones por sede/nivel/año |
| planeacion | `programa_modalidades` | `ProgramaModalidades` | Modalidades por programa |
| logistica | `logistica_rutas` | `Ruta` | Rutas de entrega por programa ✅ |
| logistica | `logistica_ruta_sedes` | `RutaSedes` | Asignación de sedes a rutas ✅ |
| logistica | `logistica_tipos_rutas` | `TipoRuta` | Tipos de ruta ✅ |

> **Nota importante:** Las rutas de entrega ya están implementadas en el módulo `logistica` con CRUD completo. **No hay que crearlas en `planeacion`**. `ProgramacionMenus` hará FK a `logistica.Ruta`.

### Tablas que ya existen pero les faltan campos

#### `tabla_ingredientes_siesa` → Modelo `TablaIngredientesSiesa` (en `nutricion/models.py`)

Actualmente tiene:
- `id_ingrediente_siesa` — código del producto
- `nombre_ingrediente` — nombre comercial

**Campos que hay que agregar (para el simulacro y la versión real):**

```python
presentacion = models.CharField(
    max_length=100,
    blank=True, null=True,
    verbose_name="Presentación comercial",
    help_text="Ej: Bolsa 1000ml, Caja 500g, Bulto 50kg"
)
unidad_medida = models.CharField(
    max_length=50,
    blank=True, null=True,
    verbose_name="Unidad de medida",
    help_text="Ej: bolsa, caja, bulto, litro, unidad"
)
contenido_gramos = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    blank=True, null=True,
    verbose_name="Contenido en gramos",
    help_text="Cuántos gramos contiene una unidad. Ej: 1000 para Bolsa 1L"
)
```

---

## Tablas nuevas que hay que crear

### 1. `EquivalenciaICBFCompras` — en `nutricion/models.py`

**Propósito:** El nutricionista realiza aquí el match entre el nombre del alimento según la tabla ICBF y el producto real que se compra en el mercado, diferenciado por programa/contrato.

**Regla clave:** La clave única es `(id_alimento_icbf, id_programa)`. Esto permite que el mismo alimento ICBF tenga un producto de compras diferente según el programa.

> **Ejemplo:**
> - ICBF "Leche cruda" + Programa CALI-2025 → Siesa "Leche descremada 500g"
> - ICBF "Leche cruda" + Programa YUMBO-2025 → Siesa "Leche entera 500g"

```python
class EquivalenciaICBFCompras(models.Model):
    """
    Relaciona un ingrediente de la tabla ICBF con su equivalente
    en el catálogo de compras/inventario (Siesa), diferenciado por programa.
    El nutricionista realiza el match una vez por (alimento ICBF + programa).

    Durante el simulacro, id_ingrediente_compras apunta a TablaIngredientesSiesa.
    Cuando llegue la integración real con Siesa, se migrará a la tabla oficial
    descargada por el módulo Api/.
    """
    id_alimento_icbf = models.ForeignKey(
        TablaAlimentos2018Icbf,
        on_delete=models.CASCADE,
        related_name='equivalencias_compras',
        verbose_name="Alimento ICBF"
    )
    id_programa = models.ForeignKey(
        'planeacion.Programa',
        on_delete=models.CASCADE,
        related_name='equivalencias_icbf',
        verbose_name="Programa/Contrato"
    )
    id_ingrediente_compras = models.ForeignKey(
        TablaIngredientesSiesa,
        on_delete=models.PROTECT,
        related_name='equivalencias_icbf',
        verbose_name="Producto de Compras (Siesa)"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario = models.CharField(max_length=100, blank=True, null=True,
                               verbose_name="Usuario que realizó el match")

    class Meta:
        db_table = 'nutricion_equivalencia_icbf_compras'
        verbose_name = "Equivalencia ICBF → Compras"
        verbose_name_plural = "Equivalencias ICBF → Compras"
        unique_together = [['id_alimento_icbf', 'id_programa']]

    def __str__(self):
        return (f"{self.id_alimento_icbf.nombre_del_alimento} → "
                f"{self.id_ingrediente_compras.nombre_ingrediente} "
                f"[{self.id_programa.programa}]")
```

**Comportamiento al borrar:**

| Acción | Efecto |
|---|---|
| Borrar un ingrediente de una preparación del menú | ✅ **NO afecta el match.** El match permanece para uso futuro. |
| Borrar toda una preparación de un menú | ✅ **NO afecta el match.** Solo se borran los ingredientes de esa preparación. |
| Borrar un alimento del catálogo ICBF | ⚠️ Se borra el match (CASCADE). Rara vez ocurre. |
| Borrar un producto del catálogo Siesa | ❌ **Bloqueado (PROTECT)** si tiene matches activos. Hay que reasignar primero. |
| Borrar un Programa/Contrato | ⚠️ Se borran todos sus matches (CASCADE). |

---

### 2. `ProgramacionMenus` — en `planeacion/models.py`

**Propósito:** Registra qué menú se sirve en qué sede, en qué fecha y para cuántas raciones. Conecta planeación con nutrición y permite calcular las necesidades de compra.

**Nota sobre rutas:** El campo `id_ruta` referencia `logistica.Ruta` (ya implementado), no un modelo nuevo.

```python
class ProgramacionMenus(models.Model):
    """
    Asigna un menú específico a una sede educativa en una fecha determinada.
    Permite calcular automáticamente la cantidad de insumos a comprar.
    """
    from nutricion.models import TablaMenus

    fecha = models.DateField(verbose_name="Fecha de entrega")

    sede_educativa = models.ForeignKey(
        SedesEducativas,
        on_delete=models.PROTECT,
        verbose_name="Sede Educativa",
        related_name='programaciones_menu'
    )
    id_menu = models.ForeignKey(
        TablaMenus,
        on_delete=models.PROTECT,
        verbose_name="Menú asignado",
        related_name='programaciones'
    )
    id_programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        verbose_name="Programa/Contrato",
        related_name='programaciones_menu'
    )
    id_modalidad = models.ForeignKey(
        'principal.ModalidadesDeConsumo',
        on_delete=models.PROTECT,
        verbose_name="Modalidad de Consumo"
    )
    # FK a logistica.Ruta — módulo ya implementado con CRUD completo
    id_ruta = models.ForeignKey(
        'logistica.Ruta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programaciones',
        verbose_name="Ruta de entrega",
        help_text="Ruta por la que se entrega el menú a esta sede"
    )
    raciones = models.IntegerField(
        verbose_name="Número de raciones",
        help_text="Cantidad de raciones a servir ese día en esa sede"
    )

    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programado',
        verbose_name="Estado"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'planeacion_programacion_menus'
        verbose_name = "Programación de Menú"
        verbose_name_plural = "Programaciones de Menús"
        ordering = ['fecha', 'sede_educativa__nombre_sede_educativa']
        indexes = [
            models.Index(fields=['fecha', 'id_programa']),
            models.Index(fields=['sede_educativa']),
        ]

    def __str__(self):
        return f"{self.fecha} - {self.sede_educativa.nombre_sede_educativa} - Menú {self.id_menu.menu}"
```

---

## Lógica de cálculo de necesidades (services.py)

```python
def calcular_necesidades_compra(id_programa, fecha_inicio, fecha_fin):
    """
    Calcula la cantidad de productos Siesa a comprar para un programa
    en un rango de fechas, basándose en los menús programados.

    Fórmula:
        unidades = (raciones × gramaje_icbf) / contenido_gramos_siesa
    """
    programaciones = ProgramacionMenus.objects.filter(
        id_programa=id_programa,
        fecha__range=[fecha_inicio, fecha_fin],
        estado='programado'
    ).select_related('id_menu')

    resumen = {}  # {id_ingrediente_siesa: total_unidades}

    for prog in programaciones:
        ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion__id_menu=prog.id_menu
        ).select_related('id_ingrediente_siesa')

        for ing in ingredientes:
            try:
                equivalencia = EquivalenciaICBFCompras.objects.get(
                    id_alimento_icbf=ing.id_ingrediente_siesa,
                    id_programa=id_programa,
                    activo=True
                )
            except EquivalenciaICBFCompras.DoesNotExist:
                continue  # Ingrediente sin match — registrar alerta

            producto = equivalencia.id_ingrediente_compras
            total_gramos = prog.raciones * ing.gramaje
            unidades = total_gramos / producto.contenido_gramos

            clave = producto.id_ingrediente_siesa
            resumen[clave] = resumen.get(clave, {
                'nombre': producto.nombre_ingrediente,
                'presentacion': producto.presentacion,
                'total_unidades': 0
            })
            resumen[clave]['total_unidades'] += unidades

    return resumen
```

---

## Rutas de entrega (ya implementadas en `logistica`)

> **Las rutas NO se crean aquí.** El módulo `logistica` ya implementa con CRUD completo:
>
> - `TipoRuta` (`logistica_tipos_rutas`)
> - `Ruta` (`logistica_rutas`) — con FK a Programa, estado activo/inactivo
> - `RutaSedes` (`logistica_ruta_sedes`) — sede + orden de visita
>
> `ProgramacionMenus` referencia `logistica.Ruta` directamente.

---

## Diagrama completo de relaciones

```
Programa (planeacion)
  ├─── FK ──► logistica.Ruta ◄── logistica.RutaSedes ── FK ──► SedesEducativas
  │
  ├─── FK ──► ProgramacionMenus ──── FK ──► TablaMenus (nutricion)
  │           ├─ FK (sede)                        │
  │           ├─ FK (ruta → logistica.Ruta)        └──► TablaPreparaciones
  │           │                                               │
  │           ▼                                               └──► TablaPreparacionIngredientes
  │     SedesEducativas                                                 │ FK (alimento ICBF)
  │                                                                     ▼
  │                                                        TablaAlimentos2018Icbf
  │                                                                     │
  └─── FK ──► EquivalenciaICBFCompras ◄──── unique_together ───────────┘
                      │ FK (PROTECT)
                      ▼
             TablaIngredientesSiesa  ← simulacro actual
             (en el futuro: tabla local descargada por Api/ desde Siesa)
                      │
                      ▼
             RESULTADO: Orden de Compra (agrupada por ruta)
```

---

## Integración con módulo Api/ y estrategia de sincronización Siesa

El módulo `Api/` (app Django ya existente, creada para este fin) será el puente con SIESA ERP:

```
[Siesa ERP SAAS]
      │
      │  tokens + endpoints (pendiente de recibir)
      ▼
  Api/ (módulo Django)
      │
      ├─► Descarga inicial: catálogos completos → tablas locales
      │     - Plan de Cuentas → tabla local de artículos Siesa
      │     - Proyectos (sedes) → tabla local de sedes Siesa
      │     - Bodegas, Centros de Costo, etc.
      │
      └─► Cron job de sincronización delta
            - Se dispara solo cuando Siesa agrega/modifica un registro
            - No hace polling continuo
            - Actualiza la tabla local afectada
```

**Ventaja:** El match y los cálculos de compra funcionan siempre contra tablas locales de PostgreSQL, sin depender de la disponibilidad de la API de Siesa en tiempo real.

**Migración del simulacro a producción:** Cuando `Api/` esté activo y las tablas locales de Siesa estén pobladas, `EquivalenciaICBFCompras.id_ingrediente_compras` migrará de `TablaIngredientesSiesa` a la tabla oficial descargada. La UI del match no cambia.

---

## Plan de implementación (orden actualizado)

### Fase 1 — Simulacro del match (completada)

| # | Acción | Archivo | Estado |
|---|---|---|---|
| 1 | Agregar `presentacion`, `unidad_medida`, `contenido_gramos` a `TablaIngredientesSiesa` | `nutricion/models.py` | ✅ Completado |
| 2 | Migración de los campos nuevos | `nutricion/migrations/0038_*` | ✅ Completado |
| 3 | Crear modelo `EquivalenciaICBFCompras` | `nutricion/models.py` | ✅ Completado |
| 4 | Migración del nuevo modelo | `nutricion/migrations/0038_*` | ✅ Completado |
| 5 | CRUD básico de catálogo Siesa (carga manual de productos) | `nutricion/views/match_icbf.py` | ✅ Completado |
| 6 | Vista del match: lista ICBF ↔ selector Siesa + semáforo | `nutricion/views/match_icbf.py` | ✅ Completado (1:1) |

### Fase 1.5 — Refactor: match 1 a N (implementar ahora)

> **Origen:** La nutricionista confirmó que un mismo ingrediente ICBF puede comprarse en varias presentaciones comerciales dentro de un mismo programa. La vista actual (1 ingrediente → 1 producto) no lo soporta.

**Decisión tomada: Opción A** — múltiples matches por ingrediente (ver sección "Decisión" más abajo). Ya no está pendiente.

#### Cambios de modelo

```python
# nutricion/models.py — EquivalenciaICBFCompras

# ANTES  (constraint 1:1 por programa)
unique_together = [['id_alimento_icbf', 'id_programa']]

# AHORA  (constraint 1:N — mismo ingrediente puede tener varios productos Siesa)
unique_together = [['id_alimento_icbf', 'id_programa', 'id_ingrediente_compras']]

# Campo nuevo para orden de compra base
es_principal = models.BooleanField(
    default=False,
    verbose_name="Producto principal",
    help_text="Marca el producto preferido cuando hay varios matches. "
              "El cálculo de orden de compra lo usa por defecto."
)
```

> **Regla de negocio:** Solo puede haber un `es_principal=True` por `(id_alimento_icbf, id_programa)`. El servicio de cálculo de compra usa el match principal; la orden muestra todos los disponibles.

#### Cambios de vista y API

| Elemento | Antes | Ahora |
|---|---|---|
| `_obtener_ingredientes_programa` | Lista de alimentos ICBF | Idem + anota en qué menús/preparaciones aparece cada uno |
| `vista_match_icbf` context | `filas[]{alimento, match, tiene_match}` | `filas[]{alimento, usos[], matches[]}` |
| Template | Tabla plana, 1 fila = 1 match | Tarjetas por ingrediente con sublistado de contexto y chips de matches |
| `api_guardar_match` | `update_or_create` (reemplaza) | `get_or_create` por trío (icbf, programa, siesa) — agrega sin borrar los anteriores |
| `api_eliminar_match` | Recibe `codigo_icbf` + `programa_id` | Recibe `match_id` (PK de `EquivalenciaICBFCompras`) |
| Semáforo | Verde si tiene 1 match | Verde si tiene ≥1 match; contador muestra cuántos tiene |

#### Rediseño de la vista — Tarjeta por ingrediente

La vista pasa de tabla plana a **tarjetas expandibles**. Cada tarjeta representa un alimento ICBF y muestra:

1. **Cabecera:** nombre del alimento, grupo nutricional, semáforo (verde/rojo) y badge con cantidad de matches (`2 productos`).
2. **Contexto de uso:** lista de los menús y preparaciones donde aparece ese alimento, para que la nutricionista entienda *por qué* necesita múltiples productos.
3. **Matches asignados:** chips/pills con el nombre del producto Siesa, presentación y botón ✗ para quitar. El producto marcado como principal lleva un ★.
4. **Acción:** botón `+ Agregar producto` que abre el modal de búsqueda (Select2) y añade un nuevo match sin borrar los existentes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ●  ACEITE DE PALMA  [G1 - Grasas]                       2 productos  ▼    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Usado en:                                                                  │
│    • Menú 3 › Preparación: Arroz con pollo guisado                         │
│    • Menú 7 › Preparación: Guiso de verduras                               │
│    • Menú 12 › Preparación: Avena con leche                                │
│                                                                             │
│  Productos asignados:                                                       │
│    ★ [ Aceite de palma — Botella 1L (1000 g)       ]  [✗ Quitar]          │
│      [ Aceite de palma — Bidón 3L  (2760 g)        ]  [✗ Quitar]          │
│                                                                             │
│    [+ Agregar producto]                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ●  LECHE CRUDA ENTERA  [G2 - Lácteos]                   1 producto   ▼   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Usado en:                                                                  │
│    • Menú 2 › Preparación: Avena                                           │
│    • Menú 5 › Preparación: Colada de maíz                                  │
│                                                                             │
│  Productos asignados:                                                       │
│    ★ [ Leche entera — Bolsa 1000ml (1000 g)        ]  [✗ Quitar]          │
│                                                                             │
│    [+ Agregar producto]                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ○  HUEVO DE GALLINA  [G3 - Proteínas]                   Sin match   ▼    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Usado en:                                                                  │
│    • Menú 1 › Preparación: Huevo revuelto                                  │
│                                                                             │
│  Productos asignados:                                                       │
│    (ninguno)                                                                │
│                                                                             │
│    [+ Agregar producto]                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Pasos de implementación

| # | Acción | Archivo | Estado |
|---|---|---|---|
| F1.5-1 | Agregar `es_principal` a `EquivalenciaICBFCompras` y cambiar `unique_together` | `nutricion/models.py` | Pendiente |
| F1.5-2 | Migración | Django migrations | Pendiente |
| F1.5-3 | Actualizar `_obtener_ingredientes_programa` para incluir contexto de usos (menús/preps) | `nutricion/views/match_icbf.py` | Pendiente |
| F1.5-4 | Actualizar context en `vista_match_icbf`: `matches` pasa a ser lista | `nutricion/views/match_icbf.py` | Pendiente |
| F1.5-5 | Rediseñar template: tabla → tarjetas por ingrediente | `templates/nutricion/match_icbf.html` | Pendiente |
| F1.5-6 | Actualizar `api_guardar_match`: `get_or_create` en vez de `update_or_create` | `nutricion/views/match_icbf.py` | Pendiente |
| F1.5-7 | Actualizar `api_eliminar_match`: recibir `match_id` (PK) | `nutricion/views/match_icbf.py` | Pendiente |
| F1.5-8 | Actualizar JS: modal agrega match sin reemplazar; quitar usa `match_id` | `static/js/nutricion/match_icbf.js` | Pendiente |
| F1.5-9 | Actualizar CSS: estilos de tarjeta, chips de productos, badge contador | `static/css/nutricion/match_icbf.css` | Pendiente |

### Fase 2 — Programación de menús por sede y fecha

| # | Acción | Archivo | Estado |
|---|---|---|---|
| 7 | Crear modelo `ProgramacionMenus` (con FK a `logistica.Ruta`) | `planeacion/models.py` | Pendiente |
| 8 | Migración | Django migrations | Pendiente |
| 9 | Vista de programación de menús por sede y fecha | `planeacion/views.py` | Pendiente |
| 10 | Servicio de cálculo de necesidades de compra | `planeacion/services.py` | Pendiente |
| 11 | Reporte de orden de compra (PDF/Excel) | `planeacion/` | Pendiente |

### Fase 3 — Integración real con Siesa via Api/

| # | Acción | Archivo | Estado |
|---|---|---|---|
| 12 | Recibir tokens y endpoints de Siesa | `Api/` | Bloqueado (esperando Siesa) |
| 13 | Modelos de tablas locales Siesa (Plan de Cuentas, Proyectos, etc.) | `Api/models.py` | Pendiente |
| 14 | Conector SC — descarga y sincronización | `Api/` | Pendiente |
| 15 | Conector RQI — descarga y sincronización | `Api/` | Pendiente |
| 16 | Cron job de sincronización delta | `Api/` | Pendiente |
| 17 | Migrar `EquivalenciaICBFCompras` a tabla oficial Siesa | `nutricion/models.py` | Pendiente |
| 18 | Generación automática de SC/RQI desde orden de compra | `Api/` + `planeacion/` | Pendiente |

---

## Decisión — Manejo de múltiples productos por ingrediente

> **✅ RESUELTA (2026-03-10):** La nutricionista confirmó que un mismo ingrediente ICBF puede comprarse en varios productos dentro de un mismo programa (distinta presentación, marca o tamaño). Se adopta **Opción A**.

> **Contexto original:** Planeación señaló que un mismo ingrediente ICBF puede comprarse en varias presentaciones comerciales. Ejemplo: "Aceite de Palma" puede adquirirse en Botella 1000cc (920g) o Bidón 3000cc (2760g). El comprador elige el mix según precio y disponibilidad.
>
> **La decisión ya no depende de la estructura de Siesa** — el requisito viene del flujo operativo confirmado por la nutricionista.

### ✅ Opción A — Múltiples matches por ingrediente (ELEGIDA)

Eliminar el `unique_together = [['id_alimento_icbf', 'id_programa']]` y reemplazarlo por `unique_together = [['id_alimento_icbf', 'id_programa', 'id_ingrediente_compras']]`. Se agrega un campo `es_principal` para marcar la presentación preferida.

La nutricionista puede vincular el mismo ingrediente ICBF a varias presentaciones Siesa. El cálculo base usa la presentación marcada como principal; la orden de compra muestra todas las disponibles.

**Razón de la elección:** La nutricionista confirmó el requisito directamente. No depende de la estructura del catálogo Siesa.

### Opción B — Producto base + presentaciones como variantes (más correcta conceptualmente)

Reestructurar el catálogo local en dos tablas:

```
ProductoSiesa  (familia de producto — "Aceite de Palma")
    └─► PresentacionProductoSiesa  (variantes — "Botella 1000cc", "Bidón 3000cc")
```

El match del nutricionista apunta a `ProductoSiesa` (sin comprometerse con una presentación). El cálculo de compra trabaja en **gramos totales** y la orden de compra tiene una capa separada donde el comprador decide cuántas unidades de cada presentación usar para cubrir esos gramos.

```python
# Cambio en EquivalenciaICBFCompras:
id_producto = FK(ProductoSiesa)   # ← producto base, NO una presentación específica

# Nuevo modelo en planeacion:
class OrdenCompraDetalle(models.Model):
    orden_compra  = FK(OrdenCompra)
    presentacion  = FK(PresentacionProductoSiesa)
    cantidad      = IntegerField()   # unidades de ESA presentación
    # gramos cubiertos = cantidad × presentacion.contenido_gramos
```

**Cuándo elegirla:** Si Siesa agrupa variantes bajo un mismo código de artículo padre, o si se confirma que el comprador siempre debe poder mezclar presentaciones en una misma orden.

### Comparación rápida

| Criterio | Opción A | Opción B |
|---|---|---|
| Cambio al modelo `EquivalenciaICBFCompras` | Mínimo | Moderado (FK cambia de target) |
| Tablas nuevas requeridas | Ninguna | `ProductoSiesa` + `PresentacionProductoSiesa` |
| ¿Quién decide el mix de presentaciones? | Nutricionista al hacer el match | Comprador en la orden de compra |
| Separación de responsabilidades | Parcial | Clara |
| Depende de estructura Siesa | No | Sí (si Siesa tiene jerarquía artículo-variante) |

> **Acción:** Verificar la estructura del catálogo Siesa cuando lleguen los tokens. Si cada presentación tiene código propio → Opción A. Si hay jerarquía artículo-variante → Opción B. El simulacro actual con `TablaIngredientesSiesa` implementa Opción A por defecto.

---

## Notas importantes

- **Rutas ya implementadas:** `logistica.Ruta` y `logistica.RutaSedes` tienen CRUD completo. No duplicar en `planeacion`.
- **El match es permanente:** Borrar un ingrediente de un menú NO borra el match ICBF→Compras.
- **Simulacro primero:** La UI del match se construye con `TablaIngredientesSiesa`. La migración a Siesa real solo cambia la FK y la fuente del selector.
- **Cron job, no polling:** La sincronización con Siesa es reactiva (delta), no un ciclo constante.
- **Un menú NO se asocia a un programa directamente:** Ya tiene `id_contrato` (FK a `Programa`), el programa está implícito.
- **Match 1:N confirmado:** Se adoptó Opción A. El mismo ingrediente ICBF puede tener múltiples productos Siesa por programa. El campo `es_principal` marca el producto preferido para la orden de compra base.
- **Vista rediseñada:** La tabla plana se reemplaza por tarjetas por ingrediente que muestran el contexto (menús y preparaciones donde aparece) y la lista de matches asignados.
