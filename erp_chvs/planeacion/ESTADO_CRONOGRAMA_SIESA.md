# Estado vs. Cronograma SIESA — ERP_CHVS

## Resumen ejecutivo

| Fase | Período | Estado ERP_CHVS |
|---|---|---|
| Fase 1 — Levantamiento | Días 1–10 | ✅ **Completa** — arquitectura documentada, maestros implementados |
| Fase 2 — Diseño y Desarrollo | Días 11–30 | 🟡 **Parcial** — sincronización y frontend listos; SC/RQI y módulo planeación pendientes |
| Fase 3 — Integración y Pruebas | Días 31–40 | 🔴 **Bloqueada** — depende de endpoints POST SIESA + Fase 2 completa |
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

| Maestro | Estado | Modelo real en código |
|---|---|---|
| Ítems / Plan de Cuentas | ✅ **Implementado** | `SiesaItem` (`payload = JSONField()` — SIESA aún vacío) |
| Bodegas / Ubicaciones | ✅ **Implementado** | `SiesaUbicacion` — 33 registros |
| Centros de Operación | ✅ **Implementado** | `SiesaCentroOperacion` — 1 registro |
| Instalaciones | ✅ **Implementado** | `SiesaInstalacion` — 3 registros |
| Proyectos y centros de costo | ✅ **Implementado** | `SiesaProyecto` (1.718 reg.) + `SiesaCentroCosto` (73 reg.) |
| Unidades de Negocio | ✅ **Implementado** | `SiesaUnidadNegocio` — 13 registros |
| Conceptos y motivos | ✅ **Implementado** | `SiesaConcepto` (38 reg.) + `SiesaMotivo` (89 reg.) |
| Tipos de Documento | ✅ **Implementado** | `SiesaTipoDocumento` — 90 registros |
| Solicitantes / Terceros | ✅ **Implementado** | `SiesaSolicitante` (`payload = JSONField()` — SIESA aún vacío) |

> **Nota de nomenclatura**: los campos de los modelos reales preservan la nomenclatura original de SIESA (`f<num>_<campo>`, e.g. `f107_id`, `f107_descripcion`). Los nombres propuestos en `PROPUESTA_INTEGRACION_SIESA.md` (como `SiesaArticulo`, `SiesaBodega`, `SiesaCO`) eran nombres de diseño previo a recibir las credenciales. Ver mapeo completo en `PROPUESTA_INTEGRACION_SIESA.md` — sección "Mapeo nombres propuestos → implementados".

### 1.3 Definición técnica de integración

| Ítem | Estado | Detalle |
|---|---|---|
| Arquitectura (API REST con token) | ✅ Definida | Tablas locales PostgreSQL + full sync vía management command |
| Frecuencia de sincronización | 🟡 Full sync por ahora | Delta sync pendiente de que SIESA exponga filtro por fecha |
| Definición estructura JSON | ✅ Parcial | Encabezado y líneas de SC/RQI documentados. Pendiente validar contra diccionario SIESA. |

### 1.4 Validaciones de negocio

| Ítem | Estado | Detalle |
|---|---|---|
| Definición campo "Tercero" | ❓ Abierto | ¿Es el proveedor del alimento o el operador (CHVS)? Sin confirmar. |
| Reglas para costos (promedio unitario) | ✅ Contemplado | Campo previsto en diseño de `SiesaArticulo` (pendiente de datos reales en `SiesaItem`) |
| Alcance de terceros (proveedores/clientes) | ❓ Abierto | Pendiente confirmar con SIESA |

**Preguntas críticas para llevar al Kickoff:**
1. ¿Cada presentación de artículo tiene código propio en SIESA, o hay jerarquía artículo-variante?
2. ¿El DANE es la llave de cruce suficiente entre `SedesEducativas` y `SiesaProyecto`?
3. ¿El SAAS soporta webhooks o solo polling?
4. ¿Quién es el "Tercero" en una SC/RQI del PAE?
5. ¿Los tokens de prueba se entregan en el kickoff?

---

## FASE 2 — Diseño y Desarrollo (Días 11–30)

### 2.1 Diseño de servicios (APIs)

