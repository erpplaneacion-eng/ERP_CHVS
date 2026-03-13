# AGENTE_CONTEXTO.md — Módulo Contabilidad

Este archivo es el "cerebro" para un agente de IA que deba continuar, mantener o extender este módulo
sin haber participado en su construcción original.

---

## 1. Por qué existe este módulo

**Problema de negocio**: Los líderes de área (quienes contratan servicios y adquieren materias primas)
generaban facturas en papel sin ningún sistema de trazabilidad. Compras verificaba contra documentos
físicos de forma manual y sin registro. Contabilidad hacía una segunda revisión sin evidencia del proceso.
Gerencia no tenía visibilidad del estado de ningún registro.

**Lo que resuelve**: Un flujo digital con estados, fechas automáticas y checklist de verificación que
garantiza:
- Los líderes registran facturas digitalmente (sin adjuntos, los documentos se entregan en físico).
- Compras verifica contra físicos con un checklist configurable y puede devolver o aprobar.
- Contabilidad hace segunda revisión y puede observar o cerrar definitivamente.
- Gerencia tiene trazabilidad completa con métricas de tiempo y devoluciones.

---

## 2. Los 4 actores y sus responsabilidades exactas

| Actor | Grupo Django | Responsabilidades |
|-------|-------------|------------------|
| **Líder** | `LIDER_CONTABLE` | Crea registros, agrega facturas, envía a Compras, corrige y reenvía si fue devuelto |
| **Compras** | `COMPRAS_CONTABLE` | Confirma recepción física, completa checklist, devuelve (con motivo) o aprueba |
| **Contabilidad** | `CONTABILIDAD` | Revisa registros aprobados por Compras, aprueba+cierra o envía observaciones |
| **Gerencia** | `GERENCIA` | Solo lectura: dashboard con KPIs, filtros y trazabilidad completa |

Un usuario de `ADMINISTRACION` puede hacer todo lo de todos los actores.

---

## 3. El flujo de estados completo

```
BORRADOR ──(enviar)──► ENVIADO
    ▲                      │
    │               (confirmar_recepcion)
    │                      │
    │              EN_REVISION_COMPRAS ──(devolver)──► DEVUELTO_COMPRAS
    │                      │                                  │
    │               (aprobar_compras)                    (enviar, reenvío)
    │                      │                                  │
    └──────────────────────┘──────────────────────────────────┘
                           ▼
                  APROBADO_COMPRAS
                     /          \
         (observar)              (aprobar_contabilidad)
               /                          \
    OBSERVADO_CONTABILIDAD              CERRADO
               │
    (responder_observacion, por Compras)
               │
        APROBADO_COMPRAS (de vuelta)
```

### Transiciones válidas y actor ejecutor

| Desde | Hacia | Acción | Actor |
|-------|-------|--------|-------|
| BORRADOR | ENVIADO | `enviar()` | Líder |
| DEVUELTO_COMPRAS | ENVIADO | `enviar()` (reenvío) | Líder |
| ENVIADO | EN_REVISION_COMPRAS | `confirmar_recepcion()` | Compras |
| EN_REVISION_COMPRAS | DEVUELTO_COMPRAS | `devolver_compras()` | Compras |
| EN_REVISION_COMPRAS | APROBADO_COMPRAS | `aprobar_compras()` | Compras |
| APROBADO_COMPRAS | OBSERVADO_CONTABILIDAD | `observar_contabilidad()` | Contabilidad |
| APROBADO_COMPRAS | CERRADO | `aprobar_contabilidad()` | Contabilidad |
| OBSERVADO_CONTABILIDAD | APROBADO_COMPRAS | `responder_observacion()` | Compras |

---

## 4. Por qué no hay archivos adjuntos

Los documentos físicos (facturas originales, remisiones, soportes) se entregan en mano al área de
Compras. No se escanean ni se suben al sistema porque:
1. El ERP no tiene sistema de almacenamiento de archivos robusto para documentos de peso considerable.
2. Los procesos internos de la empresa ya contemplan la entrega física como evidencia formal.
3. Simplifica enormemente la implementación (sin `FileField`, sin gestión de Cloudinary para documentos).
4. La confirmación de recepción (`confirmar_recepcion()`) es el mecanismo digital que certifica que
   los físicos llegaron a Compras.

