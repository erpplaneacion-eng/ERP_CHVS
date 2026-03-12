# Documento 11: Orquestación de Compras y Factores de Conversión

Hasta ahora habíamos mirado "hacia adelante" (hacia la escuela y el camión). Ahora miraremos **"hacia atrás"** (hacia los proveedores y la chequera).

El operador no le pide a Roa "50.000 gramos de arroz blanco crudo". Le pide "Bultos de 50 Kg".
¿Cómo el sistema **ERP_CHVS** orquesta esta traducción masiva para generar las **Órdenes de Compra en SIESA**?

Este es el simulacro del "Cerebro Matemático" de Compras.

---

## 🏗️ 1. Los Tres Diccionarios del Sistema (Parametrización)

Para que la magia funcione, ERP_CHVS usa 3 "llaves" almacenadas en la base de datos:

1.  **El Menú Nutricional:** Dice: *"1 ración de Pollo (Nivel Primaria) = 50 gramos netos"*.
2.  **Tabla de Desechos (TCAC ICBF):** Dice: *"El Pollo con hueso tiene un Factor de Desecho del 30%"*. (Pierde peso al quitarle huesos y grasa).
3.  **El Match SIESA (`mapeo_nutricion.json` / `Planeacion`):** Dice: *"El Alimento ICBF 'Pollo crudo' equivale al SKU-SIESA 'P-1002 Pollo Entero Congelado'. Su Presentación Comercial es 'Canastilla de 20 Kilos'."*

---

## 🧮 2. Simulacro Paso a Paso: La Compra Semanal

Es **Jueves 12 de Marzo, 8:00 AM**.
El Gerente de Compras se sienta en ERP_CHVS. Necesita comprar la proteína para los Despachos de toda la próxima semana (16 al 20 de Marzo) en todo el Valle del Cauca (Cali y Yumbo).

### Paso 2.1: El Consolidado Demográfico por Niveles
El usuario selecciona en pantalla: **Generar Proyección de Compras (16 al 20 Mar)**.
- El sistema agrupa automáticamente las raciones en TODAS las escuelas de la ruta seleccionada, pero **separando por nivel escolar** porque los gramos exigidos por el ICBF varían según la edad:
  - **Primaria:** 12.000 raciones semanales donde se consume el Menú de Pollo.
  - **Secundaria / Media:** 8.000 raciones donde se consume el Menú de Pollo.
- Total de raciones a servir: **20.000**.

### Paso 2.2: Cálculo del Gramaje NETO (Cruce Nivel Escolar vs Menú ICBF)
Aquí el orquestador no multiplica un solo valor, cruza cada ración con su nivel correspondiente en la minuta:
- **Cálculo Primaria:** 12.000 raciones × 50 gramos (Pollo Primaria) = **600.000 Gramos Netos**.
- **Cálculo Secundaria:** 8.000 raciones × 70 gramos (Pollo Secundaria) = **560.000 Gramos Netos**.
- **Gran Total (Cálculo Agrupado):** 600.000 + 560.000 = **1.160.000 Gramos Netos** (1.160 Kilos).

### Paso 2.3: La Bofetada de la Realidad (Factor de Desecho / Merma de Cocina)
Si solo compras 1.160 Kilos de pollo, a la ecónoma le quedarán mucho menos después de pelarlo y quitarle los huesos (mermará). Los niños no comerán la grama exigida y el ICBF multa al Consorcio.
- ERP_CHVS consulta la Tabla ICBF: Factor de Desecho del Pollo = 30%.
- Fórmula universal de Peso Bruto: `Peso Neto / (1 - Factor de Desecho)`.
- Cálculo: `1.160 Kilos / (1 - 0.30)` = **1.657,1 Kilos Brutos de Pollo a Comprar**.
- *Nota:* ERP_CHVS acaba de calcular el peso exacto combinando edades y resguardando al operador de multas.

### Paso 2.4: El Factor de Conversión Comercial (Hablándole a SIESA)
Pero en la vida real nadie le vende "1.657,1 Kilos" a un operador logístico. El proveedor (ej. MacPollo) vende en unidades cerradas, por ejemplo: *Canastillas de 20 Kilos*.

Aquí entra a jugar la integración que documentamos en la Fase 1 (`Nutrición <-> SIESA`):
- El sistema toma el requerimiento teórico: `1.657,1 Kilos totales`.
- Consulta la Presentación de SIESA (`mapeo_nutricion`): `Valor Venta = 20 Kilos / Canastilla`.
- Operación de Conversión: `1.657,1 / 20 = 82.85 Canastillas`.

### Paso 2.5: El Redondeo Logístico (Funciones de Tejado)
El proveedor no te va a despachar 0.85 de una canastilla.
- ERP_CHVS aplica matemáticamente `math.ceil()` (redondeo siempre hacia arriba por seguridad alimenticia).
- **Resultado Final de Necesidad: 83 Canastillas de Pollo**.

---

## 🚀 3. La Orquestación Final hacia SIESA (El JSON)

Con los números listos y redondeados en unidades comerciales válidas, el módulo de `Planeacion` ensambla una **Orden de Compra / Requisición Consolidada** y dispara la API hacia SIESA.

El JSON que viaja a SIESA por debajo (usando tu módulo `Api/`) se ve así:

```json
{
  "documento_siesa": "orden_compra",
  "fecha": "2026-03-12",
  "bodega_destino": "Cali_Principal",
  "detalle": [
    {
      "sku_siesa": "P-1002",
      "descripcion": "Pollo Entero Congelado 20Kg",
      "cantidad_comercial": 72,
      "unidad_medida": "UN",
      "gramos_teoricos_referencia": 1428500
    },
    {
      "sku_siesa": "A-5001",
      "descripcion": "Arroz Blanco Roa - Bulto 50Kg",
      "cantidad_comercial": 41,
      "unidad_medida": "BLT",
      "gramos_teoricos_referencia": 2040000
    }
  ]
}
```

## 4. El Valor Oculto del Simulacro

A SIESA (el software financiero) este análisis matemático no le importa. Él solo asienta contablemente la compra de 72 canastillas a MacPollo y genera la cuenta por pagar.

El verdadero **Oro Tecnológico** reside en **ERP_CHVS**:
El ERP_CHVS acaba de condensar en 2 segundos lo que a 5 ingenieros de alimentos les tomaba 3 días en tablas dinámicas de Excel llenas de errores. Y lo más importante: mantuvo la trazabilidad.

Mañana, cuando la interventoría del ICBF pregunte: *"¿Por qué compró 72 canastillas de pollo para 20.000 niños?"*, ERP_CHVS puede imprimir un reporte histórico instantáneo que dice:
*   Niños: 20.000
*   Menú Base: 50 gr
*   Desecho Técnico: 30%
*   Conversión Prov: 20 Kg/Unidad.
*   **Decisión:** Matemática pura, cero sobrecostos.
