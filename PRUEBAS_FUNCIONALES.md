# 🧪 Guía de Pruebas Funcionales - Módulo de Nutrición

## 📋 Checklist de Verificación

### ✅ Pre-requisitos
- [ ] Servidor Django ejecutándose
- [ ] Base de datos con datos de prueba
- [ ] Navegador con DevTools abierto (F12)
- [ ] Al menos 1 menú con preparaciones e ingredientes configurado

---

## 🎯 PRUEBA 1: Edición de Peso Neto (Unidireccional)

### Objetivo
Verificar que al cambiar el peso neto de un ingrediente, se actualicen automáticamente:
- Peso bruto
- Todos los nutrientes del ingrediente
- Totales del nivel
- Porcentajes de adecuación

### Pasos
1. Navegar a: Nutrición → Gestión de Menús
2. Seleccionar un municipio, programa y modalidad
3. Abrir un menú con preparaciones
4. Clic en "Ver Análisis Nutricional"
5. Expandir un nivel escolar
6. Localizar un ingrediente (ej: Arroz blanco)
7. Anotar valores actuales:
   ```
   Peso Neto:    _______ g
   Peso Bruto:   _______ g
   Calorías:     _______ kcal
   % Calorías:   _______ %
   ```

8. **Cambiar el peso neto** (ej: de 100g a 150g)

### Resultados Esperados ✅

| Campo | Comportamiento Esperado |
|-------|------------------------|
| **Peso Neto** | Cambia a 150g |
| **Peso Bruto** | Se recalcula automáticamente según parte comestible |
| **Calorías** | Aumenta proporcionalmente (1.5x si pasó de 100 a 150) |
| **Proteína** | Aumenta proporcionalmente |
| **Grasa** | Aumenta proporcionalmente |
| **CHO** | Aumenta proporcionalmente |
| **Calcio** | Aumenta proporcionalmente |
| **Hierro** | Aumenta proporcionalmente |
| **Sodio** | Aumenta proporcionalmente |
| **Total Calorías** | Aumenta (suma de todos) |
| **% Calorías** | Se recalcula automáticamente |
| **Colores** | Pueden cambiar si cruzan umbrales (35%, 70%) |

### Ejemplo Numérico
```
Ingrediente: Arroz blanco (130 kcal/100g, 100% comestible)

ANTES:
- Peso Neto: 100g
- Peso Bruto: (100 × 100) ÷ 100 = 100g
- Calorías: (130 × 100) ÷ 100 = 130 kcal

DESPUÉS (cambio a 150g):
- Peso Neto: 150g
- Peso Bruto: (150 × 100) ÷ 100 = 150g  ✅
- Calorías: (130 × 150) ÷ 100 = 195 kcal  ✅
```

### Verificación en Consola
```javascript
// Deberías ver logs como:
Peso actualizado: { nivelIndex: 0, prepIndex: 0, ingIndex: 0, pesoNeto: 150 }
Recalculando porcentajes para nivel: 0 totales: {...}
```

---

## 🔄 PRUEBA 2: Edición de % Adecuación (Bidireccional) - MEJORA IMPLEMENTADA

### Objetivo
Verificar que al cambiar el % de adecuación de un nutriente:
- TODOS los pesos de ingredientes se ajusten proporcionalmente
- Se mantengan las proporciones de la receta
- Se actualicen todos los campos derivados

### Pasos
1. En el mismo análisis nutricional
2. Localizar la sección "% de Adecuación"
3. Anotar valores actuales de TODOS los ingredientes:
   ```
   Ingrediente 1: _______ g
   Ingrediente 2: _______ g
   Ingrediente 3: _______ g
   % Calorías actual: _______ %
   ```

4. Calcular las proporciones:
   ```
   Proporción = Ing1:Ing2:Ing3
   Ejemplo: 100:80:50 = 2:1.6:1
   ```

5. **Cambiar el % de Calorías** (ej: de 25% a 50%)

### Resultados Esperados ✅

| Campo | Comportamiento Esperado |
|-------|------------------------|
| **Peso Ingrediente 1** | Cambia proporcionalmente (factor ~2.0) |
| **Peso Ingrediente 2** | Cambia con el MISMO factor |
| **Peso Ingrediente 3** | Cambia con el MISMO factor |
| **Proporciones** | SE MANTIENEN (ej: 200:160:100 = 2:1.6:1) ✅ |
| **Pesos Bruto** | Se recalculan para cada ingrediente |
| **TODOS los nutrientes** | Se recalculan para cada ingrediente |
| **Totales** | Se actualizan (7 nutrientes) |
| **% de TODOS los nutrientes** | Se recalculan (no solo calorías) |
| **% Calorías** | Llega exactamente al valor deseado (50%) |