**Consecuencia de diseño**: `Factura` NO tiene `FileField` en ningún campo. Si en el futuro se decide
agregar adjuntos, ver `planeacion/models.py::Programa.logo` como referencia del patrón Cloudinary.

---

## 5. Por qué las fechas son automáticas

Todas las fechas de transición se setean desde `ContabilidadService._transicion()` usando `timezone.now()`
en el momento exacto de la acción. Nunca desde la vista ni desde el frontend. Esto garantiza:

1. **Trazabilidad real**: Las fechas reflejan cuándo ocurrió exactamente cada paso, no cuándo alguien
   decidió ingresarlas manualmente.
2. **No manipulables**: Un usuario no puede antedatar o postdatar una acción para cumplir SLAs ficticios.
3. **Métricas confiables**: El dashboard de gerencia puede calcular tiempos reales entre etapas.

---

## 6. Descripción de cada modelo

### `RegistroContable` (tabla: `contabilidad_registros`)
El objeto central del flujo. Representa un lote de facturas de un mismo tipo y período.
- `tipo`: SERVICIOS o MATERIAS_PRIMAS — determina qué ítems del checklist aplican.
- `periodo_mes/periodo_ano`: Mes y año de las facturas incluidas.
- `lider`: FK al User que creó el registro. PROTECT (no se puede eliminar un usuario con registros).
- `estado`: Estado actual en el flujo (ver sección 3).
- `descripcion`: Texto libre opcional del líder para dar contexto.
- Campos `fecha_*`: Seteados automáticamente por el servicio en cada transición. Null hasta que ocurre.
- `valor_total` (property): Suma de `Factura.valor` de todas las facturas del registro.
- `total_documentos` (property): Count de facturas del registro.

### `Factura` (tabla: `contabilidad_facturas`)
Representa una factura individual dentro de un registro. Sin adjuntos.
- `registro`: FK al RegistroContable padre. CASCADE — si se elimina el registro, se eliminan sus facturas.
- `numero_factura`, `proveedor`, `concepto`: Datos descriptivos de la factura.
- `valor`: Monto de la factura en pesos colombianos.
- `fecha_factura`: Fecha que aparece en la factura física (ingresada por el líder, tipo DateField).
- `fecha_carga`: Cuándo se registró en el sistema (auto_now_add, no modificable).

### `ItemChecklist` (tabla: `contabilidad_items_checklist`)
Catálogo de ítems de verificación que Compras debe revisar físicamente.
- `tipo_proceso`: SERVICIOS, MATERIAS_PRIMAS o AMBOS — filtra qué ítems aplican según el tipo del registro.
- `obligatorio`: Si es True, no se puede aprobar con este ítem en PENDIENTE.
- `activo`: Permite desactivar ítems sin eliminarlos (historial intacto).
- `orden`: Para ordenar el checklist de forma lógica.

### `VerificacionChecklist` (tabla: `contabilidad_verificaciones`)
Instancia de un ItemChecklist para un RegistroContable específico.
- `unique_together: (registro, item)`: Cada ítem aparece una sola vez por registro.
- `estado`: PENDIENTE (no revisado), OK, NO_OK, NA (no aplica para este caso).
- `verificado_por`: El usuario de Compras que marcó este ítem.
- `fecha_verificacion`: Cuándo se marcó (seteado por `guardar_checklist()`).

### `HistorialEstado` (tabla: `contabilidad_historial`)
Log inmutable de todas las transiciones del registro. No se actualiza ni se elimina.
- `accion`: Código de la acción ejecutada (ver choices en el modelo).
- `estado_anterior/estado_nuevo`: Snapshot del estado antes y después.
- `comentario`: Obligatorio para devoluciones y observaciones, opcional en otros casos.
- `fecha`: auto_now_add — exactamente cuando ocurrió la transición.

---

## 7. Descripción de cada método de ContabilidadService

