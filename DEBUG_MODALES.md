# 🔍 GUÍA DE DEBUGGING - MODALES DE NUTRICIÓN

## 📋 TESTS A EJECUTAR EN CONSOLA DEL NAVEGADOR

### **Test 1: Verificar que las funciones estén disponibles**

```javascript
// Copiar y pegar esto en la consola (F12)
console.log('=== VERIFICACIÓN DE FUNCIONES GLOBALES ===');
console.log('cerrarModalPreparacion:', typeof window.cerrarModalPreparacion);
console.log('cerrarModalIngredientes:', typeof window.cerrarModalIngredientes);
console.log('abrirAgregarIngrediente:', typeof window.abrirAgregarIngrediente);
console.log('agregarFilaIngrediente:', typeof window.agregarFilaIngrediente);
console.log('guardarIngredientes:', typeof window.guardarIngredientes);
```

**Resultado esperado:** Todas deben mostrar `"function"`

---

### **Test 2: Verificar que los modales existan en el DOM**

```javascript
// Verificar modales
console.log('=== VERIFICACIÓN DE MODALES EN DOM ===');
console.log('modalPreparaciones:', document.getElementById('modalPreparaciones') ? '✅ Existe' : '❌ No existe');
console.log('modalNuevaPreparacion:', document.getElementById('modalNuevaPreparacion') ? '✅ Existe' : '❌ No existe');
console.log('modalAgregarIngredientes:', document.getElementById('modalAgregarIngredientes') ? '✅ Existe' : '❌ No existe');
console.log('modalAnalisisNutricional:', document.getElementById('modalAnalisisNutricional') ? '✅ Existe' : '❌ No existe');
```

**Resultado esperado:** Todos deben mostrar `✅ Existe`

---

### **Test 3: Verificar Z-Index de los modales**

```javascript
// Verificar z-index
console.log('=== VERIFICACIÓN DE Z-INDEX ===');
const modales = [
    'modalPreparaciones',
    'modalNuevaPreparacion', 
    'modalAgregarIngredientes',
    'modalAnalisisNutricional'
];

modales.forEach(modalId => {
    const modal = document.getElementById(modalId);
    if (modal) {
        const zIndex = window.getComputedStyle(modal).zIndex;
        console.log(`${modalId}: z-index = ${zIndex}`);
    }
});
```

**Resultado esperado:**
- modalPreparaciones: 1000
- modalNuevaPreparacion: 1100
- modalAgregarIngredientes: 1150
- modalAnalisisNutricional: 1200

---

### **Test 4: Probar abrir modal de ingredientes manualmente**

```javascript
// Probar abrir el modal directamente
console.log('=== TEST MANUAL DE MODAL INGREDIENTES ===');
window.abrirAgregarIngrediente(1); // Usar ID de una preparación real
```

**Resultado esperado:** El modal debe abrirse y ver en consola:
```
🟢 [COMPLETA] abrirAgregarIngrediente llamada para preparación: 1
Agregando primera fila de ingrediente...
✅ Abriendo modal de ingredientes (versión completa)
```

---

### **Test 5: Ver eventos asignados a botones**

```javascript
// Verificar eventos del botón "Agregar Preparación"
console.log('=== EVENTOS EN BOTONES ===');
const btnAgregar = document.getElementById('btnAgregarPreparacion');
if (btnAgregar) {
    console.log('Botón "Agregar Preparación" encontrado');
    console.log('onclick:', btnAgregar.onclick);
    console.log('Event listeners:', getEventListeners(btnAgregar)); // Solo en Chrome
} else {
    console.log('❌ Botón "Agregar Preparación" NO encontrado');
}
```

---

### **Test 6: Ver todos los modales abiertos actualmente**

