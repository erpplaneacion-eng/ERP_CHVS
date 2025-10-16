# 📦 INSTRUCCIONES DE INSTALACIÓN - Módulos Refactorizados

## 🎯 OBJETIVO
Reemplazar el archivo monolítico `menus_avanzado.js` (1644 líneas) con el sistema modularizado (8 módulos).

---

## 📋 PASO 1: ACTUALIZAR HTML

### **Archivo:** `erp_chvs/templates/nutricion/lista_menus.html`

### **REEMPLAZAR:**
```html
{% block extra_js %}
<!-- jQuery (requerido por Select2) -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<!-- Select2 JS -->
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<!-- Utilidades de Nutrición -->
<script src="{% static 'js/nutricion/core/utils.js' %}"></script>
<!-- Módulos de Análisis Nutricional -->
<script src="{% static 'js/nutricion/modules/calculos.js' %}"></script>
<script src="{% static 'js/nutricion/modules/guardado-automatico.js' %}"></script>
<script>
    const PROGRAMA_ACTUAL = {{ programa_seleccionado|default:"null" }};
    const MUNICIPIO_ACTUAL = {{ municipio_seleccionado|default:"null" }};
</script>
<script src="{% static 'js/nutricion/menus_avanzado.js' %}"></script>
{% endblock %}
```

### **POR:**
```html
{% block extra_js %}
<!-- jQuery (requerido por Select2) -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<!-- Select2 JS -->
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<!-- SweetAlert2 para confirmaciones -->
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

<!-- Utilidades de Nutrición -->
<script src="{% static 'js/nutricion/core/utils.js' %}"></script>

<!-- Módulos de Análisis Nutricional -->
<script src="{% static 'js/nutricion/modules/calculos.js' %}"></script>
<script src="{% static 'js/nutricion/modules/guardado-automatico.js' %}"></script>

<!-- ⭐ MÓDULOS REFACTORIZADOS (CARGAR EN ESTE ORDEN) ⭐ -->
<script src="{% static 'js/nutricion/modules/ModalesManager.js' %}"></script>
<script src="{% static 'js/nutricion/modules/FiltrosManager.js' %}"></script>
<script src="{% static 'js/nutricion/modules/ModalidadesManager.js' %}"></script>
<script src="{% static 'js/nutricion/modules/PreparacionesManager.js' %}"></script>
<script src="{% static 'js/nutricion/modules/IngredientesManager.js' %}"></script>
<script src="{% static 'js/nutricion/modules/AnalisisNutricionalManager.js' %}"></script>
<script src="{% static 'js/nutricion/modules/MenusEspecialesManager.js' %}"></script>

<!-- Variables globales -->
<script>
    const PROGRAMA_ACTUAL = {{ programa_seleccionado|default:"null" }};
    const MUNICIPIO_ACTUAL = {{ municipio_seleccionado|default:"null" }};
</script>

<!-- Controlador principal refactorizado -->
<script src="{% static 'js/nutricion/menus_avanzado_refactorizado.js' %}"></script>
{% endblock %}
```

---

## ⚠️ IMPORTANTE: ORDEN DE CARGA

Los módulos **DEBEN** cargarse en este orden específico:

1. **ModalesManager** - No tiene dependencias
2. **FiltrosManager** - No tiene dependencias
3. **ModalidadesManager** - Depende de getCookie (global)
4. **PreparacionesManager** - Depende de ModalesManager
5. **IngredientesManager** - Depende de ModalesManager
6. **AnalisisNutricionalManager** - Depende de ModalesManager
7. **MenusEspecialesManager** - Depende de getCookie
8. **menus_avanzado_refactorizado.js** - ÚLTIMO (integra todos)

---

## 🧪 PASO 2: PROBAR LA INSTALACIÓN

### **Opción A: Test Rápido en Consola**

Abre la consola del navegador (F12) y ejecuta:

```javascript
// Verificar que todo se cargó
console.log('🧪 TEST RÁPIDO:');
console.log('MenusController:', typeof window.menusController);
console.log('FiltrosManager:', window.menusController?.filtrosManager instanceof FiltrosManager);
console.log('ModalidadesManager:', window.menusController?.modalidadesManager instanceof ModalidadesManager);
console.log('PreparacionesManager:', window.menusController?.preparacionesManager instanceof PreparacionesManager);
console.log('IngredientesManager:', window.menusController?.ingredientesManager instanceof IngredientesManager);
console.log('ModalesManager:', window.menusController?.modalesManager instanceof ModalesManager);
console.log('AnalisisNutricionalManager:', window.menusController?.analisisNutricionalManager instanceof AnalisisNutricionalManager);
console.log('MenusEspecialesManager:', window.menusController?.menusEspecialesManager instanceof MenusEspecialesManager);
```

### **Resultado Esperado:**
```
🧪 TEST RÁPIDO:
MenusController: object
FiltrosManager: true
ModalidadesManager: true
PreparacionesManager: true
IngredientesManager: true
ModalesManager: true
AnalisisNutricionalManager: true
MenusEspecialesManager: true
```

### **Opción B: Test Completo con HTML**

1. Navegar a: `http://localhost:8000/static/js/nutricion/modules/test_refactorizacion.html`
2. Hacer click en "🚀 Test Completo"
3. Verificar que todos los tests pasen

---

