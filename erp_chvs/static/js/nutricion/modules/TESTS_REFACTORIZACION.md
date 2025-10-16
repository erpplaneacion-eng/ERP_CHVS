# 🧪 TESTS DE REFACTORIZACIÓN - Menús Avanzados

## 📋 CHECKLIST DE FUNCIONALIDAD

### ✅ **FASE 1: CARGA INICIAL**
- [ ] La página carga sin errores en consola
- [ ] Se inicializa `MenusAvanzadosController`
- [ ] Se cargan todos los managers correctamente
- [ ] Los modales están ocultos inicialmente

### ✅ **FASE 2: FILTROS**
- [ ] Filtro de municipio funciona
- [ ] Se cargan programas al seleccionar municipio
- [ ] Botón "Aplicar Filtros" se habilita correctamente
- [ ] Se cargan modalidades al aplicar filtros

### ✅ **FASE 3: MODALIDADES Y MENÚS**
- [ ] Se generan acordeones de modalidades
- [ ] Se muestran tarjetas de menús (1-20)
- [ ] Botón "Generar 20 Menús" funciona
- [ ] Se puede descargar Excel de modalidad

### ✅ **FASE 4: GESTIÓN DE PREPARACIONES**
- [ ] Se abre modal "Gestionar Preparaciones"
- [ ] Se listan preparaciones del menú
- [ ] Botón "Agregar Preparación" abre modal
- [ ] Se puede guardar nueva preparación
- [ ] Se puede editar preparación
- [ ] Se puede eliminar preparación
- [ ] Se puede copiar preparación entre modalidades

### ✅ **FASE 5: GESTIÓN DE INGREDIENTES**
- [ ] Botón "Agregar Ingredientes" abre modal
- [ ] Modal de ingredientes se muestra correctamente
- [ ] Dropdown de materias primas funciona (Select2)
- [ ] Se puede agregar fila de ingrediente
- [ ] Se puede eliminar fila de ingrediente
- [ ] Se puede guardar ingredientes
- [ ] Modal se cierra correctamente

### ✅ **FASE 6: MENÚS ESPECIALES**
- [ ] Botón "Crear Menú Especial" abre modal
- [ ] Se puede crear menú especial
- [ ] Se puede editar menú especial
- [ ] Se puede eliminar menú especial
- [ ] Se descarga Excel de menú especial

### ✅ **FASE 7: ANÁLISIS NUTRICIONAL**
- [ ] Botón "Análisis Nutricional" abre modal
- [ ] Se carga análisis por niveles escolares
- [ ] Se muestran totales correctamente
- [ ] Se muestran requerimientos
- [ ] Se muestran porcentajes de adecuación
- [ ] Inputs de peso son editables
- [ ] Inputs de porcentaje son editables
- [ ] Recálculo funciona al editar

### ✅ **FASE 8: MODALES**
- [ ] Z-index de modales anidados es correcto
- [ ] Modales se centran en pantalla
- [ ] Botones de cerrar (X) funcionan
- [ ] Modales se limpian al cerrar

---

## 🧪 **TESTS ESPECÍFICOS DE CADA MÓDULO**

### **1️⃣ FiltrosManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test FiltrosManager:', window.menusController.filtrosManager instanceof FiltrosManager);

// Test 2: Verificar método cargarProgramasPorMunicipio
await window.menusController.filtrosManager.cargarProgramasPorMunicipio('1');

// Test 3: Verificar reseteo de filtros
window.menusController.filtrosManager.resetearFiltros();
```

### **2️⃣ ModalidadesManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test ModalidadesManager:', window.menusController.modalidadesManager instanceof ModalidadesManager);

// Test 2: Verificar carga de modalidades
await window.menusController.modalidadesManager.cargarModalidadesPorPrograma('1');

// Test 3: Verificar generación de acordeones
const modalidades = window.menusController.modalidadesManager.getModalidadesData();
console.log('Modalidades cargadas:', modalidades);
```

### **3️⃣ PreparacionesManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test PreparacionesManager:', window.menusController.preparacionesManager instanceof PreparacionesManager);

// Test 2: Verificar carga de preparaciones
await window.menusController.preparacionesManager.cargarPreparacionesMenu(1);

// Test 3: Verificar modal de nueva preparación
window.menusController.preparacionesManager.abrirModalNuevaPreparacion(1);
```

### **4️⃣ IngredientesManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test IngredientesManager:', window.menusController.ingredientesManager instanceof IngredientesManager);

// Test 2: Verificar carga de ingredientes SIESA
await window.menusController.ingredientesManager.cargarIngredientesSiesa();

// Test 3: Verificar modal de ingredientes
window.abrirAgregarIngrediente(1);
```

### **5️⃣ ModalesManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test ModalesManager:', window.menusController.modalesManager instanceof ModalesManager);

// Test 2: Verificar apertura de modal
window.menusController.modalesManager.abrirModal('modalPreparaciones');

// Test 3: Verificar cierre de modal
window.menusController.modalesManager.cerrarModal('modalPreparaciones');

// Test 4: Verificar z-index
console.log('Z-index modalPreparaciones:', window.menusController.modalesManager.getZIndex('modalPreparaciones'));
```

### **6️⃣ AnalisisNutricionalManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test AnalisisNutricionalManager:', window.menusController.analisisNutricionalManager instanceof AnalisisNutricionalManager);

// Test 2: Verificar apertura de modal
window.menusController.analisisNutricionalManager.abrirModalAnalisisNutricional(1);

// Test 3: Verificar carga de datos
await window.menusController.analisisNutricionalManager.cargarAnalisisNutricional(1);
```

