# Propuesta de Integración PAE ↔ SIESA ERP

**Documento:** Proyecto de Integración Modalidad SAAS del Desarrollo de Planeación Interna al Sistema ERP SIESA
**Fecha:** 20 de febrero de 2026
**Destinatario:** Corporación para un Valle Solidario (Dra. Cielo Muñoz)
**Proveedor:** Alianza y Gestión Estratégica S.A.S.

---

## Objetivo

Integrar técnica y funcionalmente el aplicativo interno de planeación (**PAE / ERP_CHVS**) con el sistema **SIESA ERP** en modalidad SAAS, enfocándose en la generación y envío de:

- **Solicitudes de Compra (SC)**
- **Requisiciones de Inventario (RQI)**

---

## Alcance Funcional: Maestros (Consultas SIESA)

Los maestros de SIESA se consultan para **alimentar y validar** la aplicación PAE antes de generar documentos. Ningún documento puede crearse sin que sus campos estén validados contra estos maestros.

---

### 1. Plan de Cuentas / Ítems (Referencia de Artículos)

> Catálogo maestro de artículos. Es el más crítico: cada línea de SC o RQI debe referenciar un ítem válido aquí.

| Campo | Descripción |
|---|---|
| `codigo_referencia` | Identificador único del artículo en SIESA |
| `descripcion` | Nombre del artículo |
| `estado` | `Activo` / `Inactivo` |
| `stock_disponible` | Cantidad disponible para validación |
| `unidad_medida` | Unidad de medida del artículo |
| `costo_promedio_unitario` | Valor financiero de referencia |

**Validaciones:**
- Verificación de existencia y estado antes de crear el documento
- El `codigo_referencia` es la llave que vincula cada ingrediente ICBF con SIESA

**Relación con PAE:** El campo `codigo_siesa` del match ICBF–Compras mapea directamente a `codigo_referencia`.

---

### 2. Centro de Operación (CO)

> Identifica el origen administrativo del documento. Va en el **encabezado** de toda SC y RQI.

| Campo | Descripción |
|---|---|
| `codigo` | Identificador único del CO |
| `descripcion` | Nombre del centro |
| `estado` | `Activo` / `Inactivo` |

**Relación con PAE:** Corresponde a la **sede** del operador (Cali → CO Cali / Yumbo → CO Yumbo).

---

### 3. Bodegas (Grupo de Bodegas – Bodega de Salida)

> Define el origen físico de los materiales. Va a nivel de **línea de detalle** (por cada ítem).

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

**Uso:** Indica de dónde debe salir físicamente el inventario para cada movimiento.

---

### 4. Proyectos (Equivalencia de Sedes)

> Mapea las sedes educativas del PAE con proyectos en SIESA. Es el **puente** entre `SedesEducativas` (Django) y SIESA.

| Campo | Descripción |
|---|---|
| `codigo` | Código interno del proyecto en SIESA |
| `descripcion` | Nombre del proyecto |
| `dane` | Código DANE oficial de la sede educativa |
| `zona` | Zona geográfica (`Urbana` / `Rural`) |
| `direccion` | Dirección de la sede |
| `contacto` | Persona responsable en la sede |

**Relación con PAE:** `SedesEducativas.codigo_dane` → `Proyecto.dane` en SIESA.

---

### 5. Centros de Costo

> Afectación presupuestal. Va en cada **línea de detalle** para trazabilidad contable.

| Campo | Descripción |
|---|---|
| `codigo` | Identificador del centro de costo |
| `descripcion` | Nombre del centro de costo |

---

### 6. Tipo de Documento

> Clasifica la transacción que se envía a SIESA. Va en el **encabezado**.

| Campo | Descripción |
|---|---|
| `CO` | Centro de operación asociado |
| `codigo` | Sigla del documento (ej: `SC`, `RQI`) |
| `descripcion` | Nombre del tipo de documento |
| `estado` | Vigencia del tipo |

---

### 7. Concepto y Motivo

> Clasifican el **porqué** de la transacción para trazabilidad contable y operativa.

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

### 8. Terceros (Proveedores / Clientes)

> Maestro de proveedores y clientes. El PDF no detalla campos específicos; usa el estándar de SIESA.

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
├── Centro de Operación (CO)    → Maestro #2
├── Tipo de Documento           → Maestro #6
└── Estado

LÍNEAS DE DETALLE (por cada ingrediente/artículo)
├── Referencia / Ítem           → Maestro #1 (Plan de Cuentas)
├── Cantidad + Unidad de Medida
├── Bodega de Salida            → Maestro #3
├── Centro de Costo             → Maestro #5
├── Proyecto / Sede (DANE)      → Maestro #4
└── Concepto + Motivo           → Maestro #7
```

---

## Alcance Funcional: Solicitudes de Compra (SC)

**Operaciones:**
- Consulta por rango de fechas
- Obtención de estados
- Validación de sincronización

**Campos del Encabezado:** CO, Tipo de Documento, Estado
**Campos del Detalle:**
- Referencia de ítem (validado contra Plan de Cuentas)
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

## Conectores a Implementar

1. **Conector SC** – Solicitudes de Compra
2. **Conector RQI** – Requisiciones Aprobadas

Cada conector incluye:
- Mapeo de campos PAE ↔ SIESA
- Pruebas unitarias e integrales
- Manejo de errores y respuestas del ERP

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

---

## Pendientes / Preguntas Abiertas

- [ ] Definir tipos de dato exactos (alfanumérico vs entero) cruzando con diccionario de datos SIESA
- [ ] Confirmar si Terceros tiene campos adicionales o usa estándar SIESA sin modificación
- [ ] Validar mapeo de errores detallado en sección de Conectores (pág. 5-6 del PDF)
- [ ] Confirmar equivalencia CO ↔ Sede (Cali / Yumbo)
- [ ] Confirmar si `codigo_siesa` en el match ICBF corresponde directamente al campo `codigo_referencia` del Plan de Cuentas
