# Estado vs. Cronograma SIESA — ERP_CHVS

## Resumen ejecutivo

| Fase | Período | Estado ERP_CHVS |
|---|---|---|
| Fase 1 — Levantamiento | Días 1–10 | 🟡 **Parcial** — arquitectura y flujos documentados, pendientes de validar con SIESA |
| Fase 2 — Diseño y Desarrollo | Días 11–30 | 🔴 **No iniciada** — hay trabajo interno crítico que debe arrancar YA en paralelo |
| Fase 3 — Integración y Pruebas | Días 31–40 | 🔴 **Bloqueada** — depende de tokens SIESA + Fase 2 completa |
| Fase 4 — Despliegue y Cierre | Días 41–45 | 🔴 **Bloqueada** — depende de Fase 3 |

---

## FASE 1 — Levantamiento (Días 1–10)

### 1.1 Levantamiento funcional

| Ítem SIESA | Estado | Detalle |
|---|---|---|
| Kick off Proyecto | ⏳ Pendiente | No realizado aún |
| Identificación de procesos (requisiciones, SC) | ✅ Documentado | `PROPUESTA_INTEGRACION_SIESA.md` — flujo SC/RQI completo |
| Validación flujo actual vs flujo objetivo | ✅ Documentado | `PLAN_MATCH_ICBF_COMPRAS.md` — diagrama de relaciones completo |
| Definición de actores (nutrición, compras, logística) | ✅ Documentado | Nutricionista hace match, Planeación programa, Api/ dispara a SIESA |

### 1.2 Definición de maestros a integrar

| Maestro | Estado | Detalle |
|---|---|---|
| Ítems (activos, unidades, presentaciones, costos) | ✅ Diseñado | Modelo `SiesaArticulo` definido en `PROPUESTA_INTEGRACION_SIESA.md`. **No existe en código.** |
| Bodegas y centros de operación | ✅ Diseñado | Modelos `SiesaBodega` y `SiesaCO` definidos en doc. **No existen en código.** |
| Proyectos y centros de costo | ✅ Diseñado | Modelos `SiesaProyecto` y `SiesaCentroCosto` definidos en doc. **No existen en código.** |
| Conceptos y motivos | ✅ Diseñado | Estructura definida en doc. **No existe en código.** |

> **Importante:** Todos los maestros están diseñados conceptualmente pero `Api/models.py` está vacío.
> No tiene sentido crearlos hasta tener los tokens SIESA — la estructura real puede diferir del diseño.

### 1.3 Definición técnica de integración

| Ítem | Estado | Detalle |
|---|---|---|
| Arquitectura (API REST con token) | ✅ Definida | Tablas locales PostgreSQL + cron job delta. Sin polling en tiempo real. |
| Frecuencia de sincronización | ❓ Pendiente decisión | Webhook vs polling nocturno — depende de capacidad del SAAS de SIESA |
| Definición estructura JSON | ✅ Parcial | Encabezado y líneas de SC/RQI documentados. Pendiente validar contra diccionario SIESA. |

### 1.4 Validaciones de negocio

| Ítem | Estado | Detalle |
|---|---|---|
| Definición campo "Tercero" | ❓ Abierto | ¿Es el proveedor del alimento o el operador (CHVS)? Sin confirmar. |
| Reglas para costos (promedio unitario) | ✅ Contemplado | Campo `costo_promedio_unitario` en diseño de `SiesaArticulo` |
| Alcance de terceros (proveedores/clientes) | ❓ Abierto | Pendiente confirmar con SIESA |

**Preguntas críticas para llevar al Kickoff:**
1. ¿Cada presentación de artículo tiene código propio en SIESA, o hay jerarquía artículo-variante?
2. ¿Qué campo usa SIESA como llave de sede educativa? (confirmamos DANE)
3. ¿El SAAS soporta webhooks o solo polling?
4. ¿Quién es el "Tercero" en una SC/RQI del PAE?
5. ¿Los tokens de prueba se entregan en el kickoff?

---

## FASE 2 — Diseño y Desarrollo (Días 11–30)

Esta es la fase con mayor riesgo. Varios ítems tienen **dependencias internas** que deben resolverse en paralelo con SIESA o incluso antes.

### 2.1 Diseño de servicios (APIs)

| Ítem | Estado | Responsable |
|---|---|---|
| Endpoint de maestros (artículos, bodegas, etc.) | 🔴 No iniciado | SIESA desarrolla — nosotros consumimos |
| Endpoint de requisiciones (RQI) | 🔴 No iniciado | SIESA desarrolla |
| Endpoint de solicitudes de compra (SC) | 🔴 No iniciado | SIESA desarrolla |

