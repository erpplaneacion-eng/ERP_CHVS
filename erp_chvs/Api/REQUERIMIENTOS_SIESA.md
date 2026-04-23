# Requerimientos de Integración PAE ↔ SIESA ERP

**Módulo:** `Api/` — ERP_CHVS  
**Fecha:** 23 de abril de 2026  
**Estado:** En espera de entrega por parte de SIESA

---

## Qué debe entregar SIESA

### 1. Credenciales de acceso (confirmado)

SIESA entregará las credenciales para consumir su API en la siguiente forma:

| Dato | Descripción |
|---|---|
| **URL base** | Dirección del servicio SIESA (ambiente de pruebas y producción) |
| **Usuario** | Cuenta de acceso a la API |
| **Contraseña** | Clave asociada al usuario |

> Estas credenciales se almacenarán como variables de entorno en ERP_CHVS (`.env` local y variables Railway en producción). Nunca se hardcodean en el código.

---

### 2. Endpoints de consulta de catálogos (maestros)

Los catálogos de SIESA se descargan a tablas locales de PostgreSQL (`Api/models.py`) para no depender de SIESA en tiempo real. SIESA debe exponer un endpoint de consulta por cada catálogo.

Cada endpoint debe permitir **filtrar por fecha de modificación** para que el cron job descargue solo registros nuevos o modificados desde la última sincronización.

| Catálogo | Modelo local destino | Uso en PAE |
|---|---|---|
| Plan de Cuentas / Artículos | `SiesaArticulo` | Cada línea de SC/RQI referencia un ítem válido de este catálogo |
| Centros de Operación (CO) | `SiesaCO` | Encabezado de toda SC y RQI — identifica la sede del operador (Cali / Yumbo) |
| Bodegas | `SiesaBodega` | Línea de detalle — origen físico de los materiales |
| Proyectos (sedes DANE) | `SiesaProyecto` | Mapeo `SedesEducativas.cod_dane` → proyecto SIESA |
| Centros de Costo | `SiesaCentroCosto` | Afectación presupuestal en cada línea de detalle |
| Tipos de Documento | `SiesaTipoDocumento` | Encabezado — clasifica si el documento es SC o RQI |
| Concepto y Motivo | *(modelo por definir)* | Clasifica el porqué de la transacción (entradas / salidas) |
| Terceros / Proveedores | `SiesaTercero` | NIT, razón social y datos de contacto del proveedor |

#### Campos esperados por catálogo

**Plan de Cuentas / Artículos (`SiesaArticulo`)**

| Campo | Descripción |
|---|---|
| `codigo_referencia` | Identificador único del artículo en SIESA |
| `descripcion` | Nombre del artículo |
| `unidad_medida` | Unidad de medida |
| `costo_promedio_unitario` | Valor financiero de referencia |
| `stock_disponible` | Cantidad disponible |
| `estado` | `Activo` / `Inactivo` |

**Centros de Operación (`SiesaCO`)**

| Campo | Descripción |
|---|---|
| `codigo` | Identificador único |
| `descripcion` | Nombre del centro |
| `estado` | `Activo` / `Inactivo` |

**Bodegas (`SiesaBodega`)**

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

**Proyectos / Sedes DANE (`SiesaProyecto`)**

| Campo | Descripción |
|---|---|
| `codigo` | Código interno del proyecto en SIESA |
| `descripcion` | Nombre del proyecto |
| `dane` | Código DANE de la sede educativa |
| `zona` | `Urbana` / `Rural` |
| `direccion` | Dirección de la sede |
| `contacto` | Persona responsable |

**Centros de Costo (`SiesaCentroCosto`)**

| Campo | Descripción |
|---|---|
| `codigo` | Identificador |
| `descripcion` | Nombre del centro de costo |

**Tipos de Documento (`SiesaTipoDocumento`)**