```javascript
// Ver estado de todos los modales
console.log('=== ESTADO ACTUAL DE MODALES ===');
['modalPreparaciones', 'modalNuevaPreparacion', 'modalAgregarIngredientes', 'modalAnalisisNutricional'].forEach(id => {
    const modal = document.getElementById(id);
    if (modal) {
        const display = window.getComputedStyle(modal).display;
        const zIndex = window.getComputedStyle(modal).zIndex;
        console.log(`${id}:`, {
            display: display,
            zIndex: zIndex,
            visible: display !== 'none'
        });
    }
});
```

---

## 🐛 **PROBLEMAS COMUNES Y SOLUCIONES**

### **Problema 1: Modal se abre detrás de otro**

**Síntoma:** Haces click pero no ves el modal

**Verificar:**
```javascript
// Ver z-index de modales visibles
document.querySelectorAll('.modal[style*="display: block"]').forEach(m => {
    console.log(m.id, '- z-index:', window.getComputedStyle(m).zIndex);
});
```

**Solución:** Verificar que los z-index en `inline_styles.css` estén correctos

---

### **Problema 2: Función no está definida**

**Síntoma:** Error "X is not a function"

**Verificar:**
```javascript
console.log('Función:', window.nombreDeLaFuncion);
```

**Solución:** Asegurarse que el archivo JS se haya cargado completamente

---

### **Problema 3: Click no hace nada**

**Síntoma:** Click en botón no abre modal

**Verificar:**
```javascript
// Ver si hay errores en consola
// Ver si la función se está llamando
// Agregar console.log temporal
window.abrirAgregarIngrediente = new Proxy(window.abrirAgregarIngrediente, {
    apply(target, thisArg, args) {
        console.log('🔴 INTERCEPTADO:', target.name, 'args:', args);
        return target.apply(thisArg, args);
    }
});
```

---

## 📝 **LOGS ESPERADOS AL HACER CLICK EN "AGREGAR INGREDIENTE"**

Cuando haces click en el botón "Agregar Ingrediente", deberías ver en consola:

```
🟢 [COMPLETA] abrirAgregarIngrediente llamada para preparación: 123
Cargando ingredientes SIESA...  (si es primera vez)
Agregando primera fila de ingrediente...
✅ Abriendo modal de ingredientes (versión completa)
```

---

## 🎯 **SECUENCIA CORRECTA DE APERTURA**

1. Usuario abre "Gestionar Preparaciones" → z-index: 1000
2. Usuario expande una preparación
3. **Usuario hace click en "Agregar Ingrediente"**
   - Console: `🟢 [COMPLETA] abrirAgregarIngrediente llamada...`
   - Modal se abre con z-index: 1150
   - Modal está DELANTE del modal de preparaciones

---

## 🆘 **SI NADA FUNCIONA**

Ejecuta este reset completo:

```javascript
// RESET COMPLETO
console.log('=== RESET DE MODALES ===');

// Cerrar todos los modales
['modalPreparaciones', 'modalNuevaPreparacion', 'modalAgregarIngredientes', 'modalAnalisisNutricional'].forEach(id => {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'none';
        console.log(`✅ Cerrado: ${id}`);
    }
});

// Recargar la página
setTimeout(() => {
    console.log('Recargando página...');
    location.reload();
}, 1000);
```

---

## 📞 **INFORMACIÓN PARA REPORTAR**

Si sigues teniendo problemas, copia y pega el resultado de esto:

```javascript
console.log('=== INFORMACIÓN DE DEBUG ===');
console.log('URL actual:', window.location.href);
console.log('Funciones globales:', {
    abrirAgregarIngrediente: typeof window.abrirAgregarIngrediente,
    cerrarModalIngredientes: typeof window.cerrarModalIngredientes,
    agregarFilaIngrediente: typeof window.agregarFilaIngrediente
});
console.log('Modales existentes:', {
    modalPreparaciones: !!document.getElementById('modalPreparaciones'),
    modalNuevaPreparacion: !!document.getElementById('modalNuevaPreparacion'),
    modalAgregarIngredientes: !!document.getElementById('modalAgregarIngredientes')
});
console.log('Scripts cargados:', Array.from(document.scripts).map(s => s.src).filter(s => s.includes('nutricion')));
```