> Estos endpoints los construye SIESA. Nosotros los consumimos desde `Api/`.

### 2.2 Desarrollo de sincronización de maestros

| Ítem | Estado | Archivo ERP_CHVS |
|---|---|---|
| Servicio unificado de consulta | ✅ **Implementado** | `Api/services/sync_service.py` |
| Filtro por estado activo | 🟡 N/A por ahora | Full sync — endpoints SIESA no exponen filtro por fecha |
| Parametrización dinámica de campos | ✅ **Implementado** | `Api/services/mappers.py` (mapper por catálogo) |
| Modelos locales (11 catálogos reales) | ✅ **Implementado** | `Api/models.py` — campos 1:1 con JSON SIESA real |
| Sincronización (full sync) | ✅ **Implementado** | `python manage.py sync_siesa [--catalogo X] [--dry-run]` |

> **Desbloqueado**: credenciales y endpoints recibidos de SIESA (abril 2026). App activada, modelos creados, sync operativo. Pendiente: ejecutar `migrate` + primera sincronización en local.

### 2.3 Desarrollo módulo planeación (lado cliente) — ⚠️ RIESGO ALTO

Este ítem depende de trabajo **interno nuestro** que todavía no existe. Si no lo arrancamos en paralelo con la Fase 1, llegamos tarde al Día 11.

| Ítem | Estado | Archivo ERP_CHVS | Urgencia |
|---|---|---|---|
| Consumo de APIs SIESA (integrar catálogo real) | 🔴 No iniciado | `planeacion/views.py` | Después de tokens |
| **Modelo `ProgramacionMenus`** | 🔴 **No creado** | `planeacion/models.py` | 🔥 Arrancar YA |
| **Interfaz de programación de menús** (calendario Despachos) | 🔴 **No iniciada** | `planeacion/` nuevo | 🔥 Arrancar YA |
| **Modelo `Despacho`** (con rango fecha inicio/fin) | 🔴 **No creado** | `planeacion/models.py` | 🔥 Arrancar YA |
| Interfaz de selección de ítems (catálogo Siesa) | 🔴 No iniciada | Depende de tokens | Después de tokens |
| Manejo de unidades y presentaciones | ✅ Base lista | Match ICBF ya implementado | — |

### 2.4 Desarrollo de generación de documentos

| Ítem | Estado | Archivo ERP_CHVS |
|---|---|---|
| Creación de solicitudes de compra (SC) | 🔴 No iniciado | `Api/` |
| Creación de requisiciones (RQI) | 🔴 No iniciado | `Api/` |
| Estructura de envío a SIESA | ✅ Diseñada | Definida en `PROPUESTA_INTEGRACION_SIESA.md` |
| Servicio `calcular_necesidades_compra()` | 🔴 No iniciado | `planeacion/services.py` |
| Lógica urbano (multi-RQI por categoría) vs rural (RQI única) | ✅ Diseñada | `DOC_07_LOGISTICA_RUTAS_Y_PERIODOS.md` |
| Pre-validación de matches incompletos | ✅ Diseñada | `DOC_04_CONSIDERACIONES_ESTRATEGICAS.md` |

### 2.5 Ajustes estructurales internos

| Ítem | Estado | Detalle |
|---|---|---|
| Rediseño tabla sedes/bodegas | 🟡 Parcial | `SedesEducativas.cod_dane` ↔ `SiesaProyecto.dane` diseñado. Confirmar con SIESA que el DANE es la llave de cruce suficiente. |
| Campo `categoria_logistica` en artículos | 🔴 No iniciado | Depende de si SIESA ya lo tiene o hay que añadirlo manualmente. |
| Campo `frecuencia_despacho` en sedes | 🔴 No iniciado | Diseñado en `DOC_07`. Necesario para sedes con pedido semanal consolidado. |

---

## FASE 3 — Integración y Pruebas (Días 31–40)

| Ítem | Estado | Bloqueo |
|---|---|---|
| Conexión APIs ↔ sistema planeación | 🔴 No iniciado | Necesita tokens + Fase 2 completa |
| Pruebas de sincronización de maestros | 🔴 No iniciado | Idem |
| Pruebas funcionales end-to-end | 🔴 No iniciado | Idem |
| Ajustes y correcciones | 🔴 No iniciado | Idem |

---

## FASE 4 — Despliegue y Cierre (Días 41–45)

| Ítem | Estado |
|---|---|
| UAT con planeación, compras y logística | 🔴 No iniciado |
| Capacitación (módulo + flujo requisiciones) | 🔴 No iniciado |
| Activación servicios producción | 🔴 No iniciado |
| Documentación técnica final | 🔴 No iniciado |

---

