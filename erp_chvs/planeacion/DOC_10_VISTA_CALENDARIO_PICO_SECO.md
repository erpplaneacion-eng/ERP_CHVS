# Documento 10: Vista UI del Calendario (Caso: Sede Pico Seco)

Para entender cómo el operador logístico percibirá el simulacro de la **Sede Pico Seco** (donde se despachan 5 días de comida el mismo viernes, mientras que al resto de la ruta solo se le despachan 3), debemos recordar que la UI principal es el **Calendario Interactivo** (descrito en `DOC_03`).

Aquí te muestro cómo el sistema renderizará esta complejidad logística de forma visual, limpia y sin enredar al usuario.

---

## 1. El Tablero Mensual (Marzo 2026)

Filtros Activos en Panatalla:
- **Ruta:** Ruta Rural Montaña
- **Mes:** Marzo 2026

### 🗓️ Lógica de Renderizado en Calendario (FullCalendar)
El calendario NO dibuja cajas por sede (sería un caos visual si hay 40 sedes). El calendario dibuja "Píldoras" (Badges) correspondientes a la entidad `Despacho`.

Sin embargo, como *Pico Seco* rompió la regla y se extendió hasta el viernes cubriendo días que el Despacho principal no cubría, **ERP_CHVS debe segmentar el evento visualmente**.

---
### 📅 Así se vería la cuadrícula de la semana (Lunes 16 al Viernes 20):

```text
  LUNES 16               MARTES 17               MIÉRCOLES 18            JUEVES 19               VIERNES 20
┌──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│                      │                      │                      │                      │                      │
│ [🟢 SC-103: Rura...] │ [🟢 SC-103]          │ [🟢 SC-103]          │ [🔵 SC-104: Rura...] │ [🔵 SC-104]          │
│                      │                      │                      │                      │                      │
│ ──────────────────── │ ──────────────────── │ ──────────────────── │ ──────────────────── │ ──────────────────── │
│                      │                      │                      │                      │                      │
│ [🟢 SC-103 (Ext.. ]  │ [🟢 SC-103 (Ext)]    │ [🟢 SC-103 (Ext)]    │ [🟢 SC-103 (Ext)]    │ [🟢 SC-103 (Ext)]    │
│                      │                      │                      │                      │                      │
└──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

### ¿Qué significa este dibujo? Explicación de los Eventos:

#### Evento Superior: El Despacho Estándar de la Ruta
La primera píldora cruzando Lunes-Miércoles es el Despacho General `SC-103`.
*   **Color:** `Verde 🟢` (Significa que SIESA aprobó la RQI).
*   **Comportamiento UI:** Si el usuario le hace **clic a la píldora superior**, se abre el panel lateral (Offcanvas) diciendo:
    > **Detalle del Despacho:**
    > - **Periodo:** 16 al 18 de Marzo.
    > - **Sedes (4):** El Mirador, La Esperanza, Bella Vista, San Juan.
    > - **Ojo:** *No incluye a Pico Seco.*

El Jueves-Viernes superior vemos el despacho `SC-104`.
*   **Color:** `Azul 🔵` (Significa que está Aprobado en Planeación, pero aún no viaja a SIESA).
*   **Sedes:** Las mismas 4 de arriba.

#### Evento Inferior: La Extensión de Pico Seco
El sistema es inteligente. Sabe que dentro del mismo ID de Despacho (`SC-103` físico del viernes), hubo una sola sede a la que se le extendió el periodo de consumo.
El calendario dibuja una **segunda píldora alargada** que cruza de Lunes a Viernes de par en par.
*   **Comportamiento UI:** Al hacerle **clic a la píldora inferior** (`Ext`), el panel lateral dice:
    > **Excepciones Consolidadas del Despacho SC-103:**
    > - **Periodo:** 16 al 20 de Marzo (5 días).
    > - **Sedes (1):** Pico Seco.
    > - **Razón:** Frecuencia Semanal Parametrizada.

---

## 2. Prevención de Errores (Lo más importante de UI)

### El Error Común: ¿Qué pasa cuando llegue el Miércoles y quieran planear Jueves y Viernes?
Si el operador no tiene este calendario, el Miércoles 18 intentaría generar el despacho para las 5 escuelas de la montaña. ¡Y le mandaría doble comida el Jueves/Viernes a Pico Seco! Mermas, pudrición e investigaciones de la Contraloría.

### La Solución de la Interfaz ERP_CHVS:
Cuando el operador entre a "Generar Despacho" el miércoles y seleccione "Ruta Rural Montaña" + Fechas "19 y 20", una alerta bloqueante azul cielo (`Alert-Info` de Bootstrap) aparecerá en la parte superior:

> ℹ️ **Información de Enrutamiento:**
> La sede **Pico Seco** perteneciente a esta ruta ha sido excluida del cálculo porque en el periodo seleccionado (19-20 de Marzo) ya cuenta con **raciones activas generadas en un despacho consolidado anterior (SC-103)**.

---

## 3. Resumen Visto desde la Perspectiva del SIESA vs Planeación

*   A **SIESA** del Área Contable no le importa este diseño de UI. SIESA en su sistema en Cali solo recibe un JSON que dice "Saquen X bultos de comida y cobrenselo a estos 5 centros de costo". SIESA ve todo esto como una sola transacción gigante.
*   Para **ERP_CHVS**, este calendario y los carteles de advertencia son los que protegen a la empresa operadora de cometer errores humanos mandando doble remesa por problemas geográficos. La UI divide lo que el backend mezcló, para hacerle la vida fácil al humano que lee la pantalla.
