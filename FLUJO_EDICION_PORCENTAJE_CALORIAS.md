# 📊 Flujo de Actualización Dinámica al Editar % de Calorías

## 🎯 Escenario: Usuario edita el input de "% Calorías" de 25% a 50%

---

## 🔄 FLUJO COMPLETO DE CAMBIOS DINÁMICOS

### **PASO 1: Evento Inicial**
```javascript
// Ubicación: menus_avanzado.js líneas 1297-1313
$(document).on('input change', '.porcentaje-input', function() {
    const nutriente = 'calorias';  // Obtenido del data-nutriente
    const porcentajeDeseado = 50;  // Nuevo valor ingresado

    calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado);
});
```

**Input afectado:**
```html
<input class="porcentaje-input"
       data-nivel="0"
       data-nutriente="calorias"
       value="25" → value="50">  ✏️ CAMBIO MANUAL
```

---

### **PASO 2: Cálculo del Objetivo**
```javascript
// Ubicación: menus_avanzado.js líneas 1433-1437

// Datos de ejemplo:
const requerimientoNecesario = 800;  // kcal máximo permitido (de la BD)
const porcentajeValido = 50;         // Validado entre 0-100
const valorObjetivo = (50 * 800) / 100 = 400 kcal;  // Objetivo a alcanzar
```

**Logs en consola:**
```
[calorias] Objetivo: 400.00 (50% de 800)
```

---

### **PASO 3: Análisis de Ingredientes Actuales**
```javascript
// Ubicación: menus_avanzado.js líneas 1443-1491

// Recolecta TODOS los ingredientes que aportan calorías:
ingredientesData = [
    {
        nombre: "Arroz blanco",
        pesoActual: 100g,
        nutrientePor100g: 130 kcal/100g,
        valorActual: (130 * 100) / 100 = 130 kcal
    },
    {
        nombre: "Pollo pechuga",
        pesoActual: 80g,
        nutrientePor100g: 165 kcal/100g,
        valorActual: (165 * 80) / 100 = 132 kcal
    },
    {
        nombre: "Zanahoria",
        pesoActual: 50g,
        nutrientePor100g: 41 kcal/100g,
        valorActual: (41 * 50) / 100 = 20.5 kcal
    }
];

valorActualTotal = 130 + 132 + 20.5 = 282.5 kcal
```

---

### **PASO 4: Cálculo del Factor de Escala Proporcional**
```javascript
// Ubicación: menus_avanzado.js líneas 1508-1510

const diferencia = 400 - 282.5 = 117.5 kcal  // Necesitamos aumentar

// Factor de escala para mantener proporciones:
const factorEscala = 400 / 282.5 = 1.416

// Esto significa: multiplicar TODOS los pesos por 1.416
```

**Logs en consola:**
```
Diferencia a ajustar: 117.50
```

---

### **PASO 5: Ajuste Proporcional de TODOS los Pesos**
```javascript
// Ubicación: menus_avanzado.js líneas 1513-1522

// Ingrediente 1: Arroz blanco
nuevoPeso = 100 * 1.416 = 141.6g
pesoInput.val("141.6")  ✅ ACTUALIZADO

// Ingrediente 2: Pollo pechuga
nuevoPeso = 80 * 1.416 = 113.3g
pesoInput.val("113.3")  ✅ ACTUALIZADO

// Ingrediente 3: Zanahoria
nuevoPeso = 50 * 1.416 = 70.8g
pesoInput.val("70.8")  ✅ ACTUALIZADO
```

**Logs en consola:**
```
  - Ingrediente [0-0]: 100.0g → 141.6g
  - Ingrediente [0-1]: 80.0g → 113.3g
  - Ingrediente [0-2]: 50.0g → 70.8g
✓ Ajuste proporcional completado para calorias_kcal (factor: 1.416)
```

**Campos HTML actualizados:**
```html
<!-- Arroz blanco -->
<input class="peso-input" value="100" → value="141.6">  ✏️ CAMBIO 1

<!-- Pollo pechuga -->
<input class="peso-input" value="80" → value="113.3">   ✏️ CAMBIO 2

<!-- Zanahoria -->
<input class="peso-input" value="50" → value="70.8">    ✏️ CAMBIO 3
```