| Ítem | Estado | Responsable |
|---|---|---|
| Endpoint de maestros (GET catálogos) | ✅ **Recibidos** | SIESA entregó — ya sincronizados |
| Endpoint de requisiciones (RQI POST) | 🔴 No entregado | SIESA construye — pendiente |
| Endpoint de solicitudes de compra (SC POST) | 🔴 No entregado | SIESA construye — pendiente |

### 2.2 Desarrollo de sincronización de maestros

| Ítem | Estado | Archivo ERP_CHVS |
|---|---|---|
| Cliente HTTP (Basic Auth, retry, timeout) | ✅ **Implementado** | `Api/services/siesa_client.py` — clase `SiesaClient` |
| Servicio unificado de consulta | ✅ **Implementado** | `Api/services/sync_service.py` — `sincronizar_todo()` / `sincronizar_catalogo()` |
| Mappers JSON → modelo | ✅ **Implementado** | `Api/services/mappers.py` — `map_*()` por catálogo |
| Modelos locales (11 catálogos + SyncLog) | ✅ **Implementado** | `Api/models.py` — campos 1:1 con JSON SIESA real |
| Sincronización full sync | ✅ **Implementado** | `python manage.py sync_siesa [--catalogo X] [--dry-run]` |
| Exploración de endpoints crudos | ✅ **Implementado** | `python manage.py explorar_siesa [--endpoint X] [--pretty]` |
| Registro de historial de sync | ✅ **Implementado** | Modelo `SiesaSyncLog` — tabla `siesa_sync_log` |
| Delta sync (filtro por fecha) | 🔴 Pendiente | Esperando que SIESA exponga filtro por fecha en sus endpoints |
| **Frontend de catálogos (módulo SIESA)** | ✅ **Implementado** | `/siesa/` — índice + 11 listas read-only con DataTables. Solo `ADMINISTRACION`. |

### 2.3 Desarrollo módulo planeación (lado cliente) — ⚠️ RIESGO ALTO

| Ítem | Estado | Archivo ERP_CHVS | Urgencia |
|---|---|---|---|
| Consumo de APIs SIESA (integrar catálogo real) | 🔴 No iniciado | `planeacion/views.py` | Después de tokens POST |
| **Modelo `ProgramacionMenus`** | 🔴 **No creado** | `planeacion/models.py` | 🔥 Arrancar YA |
| **Interfaz de programación de menús** (calendario Despachos) | 🔴 **No iniciada** | `planeacion/` nuevo | 🔥 Arrancar YA |
| **Modelo `Despacho`** (con rango fecha inicio/fin) | 🔴 **No creado** | `planeacion/models.py` | 🔥 Arrancar YA |
| Interfaz de selección de ítems (catálogo Siesa) | 🔴 No iniciada | Depende de tokens POST | Después de tokens |
| Manejo de unidades y presentaciones | ✅ Base lista | Match ICBF ya implementado | — |

### 2.4 Desarrollo de generación de documentos

| Ítem | Estado | Archivo ERP_CHVS |
|---|---|---|
| Creación de solicitudes de compra (SC) | 🔴 No iniciado | `Api/` — bloqueado por endpoint POST SIESA |
| Creación de requisiciones (RQI) | 🔴 No iniciado | `Api/` — bloqueado por endpoint POST SIESA |
| Estructura de envío a SIESA | ✅ Diseñada | Definida en `PROPUESTA_INTEGRACION_SIESA.md` |
| Servicio `calcular_necesidades_compra()` | 🔴 No iniciado | `planeacion/services.py` |
| Lógica urbano (multi-RQI por categoría) vs rural (RQI única) | ✅ Diseñada | `DOC_07_LOGISTICA_RUTAS_Y_PERIODOS.md` |
| Pre-validación de matches incompletos | ✅ Diseñada | `DOC_04_CONSIDERACIONES_ESTRATEGICAS.md` |

### 2.5 Ajustes estructurales internos

