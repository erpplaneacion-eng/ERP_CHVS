# 🧪 CÓMO PROBAR LA REFACTORIZACIÓN

## ✅ **EL SERVIDOR YA ESTÁ CORRIENDO**
El servidor Django está ejecutándose en segundo plano en el puerto 8000.

---

## 🚀 **PASO 1: ABRIR LA APLICACIÓN**

### **Opción A: Navegador**
1. Abre tu navegador
2. Ve a: `http://localhost:8000/nutricion/menus/`
3. Abre la consola del navegador (F12)

### **Opción B: Página de Tests**
1. Ve a: `http://localhost:8000/static/js/nutricion/modules/test_refactorizacion.html`
2. Click en "🚀 Test Completo"
3. Verifica que todos los tests pasen

---

## 🧪 **PASO 2: TEST RÁPIDO EN CONSOLA**

Abre la consola del navegador (F12) y pega este código:

```javascript
// 🧪 TEST RÁPIDO DE INICIALIZACIÓN
console.log('═══════════════════════════════════════════');
console.log('🧪 TEST RÁPIDO DE REFACTORIZACIÓN');
console.log('═══════════════════════════════════════════');

// Verificar controlador principal
console.log('\n1️⃣ CONTROLADOR PRINCIPAL:');
console.log('   MenusController:', typeof window.menusController);
console.log('   Es instancia:', window.menusController instanceof MenusAvanzadosController);

// Verificar todos los managers
console.log('\n2️⃣ MANAGERS:');
const managers = {
    'FiltrosManager': window.menusController?.filtrosManager instanceof FiltrosManager,
    'ModalidadesManager': window.menusController?.modalidadesManager instanceof ModalidadesManager,
    'PreparacionesManager': window.menusController?.preparacionesManager instanceof PreparacionesManager,
    'IngredientesManager': window.menusController?.ingredientesManager instanceof IngredientesManager,
    'ModalesManager': window.menusController?.modalesManager instanceof ModalesManager,
    'AnalisisNutricionalManager': window.menusController?.analisisNutricionalManager instanceof AnalisisNutricionalManager,
    'MenusEspecialesManager': window.menusController?.menusEspecialesManager instanceof MenusEspecialesManager
};

Object.entries(managers).forEach(([name, status]) => {
    console.log(`   ${status ? '✅' : '❌'} ${name}`);
});

// Verificar funciones globales
console.log('\n3️⃣ FUNCIONES GLOBALES:');
const funciones = [
    'abrirGestionPreparaciones',
    'abrirModalMenuEspecial',
    'cerrarModalPreparacion',
    'cerrarModalIngredientes',
    'abrirAgregarIngrediente',
    'agregarFilaIngrediente'
];

funciones.forEach(fn => {
    console.log(`   ${typeof window[fn] === 'function' ? '✅' : '❌'} ${fn}`);
});

// Resultado final
console.log('\n═══════════════════════════════════════════');
const todosPasaron = Object.values(managers).every(v => v) && 
                     funciones.every(fn => typeof window[fn] === 'function');
console.log(todosPasaron ? '🎉 TODOS LOS TESTS PASARON!' : '⚠️ ALGUNOS TESTS FALLARON');
console.log('═══════════════════════════════════════════\n');
```

### **✅ RESULTADO ESPERADO:**
```
═══════════════════════════════════════════
🧪 TEST RÁPIDO DE REFACTORIZACIÓN
═══════════════════════════════════════════

1️⃣ CONTROLADOR PRINCIPAL:
   MenusController: object
   Es instancia: true

2️⃣ MANAGERS:
   ✅ FiltrosManager
   ✅ ModalidadesManager
   ✅ PreparacionesManager
   ✅ IngredientesManager
   ✅ ModalesManager
   ✅ AnalisisNutricionalManager
   ✅ MenusEspecialesManager

3️⃣ FUNCIONES GLOBALES:
   ✅ abrirGestionPreparaciones
   ✅ abrirModalMenuEspecial
   ✅ cerrarModalPreparacion
   ✅ cerrarModalIngredientes
   ✅ abrirAgregarIngrediente
   ✅ agregarFilaIngrediente

═══════════════════════════════════════════
🎉 TODOS LOS TESTS PASARON!
═══════════════════════════════════════════
```