---

### **PASO 6: Trigger en Cascada de Eventos `change`**
```javascript
// Ubicación: menus_avanzado.js líneas 1537-1541

// Dispara el evento change en cada input con delay escalonado
ingredientesData.forEach((ing, index) => {
    setTimeout(() => {
        ing.pesoInput.trigger('change');  // ⚡ DISPARA EVENTO
    }, index * 10);  // 0ms, 10ms, 20ms...
});
```

**Resultado:** Cada ingrediente dispara su propio evento `.peso-input change`

---

### **PASO 7: Recalcular Peso Bruto de cada Ingrediente**
```javascript
// Ubicación: menus_avanzado.js líneas 1261-1264
// Se ejecuta 3 veces (una por ingrediente)

// INGREDIENTE 1: Arroz blanco
pesoNeto = 141.6g
parteComestible = 100%
pesoBruto = (141.6 * 100) / 100 = 141.6g
$('#bruto-0-0-0').text("142")  ✏️ CAMBIO 4

// INGREDIENTE 2: Pollo pechuga
pesoNeto = 113.3g
parteComestible = 85%  (se pierde piel, grasa, huesos)
pesoBruto = (113.3 * 100) / 85 = 133.3g
$('#bruto-0-0-1').text("133")  ✏️ CAMBIO 5

// INGREDIENTE 3: Zanahoria
pesoNeto = 70.8g
parteComestible = 95%  (se pierde cáscara)
pesoBruto = (70.8 * 100) / 95 = 74.5g
$('#bruto-0-0-2').text("75")  ✏️ CAMBIO 6
```

**Campos HTML actualizados:**
```html
<!-- Arroz blanco -->
<td id="bruto-0-0-0">100 → 142</td>  ✏️ PESO BRUTO

<!-- Pollo pechuga -->
<td id="bruto-0-0-1">94 → 133</td>   ✏️ PESO BRUTO

<!-- Zanahoria -->
<td id="bruto-0-0-2">53 → 75</td>    ✏️ PESO BRUTO
```

---

### **PASO 8: Recalcular TODOS los Nutrientes de cada Ingrediente**
```javascript
// Ubicación: menus_avanzado.js líneas 1266-1288
// Se ejecuta para CADA ingrediente (3 veces)

// INGREDIENTE 1: Arroz blanco (141.6g)
factor = 141.6 / 100 = 1.416
calorias = 130 * 1.416 = 184.1 kcal  ✏️
proteina = 2.7 * 1.416 = 3.8g        ✏️
grasa = 0.3 * 1.416 = 0.4g           ✏️
cho = 28.2 * 1.416 = 39.9g           ✏️
calcio = 10 * 1.416 = 14.2mg         ✏️
hierro = 0.8 * 1.416 = 1.1mg         ✏️
sodio = 1 * 1.416 = 1.4mg            ✏️

// Actualiza 7 celdas por ingrediente:
$('#cal-0-0-0').text("184.1")   ✏️ CAMBIO 7
$('#prot-0-0-0').text("3.8")    ✏️ CAMBIO 8
$('#grasa-0-0-0').text("0.4")   ✏️ CAMBIO 9
$('#cho-0-0-0').text("39.9")    ✏️ CAMBIO 10
$('#calcio-0-0-0').text("14.2") ✏️ CAMBIO 11
$('#hierro-0-0-0').text("1.1")  ✏️ CAMBIO 12
$('#sodio-0-0-0').text("1.4")   ✏️ CAMBIO 13

// ... Lo mismo para Pollo pechuga (7 celdas)
// ... Lo mismo para Zanahoria (7 celdas)
// TOTAL: 21 celdas de nutrientes actualizadas
```