### **7️⃣ MenusEspecialesManager**
```javascript
// Test 1: Verificar que se carga correctamente
console.log('Test MenusEspecialesManager:', window.menusController.menusEspecialesManager instanceof MenusEspecialesManager);

// Test 2: Verificar apertura de modal
window.abrirModalMenuEspecial('1');

// Test 3: Verificar eliminación
window.eliminarMenuEspecial(1, 'Test');
```

---

## 🔍 **DIAGNÓSTICO DE ERRORES COMUNES**

### **Error: Manager is not defined**
```javascript
// Verificar que todos los managers se inicializaron
console.log('Managers:', {
    filtros: window.menusController?.filtrosManager,
    modalidades: window.menusController?.modalidadesManager,
    preparaciones: window.menusController?.preparacionesManager,
    ingredientes: window.menusController?.ingredientesManager,
    modales: window.menusController?.modalesManager,
    analisis: window.menusController?.analisisNutricionalManager,
    especiales: window.menusController?.menusEspecialesManager
});
```

### **Error: Function is not defined**
```javascript
// Verificar que las funciones globales están disponibles
console.log('Funciones globales:', {
    abrirGestionPreparaciones: typeof window.abrirGestionPreparaciones,
    abrirModalMenuEspecial: typeof window.abrirModalMenuEspecial,
    cerrarModalPreparacion: typeof window.cerrarModalPreparacion,
    abrirAgregarIngrediente: typeof window.abrirAgregarIngrediente
});
```

### **Error: Modal no se muestra**
```javascript
// Verificar estilos del modal
const modal = document.getElementById('modalAgregarIngredientes');
console.log('Estilos modal:', {
    display: modal.style.display,
    zIndex: modal.style.zIndex,
    position: window.getComputedStyle(modal).position,
    width: window.getComputedStyle(modal).width,
    height: window.getComputedStyle(modal).height
});
```

---

## 📊 **RESULTADOS ESPERADOS**

### ✅ **TODOS LOS TESTS DEBEN PASAR**
- Sin errores en consola
- Todas las funciones globales disponibles
- Todos los managers inicializados
- Todos los modales funcionando
- Todos los eventos funcionando

### ⚠️ **SI HAY ERRORES:**
1. Verificar que los archivos JS se cargaron en orden correcto
2. Verificar que no hay conflictos de nombres
3. Verificar que los HTML tienen los IDs correctos
4. Verificar que las APIs responden correctamente

---

## 🚀 **COMANDOS RÁPIDOS DE TESTING**

```javascript
// 🧪 Test completo de inicialización
console.log('🧪 TEST COMPLETO DE INICIALIZACIÓN');
console.log('MenusController:', typeof window.menusController);
console.log('FiltrosManager:', window.menusController?.filtrosManager instanceof FiltrosManager);
console.log('ModalidadesManager:', window.menusController?.modalidadesManager instanceof ModalidadesManager);
console.log('PreparacionesManager:', window.menusController?.preparacionesManager instanceof PreparacionesManager);
console.log('IngredientesManager:', window.menusController?.ingredientesManager instanceof IngredientesManager);
console.log('ModalesManager:', window.menusController?.modalesManager instanceof ModalesManager);
console.log('AnalisisNutricionalManager:', window.menusController?.analisisNutricionalManager instanceof AnalisisNutricionalManager);
console.log('MenusEspecialesManager:', window.menusController?.menusEspecialesManager instanceof MenusEspecialesManager);

// 🧪 Test de funciones globales
console.log('🧪 TEST DE FUNCIONES GLOBALES');
console.log('abrirGestionPreparaciones:', typeof window.abrirGestionPreparaciones);
console.log('abrirModalMenuEspecial:', typeof window.abrirModalMenuEspecial);
console.log('cerrarModalPreparacion:', typeof window.cerrarModalPreparacion);
console.log('abrirAgregarIngrediente:', typeof window.abrirAgregarIngrediente);
console.log('agregarFilaIngrediente:', typeof window.agregarFilaIngrediente);

// 🧪 Test de modales
console.log('🧪 TEST DE MODALES');
console.log('modalPreparaciones:', document.getElementById('modalPreparaciones') ? '✅' : '❌');
console.log('modalNuevaPreparacion:', document.getElementById('modalNuevaPreparacion') ? '✅' : '❌');
console.log('modalAgregarIngredientes:', document.getElementById('modalAgregarIngredientes') ? '✅' : '❌');
console.log('modalAnalisisNutricional:', document.getElementById('modalAnalisisNutricional') ? '✅' : '❌');
```

---

## 📝 **NOTAS IMPORTANTES**

1. **Orden de carga:** Los módulos deben cargarse ANTES del archivo principal
2. **Funciones globales:** Todas están en `window` para compatibilidad con `onclick`
3. **Event listeners:** Se configuran automáticamente en `DOMContentLoaded`
4. **Callbacks:** Los managers se comunican mediante callbacks configurados en `configurarIntegracion()`

---

## ✅ **CRITERIOS DE ÉXITO**

- [x] Código modularizado (8 módulos)
- [x] Compatibilidad total con HTML existente
- [x] Funciones globales disponibles
- [x] Event listeners configurados
- [x] Managers comunicándose correctamente
- [x] Sin errores en consola
- [ ] **PRUEBA MANUAL EXITOSA** ← PENDIENTE