| Método | Valida | Efecto |
|--------|--------|--------|
| `crear_registro()` | tipo, mes, año | Crea en BORRADOR + entrada CREACION en historial |
| `agregar_factura()` | Estado editable | Crea Factura |
| `eliminar_factura()` | Estado editable | Elimina Factura |
| `editar_descripcion()` | Estado editable | Actualiza campo descripcion |
| `enviar()` | BORRADOR o DEVUELTO, min 1 factura | → ENVIADO, fecha_envio o fecha_reenvio |
| `confirmar_recepcion()` | ENVIADO | → EN_REVISION_COMPRAS, fecha_entrega_fisica o fecha_reentrega_fisica, llama inicializar_checklist() |
| `devolver_compras()` | EN_REVISION_COMPRAS, comentario obligatorio | → DEVUELTO_COMPRAS, fecha_devolucion_compras |
| `aprobar_compras()` | EN_REVISION o OBSERVADO, sin PENDIENTE obligatorios | → APROBADO_COMPRAS, fecha_aprobacion_compras o fecha_respuesta_compras |
| `inicializar_checklist()` | (interno) | bulk_create VerificacionChecklist, ignore_conflicts=True |
| `guardar_checklist()` | (interno) | Actualiza estado/obs de cada VerificacionChecklist |
| `observar_contabilidad()` | APROBADO_COMPRAS, comentario obligatorio | → OBSERVADO_CONTABILIDAD, fecha_inicio_rev_contabilidad + fecha_observacion |
| `aprobar_contabilidad()` | APROBADO_COMPRAS | → CERRADO, fecha_inicio_rev + fecha_aprobacion + fecha_cierre |
| `responder_observacion()` | OBSERVADO_CONTABILIDAD, comentario obligatorio | → APROBADO_COMPRAS, fecha_respuesta_compras |
| `get_bandeja_compras()` | — | QS: ENVIADO + EN_REVISION_COMPRAS + OBSERVADO_CONTABILIDAD |
| `get_bandeja_contabilidad()` | — | QS: APROBADO_COMPRAS |
| `get_dashboard_data(filtros)` | — | Dict con conteos, lista de registros con métricas, lista de líderes |

**Estados editables** (para agregar/eliminar facturas y editar descripción):
```python
ESTADOS_EDITABLES = ('BORRADOR', 'DEVUELTO_COMPRAS')
```

---

## 8. Los grupos Django y qué puede hacer cada uno

| Grupo | Ver sus registros | Ver todos | Bandeja Compras | Bandeja Contabilidad | Dashboard Gerencia |
|-------|:-----------------:|:---------:|:---------------:|:--------------------:|:-----------------:|
| `LIDER_CONTABLE` | ✓ | — | — | — | — |
| `COMPRAS_CONTABLE` | — | Bandeja | ✓ | — | — |
| `CONTABILIDAD` | — | Bandeja | — | ✓ | — |
| `GERENCIA` | — | ✓ | — | — | ✓ |
| `ADMINISTRACION` | ✓ | ✓ | ✓ | ✓ | ✓ |

Los grupos se crean con `python manage.py setup_groups`.

---

## 9. Convenciones CSS

Colores por estado (en `static/css/modules/contabilidad.css`):

| Estado | Color | Clase CSS |
|--------|-------|-----------|
| BORRADOR | Gris `#6c757d` | `.estado-badge-borrador` |
| ENVIADO | Azul `#1e3a8a` | `.estado-badge-enviado` |
| EN_REVISION_COMPRAS | Celeste `#0ea5e9` | `.estado-badge-enrevisioncompras` |
| DEVUELTO_COMPRAS | Naranja `#d97706` | `.estado-badge-devueltocompras` |
| APROBADO_COMPRAS | Teal `#0d9488` | `.estado-badge-aprobadocompras` |
| OBSERVADO_CONTABILIDAD | Amarillo `#ca8a04` | `.estado-badge-observadocontabilidad` |
| APROBADO_CONTABILIDAD | Verde claro `#16a34a` | `.estado-badge-aprobadocontabilidad` |
| CERRADO | Verde oscuro `#14532d` con fondo `#dcfce7` | `.estado-badge-cerrado` |

**Nota sobre los nombres de clase**: El estado se convierte con `.toLowerCase().replace(/_/g, '')` en JS,
por eso `EN_REVISION_COMPRAS` → `.estado-badge-enrevisioncompras`. En templates Django se usa el
filtro `{{ registro.estado|lower|cut:'_' }}`.

Clases especiales:
- `.banner-devolucion`: Naranja, mostrado al líder cuando el estado es DEVUELTO_COMPRAS.
- `.banner-observacion`: Amarillo, mostrado a Compras cuando el estado es OBSERVADO_CONTABILIDAD.
- `.modal-header-warning`: Fondo amarillo `#ca8a04`, para modales de devolución y observación.
- `.modal-header-danger`: Fondo rojo, para confirmación de eliminación.
- `.historial-timeline`: Lista cronológica de entradas de HistorialEstado.
- `.checklist-table`: Tabla de verificación de ítems.

