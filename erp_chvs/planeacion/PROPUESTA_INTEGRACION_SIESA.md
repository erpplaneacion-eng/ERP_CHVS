# Propuesta de Integración PAE ↔ SIESA ERP

**Documento:** Proyecto de Integración Modalidad SAAS del Desarrollo de Planeación Interna al Sistema ERP SIESA
**Fecha:** 20 de febrero de 2026
**Destinatario:** Corporación para un Valle Solidario 
**Proveedor:** Alianza y Gestión Estratégica S.A.S.

---

## Objetivo

Integrar técnica y funcionalmente el aplicativo interno de planeación (**PAE / ERP_CHVS**) con el sistema **SIESA ERP** en modalidad SAAS, enfocándose en la generación y envío de:

- **Solicitudes de Compra (SC)**
- **Requisiciones de Inventario (RQI)**

---

## Arquitectura de integración (módulo Api/)

La integración se implementa en el módulo `Api/` (app Django ya creada para este fin). El principio central es **no depender de Siesa en tiempo real**: los catálogos de Siesa se descargan a tablas locales de PostgreSQL y se mantienen sincronizados mediante un cron job reactivo.

```
[Siesa ERP SAAS]
      │
      │  tokens + endpoints (pendiente de recibir de Siesa)
      ▼
  Api/ (módulo Django — app ya existente en ERP_CHVS)
      │
      ├─► Descarga inicial (una sola vez)
      │     Endpoint Siesa → tabla local PostgreSQL
      │     - Plan de Cuentas/Artículos  → Api/models.py (SiesaArticulo)(qui iria tambien el tema de unidades de medida)
      │     - Proyectos (sedes DANE)     → Api/models.py (SiesaProyecto)
      │     - Bodegas                    → Api/models.py (SiesaBodega)
      │     - Centros de Costo           → Api/models.py (SiesaCentroCosto)
      │     - Centros de Operación       → Api/models.py (SiesaCO)
      │     - Tipos de Documento         → Api/models.py (SiesaTipoDocumento)
      │     - Terceros (proveedores)     → Api/models.py (SiesaTercero)
      │
      └─► Cron job de sincronización delta
            - Se dispara cuando Siesa notifica un cambio (webhook) o en
              intervalos definidos (ej: cada noche)
            - Solo descarga registros nuevos o modificados
            - No hace polling continuo a la API de Siesa
```

**Estado actual:** Bloqueado — esperando tokens y endpoints de Siesa.

---

## Flujo completo con ERP_CHVS

```
[Nutrición] crea menús con ingredientes ICBF
      │
      ▼
[Match ICBF → Compras] — nutricionista asocia cada alimento ICBF
      │                  con su artículo equivalente en SiesaArticulo (local)
      │                  → tabla: EquivalenciaICBFCompras
      ▼
[Planeación] programa menús por sede y fecha
      │        → tabla: ProgramacionMenus (con FK a logistica.Ruta)
      │
      ▼
[Api/] calcula orden de compra
      │  raciones × gramaje ÷ contenido_gramos = unidades por artículo
      │
      ▼
[Api/] genera documento SC o RQI en Siesa
      │  encabezado: CO + Tipo de Documento
      │  detalle: Artículo + Cantidad + Bodega + Centro de Costo + Proyecto/Sede
      ▼
[Siesa ERP] recibe y procesa el documento
```

---

## Relación con módulo logistica (actualizado)

Las rutas de entrega ya están implementadas en el módulo `logistica` con CRUD completo:

| Modelo | Tabla | Descripción |
|---|---|---|
| `TipoRuta` | `logistica_tipos_rutas` | Clasificación de rutas |
| `Ruta` | `logistica_rutas` | Ruta de entrega por programa |
| `RutaSedes` | `logistica_ruta_sedes` | Sedes asignadas a cada ruta con orden de visita |

`ProgramacionMenus` hace FK a `logistica.Ruta` directamente. No se crean nuevos modelos de rutas en `planeacion` ni en `Api/`.

La generación de SC/RQI puede agruparse por ruta (para entregar los insumos en el orden correcto del recorrido), usando la relación:

```
ProgramacionMenus.id_ruta → logistica.Ruta → logistica.RutaSedes (ordenadas por orden_visita)
```

---

## Alcance Funcional: Maestros (Consultas SIESA)

Los maestros de Siesa se descargan a tablas locales del módulo `Api/`. Se consultan internamente para validar documentos antes de enviarlos.

---

### 1. Plan de Cuentas / Ítems (Referencia de Artículos) → `SiesaArticulo`

> Catálogo maestro de artículos. Más crítico: cada línea de SC o RQI debe referenciar un ítem válido aquí.

| Campo | Descripción |
|---|---|
| `codigo_referencia` | Identificador único del artículo en SIESA |
| `descripcion` | Nombre del artículo |
| `estado` | `Activo` / `Inactivo` |
| `stock_disponible` | Cantidad disponible para validación |
| `unidad_medida` | Unidad de medida del artículo |
| `costo_promedio_unitario` | Valor financiero de referencia |