### Ejemplo Numérico Detallado
```
Estado Inicial:
- Ingrediente 1 (Arroz): 100g → 130 kcal
- Ingrediente 2 (Pollo): 80g → 132 kcal
- Ingrediente 3 (Zanahoria): 50g → 20.5 kcal
- Total: 282.5 kcal
- Requerimiento: 800 kcal
- % Actual: (282.5 ÷ 800) × 100 = 35.3%
- Proporciones: 100:80:50 = 2:1.6:1

Cambio: Editar % a 50%

Cálculos:
1. Objetivo: (50 × 800) ÷ 100 = 400 kcal
2. Factor: 400 ÷ 282.5 = 1.416

Nuevos Pesos (multiplicar por 1.416):
- Ingrediente 1: 100 × 1.416 = 141.6g  ✅
- Ingrediente 2: 80 × 1.416 = 113.3g   ✅
- Ingrediente 3: 50 × 1.416 = 70.8g    ✅
- Proporciones: 141.6:113.3:70.8 = 2:1.6:1  ✅ MANTENIDAS

Nuevas Calorías:
- Ingrediente 1: 130 × 1.416 = 184.1 kcal
- Ingrediente 2: 165 × 1.133 = 186.9 kcal
- Ingrediente 3: 41 × 1.416 = 58.1 kcal
- Total: 400 kcal  ✅ OBJETIVO ALCANZADO
- % Final: (400 ÷ 800) × 100 = 50%  ✅
```

### Verificación en Consola
```javascript
// Deberías ver logs como:
[calorias_kcal] Objetivo: 400.00 (50% de 800)
Diferencia a ajustar: 117.50
  - Ingrediente [0-0]: 100.0g → 141.6g
  - Ingrediente [0-1]: 80.0g → 113.3g
  - Ingrediente [0-2]: 50.0g → 70.8g
✓ Ajuste proporcional completado para calorias_kcal (factor: 1.416)
```

### ⚠️ ERROR COMÚN (ya corregido)
```
ANTES DE LA MEJORA:
- Solo se ajustaba 1 ingrediente (el de mayor aporte)
- Las proporciones se rompían
- La receta quedaba desbalanceada

DESPUÉS DE LA MEJORA:
- Se ajustan TODOS los ingredientes
- Las proporciones se mantienen
- La receta queda balanceada ✅
```

---

## 🎨 PRUEBA 3: Cambio de Colores por Umbrales

### Objetivo
Verificar que los colores cambien correctamente según los rangos de adecuación

### Rangos Definidos
- 🟢 Verde (ÓPTIMO): 0-35%
- 🟡 Amarillo (ACEPTABLE): 35.1-70%
- 🔴 Rojo (ALTO): >70%

### Pasos
1. Localizar un nutriente en ~30% (verde)
2. Anotar el color de la tarjeta
3. Cambiar el % a 40% (debe pasar a amarillo)
4. Cambiar el % a 75% (debe pasar a rojo)
5. Cambiar el % a 30% (debe volver a verde)

### Resultados Esperados ✅

| % Adecuación | Color Esperado | CSS Class |
|--------------|----------------|-----------|
| 10% | 🟢 Verde | `data-estado="optimo"` |
| 25% | 🟢 Verde | `data-estado="optimo"` |
| 35% | 🟢 Verde | `data-estado="optimo"` |
| 36% | 🟡 Amarillo | `data-estado="aceptable"` |
| 50% | 🟡 Amarillo | `data-estado="aceptable"` |
| 70% | 🟡 Amarillo | `data-estado="aceptable"` |
| 71% | 🔴 Rojo | `data-estado="alto"` |
| 85% | 🔴 Rojo | `data-estado="alto"` |
| 100% | 🔴 Rojo | `data-estado="alto"` |

### Inspección Visual
- Abre DevTools (F12)
- Inspecciona una tarjeta `.total-mini` o `.adecuacion-mini`
- Verifica el atributo `data-estado`
- Verifica que el CSS aplicado coincida con el color

---

## ⚖️ PRUEBA 4: Cálculo de Peso Bruto con Parte Comestible

### Objetivo
Verificar que el peso bruto se calcule correctamente según la parte comestible

### Casos de Prueba