| Campo | Descripción |
|---|---|
| `CO` | Centro de operación asociado |
| `codigo` | Sigla del documento (ej: `SC`, `RQI`) |
| `descripcion` | Nombre del tipo de documento |
| `estado` | Vigencia |

**Concepto y Motivo**

| Campo | Descripción |
|---|---|
| `codigo` | Código del concepto |
| `descripcion` | Descripción |
| `clase` | Clase del concepto |
| `motivo` | Motivo asociado |
| `naturaleza` | `1` = Entradas / `2` = Salidas |

**Terceros / Proveedores (`SiesaTercero`)**

| Campo | Descripción |
|---|---|
| `nit` | NIT del tercero |
| `razon_social` | Razón social |
| `direccion` | Dirección |
| `email` | Correo electrónico |
| `telefono` | Teléfono |

---

### 3. Endpoints de escritura — creación de documentos en SIESA

Dos operaciones que ERP_CHVS invocará para enviar documentos a SIESA:

#### Solicitud de Compra (SC)

- **Operación:** `POST` al endpoint SC de SIESA
- **Estructura del payload:**

```
ENCABEZADO
├── Centro de Operación (CO)
├── Tipo de Documento
└── Estado

LÍNEAS DE DETALLE (una por ingrediente/artículo)
├── Referencia / Ítem (SiesaArticulo)
├── Cantidad + Unidad de Medida
├── Bodega de Salida (SiesaBodega)
├── Centro de Costo (SiesaCentroCosto)
├── Proyecto / Sede DANE (SiesaProyecto)
└── Concepto + Motivo
```

- **Operaciones adicionales:** consulta por rango de fechas, obtención de estados.

#### Requisición de Inventario (RQI)

- **Operación:** `POST` al endpoint RQI de SIESA
- **Estructura:** igual que SC, más validación de trazabilidad (SAI en caso de RQC) y manejo de estados asociados.

---

### 4. Sincronización de catálogos — Cron Job (sin webhook)

La sincronización de catálogos locales con SIESA se realizará mediante **cron job programado**, no por webhook. SIESA no necesita implementar notificaciones reactivas.

**Responsabilidad de ERP_CHVS:** implementar `Api/management/commands/sync_siesa.py` que descargue solo los registros nuevos o modificados desde la última ejecución, usando el filtro de fecha que expongan los endpoints de SIESA.

**Responsabilidad de SIESA:** que sus endpoints de catálogo soporten el parámetro de filtro por fecha de modificación (ej: `?desde=2026-04-01`).

---

## Puntos pendientes de confirmar con SIESA

- [ ] Entregar URL base + usuario + contraseña de ambiente de pruebas
- [ ] Entregar URL base + usuario + contraseña de ambiente de producción
- [ ] Confirmar tipos de dato exactos por campo (alfanumérico, entero, decimal) — cruzar con diccionario de datos SIESA
- [ ] Confirmar el parámetro de filtro delta que soportan sus endpoints (`desde`, `fecha_modificacion`, u otro)
- [ ] Confirmar mapeo CO ↔ Sede operador (¿CO Cali corresponde a la sede Cali del operador?)
- [ ] Confirmar si `codigo_siesa` del match ICBF en ERP_CHVS equivale directamente al campo `codigo_referencia` de `SiesaArticulo`
- [ ] Confirmar si `SiesaTercero` tiene campos adicionales fuera del estándar listado arriba
- [ ] Confirmar mapeo de errores detallado de sus endpoints (códigos HTTP y estructura del cuerpo de error) para manejo de excepciones en nuestros conectores

---

## Estado actual

| Ítem | Estado |
|---|---|
| Módulo `Api/` en ERP_CHVS | Listo como contenedor |
| Modelos locales (`SiesaArticulo`, etc.) | Por implementar |
| Conectores SC / RQI | Por implementar |
| Cron job de sincronización | Por implementar |
| Credenciales y endpoints SIESA | **Pendiente de recibir** |