| Ítem | Estado | Detalle |
|---|---|---|
| Cruce sedes/proyectos | 🟡 Parcial | `SedesEducativas.cod_dane` ↔ `SiesaProyecto.f107_id_referencia` — confirmar con SIESA que es la llave de cruce suficiente |
| Campo `categoria_logistica` en artículos | 🔴 No iniciado | Depende de estructura real de `SiesaItem` cuando SIESA lo llene |
| Campo `frecuencia_despacho` en sedes | 🔴 No iniciado | Diseñado en `DOC_07`. Necesario para sedes con pedido semanal consolidado |

---

## FASE 3 — Integración y Pruebas (Días 31–40)

| Ítem | Estado | Bloqueo |
|---|---|---|
| Conexión APIs POST ↔ sistema planeación | 🔴 No iniciado | Necesita endpoints POST SIESA + Fase 2 completa |
| Pruebas de sincronización de maestros | 🟡 Parcial | GET ya funciona; POST pendiente |
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
| **11 modelos locales SIESA + SyncLog** | `Api/models.py` | ✅ Campos 1:1 con JSON SIESA real |
| **Cliente HTTP + sync service + mappers** | `Api/services/` | ✅ `SiesaClient`, `sincronizar_todo()`, `map_*()` |
| **Comando sync_siesa** | `Api/management/commands/sync_siesa.py` | ✅ Full sync con `--catalogo` y `--dry-run` |
| **Comando explorar_siesa** | `Api/management/commands/explorar_siesa.py` | ✅ Inspección de endpoints crudos |
| **Frontend catálogos SIESA** | `Api/views.py` + `templates/Api/` | ✅ `/siesa/` — índice + 11 listas read-only |

---

## Lo que falta construir (trabajo interno crítico)

### Prioridad 1 — Arrancar ya (no dependen de SIESA)

| # | Qué | Dónde | Por qué urgente |
|---|---|---|---|
| 1 | Modelo `ProgramacionMenus` + migración | `planeacion/models.py` | Base de toda la programación de menús |
| 2 | Modelo `Despacho` (con fecha_inicio/fecha_fin) + migración | `planeacion/models.py` | Cabecera de la orden de salida |
| 3 | Servicio `calcular_necesidades_compra()` | `planeacion/services.py` | Corazón del cálculo de compra |
| 4 | Interfaz calendario (Generar / Consultar Despachos) | `planeacion/` | UI que consume los APIs de SIESA en Fase 2.3 |

### Prioridad 2 — Arrancar cuando lleguen endpoints POST SIESA

| # | Qué | Dónde |
|---|---|---|
| 5 | Conector SC | `Api/services/` |
| 6 | Conector RQI | `Api/services/` |
| 7 | Migrar FK `EquivalenciaICBFCompras` de simulacro → `SiesaItem` real | `nutricion/models.py` |

### Prioridad 3 — Después de validar con SIESA

| # | Qué | Dónde |
|---|---|---|
| 8 | Campo `categoria_logistica` en artículos (abarrotes/congelados/refrigerados/fruver) | Depende de estructura real de `SiesaItem` |
| 9 | Campo `frecuencia_despacho` en `SedesEducativas` | `planeacion/models.py` o `principal/models.py` |
| 10 | Pre-validación de matches incompletos antes de despachar | `planeacion/services.py` |
| 11 | Lógica multi-RQI por categoría (urbano) vs RQI única (rural) | `planeacion/services.py` + `Api/services/` |
| 12 | Delta sync cuando SIESA exponga filtro por fecha | `Api/services/siesa_client.py` + `SiesaSyncLog` |

---

## Dependencias bloqueantes actuales

| Bloqueante | Impacto | Responsable |
|---|---|---|
| Endpoints POST SC/RQI de SIESA | Sin esto los conectores no arrancan | SIESA |
| Llenar `SiesaItem` y `SiesaSolicitante` en SIESA | Sin esto el match ICBF no puede apuntar a artículos reales | SIESA |
| Confirmar DANE como llave de sedes | Sin esto no se puede mapear `SedesEducativas` ↔ `SiesaProyecto` | Validar en Fase 1.4 |
| Confirmar campo "Tercero" | Afecta encabezado de SC/RQI | Validar en Fase 1.4 |
| Estructura real del catálogo de artículos | Define si el match 1:N actual es suficiente o hay que refactorizar | Cuando SIESA llene `ITEMS` |