---

## 10. Qué archivos modificar según el cambio

### Si se agrega un nuevo estado
1. `contabilidad/models.py` → `RegistroContable.ESTADO_CHOICES` y `HistorialEstado.ACCION_CHOICES`
2. `contabilidad/services.py` → Agregar método de transición
3. `contabilidad/views.py` → Agregar API endpoint y verificación de rol
4. `contabilidad/urls.py` → Registrar la nueva URL
5. `static/css/modules/contabilidad.css` → Agregar clase `.estado-badge-{nuevo_estado}`
6. Templates relevantes → Mostrar el nuevo estado/botón
7. JS relevante → Manejar el nuevo flujo
8. `contabilidad/migrations/` → Nueva migración

### Si se agrega un nuevo actor
1. `principal/middleware.py` → Agregar el grupo a `group_permissions`
2. `principal/management/commands/setup_groups.py` → Agregar al diccionario
3. `contabilidad/views.py` → Actualizar `_tiene_rol()` donde corresponda
4. `templates/base.html` → Agregar el grupo al `{% if user|has_group:"..." %}` del nav
5. `templates/contabilidad/index.html` → Agregar card según el rol

### Si se agrega un nuevo ítem de checklist
Solo desde el admin de Django: `/admin/contabilidad/itemchecklist/add/`. No requiere código.

---

## 11. Métricas que calcula el dashboard de gerencia

`ContabilidadService.get_dashboard_data(filtros)` retorna:

1. **Conteos por estado**: Para cada estado en `RegistroContable.ESTADO_CHOICES`, cuenta cuántos
   registros existen en ese estado (sin filtros aplicados, siempre son totales globales).

2. **Lista de registros con métricas**:
   - `duracion_dias`: `(fecha_cierre or timezone.now()) - fecha_creacion` en días.
   - `num_devoluciones`: Cuenta entradas en `HistorialEstado` con `accion='DEVOLUCION_COMPRAS'`.
   - `valor_total`: Suma de facturas (vía property del modelo).
   - `total_documentos`: Count de facturas.

3. **Lista de líderes**: Para poblar el select de filtro (solo usuarios que tienen al menos un registro).

Los filtros disponibles son: `lider_id`, `periodo_mes`, `periodo_ano`, `tipo`, `estado`.

---

## 12. Decisiones de diseño tomadas y por qué

### HistorialEstado es inmutable
No tiene métodos de actualización. Una vez creado, nunca se modifica. Esto garantiza que el historial
sea una fuente de verdad confiable para auditorías. Si en el futuro se necesita "corregir" una entrada,
la práctica correcta es agregar una nueva entrada con la corrección, no modificar la existente.

### El checklist tiene catálogo separado (`ItemChecklist`)
Los ítems no están hardcodeados en el código. El admin de Django puede activar, desactivar, reordenar
y agregar ítems sin necesidad de deployar cambios. Esto permite adaptar el checklist a requisitos
regulatorios cambiantes sin involucrar a desarrollo.

### `ignore_conflicts=True` en `inicializar_checklist()`
Permite llamar al método varias veces de forma idempotente (ej: si el registro vuelve a EN_REVISION
tras una devolución). Solo crea ítems que no existan aún.

### `aprobar_contabilidad()` cierra en un solo paso
Se decidió fusionar APROBADO_CONTABILIDAD y CERRADO en una sola transición porque en el proceso real
no existe un estado intermedio entre "Contabilidad aprueba" y "el registro se archiva". Separar los dos
pasos sería burocracia digital innecesaria. El historial registra ambas acciones de forma secuencial
para que quede la trazabilidad.

### Las vistas no contienen lógica de negocio
Toda validación de negocio está en `ContabilidadService`. Las vistas solo parsean el request,
llaman al servicio y formatean la respuesta. Esto facilita testing y mantenimiento.

### `_tiene_rol(user, *roles)` en views.py
Helper local (no global) que verifica pertenencia a grupos. Siempre incluye `ADMINISTRACION` de forma
implícita. Los superusers siempre tienen acceso completo.
