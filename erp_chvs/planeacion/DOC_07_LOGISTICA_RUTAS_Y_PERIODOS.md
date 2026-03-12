# Documento 7: Lógica Logística Avanzada (Periodos, Temperatura y Rutas)

Las reglas que planteas son el "corazón" del negocio logístico alimentario. Un ERP genérico fallaría aquí, pero al estar construyendo el ERP_CHVS a la medida, podemos absorber estas reglas de negocio en la capa de servicios de `planeacion` y `Api/`.

A continuación, destilamos cómo los modelos de datos y la arquitectura deben evolucionar para soportar esta realidad operativa:

---

## 1. Evolución del Concepto de "Fecha": Los Periodos de Entrega

La realidad es que no se despacha día a día. Se entregan "paquetes de días".

**Cambio en la Arquitectura (`DOC_02` actualizado):**
El modelo `Despacho` ya no puede tener un solo campo `fecha_despacho`. Debe convertirse en un **periodo**:
```python
class Despacho(models.Model):
    fecha_inicio_consumo = models.DateField(verbose_name="Fecha Inicio (Ej: Lunes)")
    fecha_fin_consumo = models.DateField(verbose_name="Fecha Fin (Ej: Miércoles)")
    # El resto queda igual: programa, ruta_entrega, estado...
```
**Impacto en "Generar Despacho" (UI):**
El usuario logístico el viernes selecciona: "Quiero generar despachos para la Ruta Centro desde el 16 de Marzo hasta el 18 de Marzo". 
El sistema busca en `ProgramacionMenus` TODOS los menús de esos tres días, suma todas sus raciones matemáticamente y las consolida en **UN solo bloque genérico de compra**.

---

## 2. Categorías Logísticas y de Almacenamiento

Para que SIESA o los operarios de la bodega sepan qué meter en un termo-King (camión refrigerado) y qué en un camión seco (estaca), necesitamos catalogar los insumos.

**Cambios en Catálogos de SIESA (o `TablaIngredientesSiesa` local):**
Cada alimento (`SiesaArticulo`) debe heredar o tener un campo `categoria_logistica`.
```python
CATEGORIAS_FRIO = [
    ('abarrotes', 'Abarrotes / Secos'),
    ('congelados', 'Congelados (Requiere TermoKing)'),
    ('refrigerados', 'Refrigerados (Lácteos/Quesos)'),
    ('fruver', 'Frutas y Verduras')
]
```
*(Nota: Esto generalmente se mapea desde SIESA si ellos usan "Líneas de Inventario" o "Clases", si no, se debe añadir el campo manualmente en ERP_CHVS cuando se descarga el catálogo de SIESA).*

---

## 3. La Matemática de Enrutamiento (Urbano vs. Rural)

Este es el proceso más complejo. El servicio en `planeacion` (el código en `services.py`) debe tomar decisiones antes de generar la orden a SIESA (SC/RQI), basándose en la tabla `logistica_rutas.TipoRuta`.

### A. Para Rutas URBANAS (División de Vehículos)
La logística urbana requiere vehículos especializados según el clima.
- **Regla del Sistema:** Cuando `planeacion` calcula los gramos de un despacho urbano (ej: 16 al 18 de marzo), **divide** la orden matemáticamente según la `categoria_logistica`.
- **Resultado en SIESA:** `Api/` NO envía 1 documento a SIESA. Envía múltiples documentos agrupados por categoría.
    - SIESA recibe: `RQI-001 (Sólo Abarrotes - Ruta Urbana 1)` -> Para el camión seco.
    - SIESA recibe: `RQI-002 (Sólo Frío/Congelado - Ruta Urbana 1)` -> Para el TermoKing.
- **Ventaja Operativa:** La bodega imprime **dos listas de recolección separadas** y cargan camiones distintos automáticamente.

### B. Para Rutas RURALES (Consolidado Único)
En zonas rurales se despacha todo en vehículos mixtos por la distancia/costo.
- **Regla del Sistema:** El sistema consolida `abarrotes`, `congelados`, `fruver` todo mezclado en la misma matemática.
- **Resultado en SIESA:** `Api/` ensambla UN (1) solo JSON gigante. SIESA crea un solo folio de RQI por ruta rural.

---

## 4. Excepciones Logísticas por Sede (El Pedido Semanal)

Tienes el caso donde una sede pide los 5 días de una vez. Técnicamente, esto "rompe" la planeación por ruta si el camión pasa por esa sede en dos periodos distintos (Viernes para lun-mie, Miércoles para jue-vie).

**Diseño de la Excepción en `SedesEducativas`:**
Añadiremos un campo a la tabla en el modelo de `planeacion` o `principal`:
```python
frecuencia_despacho = models.CharField(
    max_length=20, 
    choices=[('estandar', 'Estándar (Partida)'), ('consolidado_semanal', 'Toda la semana')],
    default='estandar'
)
```

**La Lógica en el Cerebro (Backend):**
Cuando el usuario el viernes presiona "Generar Despachos del lunes al miércoles":
1. El sistema lee las sedes de la ruta.
2. Ve que la Escuela X tiene `frecuencia = 'estandar'`. Le calcula la comida para 3 días.
3. Ve que la Escuela Y tiene `frecuencia = 'consolidado_semanal'`. 
4. El sistema dice: *"Ah, momento. Si le voy a despachar a 'Y', debo auto-sumarle el jueves y el viernes de una vez en esta RQI"*.
5. Así, el camión del viernes le lleva 5 días a la Escuela Y, y 3 días a la Escuela X.
6. Cuando el usuario pretenda crear el despacho de Jueves-Viernes el miércoles siguiente, el sistema detecta que la Escuela Y ya tiene su comida asignada (estado: despachado en esas fechas) y la **omite** de la segunda carga de camiones para evitar doble envío.

---

## 5. Resumen del Impacto

Estas reglas demuestran que estás automatizando el "Saber Hacer" (Know-How) logístico del operador del Valle dentro del código de **ERP_CHVS**:
- La Nutricionista hace recetas (`nutricion`).
- SIESA maneja plata y existencias (`Api/`).
- **Planeación (`planeacion`) asume todo el peso de pensar**: sabe cuántos días son, en qué vehículo van (caliente o frío según geografía), y a qué escuela hay que llevarle 5 días de sopeton o solo 3. Y le entrega todo "masticado" a SIESA en forma de Requisiciones de Inventario (RQI) ya separadas por tipo de camión.
