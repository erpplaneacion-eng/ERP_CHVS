# Dashboard Gerencia — Explicación de Columnas

## ¿Cómo funciona?

La vista muestra una **tabla principal** con una fila por cada líder. Al hacer clic en una fila, se despliega una **sub-tabla** con el detalle de cada Registro Contable (RC) de ese líder.

---

## Tabla Principal (una fila por líder)

| Columna | Qué mide | Variables involucradas |
|---|---|---|
| **Líder** | Nombre completo y usuario del líder | `first_name`, `last_name`, `username` |
| **Estado** | El estado más urgente entre sus RCs activos. Prioridad: Devuelto > Observado > Enviado > En revisión | `estado` del RC activo más crítico |
| **RC** | Total de registros contables creados por este líder (aplica filtros de mes/año/tipo) | Conteo de `RegistroContable` |
| **Activos** | RCs que aún no han sido cerrados | RCs con `estado != CERRADO` |
| **Cerrados** | RCs que Contabilidad ya cerró definitivamente | RCs con `estado = CERRADO` |
| **Devoluciones** | Número total de veces que Compras devolvió documentos al líder (suma de todos sus RCs) | Conteo de eventos `DEVOLUCION_COMPRAS` en `HistorialEstado` |
| **Valor Cerrado** | Suma en pesos de todos los RCs cerrados | Suma de `valor_total` de RCs cerrados |
| **Prom. Cierre** | Promedio de días desde que el líder envió el RC hasta que Contabilidad lo cerró | `fecha_cierre − fecha_envio` (solo RCs cerrados) |
| **Máx. Cierre** | El RC que más días tardó en cerrarse. **Rojo si > 10 días** | `fecha_cierre − fecha_envio` (valor máximo) |
| **Prom. Reentrega** | Promedio de días que tardó el líder en corregir y reenviar tras una devolución | `fecha_reenvio − fecha_devolucion_compras` |
| **Máx. Reentrega** | La corrección que más tardó. **Naranja si > 5 días** | `fecha_reenvio − fecha_devolucion_compras` (valor máximo) |
| **Prom. Retención** | Promedio de días entre que el líder recibió físicamente la factura y la envió a Compras | `fecha_envio − fecha_recepcion_lider` (máximo entre facturas del RC) |
| **Máx. Retención** | La mayor retención registrada. **Rojo si > 2 días** | `fecha_envio − fecha_recepcion_lider` (valor máximo global) |
| **Prom. Retraso Carga** | Promedio de días entre la fecha de la factura y la fecha de recepción física del líder | `fecha_recepcion_lider − fecha_factura` (promedio del máximo por RC) |
| **Máx. Retraso Carga** | El mayor retraso de carga registrado. **Rojo si > 2 días** | `fecha_recepcion_lider − fecha_factura` (valor máximo global) |
---

## Sub-tabla Desplegable (una fila por RC)

Se abre al hacer clic en la fila del líder. Muestra cada RC con su detalle.