#### Caso 1: Alimento 100% Comestible
```
Ingrediente: Arroz blanco
Peso Neto: 100g
Parte Comestible: 100%

Cálculo: (100 × 100) ÷ 100 = 100g bruto ✅
Resultado: Peso Bruto = Peso Neto
```

#### Caso 2: Alimento con Desperdicio Moderado
```
Ingrediente: Pollo pechuga
Peso Neto: 100g
Parte Comestible: 85% (se pierde piel, grasa)

Cálculo: (100 × 100) ÷ 85 = 117.6g bruto ✅
Desperdicio: 117.6 - 100 = 17.6g
```

#### Caso 3: Alimento con Alto Desperdicio
```
Ingrediente: Plátano
Peso Neto: 100g
Parte Comestible: 60% (se pierde cáscara)

Cálculo: (100 × 100) ÷ 60 = 166.7g bruto ✅
Desperdicio: 166.7 - 100 = 66.7g
```

### Verificación
1. Cambiar el peso neto a 100g
2. Verificar que el peso bruto calculado coincida con la fórmula
3. Probar con diferentes ingredientes de diferentes % comestibles

---

## 🔢 PRUEBA 5: Límite de 100% en Porcentaje de Adecuación

### Objetivo
Verificar que el % de adecuación nunca supere 100%

### Pasos
1. Intentar editar un % a 150% (debe limitarse a 100%)
2. Agregar muchos ingredientes para superar el requerimiento
3. Verificar que el % mostrado sea máximo 100%

### Resultados Esperados ✅
```
Total Calculado: 1000 kcal
Requerimiento: 800 kcal
% Real: (1000 ÷ 800) × 100 = 125%
% Mostrado: min(125, 100) = 100%  ✅ LIMITADO

Estado: 🔴 ALTO (>70%)
```

### Verificación Backend
```python
# En views.py línea 856
porcentaje = min((total_actual / requerido) * 100, 100.0)
```

### Verificación Frontend
```javascript
// En menus_avanzado.js línea 1574
porcentaje = Math.min(Math.max(porcentaje, 0), 100);
```

---

## 🚫 PRUEBA 6: Validación de Valores Inválidos

### Objetivo
Verificar que el sistema maneje correctamente valores inválidos

### Casos de Prueba

#### Caso 1: Peso Negativo
```
Input: -50g
Comportamiento Esperado: Se convierte a 0g
Código: Math.max(0, pesoNeto)
```

#### Caso 2: Porcentaje Fuera de Rango
```
Input: -10%
Comportamiento Esperado: Se convierte a 0%

Input: 150%
Comportamiento Esperado: Se convierte a 100%

Código: Math.min(Math.max(porcentaje, 0), 100)
```

#### Caso 3: Parte Comestible Inválida
```
Input: 0%
Comportamiento Esperado: Se convierte a 1%

Input: 150%
Comportamiento Esperado: Se convierte a 100%

Código: max(1.0, min(100.0, parte_comestible))
```

---

## 🔄 PRUEBA 7: Prevención de Loops Infinitos

### Objetivo
Verificar que no haya loops infinitos al editar

### Escenario Peligroso (ya prevenido)
```
1. Usuario edita Peso Neto → dispara evento 'change'
2. Evento recalcula % Adecuación
3. Si NO HAY prevención, % Adecuación dispara evento 'input'
4. Evento recalcula Peso Neto
5. LOOP INFINITO ❌
```

### Mecanismo de Prevención ✅
```javascript
// Variables de control
let actualizandoPorPeso = false;
let actualizandoPorPorcentaje = false;

// En evento peso-input
if (actualizandoPorPorcentaje) return; // BLOQUEA

// En evento porcentaje-input
if (actualizandoPorPeso) return; // BLOQUEA
```

### Prueba Manual
1. Editar rápidamente peso neto varias veces
2. Editar rápidamente % varias veces
3. Verificar en consola que NO haya logs duplicados infinitamente
4. Verificar que la interfaz NO se congele

---

## 📊 PRUEBA 8: Sincronización de TODOS los Nutrientes

### Objetivo
Verificar que al editar 1 nutriente, TODOS se recalculen

### Pasos
1. Anotar % de los 7 nutrientes:
   ```
   Calorías:  ____%
   Proteína:  ____%
   Grasa:     ____%
   CHO:       ____%
   Calcio:    ____%
   Hierro:    ____%
   Sodio:     ____%
   ```

2. Editar solo % de Calorías (ej: de 30% a 60%)

3. Verificar que TODOS los % cambien (no solo calorías)