**Campos HTML actualizados (ejemplo de 1 ingrediente):**
```html
<!-- Arroz blanco - TODOS sus nutrientes se recalculan -->
<td id="cal-0-0-0">130.0 → 184.1</td>      ✏️ Calorías
<td id="prot-0-0-0">2.7 → 3.8</td>         ✏️ Proteína
<td id="grasa-0-0-0">0.3 → 0.4</td>        ✏️ Grasa
<td id="cho-0-0-0">28.2 → 39.9</td>        ✏️ CHO
<td id="calcio-0-0-0">10.0 → 14.2</td>     ✏️ Calcio
<td id="hierro-0-0-0">0.8 → 1.1</td>       ✏️ Hierro
<td id="sodio-0-0-0">1.0 → 1.4</td>        ✏️ Sodio
```

---

### **PASO 9: Recalcular Totales del Nivel**
```javascript
// Ubicación: menus_avanzado.js líneas 1347-1397

// Suma TODOS los ingredientes del nivel:
totalCalorias = 184.1 + 186.9 + 29.0 = 400.0 kcal  ✅ ¡Objetivo alcanzado!
totalProteina = 3.8 + 31.3 + 0.6 = 35.7g
totalGrasa = 0.4 + 3.1 + 0.1 = 3.6g
totalCho = 39.9 + 0.0 + 6.8 = 46.7g
totalCalcio = 14.2 + 5.7 + 23.6 = 43.5mg
totalHierro = 1.1 + 0.4 + 0.2 = 1.7mg
totalSodio = 1.4 + 69.4 + 50.7 = 121.5mg

// Actualiza las tarjetas de totales (7 tarjetas):
$('#nivel-0-calorias').text("400.0 Kcal")  ✏️ CAMBIO 22
$('#nivel-0-proteina').text("35.7 g")      ✏️ CAMBIO 23
$('#nivel-0-grasa').text("3.6 g")          ✏️ CAMBIO 24
$('#nivel-0-cho').text("46.7 g")           ✏️ CAMBIO 25
$('#nivel-0-calcio').text("43.5 mg")       ✏️ CAMBIO 26
$('#nivel-0-hierro').text("1.7 mg")        ✏️ CAMBIO 27
$('#nivel-0-sodio').text("121.5 mg")       ✏️ CAMBIO 28
```

**Campos HTML actualizados:**
```html
<!-- Sección de Totales del Nivel -->
<div class="total-mini">
    <span>Calorías:</span>
    <span id="nivel-0-calorias">282.5 Kcal → 400.0 Kcal</span>  ✏️
</div>
<div class="total-mini">
    <span>Proteína:</span>
    <span id="nivel-0-proteina">25.2 g → 35.7 g</span>          ✏️
</div>
<!-- ... 5 totales más actualizados ... -->
```

---

### **PASO 10: Recalcular TODOS los Porcentajes de Adecuación**
```javascript
// Ubicación: menus_avanzado.js líneas 1546-1598

// Recalcula los 7 nutrientes (aunque solo editaste calorías):
const requerimientos = {
    calorias_kcal: 800,
    proteina_g: 60,
    grasa_g: 45,
    cho_g: 100,
    calcio_mg: 400,
    hierro_mg: 10,
    sodio_mg: 800
};

// CALORIAS:
porcentaje = min((400.0 / 800) * 100, 100) = 50.0%  ✅ ¡Exacto!
estado = 'aceptable'  // 50% está en rango 35.1-70% (amarillo)
$('#nivel-0-calorias-pct').val("50.0")  ✏️ CAMBIO 29 (ya tenía 50, se confirma)
$('.adecuacion-mini[nutriente=calorias]').attr('data-estado', 'aceptable')  ✏️ CAMBIO 30

// PROTEINA:
porcentaje = min((35.7 / 60) * 100, 100) = 59.5%
estado = 'aceptable'  // 59.5% está en rango 35.1-70% (amarillo)
$('#nivel-0-proteina-pct').val("59.5")  ✏️ CAMBIO 31

// GRASA:
porcentaje = min((3.6 / 45) * 100, 100) = 8.0%
estado = 'optimo'  // 8.0% está en rango 0-35% (verde)
$('#nivel-0-grasa-pct').val("8.0")  ✏️ CAMBIO 32

// CHO:
porcentaje = min((46.7 / 100) * 100, 100) = 46.7%
estado = 'aceptable'  // 46.7% está en rango 35.1-70% (amarillo)
$('#nivel-0-cho-pct').val("46.7")  ✏️ CAMBIO 33

// CALCIO:
porcentaje = min((43.5 / 400) * 100, 100) = 10.9%
estado = 'optimo'  // 10.9% está en rango 0-35% (verde)
$('#nivel-0-calcio-pct').val("10.9")  ✏️ CAMBIO 34

// HIERRO:
porcentaje = min((1.7 / 10) * 100, 100) = 17.0%
estado = 'optimo'  // 17.0% está en rango 0-35% (verde)
$('#nivel-0-hierro-pct').val("17.0")  ✏️ CAMBIO 35

// SODIO:
porcentaje = min((121.5 / 800) * 100, 100) = 15.2%
estado = 'optimo'  // 15.2% está en rango 0-35% (verde)
$('#nivel-0-sodio-pct').val("15.2")  ✏️ CAMBIO 36
```