---

## 🎯 **PASO 3: PRUEBA FUNCIONAL**

### **3.1 PROBAR FILTROS**
1. Selecciona un municipio del dropdown
2. ✅ Verifica que se cargan programas
3. Selecciona un programa
4. Click en "Cargar Modalidades"
5. ✅ Verifica que se muestran acordeones de modalidades

### **3.2 PROBAR MODALIDADES**
1. ✅ Verifica que se muestran tarjetas de menús (1-20)
2. Click en una modalidad para expandir
3. ✅ Verifica que se ven las tarjetas de menús

### **3.3 PROBAR GESTIÓN DE PREPARACIONES**
1. Click en un menú (cualquier número del 1-20)
2. ✅ Verifica que se abre el modal "Gestionar Preparaciones"
3. ✅ Verifica que se muestra la lista de preparaciones
4. Click en "Agregar Preparación"
5. ✅ Verifica que se abre el modal "Nueva Preparación"
6. Llena los campos y guarda
7. ✅ Verifica que la preparación se agregó a la lista

### **3.4 PROBAR AGREGAR INGREDIENTES** ⭐ IMPORTANTE
1. En la lista de preparaciones, click en "Agregar Ingredientes"
2. ✅ Verifica que se abre el modal de ingredientes
3. ✅ Verifica que el modal es VISIBLE (centrado, con fondo blanco)
4. ✅ Verifica que el dropdown de materias primas funciona
5. Click en "Agregar Fila"
6. ✅ Verifica que se agrega una nueva fila
7. Selecciona un ingrediente
8. Click en "Guardar Ingredientes"
9. ✅ Verifica que se guardan los ingredientes
10. Click en la X para cerrar
11. ✅ Verifica que el modal se cierra correctamente

### **3.5 PROBAR MENÚS ESPECIALES**
1. En una modalidad, click en "Crear Menú Especial"
2. ✅ Verifica que se abre el modal
3. Ingresa un nombre
4. Click en "Crear"
5. ✅ Verifica que se crea el menú especial
6. Click en "Editar" en el menú especial
7. ✅ Verifica que se puede editar
8. Click en "Eliminar"
9. ✅ Verifica que se puede eliminar

### **3.6 PROBAR ANÁLISIS NUTRICIONAL**
1. En el modal de preparaciones, click en "Análisis Nutricional"
2. ✅ Verifica que se abre el modal de análisis
3. ✅ Verifica que se cargan los niveles escolares
4. ✅ Verifica que se muestran totales correctamente
5. ✅ Verifica que se pueden editar los pesos
6. ✅ Verifica que se pueden editar los porcentajes

---

## ⚠️ **SI ENCUENTRAS ERRORES**

### **Error: "Manager is not defined"**
```javascript
// Verificar en consola:
console.log('¿Módulos cargados?', {
    ModalesManager: typeof ModalesManager,
    FiltrosManager: typeof FiltrosManager,
    ModalidadesManager: typeof ModalidadesManager,
    PreparacionesManager: typeof PreparacionesManager,
    IngredientesManager: typeof IngredientesManager,
    AnalisisNutricionalManager: typeof AnalisisNutricionalManager,
    MenusEspecialesManager: typeof MenusEspecialesManager
});
```

**Solución:** Revisar que todos los scripts se cargaron en el orden correcto.

### **Error: Modal no se muestra**
```javascript
// Verificar estilos del modal en consola:
const modal = document.getElementById('modalAgregarIngredientes');
console.log('Modal existe:', !!modal);
console.log('Display:', window.getComputedStyle(modal).display);
console.log('Z-index:', window.getComputedStyle(modal).zIndex);
console.log('Width:', window.getComputedStyle(modal).width);
console.log('Height:', window.getComputedStyle(modal).height);

// Forzar apertura:
window.menusController.modalesManager.abrirModal('modalAgregarIngredientes');
```