| Columna | Qué mide | Variables involucradas |
|---|---|---|
| **RC** | Número del registro con link directo al detalle | `RegistroContable.pk` |
| **Tipo** | Tipo de registro (Servicios, Materias Primas, etc.) | `tipo` |
| **Período** | Mes y año al que corresponde el RC | `periodo_mes`, `periodo_ano` |
| **Estado** | Estado actual del RC con badge de color | `estado` |
| **Días estado** | Cuántos días lleva en el estado actual. **Rojo si > 5 días y no está cerrado** | `now − ultima_transicion` |
| **Devoluciones** | Cuántas veces fue devuelto este RC específico | Conteo de `DEVOLUCION_COMPRAS` en historial |
| **T. Líder** | Tiempo total que el RC estuvo en manos del líder. Si hubo devolución, suma los dos períodos. **Rojo si > 9h** | Sin devolución: `fecha_envio − fecha_creacion`. Con devolución: `T1 + T2` |
| **T. Compras** | Tiempo total que el RC estuvo en revisión de Compras. Si hubo devolución, suma ambos períodos de revisión. **Rojo si > 48h** | Sin devolución: `fecha_aprobacion_compras − fecha_entrega_fisica`. Con devolución: `T1 + T2` |
| **T. Contab.** | Tiempo total que el RC estuvo en manos de Contabilidad. Si hubo observación, suma los dos períodos. **Rojo si > 48h** | Sin observación: `fecha_cierre − fecha_aprobacion_compras`. Con observación: `T1 + T2` |
| **Distribución** | Barra proporcional de los tres tiempos anteriores. Solo aparece cuando el RC está completamente cerrado (los 3 tiempos disponibles) | Azul = T. Líder · Naranja = T. Compras · Verde = T. Contabilidad |
| **Retención** | Días entre que el líder recibió físicamente la factura más tardía y el envío a Compras | `fecha_envio − max(fecha_recepcion_lider)` entre facturas |
| **Ret. carga** | Días entre la fecha de la factura y la fecha de recepción física del líder | `fecha_recepcion_lider − fecha_factura` |
| **Docs** | Número de facturas incluidas en el RC | Conteo de `Factura` del RC |
| **Valor** | Valor total de las facturas del RC | Suma de `valor` de cada `Factura` |

---

## Indicador `🔄 incluye correc.`

Aparece debajo del tiempo en las columnas **T. Líder**, **T. Compras** y **T. Contab.** cuando el tiempo reportado no fue continuo — hubo una interrupción donde el documento salió del área y regresó.

Al pasar el mouse sobre el indicador aparece un **tooltip** con el desglose exacto:

| Columna | Tooltip muestra |
|---|---|
| **T. Líder** | `1er envío: Xh \| Corrección tras devolución: Xh` |
| **T. Compras** | `1ra revisión: Xh \| 2da revisión: Xh` |
| **T. Contab.** | `1ra revisión: Xh \| 2da revisión: Xh` |

---

## Cómo se calcula T. Líder, T. Compras y T. Contab. con devoluciones

### Sin devolución / observación (flujo limpio)

```
LÍDER:        fecha_creacion ──────────────────► fecha_envio
COMPRAS:      fecha_entrega_fisica ─────────────► fecha_aprobacion_compras
CONTABILIDAD: fecha_aprobacion_compras ──────────► fecha_cierre
```

### Con devolución de Compras al Líder

```
LÍDER:    [fecha_creacion → fecha_envio] + [fecha_devolucion_compras → fecha_reenvio]
           T1 (envío inicial)               T2 (corrección)
           └─────────────── T. Líder = T1 + T2 ───────────────┘

COMPRAS:  [fecha_entrega_fisica → fecha_devolucion_compras] + [fecha_reentrega_fisica → fecha_aprobacion_compras]
           T1 (1ra revisión)                                    T2 (2da revisión)
           └──────────────────── T. Compras = T1 + T2 ────────────────────────────┘
```

### Con observación de Contabilidad

```
CONTABILIDAD: [fecha_aprobacion_compras → fecha_observacion_contabilidad] + [fecha_respuesta_compras → fecha_cierre]
               T1 (1ra revisión)                                              T2 (2da revisión tras respuesta)
               └──────────────────────── T. Contab. = T1 + T2 ─────────────────────────────────────────────────┘
```

> **Nota:** El tiempo que el RC estuvo en manos del otro área (líder corrigiendo, Compras respondiendo observación) **no se cuenta** en el tiempo de la etapa. Cada área solo acumula el tiempo que el documento estuvo efectivamente en su poder.

---

## Umbrales de alerta (colores)

| Columna | Naranja | Rojo |
|---|---|---|
| Máx. Cierre | — | > 10 días |
| Máx. Reentrega | > 5 días | — |
| Máx. Retención | — | > 2 días |
| Máx. Retraso Carga | — | > 2 días |
| Días estado (sub-tabla) | — | > 5 días (si no está cerrado) |
| T. Líder (sub-tabla) | — | > 9h |
| T. Compras (sub-tabla) | — | > 48h |
| T. Contab. (sub-tabla) | — | > 48h |
| Ret. carga (sub-tabla) | > 0 días | > 2 días |