## 🔄 PASO 3: ROLLBACK (SI HAY PROBLEMAS)

Si algo sale mal, simplemente revierte el cambio en el HTML:

```html
<!-- Comentar módulos nuevos -->
<!--
<script src="{% static 'js/nutricion/modules/ModalesManager.js' %}"></script>
...
<script src="{% static 'js/nutricion/menus_avanzado_refactorizado.js' %}"></script>
-->

<!-- Descomentar archivo original -->
<script src="{% static 'js/nutricion/menus_avanzado.js' %}"></script>
```

---

## ✅ VERIFICACIÓN DE FUNCIONALIDAD

Después de instalar, verifica que todo funciona:

### **1. Filtros**
- [ ] Seleccionar municipio carga programas
- [ ] Botón "Cargar Modalidades" se habilita
- [ ] Aplicar filtros carga las modalidades

### **2. Modalidades**
- [ ] Se muestran acordeones de modalidades
- [ ] Se muestran tarjetas de menús (1-20)
- [ ] Botón "Generar 20 Menús" funciona
- [ ] Descargar Excel de modalidad funciona

### **3. Gestionar Preparaciones**
- [ ] Click en menú abre modal de preparaciones
- [ ] Lista de preparaciones se muestra
- [ ] Botón "Agregar Preparación" funciona
- [ ] Editar preparación funciona
- [ ] Eliminar preparación funciona
- [ ] Copiar preparación funciona

### **4. Agregar Ingredientes**
- [ ] Botón "Agregar Ingredientes" abre modal
- [ ] Modal se muestra correctamente (centrado, visible)
- [ ] Dropdown de materias primas funciona (Select2)
- [ ] Agregar fila funciona
- [ ] Eliminar fila funciona
- [ ] Guardar ingredientes funciona
- [ ] Cerrar modal funciona

### **5. Menús Especiales**
- [ ] Botón "Crear Menú Especial" abre modal
- [ ] Crear menú especial funciona
- [ ] Editar menú especial funciona
- [ ] Eliminar menú especial funciona

### **6. Análisis Nutricional**
- [ ] Botón "Análisis Nutricional" abre modal
- [ ] Se cargan datos por niveles escolares
- [ ] Se muestran totales correctamente
- [ ] Inputs son editables
- [ ] Recálculo funciona

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### **Error: "Manager is not defined"**
**Causa:** Orden de carga incorrecto de scripts
**Solución:** Verificar que los módulos se cargan en el orden especificado arriba

### **Error: "Function is not defined"**
**Causa:** El archivo principal no se cargó después de los módulos
**Solución:** Verificar que `menus_avanzado_refactorizado.js` es el ÚLTIMO script

### **Error: Modal no se muestra**
**Causa:** ModalesManager no se inicializó correctamente
**Solución:** 
```javascript
// En consola:
window.menusController.modalesManager.abrirModal('modalPreparaciones');
```

### **Error: "Cannot read property of null"**
**Causa:** El DOM no está listo cuando se ejecuta el código
**Solución:** Verificar que todos los IDs de HTML coinciden con los que usan los managers

---

## 📦 ARCHIVOS DEL SISTEMA REFACTORIZADO

```
erp_chvs/static/js/nutricion/
├── modules/
│   ├── ModalesManager.js                  ← Gestión de modales
│   ├── FiltrosManager.js                  ← Gestión de filtros
│   ├── ModalidadesManager.js              ← Gestión de modalidades
│   ├── PreparacionesManager.js            ← Gestión de preparaciones
│   ├── IngredientesManager.js             ← Gestión de ingredientes
│   ├── AnalisisNutricionalManager.js      ← Análisis nutricional
│   ├── MenusEspecialesManager.js          ← Menús especiales
│   ├── TESTS_REFACTORIZACION.md           ← Documentación de tests
│   ├── INSTRUCCIONES_INSTALACION.md       ← Este archivo
│   └── test_refactorizacion.html          ← Página de tests
├── menus_avanzado_refactorizado.js        ← Controlador principal
└── menus_avanzado.js                      ← Archivo original (backup)
```

---

## 🎯 BENEFICIOS DE LA REFACTORIZACIÓN

1. **Mantenibilidad:** Código organizado en módulos pequeños y específicos
2. **Testeable:** Cada módulo se puede probar independientemente
3. **Reutilizable:** Los managers pueden usarse en otras vistas
4. **Escalable:** Fácil agregar nuevas funcionalidades
5. **Legible:** Código más claro y fácil de entender
6. **Debuggable:** Más fácil encontrar y corregir errores

---

## 📞 SOPORTE

Si encuentras algún problema:
1. Revisar la consola del navegador (F12)
2. Ejecutar tests de diagnóstico (ver arriba)
3. Consultar `TESTS_REFACTORIZACION.md`
4. Hacer rollback si es necesario

---

## ✅ CHECKLIST DE INSTALACIÓN

- [ ] Actualizar HTML con nuevos scripts
- [ ] Verificar orden de carga de módulos
- [ ] Ejecutar test rápido en consola
- [ ] Probar funcionalidad básica (filtros, menús, preparaciones)
- [ ] Probar modal de ingredientes
- [ ] Probar análisis nutricional
- [ ] Verificar que no hay errores en consola
- [ ] Hacer commit del cambio

---

**¡Listo para usar!** 🚀
