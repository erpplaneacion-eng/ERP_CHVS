# Documento 5: Simulacro - "Un Día en la Vida de un Despacho"

Para validar que la arquitectura de `planeacion` propuesta en los documentos anteriores realmente funciona en conjunto con `nutricion` y `logistica`, haremos un **simulacro textual y matemático paso a paso**.

---

## ESCENARIO BASE

**El Entorno:**
- **Programa:** Consorcio Alimentando Cali 2026.
- **Fecha a despachar:** Lunes 16 de Marzo de 2026.
- **Ruta a despachar:** Ruta Norte-01 (Tiene 2 sedes educativas asignadas en `logistica_ruta_sedes`).
- **Modalidad:** Almuerzo Jornada Única.
- **Menú asignado para ese día:** Menú #1 (Sopa de Arroz con Carne).

### 1. Estado Inicial de las Bases de Datos

Antes de que Planeación haga un solo clic, esto es lo que **ya existe** en el sistema:

| Módulo | Datos Existentes |
| :--- | :--- |
| **Logística** | `Ruta Norte-01` tiene asociadas 2 sedes: <br>1. Institución Educativa A (Requiere 150 raciones) <br>2. Institución Educativa B (Requiere 200 raciones) <br>*(Total raciones Ruta Norte-01: 350 raciones)* |
| **Nutrición** | Alimento ICBF: `Arroz blanco crudo`. <br>Gramaje en Menú #1: `50 gramos` por ración. |
| **Nutrición (Match)** | `Arroz blanco crudo` = `Arroz Doña Pepa Bulto 50kg (50,000g)` en código SIESA (`ART-0023`). |

---

## EL FLUJO OPERATIVO (El Simulacro)

### Paso 1: Interfaz de Usuario (El operador logístico)

El operador entra a la pantalla **"Generar Despacho"** (`DOC_03_DISENO_UI_DESPACHOS.md`).
1. Selecciona el Programa: *Consorcio Cali 2026*.
2. Selecciona la Fecha: *16 de Marzo*.
3. Selecciona la Modalidad: *Almuerzo Jornada Única*.
4. Selecciona el Ciclo de Menú: *Ciclo 1*.
5. El sistema le muestra una lista de checkboxes con rutas. El usuario marca chulo (✔) en **"Ruta Norte-01"**.
6. Hace clic en: **[ Generar y Previsualizar ]**

---

### Paso 2: Creación del "Borrador" en Base de Datos

El backend (`planeacion.views` / `planeacion.services`) toma acción inmediata:

1.  **Crea el Encabezado (`Despacho`):**
    ```json
    {
      "id": 1001,
      "fecha": "2026-03-16",
      "programa": "Consorcio Cali 2026",
      "ruta": "Ruta Norte-01",
      "estado": "borrador"
    }
    ```

2.  **Crea el Detalle por Sede (`ProgramacionMenus`):**
    El sistema va a `logistica_ruta_sedes`, ve que la Ruta Norte-01 tiene 2 escuelas y las "baja" al Despacho:
    ```json
    [
      {
        "id_despacho": 1001,
        "sede": "I.E. A",
        "menu": "Menú #1",
        "raciones": 150
      },
      {
        "id_despacho": 1001,
        "sede": "I.E. B",
        "menu": "Menú #1",
        "raciones": 200
      }
    ]
    ```
*(El despacho está en estado Borrador. Se ve de color 🟡 AMARILLO en el calendario del tablero de control).*

---

### Paso 3: Aprobación y Cálculos (El Cerebro Matemático)

El operador revisa en el calendario visual, ve el Despacho 1001 en amarillo, le hace clic y en el panel derecho presiona el botón: **[ Procesar hacia SIESA ]**.

Aquí es donde se detona la lógica de `calcular_necesidades_compra()`:

1.  **La Suma Total de Raciones:** 
    El sistema suma todas las raciones del Despacho 1001.
    `150 raciones (I.E. A) + 200 raciones (I.E. B) = 350 raciones totales.`

2.  **La Necesidad Nutricional (Gramos):**
    Busca los ingredientes del Menú #1. Tomemos el arroz como ejemplo (50g por ración).
    `350 raciones * 50 gramos = 17,500 gramos de arroz blanco crudo requeridos.`

3.  **El Match ICBF -> SIESA (Unidades Físicas):**
    Busca la equivalencia de "Arroz blanco crudo". Sabemos que el nutricionista lo asoció al producto SIESA `ART-0023` (Bulto de 50,000 gramos).
    *Fórmula:* `Gramos Requeridos / Gramos de la Presentación SIESA`
    `17,500 g / 50,000 g = 0.35 Bultos`

    *(Nota: Aquí `planeacion` y SIESA deben acordar la regla comercial de redondeo. Supongamos que SIESA maneja fracciones o se redondea siempre al techo, ej: 1 Bulto. O si es 'Bolsa de 1000g' serían 17.5 bolsas -> redondeo a 18 bolsas).*

---

### Paso 4: El Envío (Notificando a SIESA)

Con la matemática lista, el módulo llama internamente a la aplicación `Api/`.

`Api/` ensambla el JSON gigantesco que la documentación en `PROPUESTA_INTEGRACION_SIESA.md` describió. Este JSON dice algo como (versión simplificada):

```json
{
  "CentroOperacion": "Cali",
  "TipoDocumento": "RQI",
  "Ruta": "Ruta Norte-01",
  "Lineas": [
    {
      "Articulo": "ART-0023", // El código real en SIESA para el Arroz
      "Cantidad": 1, 
      "BodegaSalida": "Bodega Principal Yumbo",
      "ProyectoDane": "76001000..." // Centrado del costo a la primera escuela
    }
    // ... más ingredientes (carne, papa, jugo)
  ]
}
```

### Paso 5: El Final Feliz (O el Manejo del Error)

`Api/` hace el `POST` a la nube de SIESA.
*   **Si SIESA responde OK (200):** Devuelve un número de folio `RQI-9945`.
    El registro de nuestro `Despacho 1001` se actualiza:
    `estado = "siesa_integrado"`, `numero_rqi_siesa = "RQI-9945"`.
    La píldora en el calendario del operador cambia a 🟢 VERDE. Fin del proceso.

*   **Si SIESA responde Error (400):** Por ejemplo, el `ART-0023` fue desactivado ayer en contabilidad.
    El registro del `Despacho 1001` se actualiza:
    `estado = "error"`. 
    La píldora cambia a 🔴 ROJO. El operador logístico lo ve, revisa el mensaje, llama a almacén para que arreglen SIESA, y oprime luego el botón "Reintentar Despacho".