**Relación con PAE:** `EquivalenciaICBFCompras.id_ingrediente_compras` apuntará a `SiesaArticulo` cuando la integración esté activa (en el simulacro actual apunta a `TablaIngredientesSiesa`).

---

### 2. Centro de Operación (CO) → `SiesaCO`

> Identifica el origen administrativo del documento. Va en el **encabezado** de toda SC y RQI.

| Campo | Descripción |
|---|---|
| `codigo` | Identificador único del CO |
| `descripcion` | Nombre del centro |
| `estado` | `Activo` / `Inactivo` |

**Relación con PAE:** Corresponde a la **sede** del operador (Cali → CO Cali / Yumbo → CO Yumbo).

---

### 3. Bodegas → `SiesaBodega`

> Define el origen físico de los materiales. Va a nivel de **línea de detalle**.

| Campo | Descripción |
|---|---|
| `CO` | Centro de operación asociado |
| `descripcion` | Nombre de la bodega |
| `estado` | `Activo` / `Inactivo` |
| `pais` | País |
| `departamento` | Departamento |
| `ciudad` | Ciudad |
| `direccion_1` | Primera línea de dirección |
| `direccion_2` | Segunda línea de dirección |
| `direccion_3` | Tercera línea de dirección |
| `celular` | Teléfono de contacto |
| `email` | Correo electrónico |

---

### 4. Proyectos (Equivalencia de Sedes) → `SiesaProyecto`

> Mapea las sedes educativas del PAE con proyectos en SIESA.

| Campo | Descripción |
|---|---|
| `codigo` | Código interno del proyecto en SIESA |
| `descripcion` | Nombre del proyecto |
| `dane` | Código DANE oficial de la sede educativa |
| `zona` | Zona geográfica (`Urbana` / `Rural`) |
| `direccion` | Dirección de la sede |
| `contacto` | Persona responsable en la sede |

**Relación con PAE:** `SedesEducativas.codigo_dane` → `SiesaProyecto.dane`.

---

### 5. Centros de Costo → `SiesaCentroCosto`

> Afectación presupuestal. Va en cada **línea de detalle**.

| Campo | Descripción |
|---|---|
| `codigo` | Identificador del centro de costo |
| `descripcion` | Nombre del centro de costo |

---

### 6. Tipo de Documento → `SiesaTipoDocumento`

> Clasifica la transacción que se envía a SIESA. Va en el **encabezado**.

| Campo | Descripción |
|---|---|
| `CO` | Centro de operación asociado |
| `codigo` | Sigla del documento (ej: `SC`, `RQI`) |
| `descripcion` | Nombre del tipo de documento |
| `estado` | Vigencia del tipo |

---

### 7. Concepto y Motivo

> Clasifican el **porqué** de la transacción.

| Campo | Descripción |
|---|---|
| **Concepto** | |
| `codigo` | Código del concepto |
| `descripcion` | Descripción del concepto |
| `clase` | Clase del concepto |
| `motivo` | Motivo asociado |
| **Motivo** | |
| `naturaleza` | `1` = Entradas / `2` = Salidas |

---

### 8. Terceros (Proveedores / Clientes) → `SiesaTercero`

| Campo | Descripción |
|---|---|
| `nit` | NIT del tercero |
| `razon_social` | Razón social |
| `direccion` | Dirección |
| `email` | Correo electrónico |
| `telefono` | Teléfono |

---

## Estructura de un Documento SC / RQI

```
ENCABEZADO
├── Centro de Operación (CO)    → SiesaCO
├── Tipo de Documento           → SiesaTipoDocumento
└── Estado

LÍNEAS DE DETALLE (por cada ingrediente/artículo)
├── Referencia / Ítem           → SiesaArticulo (Plan de Cuentas)
├── Cantidad + Unidad de Medida
├── Bodega de Salida            → SiesaBodega
├── Centro de Costo             → SiesaCentroCosto
├── Proyecto / Sede (DANE)      → SiesaProyecto
└── Concepto + Motivo
```

---

## Alcance Funcional: Solicitudes de Compra (SC)

**Operaciones:**
- Consulta por rango de fechas
- Obtención de estados
- Validación de sincronización

**Campos del Encabezado:** CO, Tipo de Documento, Estado
**Campos del Detalle:**
- Referencia de ítem (validado contra SiesaArticulo)
- Unidad de medida y cantidades
- Grupo de bodegas
- Datos de contacto (Teléfono, Email, Dirección)
- Conceptos y Motivos
- Equivalencia de sedes (Código DANE, Zona, Dirección)
- Costo promedio unitario

---

## Alcance Funcional: Requisiciones de Inventario (RQI)

Estructura similar a las SC con adiciones:
- Validación de **trazabilidad** entre la aprobación y la generación en el ERP
- Manejo de estados y documentos asociados (SAI en caso de RQC)

---

## Conectores a Implementar en Api/

### Conector SC — Solicitudes de Compra

```
Api/views.py o Api/services.py
    generar_sc(id_programa, fecha_inicio, fecha_fin)
        → calcular_necesidades_compra() [planeacion/services.py]
        → validar artículos contra SiesaArticulo (local)
        → construir payload SC
        → POST endpoint Siesa SC
        → registrar resultado
```