**Campos HTML actualizados:**
```html
<!-- Inputs de % Adecuación (7 inputs) -->
<input id="nivel-0-calorias-pct" value="25.0" → value="50.0" data-estado="aceptable"> ✏️
<input id="nivel-0-proteina-pct" value="42.0" → value="59.5" data-estado="aceptable"> ✏️
<input id="nivel-0-grasa-pct" value="5.6" → value="8.0" data-estado="optimo">       ✏️
<input id="nivel-0-cho-pct" value="33.0" → value="46.7" data-estado="aceptable">    ✏️
<input id="nivel-0-calcio-pct" value="7.7" → value="10.9" data-estado="optimo">     ✏️
<input id="nivel-0-hierro-pct" value="12.0" → value="17.0" data-estado="optimo">    ✏️
<input id="nivel-0-sodio-pct" value="10.7" → value="15.2" data-estado="optimo">     ✏️
```

---

### **PASO 11: Actualizar Colores de Estado**
```javascript
// Ubicación: menus_avanzado.js líneas 1582, 1595

// Se actualizan los atributos data-estado en:
// - 7 tarjetas .adecuacion-mini (inputs de %)
// - 7 tarjetas .total-mini (totales)

// Los colores CSS se aplican automáticamente vía CSS:
.total-mini[data-estado="optimo"] { border-color: #28a745; background: verde; }
.total-mini[data-estado="aceptable"] { border-color: #ffc107; background: amarillo; }
.total-mini[data-estado="alto"] { border-color: #dc3545; background: rojo; }
```

**Cambios visuales:**
```html
<!-- ANTES -->
<div class="total-mini" data-estado="optimo">Calorías: 282.5 Kcal</div>  🟢

<!-- DESPUÉS -->
<div class="total-mini" data-estado="aceptable">Calorías: 400.0 Kcal</div>  🟡 CAMBIO DE COLOR
```

---

## 📊 RESUMEN TOTAL DE CAMBIOS DINÁMICOS

### **Cuando editas el % de Calorías de 25% a 50%, se actualizan:**

