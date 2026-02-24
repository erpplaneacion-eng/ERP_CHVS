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
                                   (alimento ICBF + Programa → producto Siesa)
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

### Tablas que ya existen pero les faltan campos

#### `tabla_ingredientes_siesa` → Modelo `TablaIngredientesSiesa` (en `nutricion/models.py`)

Actualmente tiene:
- `id_ingrediente_siesa` — código del producto
- `nombre_ingrediente` — nombre comercial

**Campos que hay que agregar:**

```python
presentacion = models.CharField(
    max_length=100,
    verbose_name="Presentación comercial",
    help_text="Ej: Bolsa 1000ml, Caja 500g, Bulto 50kg"
)
unidad_medida = models.CharField(
    max_length=50,
    verbose_name="Unidad de medida",
    help_text="Ej: bolsa, caja, bulto, litro, unidad"
)
contenido_gramos = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    verbose_name="Contenido en gramos",
    help_text="Cuántos gramos contiene una unidad de esta presentación. Ej: 1000 para Bolsa 1L"
)
```

---

## Tablas nuevas que hay que crear

### 1. `EquivalenciaICBFCompras` — en `nutricion/models.py`

**Propósito:** El nutricionista realiza aquí el match entre el nombre del alimento según la tabla ICBF y el producto real que se compra en el mercado, diferenciado por programa/contrato.

**Regla clave:** La clave única es `(id_alimento_icbf, id_programa)`. Esto permite que el mismo alimento ICBF tenga un producto de compras diferente según el programa, ya que los términos legales de los contratos pueden variar por municipio.

> **Ejemplo:**
> - ICBF "Leche cruda" + Programa CALI-2025 → Siesa "Leche descremada 500g"
> - ICBF "Leche cruda" + Programa YUMBO-2025 → Siesa "Leche entera 500g"

```python
class EquivalenciaICBFCompras(models.Model):
    """
    Relaciona un ingrediente de la tabla ICBF con su equivalente
    en el catálogo de compras/inventario (Siesa), diferenciado por programa.
    El nutricionista realiza el match una vez por (alimento ICBF + programa).
    """
    id_alimento_icbf = models.ForeignKey(
        TablaAlimentos2018Icbf,
        on_delete=models.CASCADE,   # Si se borra el alimento ICBF, se borra el match
        related_name='equivalencias_compras',
        verbose_name="Alimento ICBF"
    )
    id_programa = models.ForeignKey(
        'planeacion.Programa',
        on_delete=models.CASCADE,   # Si se borra el programa, se borran sus matches
        related_name='equivalencias_icbf',
        verbose_name="Programa/Contrato"
    )
    id_ingrediente_compras = models.ForeignKey(
        TablaIngredientesSiesa,
        on_delete=models.PROTECT,   # No permite borrar un producto Siesa si tiene matches activos
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
        # Un alimento ICBF solo tiene UN producto Siesa por programa
        unique_together = [['id_alimento_icbf', 'id_programa']]

    def __str__(self):
        return (f"{self.id_alimento_icbf.nombre_del_alimento} → "
                f"{self.id_ingrediente_compras.nombre_ingrediente} "
                f"[{self.id_programa.programa}]")
```

**Comportamiento al borrar:**

| Acción | Efecto |
|---|---|
| Borrar un ingrediente de una preparación del menú | ✅ **NO afecta el match.** El match permanece intacto para uso futuro. |
| Borrar toda una preparación de un menú | ✅ **NO afecta el match.** Solo se borran los ingredientes de esa preparación (CASCADE interno). |
| Borrar un alimento del catálogo ICBF | ⚠️ Se borra el match (CASCADE). Rara vez ocurre. |
| Borrar un producto del catálogo Siesa | ❌ **Bloqueado (PROTECT)** si tiene matches activos. Hay que reasignar primero. |
| Borrar un Programa/Contrato | ⚠️ Se borran todos sus matches (CASCADE). |

---

### 2. `ProgramacionMenus` — en `planeacion/models.py`