### Conector RQI — Requisiciones Aprobadas

```
Api/views.py o Api/services.py
    generar_rqi(id_programa, fecha_inicio, fecha_fin)
        → similar a SC + validación de trazabilidad
        → POST endpoint Siesa RQI
```

### Cron job de sincronización

```python
# Ejemplo de estructura (implementar cuando lleguen endpoints)
# Archivo: Api/management/commands/sync_siesa.py

class Command(BaseCommand):
    help = 'Sincroniza catálogos locales con Siesa (delta)'

    def handle(self, *args, **options):
        # Solo descarga registros nuevos o modificados desde la última sync
        ultima_sync = SiesaSyncLog.objects.last()
        registros_nuevos = client.get_articulos(desde=ultima_sync.fecha)
        SiesaArticulo.objects.bulk_create(
            registros_nuevos, update_conflicts=True, ...
        )
        SiesaSyncLog.objects.create(tipo='articulos', resultado='ok')
```

---

## Metodología de Trabajo (8 Etapas)

| # | Etapa |
|---|---|
| 1 | Levantamiento técnico y funcional |
| 2 | Validación de requerimientos |
| 3 | Diseño del mapeo de integración |
| 4 | Desarrollo y configuración de conectores |
| 5 | Pruebas funcionales y técnicas |
| 6 | Ajustes finales |
| 7 | Puesta en producción |
| 8 | Acompañamiento post-implementación |

---

## Especificaciones Técnicas

| Parámetro | Valor |
|---|---|
| **Tiempo de ejecución** | 30 días hábiles desde firma / OC |
| **Equipo asignado** | 1 desarrollador, 8 horas semanales |
| **Modalidad** | SAAS |
| **Requisitos cliente** | VPN/Red SIESA, credenciales de pruebas, acceso a internet |

---

## Beneficios Esperados

- ✅ Automatización del flujo de planeación hacia el ERP
- ✅ Eliminación de procesos manuales de digitación
- ✅ Mayor trazabilidad y control presupuestario
- ✅ Integridad de la información entre sistemas
- ✅ Sin dependencia de Siesa en tiempo real (tablas locales sincronizadas)

---

## Mapeo nombres propuestos → implementados

Este documento fue escrito antes de recibir las credenciales SIESA (feb. 2026). Los nombres de modelos propuestos aquí difieren de los implementados, que preservan la nomenclatura real de los campos SIESA (`f<num>_<campo>`).

| Nombre propuesto (doc) | Modelo implementado (`Api/models.py`) | Estado |
|---|---|---|
| `SiesaArticulo` (Plan de Cuentas) | `SiesaItem` | ✅ Modelo creado — `payload = JSONField()` hasta que SIESA llene el catálogo |
| `SiesaBodega` | `SiesaUbicacion` | ✅ 33 registros (`f155_id`, `f155_descripcion`, `f150_id`) |
| `SiesaCO` (Centro Operación) | `SiesaCentroOperacion` | ✅ 1 registro (`f285_id`, `f285_descripcion`) |
| `SiesaTercero` | `SiesaSolicitante` | ✅ Modelo creado — `payload = JSONField()` hasta que SIESA llene el catálogo |
| `SiesaProyecto` | `SiesaProyecto` | ✅ 1.718 registros (`f107_id`, `f107_descripcion`, `f107_id_referencia`) |
| `SiesaCentroCosto` | `SiesaCentroCosto` | ✅ 73 registros (`f284_id`, `f284_descripcion`, `f284_id_co`, `f284_id_un`) |
| `SiesaTipoDocumento` | `SiesaTipoDocumento` | ✅ 90 registros (`f021_id`, `f021_descripcion`) |
| Concepto / Motivo | `SiesaConcepto` + `SiesaMotivo` | ✅ 38 + 89 registros |
| *(no estaba en diseño)* | `SiesaInstalacion` | ✅ 3 registros — instalaciones físicas del operador |
| *(no estaba en diseño)* | `SiesaUnidadNegocio` | ✅ 13 registros — contratos del operador |

El comando `python manage.py sync_siesa` reemplaza el "cron job de sincronización" descrito en este documento. El "cron job delta" sigue pendiente.

---

## Pendientes / Preguntas Abiertas

- [ ] Recibir tokens y endpoints de Siesa (bloqueante para Fase 3)
- [ ] Definir tipos de dato exactos (alfanumérico vs entero) cruzando con diccionario de datos SIESA
- [ ] Confirmar si Terceros tiene campos adicionales o usa estándar SIESA sin modificación
- [ ] Validar mapeo de errores detallado en sección de Conectores (pág. 5-6 del PDF)
- [ ] Confirmar equivalencia CO ↔ Sede (Cali / Yumbo)
- [ ] Confirmar si `codigo_siesa` en el match ICBF corresponde directamente al campo `codigo_referencia` de SiesaArticulo
- [ ] Definir mecanismo de notificación de cambios de Siesa (webhook vs polling nocturno)
