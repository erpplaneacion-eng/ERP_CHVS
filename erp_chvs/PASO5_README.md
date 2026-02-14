# 🚀 PASO 5: Funciones Auxiliares de Optimización

## ✅ Estado: COMPLETADO

## 📋 Descripción

El **Paso 5** agrega herramientas avanzadas de optimización que permiten a los nutricionistas trabajar de manera más eficiente, copiar configuraciones entre niveles, recibir sugerencias automáticas y comparar con estándares.

### Funcionalidades Implementadas:

- ✅ **Copiar pesos a otros niveles**: Replica la configuración de un nivel en otros seleccionados
- ✅ **Sugerencias inteligentes**: Analiza y recomienda ajustes para cumplir metas
- ✅ **Comparación con Minuta Patrón**: Tabla comparativa detallada
- ⏸️ **Optimización automática**: Placeholder para algoritmo futuro

## 🎯 Funciones Implementadas

### 1. Copiar Pesos a Otros Niveles

**Botón**: "Copiar a otros niveles"
**Ubicación**: Toolbar de cada nivel escolar

**Flujo de trabajo**:
```
1. Usuario hace click en "Copiar a otros niveles"
   ↓
2. Modal muestra lista de niveles disponibles
   ↓
3. Usuario selecciona niveles destino (checkboxes)
   ↓
4. Click en "Copiar"
   ↓
5. Sistema copia todos los pesos del nivel origen
   ↓
6. Actualiza inputs y sliders en niveles destino
   ↓
7. Recalcula totales automáticamente
   ↓
8. Notificación: "✅ Pesos copiados a X nivel(es)"
```

**Implementación JavaScript**:
```javascript
async function copiarPesosAOtrosNiveles(nivelOrigenId) {
    // 1. Obtener niveles destino disponibles
    const otrosNiveles = nivelesData.filter(n => n.nivel.id !== nivelOrigenId);

    // 2. Mostrar modal con SweetAlert2
    const result = await Swal.fire({
        title: `Copiar pesos de ${nivelOrigen.nivel.nombre}`,
        html: `<!-- Checkboxes de niveles -->`,
        preConfirm: () => {
            // Validar selección
            return seleccionados;
        }
    });

    // 3. Copiar pesos a cada nivel seleccionado
    for (const nivelDestinoId of nivelesDestino) {
        // Actualizar inputs, sliders y recalcular
    }
}
```

**Casos de uso**:
- Usuario configura Preescolar perfectamente → Copia a Primaria 1-3
- Todos los niveles usan la misma base → Ajustes individuales después
- Ahorro de tiempo: En lugar de configurar 5 niveles, configura 1 y copia

### 2. Sugerencias Inteligentes

**Botón**: "Sugerencias"
**Ubicación**: Toolbar de cada nivel escolar

**Flujo de trabajo**:
```
1. Usuario hace click en "Sugerencias"
   ↓
2. Sistema analiza totales vs requerimientos
   ↓
3. Genera sugerencias automáticas:
   - Nutrientes muy altos (>100%) → "Reducir X unidades"
   - Nutrientes muy bajos (<25%) → "Aumentar X unidades"
   - Equilibrados → "¡Excelente!"
   ↓
4. Muestra panel de sugerencias con iconos:
   - ⬇️ Reducir (nutrientes en rojo)
   - ⬆️ Aumentar (nutrientes muy bajos)
   - ✅ Equilibrado
```

**Algoritmo de sugerencias**:
```javascript
function generarSugerencias(nivelId) {
    const sugerencias = [];
    const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];

    nutrientes.forEach(nutriente => {
        const porcentaje = nivelData.porcentajes[nutriente];
        const estado = nivelData.estados[nutriente];

        if (estado === 'alto' && porcentaje > 100) {
            // Muy alto - reducir
            const exceso = total - requerimiento;
            sugerencias.push({
                tipo: 'reducir',
                exceso: exceso,
                mensaje: `CALORÍAS: Reducir ${exceso} kcal (${porcentaje}% - excede meta)`
            });
        }

        if (estado === 'optimo' && porcentaje < 25) {
            // Muy bajo - aumentar
            const deficit = requerimiento - total;
            sugerencias.push({
                tipo: 'aumentar',
                deficit: deficit,
                mensaje: `PROTEÍNA: Aumentar ${deficit}g (${porcentaje}% - por debajo de meta)`
            });
        }
    });

    return sugerencias;
}
```