**Propósito:** Registra qué menú se sirve en qué sede, en qué fecha y para cuántas raciones. Es el eslabón que conecta planeación con nutrición y permite calcular las necesidades de compra.

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

> **Nota:** El campo `id_ruta` se agregará a este modelo cuando las rutas estén implementadas (ver sección de Rutas más abajo).

---

## Lógica de cálculo de necesidades (services.py)

Cuando planeación necesite calcular insumos para un rango de fechas:

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
        # Obtener todos los ingredientes del menú programado
        ingredientes = TablaPreparacionIngredientes.objects.filter(
            id_preparacion__id_menu=prog.id_menu
        ).select_related('id_ingrediente_siesa')

        for ing in ingredientes:
            # Buscar el match para este programa
            try:
                equivalencia = EquivalenciaICBFCompras.objects.get(
                    id_alimento_icbf=ing.id_ingrediente_siesa,
                    id_programa=id_programa,
                    activo=True
                )
            except EquivalenciaICBFCompras.DoesNotExist:
                # Ingrediente sin match configurado — registrar alerta
                continue

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

## Rutas de entrega (PENDIENTE — tablas nuevas)

Una ruta agrupa un conjunto de sedes educativas que son atendidas por el mismo vehículo/transportador en una misma jornada de entrega. Las rutas pertenecen a un programa/contrato.

### 3. `Ruta` — en `planeacion/models.py`

```python
class Ruta(models.Model):
    """
    Define una ruta de entrega de alimentos para un programa.
    Una ruta agrupa varias sedes que reciben el menú en el mismo recorrido.
    """
    nombre_ruta = models.CharField(max_length=100, verbose_name="Nombre de la Ruta")
    id_programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name='rutas',
        verbose_name="Programa/Contrato"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'planeacion_rutas'
        verbose_name = "Ruta de Entrega"
        verbose_name_plural = "Rutas de Entrega"
        ordering = ['id_programa', 'nombre_ruta']
        unique_together = [['nombre_ruta', 'id_programa']]

    def __str__(self):
        return f"{self.nombre_ruta} — {self.id_programa.programa}"
```

### 4. `RutaSedes` — en `planeacion/models.py`

Tabla puente que asigna sedes a rutas, con un orden de visita.

```python
class RutaSedes(models.Model):
    """
    Asigna sedes educativas a una ruta de entrega.
    El campo 'orden' define el orden de visita dentro de la ruta.
    """
    id_ruta = models.ForeignKey(
        Ruta,
        on_delete=models.CASCADE,
        related_name='sedes',
        verbose_name="Ruta"
    )
    sede_educativa = models.ForeignKey(
        SedesEducativas,
        on_delete=models.PROTECT,
        related_name='rutas_asignadas',
        verbose_name="Sede Educativa"
    )
    orden = models.PositiveIntegerField(
        default=1,
        verbose_name="Orden de visita",
        help_text="Posición de la sede dentro del recorrido de la ruta"
    )

    class Meta:
        db_table = 'planeacion_ruta_sedes'
        verbose_name = "Sede en Ruta"
        verbose_name_plural = "Sedes en Rutas"
        ordering = ['id_ruta', 'orden']
        unique_together = [['id_ruta', 'sede_educativa']]

    def __str__(self):
        return f"{self.id_ruta.nombre_ruta} → {self.sede_educativa.nombre_sede_educativa} (#{self.orden})"
```

### Campo a agregar en `ProgramacionMenus` cuando las rutas existan

```python
# Agregar este campo al modelo ProgramacionMenus:
id_ruta = models.ForeignKey(
    Ruta,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='programaciones',
    verbose_name="Ruta de entrega",
    help_text="Ruta por la que se entrega el menú a esta sede"
)
```

---

## Diagrama completo de relaciones