### Resultados Esperados ✅
```
ANTES:
Calorías: 30%
Proteína: 45%
Grasa: 10%
... (otros)

ACCIÓN: Editar Calorías a 60%
Factor de Escala: 60/30 = 2.0

DESPUÉS:
Calorías: 60%  ✅
Proteína: 90%  ✅ (cambió aunque no lo editaste)
Grasa: 20%     ✅ (cambió aunque no lo editaste)
... (todos cambiaron)
```

### Explicación
Al aumentar pesos para alcanzar más calorías, automáticamente:
- Aumenta la proteína (porque la carne/arroz tiene proteína)
- Aumenta la grasa (porque hay más cantidad)
- Aumenta el CHO, calcio, hierro, sodio, etc.

---

## 🎯 PRUEBA 9: Precisión de Cálculos

### Objetivo
Verificar que los cálculos sean precisos y consistentes

### Método
1. Usar calculadora externa para verificar:

```
Ingrediente: Arroz (130 kcal/100g)
Peso Neto: 75.5g

Cálculo Manual:
(130 × 75.5) ÷ 100 = 98.15 kcal

Cálculo Sistema:
Debe mostrar: 98.2 kcal (redondeado a 1 decimal) ✅
```

### Verificación de Redondeo
- Pesos: 1 decimal (ej: 141.6g)
- Nutrientes: 1 decimal (ej: 184.1 kcal)
- Porcentajes: 1 decimal (ej: 50.0%)

---

## 📝 PRUEBA 10: Comportamiento en Múltiples Niveles Escolares

### Objetivo
Verificar que los cálculos sean independientes por nivel

### Pasos
1. Abrir análisis con 3 niveles escolares (ej: Preescolar, Primaria, Secundaria)
2. Editar % de Calorías en Nivel 1
3. Verificar que:
   - ✅ Nivel 1 se actualice correctamente
   - ✅ Nivel 2 NO cambie
   - ✅ Nivel 3 NO cambie

### Explicación
Cada nivel tiene:
- Sus propios requerimientos nutricionales
- Sus propios cálculos independientes
- Su propio estado de adecuación

---

## ✅ Checklist Final de Verificación

### Funcionalidad Básica
- [ ] Editar peso neto actualiza peso bruto
- [ ] Editar peso neto actualiza nutrientes
- [ ] Editar peso neto actualiza totales
- [ ] Editar peso neto actualiza % adecuación

### Funcionalidad Bidireccional (MEJORA)
- [ ] Editar % adecuación ajusta TODOS los pesos
- [ ] Se mantienen proporciones de la receta
- [ ] Factor de escala se aplica uniformemente
- [ ] NO hay loops infinitos

### Validaciones
- [ ] Pesos negativos se convierten a 0
- [ ] % se limita entre 0-100%
- [ ] Parte comestible se limita entre 1-100%
- [ ] División por cero prevenida

### Colores y Estados
- [ ] Verde (0-35%) funciona correctamente
- [ ] Amarillo (35.1-70%) funciona correctamente
- [ ] Rojo (>70%) funciona correctamente
- [ ] Cambios de umbral actualizan colores

### Performance
- [ ] Cambios son instantáneos (<100ms)
- [ ] No hay lag perceptible
- [ ] Consola sin errores JavaScript
- [ ] No hay warnings de Django

---

## 🐛 Problemas Comunes y Soluciones

### Problema: Los pesos no cambian al editar %
**Solución:** Verificar que haya ingredientes con ese nutriente
```javascript
// En consola:
console.log(ingredientesData);
// Debe mostrar array con elementos que tienen nutrientePor100g > 0
```

### Problema: Colores no cambian
**Solución:** Verificar data-estado en DevTools
```html
<!-- Debe tener atributo: -->
<div class="total-mini" data-estado="aceptable">
```

### Problema: Cálculos incorrectos
**Solución:** Verificar requerimientos en window.requerimientosNiveles
```javascript
// En consola:
console.log(window.requerimientosNiveles);
// Debe mostrar objeto con calorias_kcal, proteina_g, etc.
```

---

## 📞 Soporte

Si encuentras algún problema:
1. Abre DevTools (F12)
2. Ve a la pestaña Console
3. Reproduce el error
4. Copia los logs de consola
5. Reporta con pasos específicos para reproducir

---

## 🎓 Documentación Adicional

- **Flujo Completo:** Ver `FLUJO_EDICION_PORCENTAJE_CALORIAS.md`
- **Diagrama ASCII:** Ver `DIAGRAMA_FLUJO_BIDIRECCIONAL.txt`
- **Código Fuente:** Ver comentarios en `menus_avanzado.js` y `views.py`
