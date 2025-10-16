# 🔍 MAPEO COMPLETO: BOTONES → FUNCIONES → MODALES

## 📋 MODAL 1: Gestionar Preparaciones (`modalPreparaciones`)

### Botón que lo abre:
- **Elemento:** Tarjeta de menú (generada dinámicamente)
- **Ubicación:** ModalidadesManager.js, línea 206 y 229
- **Código:** `onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')"`
- **Función global:** `window.abrirGestionPreparaciones(menuId, menuNumero)`
- **Manager:** MenusAvanzadosController (método directo)

### Botones dentro del modal:
1. **"Agregar Preparación"** (`#btnAgregarPreparacion`)
   - Sin onclick directo
   - Manejado por event listener en MenusAvanzadosController
   - Abre: `modalNuevaPreparacion`

2. **"Ver Análisis Nutricional"** (`#btnAnalisisNutricional`)
   - Sin onclick directo
   - Manejado por event listener en MenusAvanzadosController
   - Abre: `modalAnalisisNutricional`

---

## 📋 MODAL 2: Nueva Preparación (`modalNuevaPreparacion`)

### Botón que lo abre:
- **Elemento:** `#btnAgregarPreparacion`
- **Ubicación:** lista_menus.html, línea 79
- **Evento:** Event listener configurado dinámicamente
- **Función:** `preparacionesManager.abrirModalNuevaPreparacion(menuId)`
- **Manager:** PreparacionesManager

### Botón de cerrar:
- **Elemento:** `<span class="close" onclick="cerrarModalPreparacion()">`
- **Función global:** `window.cerrarModalPreparacion()`
- **Manager:** ModalesManager

---

## 📋 MODAL 3: Agregar Ingredientes (`modalAgregarIngredientes`)

### Botón que lo abre:
- **Elemento:** Botón "Agregar Ingredientes" (generado dinámicamente)
- **Ubicación:** PreparacionesManager.js, línea 349
- **Código:** `onclick="abrirAgregarIngrediente(${preparacion.id_preparacion})"`
- **Función global:** `window.abrirAgregarIngrediente(preparacionId)`
- **Manager:** IngredientesManager

### Botones dentro del modal:
1. **"Agregar Fila"**
   - **Código:** `onclick="agregarFilaIngrediente()"`
   - **Función global:** `window.agregarFilaIngrediente()`
   - **Manager:** IngredientesManager

2. **"Guardar Ingredientes"**
   - **Código:** `onclick="guardarIngredientes()"`
   - **Función global:** `window.guardarIngredientes()`
   - **Manager:** IngredientesManager

3. **"Cancelar"**
   - **Código:** `onclick="cerrarModalIngredientes()"`
   - **Función global:** `window.cerrarModalIngredientes()`
   - **Manager:** ModalesManager

### Botones en filas de ingredientes:
- **"Eliminar ingrediente"**
  - **Código:** `onclick="eliminarIngrediente(${preparacionId}, '${ingredienteId}')"`
  - **Función global:** `window.eliminarIngrediente(preparacionId, ingredienteId)`
  - **Manager:** IngredientesManager

---

## 📋 MODAL 4: Análisis Nutricional (`modalAnalisisNutricional`)

### Botón que lo abre:
- **Elemento:** `#btnAnalisisNutricional`
- **Ubicación:** lista_menus.html, línea 82
- **Evento:** Event listener configurado
- **Función:** `menusController.abrirModalAnalisisNutricional(menuId)`
- **Manager:** AnalisisNutricionalManager

### Botón de cerrar:
- **Elemento:** `<span class="close" onclick="cerrarModalAnalisisNutricional()">`
- **Función global:** `window.cerrarModalAnalisisNutricional()`
- **Manager:** ModalesManager

---

## 📋 MODAL 5: Crear Menú Especial (`modalMenuEspecial`)

### Botón que lo abre:
- **Elemento:** Tarjeta "Crear Menú Especial" (generada dinámicamente)
- **Ubicación:** ModalidadesManager.js, línea 246
- **Código:** `onclick="abrirModalMenuEspecial('${modalidadId}')"`
- **Función global:** `window.abrirModalMenuEspecial(modalidadId)`
- **Manager:** MenusEspecialesManager

### Botón de submit:
- **Elemento:** `<form onsubmit="event.preventDefault(); crearMenuEspecial();">`
- **Función global:** `window.crearMenuEspecial()`
- **Manager:** MenusEspecialesManager

---

## 📋 MODAL 6: Editar Menú Especial (`modalEditarMenuEspecial`)

### Botón que lo abre:
- **Elemento:** Botón "Editar" en menú especial (generado dinámicamente)
- **Ubicación:** ModalidadesManager.js, línea 217
- **Código:** `onclick="abrirEditarMenuEspecial(${menu.id_menu}, '${menuEscaped}')"`
- **Función global:** `window.abrirEditarMenuEspecial(menuId, nombreActual)`
- **Manager:** MenusEspecialesManager

### Botón de submit:
- **Elemento:** `<form onsubmit="event.preventDefault(); guardarEdicionMenuEspecial();">`
- **Función global:** `window.guardarEdicionMenuEspecial()`
- **Manager:** MenusEspecialesManager

---

## ✅ FUNCIONES GLOBALES NECESARIAS

### En menus_avanzado_refactorizado.js:

```javascript
// GESTIÓN DE PREPARACIONES
window.abrirGestionPreparaciones(menuId, menuNumero)

// INGREDIENTES
window.abrirAgregarIngrediente(preparacionId)
window.agregarFilaIngrediente()
window.guardarIngredientes()
window.eliminarIngrediente(preparacionId, ingredienteId)  // ⚠️ 2 parámetros!
window.eliminarFilaIngrediente(index)

// MENÚS ESPECIALES
window.abrirModalMenuEspecial(modalidadId)
window.crearMenuEspecial()
window.abrirEditarMenuEspecial(menuId, nombreActual)
window.guardarEdicionMenuEspecial()
window.eliminarMenuEspecial(menuId, nombreMenu)

// MODALES (cerrar)
window.cerrarModalPreparacion()
window.cerrarModalIngredientes()
window.cerrarModalAnalisisNutricional()
```

---

## ⚠️ PROBLEMAS DETECTADOS

1. **`eliminarIngrediente`** recibe **2 parámetros** en el HTML pero la función global solo recibe 1
2. Event listeners para `btnAgregarPreparacion` y `btnAnalisisNutricional` deben estar correctamente configurados