| # | Campo Actualizado | Cantidad | Descripción |
|---|-------------------|----------|-------------|
| 1 | **Pesos Neto** | 3 inputs | Cada ingrediente (proporcional) |
| 2 | **Pesos Bruto** | 3 celdas | Recalculados por parte comestible |
| 3 | **Calorías** | 3 celdas | Por ingrediente |
| 4 | **Proteína** | 3 celdas | Por ingrediente |
| 5 | **Grasa** | 3 celdas | Por ingrediente |
| 6 | **CHO** | 3 celdas | Por ingrediente |
| 7 | **Calcio** | 3 celdas | Por ingrediente |
| 8 | **Hierro** | 3 celdas | Por ingrediente |
| 9 | **Sodio** | 3 celdas | Por ingrediente |
| 10 | **Total Calorías** | 1 span | Suma de todos |
| 11 | **Total Proteína** | 1 span | Suma de todos |
| 12 | **Total Grasa** | 1 span | Suma de todos |
| 13 | **Total CHO** | 1 span | Suma de todos |
| 14 | **Total Calcio** | 1 span | Suma de todos |
| 15 | **Total Hierro** | 1 span | Suma de todos |
| 16 | **Total Sodio** | 1 span | Suma de todos |
| 17 | **% Calorías** | 1 input | Confirmado en 50% |
| 18 | **% Proteína** | 1 input | Recalculado |
| 19 | **% Grasa** | 1 input | Recalculado |
| 20 | **% CHO** | 1 input | Recalculado |
| 21 | **% Calcio** | 1 input | Recalculado |
| 22 | **% Hierro** | 1 input | Recalculado |
| 23 | **% Sodio** | 1 input | Recalculado |
| 24 | **Estados (colores)** | 14 divs | 7 totales + 7 adecuaciones |

### **TOTAL: ~57 ELEMENTOS HTML ACTUALIZADOS DINÁMICAMENTE** 🚀

---

## ⚡ PERFORMANCE

### **Tiempo de Ejecución Estimado:**
- **PASO 1-4:** ~5ms (cálculos en memoria)
- **PASO 5:** ~10ms (actualizar 3 inputs)
- **PASO 6-8:** ~60ms (3 × 20ms delay + cálculos)
- **PASO 9-11:** ~15ms (actualizar DOM)

**TOTAL: ~90ms** ⚡ Imperceptible para el usuario

### **Optimizaciones Implementadas:**
✅ Delays escalonados (10ms) para evitar bloqueo del UI
✅ Prevención de loops infinitos con flags `actualizandoPorPeso/Porcentaje`
✅ Cálculos en memoria antes de actualizar DOM
✅ Uso de selectores eficientes con IDs

---

## 🎨 EFECTO VISUAL PARA EL USUARIO

1. **Input editado:** Cambia de 25 → 50
2. **Animación sutil:** Todos los pesos neto aumentan (141.6g, 113.3g, 70.8g)
3. **Cascada:** Pesos bruto se actualizan
4. **Tabla nutrientes:** Todos los valores cambian simultáneamente
5. **Totales:** Se actualizan con los nuevos valores
6. **Porcentajes:** Todos se recalculan (aunque solo editaste 1)
7. **Colores:** Cambian si cruzan umbrales (35%, 70%)

**Resultado:** Interfaz totalmente sincronizada en tiempo real ✨

---

## 🔍 VALIDACIONES AUTOMÁTICAS

Durante todo el proceso:
- ✅ Porcentajes limitados entre 0-100%
- ✅ Pesos validados >= 0
- ✅ Parte comestible entre 1-100%
- ✅ División por cero prevenida
- ✅ NaN convertidos a 0

---

## 🐛 DEBUGGING

Para ver todo el flujo en consola:
```javascript
// Abrir DevTools (F12) y ejecutar:
localStorage.setItem('debug', 'true');

// Luego edita cualquier % y verás:
[calorias] Objetivo: 400.00 (50% de 800)
Diferencia a ajustar: 117.50
  - Ingrediente [0-0]: 100.0g → 141.6g
  - Ingrediente [0-1]: 80.0g → 113.3g
  - Ingrediente [0-2]: 50.0g → 70.8g
✓ Ajuste proporcional completado para calorias_kcal (factor: 1.416)
Recalculando porcentajes para nivel: 0 totales: {...}
```

---

## 💡 CONCLUSIÓN

Al editar **UN SOLO CAMPO** (% de Calorías), el sistema actualiza dinámicamente:
- ✅ Pesos de TODOS los ingredientes (proporcionalmente)
- ✅ Pesos brutos (según parte comestible)
- ✅ TODOS los nutrientes (no solo calorías)
- ✅ Totales de los 7 nutrientes
- ✅ Porcentajes de los 7 nutrientes
- ✅ Colores de estado

**Es una sincronización bidireccional completa y en tiempo real** 🎯
