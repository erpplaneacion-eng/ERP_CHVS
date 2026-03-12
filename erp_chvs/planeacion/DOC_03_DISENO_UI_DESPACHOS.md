# Documento 3: Diseño de Interfaz (UI/UX) y Flujos de Usuario para Despachos

Para integrar exitosamente la filosofía visual de Supply Controller (visto en su módulo de Despachos) a nuestro ERP_CHVS en Django, debemos diseñar vistas (Views) y plantillas (Templates) que sean altamente interactivas usando JavaScript/AJAX, minimizando las recargas de página.

## 1. Módulo "Generar Despacho" (Creación)

**Objetivo:** Permitir al equipo de planeación generar órdenes de salida masivas agrupadas por RUTAS, sin tener que ir sede por sede.

### Diseño de la Pantalla (`generar_despacho.html`)
- **Paso 1: Parámetros Base.**
  - `Select` Programa.
  - `Rango de Fechas` (Ej: del 15 de marzo al 20 de marzo).
  - `Select` Modalidad (Ej: Almuerzo).
- **Paso 2: Selección de Rutas (El núcleo logístico).**
  - Una vez elegidos los parámetros, mediante AJAX cargamos las rutas activas para ese programa desde la tabla `logistica_rutas`.
  - El usuario puede marcar múltiples rutas mediante checkboxes. El sistema mostrará cuántas sedes incluye cada ruta seleccionada.
- **Paso 3: Menús a Despachar.**
  - El usuario selecciona qué *Ciclo de Menú* (1 al 20) aplica para esas fechas.
- **Paso 4: Botón "Generar y Previsualizar".**
  - Dispara el cálculo y crea registros pasivos (Estado: Borrador). 
  - Muestra un modal con el resumen: *"Se generarán 4 despachos, para 86 sedes, total 14,500 raciones"*.

## 2. Módulo "Consultar Despacho" (El Tablero de Control)

**Objetivo:** Adaptar el concepto del calendario visual observado en Supply Controller, convirtiéndolo en un tablero de control (Control Tower) que hable con SIESA.

### Diseño de la Pantalla (`consultar_despacho.html`)

**Sección Superior (Filtros Estándar):**
- Igual a Supply Controller: Departamento, Municipio, Programa, Modalidad.
- **NUEVO PARA ERP_CHVS:** Un filtro de "Estado de Integración SIESA" (Borrador, Aprobado, Integrado SC, Integrado RQI).

**Sección Central (El Calendario Interactivo con FullCalendar.js):**
Reemplazaremos las tablas aburridas por la librería `FullCalendar.js` (muy estándar y compatible con Bootstrap 5).
- Cada recuadro del calendario mostrará píldoras (badges) de colores que representan despachos.
    - 🟡 **Amarillo:** Despachos generados en borrador.
    - 🔵 **Azul:** Despachos aprobados sin enviar a SIESA.
    - 🟢 **Verde:** Despachos con SC/RQI ya generada en SIESA exitosamente.
    - 🔴 **Rojo:** Error de integración con SIESA.
- **Micro-interacción:** Al hacer clic en una píldora (ej: "D-45 (12 Sedes)"), se abre un *Offcanvas* lateral derecho de Bootstrap.

**Sección Lateral (Offcanvas de Detalles y Acción):**
Este panel lateral mostrará el **Qué**, **Dónde** y **SIESA**:
- **Dónde:** Ruta Norte, Vehículo asignado, Lista de 12 sedes.
- **Qué:** Menú 4 y 5. Total 1,200 raciones.
- **Botón Crítico:** *"Procesar hacia SIESA"*. Este botón es el que ejecuta la lógica del `Api/` para convertir toda esa matemática nutricional en JSON de compra/requisición.

## 3. Consideraciones Frontend (Stack Actual)
Basado en las tecnologías del proyecto (`Bootstrap 5`, `jQuery`, `SweetAlert2`):

1. **AJAX Puro:** Toda la carga en la vista de calendario debe ser vía llamadas AJAX (`/api/planeacion/despachos/mes/03-2026/`) que retornen JSON para renderizar los eventos de `FullCalendar`.
2. **Alertas no intrusivas:** Enviar a SIESA toma tiempo. Se debe usar `SweetAlert2` con *loading spinners* mientras el backend espera la respuesta `200 OK` del SC generado.