**Solución:** Verificar que el modal existe en el HTML y que los estilos CSS están aplicados.

### **Error: Función no definida**
```javascript
// Verificar funciones globales:
console.log('Funciones globales:', {
    abrirGestionPreparaciones: typeof window.abrirGestionPreparaciones,
    abrirAgregarIngrediente: typeof window.abrirAgregarIngrediente,
    agregarFilaIngrediente: typeof window.agregarFilaIngrediente
});
```

**Solución:** Verificar que `menus_avanzado_refactorizado.js` se cargó DESPUÉS de todos los módulos.

---

## 📊 **CHECKLIST COMPLETO**

### **Inicialización:**
- [ ] MenusController está definido
- [ ] Todos los 7 managers están inicializados
- [ ] No hay errores en consola

### **Filtros:**
- [ ] Seleccionar municipio carga programas
- [ ] Botón "Cargar Modalidades" se habilita
- [ ] Aplicar filtros carga modalidades

### **Modalidades:**
- [ ] Se muestran acordeones
- [ ] Se muestran tarjetas de menús
- [ ] Click en menú abre modal

### **Preparaciones:**
- [ ] Modal "Gestionar Preparaciones" se abre
- [ ] Lista de preparaciones se muestra
- [ ] Agregar preparación funciona
- [ ] Editar preparación funciona
- [ ] Eliminar preparación funciona

### **Ingredientes:** ⭐ CRÍTICO
- [ ] Modal de ingredientes se abre
- [ ] Modal es VISIBLE (no height:0, width:0)
- [ ] Dropdown de materias primas funciona
- [ ] Agregar fila funciona
- [ ] Eliminar fila funciona
- [ ] Guardar ingredientes funciona
- [ ] Cerrar modal funciona

### **Menús Especiales:**
- [ ] Crear menú especial funciona
- [ ] Editar menú especial funciona
- [ ] Eliminar menú especial funciona

### **Análisis Nutricional:**
- [ ] Modal de análisis se abre
- [ ] Datos se cargan correctamente
- [ ] Inputs son editables
- [ ] Recálculo funciona

---

## 🎉 **SI TODO FUNCIONA:**

¡Felicitaciones! La refactorización fue exitosa. Ahora tienes:
- ✅ Código modularizado y organizado
- ✅ Fácil de mantener
- ✅ Fácil de probar
- ✅ Fácil de extender
- ✅ 100% compatible con el sistema anterior

---

## 📝 **REPORTAR RESULTADOS**

Después de probar, comparte los resultados:

```
🧪 RESULTADOS DE PRUEBAS:
✅ Inicialización: OK
✅ Filtros: OK
✅ Modalidades: OK
✅ Preparaciones: OK
✅ Ingredientes: OK
✅ Menús Especiales: OK
✅ Análisis Nutricional: OK

🎉 REFACTORIZACIÓN EXITOSA
```

O si hay problemas:

```
⚠️ PROBLEMAS ENCONTRADOS:
❌ [Descripción del problema]
📋 Error en consola: [Error específico]
🔍 Pasos para reproducir: [Pasos]
```

---

## 🔄 **ROLLBACK (SI ES NECESARIO)**

Si hay problemas críticos, puedes hacer rollback fácilmente:

1. Abre `erp_chvs/templates/nutricion/lista_menus.html`
2. Comenta los módulos refactorizados:
```html
<!-- MÓDULOS REFACTORIZADOS (TEMPORALMENTE DESHABILITADOS)
<script src="{% static 'js/nutricion/modules/ModalesManager.js' %}"></script>
...
<script src="{% static 'js/nutricion/menus_avanzado_refactorizado.js' %}"></script>
-->
```
3. Descomenta el archivo original:
```html
<script src="{% static 'js/nutricion/menus_avanzado.js' %}"></script>
```
4. Recarga la página

---

**¡Listo para probar!** 🚀