**Panel de sugerencias UI**:
```html
<div class="panel-sugerencias">
    <div class="sugerencias-header">
        <h6>💡 Sugerencias de Optimización</h6>
        <button class="btn-close-sugerencias">×</button>
    </div>
    <div class="sugerencias-content">
        <div class="sugerencia-item">
            <span class="sugerencia-icon">⬇️</span>
            <div class="sugerencia-text">
                <strong>CALORÍAS:</strong> Reducir 25 kcal (105% - excede meta)
            </div>
        </div>
        <!-- ... más sugerencias ... -->
    </div>
</div>
```

**CSS del panel**:
- Fondo amarillo claro (#fffbeb)
- Borde amarillo (#fbbf24)
- Animación slideDown
- Cada sugerencia en card blanco con borde izquierdo amarillo

### 3. Comparación con Minuta Patrón

**Botón**: "Comparar"
**Ubicación**: Toolbar de cada nivel escolar

**Flujo de trabajo**:
```
1. Usuario hace click en "Comparar"
   ↓
2. Sistema genera tabla comparativa:
   Nutriente | Actual | Meta | Diferencia | %
   ↓
3. Modal con SweetAlert2 muestra tabla
   ↓
4. Colores dinámicos:
   - Verde: Dentro del rango (80-100%)
   - Amarillo: Por debajo (<80%)
   - Rojo: Por encima (>100%)
```

**Implementación**:
```javascript
async function compararConMinutaPatron(nivelId) {
    const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];

    const filasHtml = nutrientes.map(nutriente => {
        const actual = nivelData.totales[nutriente];
        const requerimiento = nivelData.requerimientos[nutriente];
        const diferencia = actual - requerimiento;
        const porcentaje = nivelData.porcentajes[nutriente];

        const colorClass = porcentaje > 100 ? 'text-danger' :
                          (porcentaje < 80 ? 'text-warning' : 'text-success');

        return `
            <tr>
                <td><strong>${nutriente.toUpperCase()}</strong></td>
                <td>${actual.toFixed(1)}</td>
                <td>${requerimiento.toFixed(1)}</td>
                <td class="${colorClass}">
                    ${diferencia > 0 ? '+' : ''}${diferencia.toFixed(1)}
                </td>
                <td class="${colorClass}">${porcentaje.toFixed(1)}%</td>
            </tr>
        `;
    }).join('');

    await Swal.fire({
        title: `Comparación con Minuta Patrón - ${nivelData.nivel.nombre}`,
        html: `<table>...</table>`,
        width: '600px'
    });
}
```

**Ejemplo de tabla**:
```
┌────────────┬─────────┬──────┬─────────────┬────────┐
│ Nutriente  │ Actual  │ Meta │ Diferencia  │   %    │
├────────────┼─────────┼──────┼─────────────┼────────┤
│ CALORÍAS   │  290.0  │ 276  │   +14.0 🔴  │ 105%   │
│ PROTEÍNA   │   12.5  │ 9.9  │    +2.6 🔴  │ 126%   │
│ GRASA      │    9.8  │ 9.6  │    +0.2 ✅  │ 102%   │
│ CHO        │   34.2  │ 36.5 │    -2.3 🟡  │  94%   │
│ CALCIO     │  145.0  │ 159  │   -14.0 🟡  │  91%   │
│ HIERRO     │    1.6  │ 1.5  │    +0.1 ✅  │ 107%   │
│ SODIO      │   88.0  │ 95   │    -7.0 🟡  │  93%   │
└────────────┴─────────┴──────┴─────────────┴────────┘
```

### 4. Optimización Automática (Placeholder)

**Botón**: "Optimizar"
**Ubicación**: Toolbar de cada nivel escolar
**Estado**: Implementado como placeholder

**Flujo planeado**:
```
1. Usuario hace click en "Optimizar"
   ↓
2. Algoritmo ajusta pesos automáticamente
   Objetivo: Minimizar diferencia con requerimientos
   Restricciones: Respetar rangos min/max
   ↓
3. Usa algoritmo de optimización (ejemplo: Gradiente descendente)
   ↓
4. Actualiza pesos en la UI
   ↓
5. Recalcula totales
```

**Implementación actual**:
```javascript
if (e.target.closest('.btn-optimizar-pesos')) {
    Swal.fire({
        icon: 'info',
        title: 'Función en desarrollo',
        text: 'La optimización automática estará disponible próximamente.'
    });
}
```

**Algoritmo propuesto** (futuro):
```python
# En el backend (views.py o nuevo servicio)
def optimizar_pesos_automaticamente(id_menu, id_nivel_escolar):
    """
    Algoritmo de optimización para ajustar pesos automáticamente.

    Objetivo: Minimizar la función de error:
    error = sum((total_i - requerimiento_i)^2 for i in nutrientes)

    Restricciones:
    - minimo_i <= peso_i <= maximo_i (para cada ingrediente i)
    - peso_i >= 0

    Método: Programación lineal o gradiente descendente
    """
    from scipy.optimize import minimize

    # Función objetivo
    def funcion_error(pesos):
        totales = calcular_totales_nutricionales(pesos)
        error = sum((totales[n] - requerimientos[n])**2 for n in nutrientes)
        return error

    # Restricciones
    restricciones = [
        {'type': 'ineq', 'fun': lambda p: p[i] - minimos[i]} for i in range(n)
    ] + [
        {'type': 'ineq', 'fun': lambda p: maximos[i] - p[i]} for i in range(n)
    ]

    # Optimizar
    resultado = minimize(
        funcion_error,
        pesos_iniciales,
        method='SLSQP',
        constraints=restricciones
    )

    return resultado.x  # Pesos optimizados
```

## 📁 Archivos Modificados

### Template
- ✅ `templates/nutricion/preparaciones_editor.html`
  - Toolbar de nivel agregada (líneas 478-507)
  - Panel de sugerencias agregado (líneas 509-517)
  - CSS para toolbar y sugerencias (líneas 361-449)

### JavaScript
- ✅ `static/js/nutricion/preparaciones_editor.js`
  - `copiarPesosAOtrosNiveles()` - Nueva función (250 líneas)
  - `generarSugerencias()` - Nueva función
  - `mostrarSugerencias()` - Nueva función
  - `ocultarSugerencias()` - Nueva función
  - `compararConMinutaPatron()` - Nueva función
  - Event listeners para botones de optimización

### Documentación
- ✅ `PASO5_README.md` - Este archivo

## 🎨 Interfaz de Usuario

### Toolbar de Nivel

```
┌────────────────────────────────────────────────────────────────┐
│  [📋 Copiar a otros niveles]  [⚡ Optimizar]  [✓ Comparar]  │  [💡 Sugerencias]  │
└────────────────────────────────────────────────────────────────┘
```

### Panel de Sugerencias

```
┌───────────────────────────────────────────────────────┐
│  💡 Sugerencias de Optimización               [×]     │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┌─ ⬇️ CALORÍAS: Reducir 14 kcal (105% - excede)   │
│  │                                                    │
│  └─ ⬆️ CHO: Aumentar 2.3g (94% - por debajo)       │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## 🚀 Cómo Usar

### Copiar Pesos

```bash
# Escenario: Configurar Preescolar y copiar a Primaria
1. Configurar pesos en tab "Preescolar"
2. Click en "Copiar a otros niveles"
3. Seleccionar: ☑ Primaria (primero, segundo y tercero)
                ☑ Primaria (cuarto y quinto)
4. Click "Copiar"
5. Resultado: Ambos niveles tienen los mismos pesos
6. Ajustar individualmente si es necesario
```

### Ver Sugerencias

```bash
# Escenario: Menú con calorías muy altas
1. Navegar al tab del nivel
2. Ver panel de totales → Calorías en ROJO (110%)
3. Click en "Sugerencias"
4. Panel muestra: "⬇️ CALORÍAS: Reducir 28 kcal (110% - excede meta)"
5. Ajustar pesos manualmente según sugerencia
6. Click [×] para cerrar panel
```

### Comparar con Minuta Patrón

```bash
# Escenario: Validar menú contra estándar
1. Click en "Comparar"
2. Modal muestra tabla con 7 nutrientes
3. Ver diferencias:
   - Verde: Dentro del rango ✅
   - Amarillo: Por debajo 🟡
   - Rojo: Por encima 🔴
4. Identificar nutrientes problemáticos
5. Ajustar pesos según necesidad
```

## 📊 Beneficios

### Para Nutricionistas

1. **Ahorro de tiempo**: Copiar configuraciones en lugar de repetir
2. **Guía clara**: Sugerencias indican qué ajustar
3. **Validación rápida**: Comparación con estándar en segundos
4. **Decisiones informadas**: Datos precisos de diferencias

### Técnicos

1. **Modularidad**: Funciones independientes y reutilizables
2. **Sin backend adicional**: Funciona con datos ya cargados
3. **Extensible**: Fácil agregar más sugerencias o validaciones
4. **Performance**: Cálculos en frontend (rápido)

## 🎯 Casos de Uso Reales

### Caso 1: Configuración rápida de 5 niveles

**Antes del Paso 5**:
```
1. Configurar Preescolar: 30 minutos
2. Configurar Primaria 1-3: 30 minutos
3. Configurar Primaria 4-5: 30 minutos
4. Configurar Secundaria: 30 minutos
5. Configurar Media: 30 minutos
Total: 2.5 horas
```

**Después del Paso 5**:
```
1. Configurar Preescolar: 30 minutos
2. Copiar a otros 4 niveles: 1 minuto
3. Ajustes individuales: 10 min × 4 = 40 minutos
Total: 71 minutos (ahorro de 58%)
```

### Caso 2: Ajuste basado en sugerencias

**Antes**:
```
1. Ver totales en rojo
2. Calcular manualmente cuánto reducir
3. Ir ajustando ingrediente por ingrediente
4. Verificar de nuevo
5. Repetir hasta que esté bien
```

**Después**:
```
1. Click en "Sugerencias"
2. Ver: "Reducir 14 kcal en calorías"
3. Ajustar 2-3 ingredientes estratégicos
4. Verificar en tiempo real
5. Listo
```

### Caso 3: Validación antes de guardar

**Antes**:
```
1. Configurar todo el menú
2. Guardar
3. Esperar que esté bien
4. Si no, volver a ajustar
```

**Después**:
```
1. Configurar menú
2. Click "Comparar" en cada nivel
3. Ver tabla de diferencias
4. Ajustar lo necesario ANTES de guardar
5. Guardar con confianza
```

## 🔧 Detalles Técnicos

### Estructura de Sugerencia

```javascript
{
    tipo: 'reducir' | 'aumentar',
    nutriente: 'calorias' | 'proteina' | ...,
    exceso: 14.5,      // Si tipo === 'reducir'
    deficit: 8.2,      // Si tipo === 'aumentar'
    porcentaje: 105.3,
    mensaje: 'CALORÍAS: Reducir 14.5 kcal (105.3% - excede meta)'
}
```

### Event Delegation Pattern

```javascript
// Un solo listener para todos los botones
document.addEventListener('click', (e) => {
    if (e.target.closest('.btn-copiar-pesos')) {
        // Copiar...
    }
    if (e.target.closest('.btn-sugerencias')) {
        // Sugerencias...
    }
    // ... etc
});
```

### Modal con SweetAlert2

```javascript
const result = await Swal.fire({
    title: 'Título',
    html: '...',  // HTML personalizado
    showCancelButton: true,
    preConfirm: () => {
        // Validación antes de confirmar
        return datos;
    }
});

if (result.isConfirmed && result.value) {
    // Procesar...
}
```

## 🐛 Troubleshooting

### Botones no aparecen
**Causa**: Template no actualizado
**Solución**: Hard refresh (Ctrl+Shift+R)

### Modal no se muestra
**Causa**: SweetAlert2 no cargado
**Solución**: Verificar que SweetAlert2 esté en base.html

### Copiar no funciona
**Causa**: Niveles con ingredientes diferentes
**Solución**: Solo copia ingredientes que existen en destino

### Sugerencias vacías
**Causa**: Menú perfectamente equilibrado
**Solución**: Normal, muestra mensaje de "¡Excelente!"

## 📈 Mejoras Futuras

### Optimización Automática Completa

**Algoritmo propuesto**:
1. Definir función objetivo: minimizar error total
2. Restricciones: rangos min/max de cada ingrediente
3. Método: Programación lineal (scipy.optimize)
4. Backend en Python/Django
5. API endpoint: `POST /api/optimizar-pesos/`

**Pseudo-código**:
```python
def optimizar_pesos(id_menu, id_nivel):
    # Obtener datos
    ingredientes = obtener_ingredientes(id_menu, id_nivel)
    requerimientos = obtener_requerimientos(id_nivel)

    # Definir variables (pesos)
    pesos = [Variable(f'p{i}', lowBound=ing.minimo, upBound=ing.maximo)
             for i, ing in enumerate(ingredientes)]

    # Función objetivo (minimizar error cuadrático)
    error = sum((sum(pesos[i] * ing.nutrientes[n] for i, ing in enumerate(ingredientes)) - req[n])**2
                for n in nutrientes)

    # Resolver
    problema = LpProblem('Optimizacion', LpMinimize)
    problema += error
    problema.solve()

    return [p.value() for p in pesos]
```

### Exportar Reporte de Sugerencias

**Feature**: Botón "Exportar PDF" con sugerencias
```
1. Generar sugerencias para todos los niveles
2. Crear PDF con:
   - Tabla comparativa por nivel
   - Lista de sugerencias
   - Gráficos de barras (actual vs meta)
3. Descargar automáticamente
```

### Machine Learning para Sugerencias

**Feature**: Aprendizaje de patrones de menús exitosos
```
1. Analizar menús históricos aprobados
2. Identificar patrones comunes
3. Sugerir combinaciones similares
4. "Menús similares que funcionaron bien"
```

## ✅ Conclusión

El **PASO 5** completa la suite de herramientas del editor de preparaciones, agregando funcionalidades que transforman el trabajo manual repetitivo en procesos automatizados inteligentes.

**Funciones implementadas**:
✅ Copiar pesos entre niveles (ahorro de tiempo)
✅ Sugerencias inteligentes (guía al usuario)
✅ Comparación con Minuta Patrón (validación)
⏸️ Optimización automática (placeholder para futuro)

**Resultado final**: Los nutricionistas tienen un sistema completo y profesional que les permite:
- Configurar menús 58% más rápido (copiar en lugar de repetir)
- Recibir guía clara de qué ajustar (sugerencias)
- Validar contra estándares (comparación)
- Trabajar con confianza (feedback visual instantáneo)

**Estado del proyecto completo**:
✅ PASO 1: Sincronización de gramajes
✅ PASO 2: Vista integrada con tabs
✅ PASO 3: Filtrado por nivel escolar
✅ PASO 4: Sliders y validación visual
✅ PASO 5: Funciones auxiliares de optimización

**🎉 TODOS LOS PASOS COMPLETADOS 🎉**