## Lo que SÍ está listo (ventaja sobre el cronograma)

Estos elementos nos ponen adelantados en Fase 1 y parte de Fase 2:

| Componente | Archivo | Estado |
|---|---|---|
| **Match ICBF → Compras (simulacro)** | `nutricion/views/match_icbf.py` + service | ✅ Completo y funcional |
| Catálogo simulacro Siesa (`TablaIngredientesSiesa`) | `nutricion/models.py` | ✅ Con presentación, unidad, gramos |
| `EquivalenciaICBFCompras` (granularidad por menú) | `nutricion/models.py` | ✅ Con bulk + override individual |
| Rutas de entrega | `logistica/` | ✅ CRUD completo (Ruta, RutaSedes, TipoRuta) |
| CRUD Programas PAE | `planeacion/views.py` | ✅ Con optimización de logo |
| Ciclos de menús / Planificación de raciones | `planeacion/views.py` | ✅ Inicializar + edición inline |
| Arquitectura de integración documentada | `PROPUESTA_INTEGRACION_SIESA.md` | ✅ Flujo completo SC/RQI |
| Estructura JSON SC/RQI | `PROPUESTA_INTEGRACION_SIESA.md` | ✅ Encabezado + líneas de detalle |
| Reglas logísticas urbano/rural | `DOC_07_LOGISTICA_RUTAS_Y_PERIODOS.md` | ✅ Diseñadas |

---

## Lo que falta construir (trabajo interno crítico)

Ordenado por prioridad:

### Prioridad 1 — Arrancar en paralelo con Fase 1 SIESA

| # | Qué | Dónde | Por qué urgente |
|---|---|---|---|
| 1 | Modelo `ProgramacionMenus` + migración | `planeacion/models.py` | Base de toda la programación de menús |
| 2 | Modelo `Despacho` (con fecha_inicio/fecha_fin) + migración | `planeacion/models.py` | Cabecera de la orden de salida |
| 3 | Servicio `calcular_necesidades_compra()` | `planeacion/services.py` | Corazón del cálculo de compra |
| 4 | Interfaz calendario (Generar / Consultar Despachos) | `planeacion/` | UI que consume los APIs de SIESA en Fase 2.3 |

### Prioridad 2 — Arrancar cuando lleguen tokens SIESA

| # | Qué | Dónde |
|---|---|---|
| 5 | Modelos locales Siesa (`SiesaArticulo`, `SiesaBodega`, etc.) | `Api/models.py` |
| 6 | Cron job de sincronización delta | `Api/management/commands/sync_siesa.py` |
| 7 | Conector SC | `Api/services.py` |
| 8 | Conector RQI | `Api/services.py` |
| 9 | Migrar FK `EquivalenciaICBFCompras` de simulacro → `SiesaArticulo` real | `nutricion/models.py` |

### Prioridad 3 — Después de validar con SIESA

| # | Qué | Dónde |
|---|---|---|
| 10 | Campo `categoria_logistica` en artículos (abarrotes/congelados/refrigerados/fruver) | `Api/models.py` o `TablaIngredientesSiesa` |
| 11 | Campo `frecuencia_despacho` en `SedesEducativas` (estándar vs semanal consolidado) | `planeacion/models.py` o `principal/models.py` |
| 12 | Pre-validación de matches incompletos antes de despachar | `planeacion/services.py` |
| 13 | Lógica multi-RQI por categoría (urbano) vs RQI única (rural) | `planeacion/services.py` + `Api/services.py` |

---

## Ruta crítica — qué pasa si no arrancamos internamente

```
Días 1-10 (SIESA hace Fase 1)
└── Si nosotros no construimos ProgramacionMenus + Despacho + Calendario
         ↓
Día 11 (SIESA arranca Fase 2.3 "módulo planeación lado cliente")
└── No tenemos backend listo para conectar → SIESA no puede integrarse con nosotros
         ↓
Día 30 (fin Fase 2) → retraso de 2-3 semanas mínimo
```

---

## Dependencias bloqueantes al Día 1

| Bloqueante | Impacto | Responsable |
|---|---|---|
| Tokens y endpoints de prueba SIESA | Sin esto `Api/` no arranca | SIESA entrega en kickoff |
| Confirmar DANE como llave de sedes | Sin esto no se puede mapear `SedesEducativas` ↔ `SiesaProyecto` | Validar en Fase 1.4 |
| Confirmar campo "Tercero" | Afecta encabezado de SC/RQI | Validar en Fase 1.4 |
| Estructura del catálogo de artículos (código por presentación vs jerarquía) | Define si el match 1:N actual es suficiente o hay que refactorizar | Validar en Fase 1.2 |
