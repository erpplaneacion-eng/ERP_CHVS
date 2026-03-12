# Documento 4: Consideraciones Estratégicas y de Integración (ERP_CHVS)

Este documento sirve como advertencia y guía técnica sobre los puntos críticos donde el nuevo módulo de Despachos de `planeacion` se toca con las otras "piezas del reloj" del ERP_CHVS.

## 1. El Cruce Crítico: Nutrición + SIESA

El módulo de Despachos no puede funcionar sin el **"Match ICBF → Compras"** (documentado en `PLAN_MATCH_ICBF_COMPRAS.md`). 

### ¿Qué pasa cuando el usuario hace clic en "Procesar hacia SIESA"?
1. El backend (`planeacion.services`) debe buscar el *Menú* asignado a ese día en ese *Despacho*.
2. Extrae todos los ingredientes (`nutricion_tabla_preparacion_ingredientes`) y sus *gramajes* (Ej: Leche 200g, Arroz 50g).
3. Multiplica por el número de *raciones* de esa sede.
4. **Acá interviene el Match:** Va a `nutricion_equivalencia_icbf_compras` y pregunta: *"¿El alimento 'Leche Cruda ICBF' a qué código de artículo de SIESA equivale para el consorcio de Cali?"*.
5. Toma ese código (Ej: `ART-1002`) y divide el total de gramos entre el *contenido* de la presentación (Ej: Bolsa 1000g).
6. **Resultado:** SIESA necesita despachar 2 Bolsas de Leche.

**Riesgo Estratégico:** Si la Nutricionista no ha completado la tabla de matches (`EquivalenciaICBFCompras`) para los ingredientes del menú 4, el cálculo matemático se rompe. El sistema de Despachos debe incluir una **Pre-validación** que alerte: *"No se puede generar este despacho porque los siguientes alimentos ICBF no tienen un producto SIESA asociado"*.

## 2. Dependencia Directa de `logistica`

Como se estipula en la arquitectura, **`planeacion` no crea rutas**. 
Depende totalmente de la app `logistica`, específicamente de la tabla `logistica_ruta_sedes`. 

**Regla de Negocio:** La generación masiva de despachos se debe hacer a través del filtro de "Rutas". El operador logístico primero debe asegurar que todas las 168 sedes de Cali estén mapeadas a una ruta y a un vehículo en el módulo `logistica`. Si una sede no tiene ruta, se quedará huérfana y los niños no recibirán alimento. `planeacion` debe tener una alerta de **"Sedes sin Ruta Asignada"**.

## 3. Manejo de Errores de la API SIESA (`Api/`)

El modelo `Despacho` propuesto tiene el estado `siesa_integrado`. Pero la red falla y las APIs rechazan payloads.

*   **Estrategia Transaccional:** El llamado asíncrono a SIESA (para la SC o RQI) debe manejarse en un bloque `try-except` sólido.
*   Si la API de SIESA (`SIESA ERP SAAS`) responde con un error `500` o `400 Bad Request` (por ejemplo, porque un código de artículo o centro de costos no existe), el estado del `Despacho` debe cambiar a `Error Integración`.
*   El usuario en el Tablero de Control (Calendario) verá la "píldora" en **ROJO** y al hacer clic, el panel lateral debe mostrar el mensaje literal que devolvió SIESA (ej: *"Articulo no hallado en maestro"*).
*   Debe existir un botón de **Re-intentar**.

## 4. Evolución: Proyecciones a Futuro

Lo que Supply Controller llama "Generar Proyección" podemos interpretarlo como la capacidad de simular la necesidad de compras de todo un mes o trimestre *antes* de firmar los despachos reales. 
Dado que tenemos el módulo `nutricion` y los cronogramas escolares, `planeacion/services.py` puede generar un archivo Excel (o reporte tabular) agregando toda la matemática de raciones vs. SIESA para entregar a Finanzas un "Presupuesto Operativo Semanal" anticipado.