```
Programa (planeacion)
  ├─── FK ──► Ruta ◄──── RutaSedes ──── FK ──► SedesEducativas
  │             │
  ├─── FK ──► ProgramacionMenus ──── FK ──► TablaMenus (nutricion)
  │           ├─ FK (sede)  ├─ FK (ruta, opcional)       │
  │           │             │                            └──► TablaPreparaciones
  │           ▼             ▼                                        │
  │     SedesEducativas   Ruta                                       └──► TablaPreparacionIngredientes
  │                                                                              │ FK (alimento ICBF)
  │                                                                              ▼
  │                                                                   TablaAlimentos2018Icbf
  │                                                                              │
  └─── FK ──► EquivalenciaICBFCompras ◄──────── FK(unique_together) ────────────┘
                      │ FK (PROTECT)
                      ▼
             TablaIngredientesSiesa
             (+ presentacion, unidad_medida, contenido_gramos)
                      │
                      ▼
             RESULTADO: Orden de Compra (agrupada por ruta)
```

---

## Plan de implementación (orden sugerido)

### Fase 1 — Fundamentos del match ICBF → Compras

| # | Acción | Archivo | Prioridad |
|---|---|---|---|
| 1 | Agregar `presentacion`, `unidad_medida`, `contenido_gramos` a `TablaIngredientesSiesa` | `nutricion/models.py` | Alta |
| 2 | Crear modelo `EquivalenciaICBFCompras` | `nutricion/models.py` | Alta |
| 3 | Generar y aplicar migraciones | Django migrations | Alta |
| 4 | UI para que el nutricionista haga el match por programa | `nutricion/views/` | Alta |
| 5 | Indicador semáforo en el menú (ingredientes con/sin match) | `nutricion/views/` | Media |

### Fase 2 — Programación de menús por sede y fecha

| # | Acción | Archivo | Prioridad |
|---|---|---|---|
| 6 | Crear modelo `ProgramacionMenus` (sin rutas aún) | `planeacion/models.py` | Alta |
| 7 | Generar y aplicar migraciones | Django migrations | Alta |
| 8 | Vista de programación de menús por sede y fecha | `planeacion/views.py` | Alta |
| 9 | Servicio de cálculo de necesidades de compra | `planeacion/services.py` | Alta |
| 10 | Reporte de orden de compra (PDF/Excel) | `planeacion/` | Media |

### Fase 3 — Rutas de entrega

| # | Acción | Archivo | Prioridad |
|---|---|---|---|
| 11 | Crear modelo `Ruta` | `planeacion/models.py` | Alta |
| 12 | Crear modelo `RutaSedes` | `planeacion/models.py` | Alta |
| 13 | Agregar FK `id_ruta` a `ProgramacionMenus` | `planeacion/models.py` | Alta |
| 14 | Generar y aplicar migraciones | Django migrations | Alta |
| 15 | UI para gestionar rutas y asignar sedes | `planeacion/views.py` | Media |
| 16 | Reporte de entrega agrupado por ruta | `planeacion/` | Media |

---

## Notas importantes

- **Un menú NO se asocia a un programa directamente.** Los menús en `TablaMenus` ya tienen `id_contrato` (FK a `Programa`), por lo que el programa ya está implícito en el menú. `ProgramacionMenus` hereda eso.
- **Alertas de match faltante:** El sistema debe mostrar una alerta cuando se programa un menú que tiene ingredientes sin match configurado en `EquivalenciaICBFCompras` para ese programa.
- **El match es permanente:** Borrar un ingrediente de un menú NO borra el match ICBF→Compras. El match se mantiene para cuando ese ingrediente vuelva a usarse en cualquier menú del mismo programa.
- **Rutas son opcionales en ProgramacionMenus:** En la Fase 2 se puede programar sin rutas. En la Fase 3 se agrega el FK a ruta sin romper lo ya construido (`null=True, blank=True`).
- **Orden de visita en rutas:** El campo `orden` en `RutaSedes` es importante para generar la planilla de entrega en el orden correcto del recorrido.
- **Una sede puede estar en varias rutas:** Si en el futuro una sede recibe CAP AM por una ruta y Almuerzo por otra, `RutaSedes` lo permite naturalmente (la clave única es ruta+sede, no solo sede).
