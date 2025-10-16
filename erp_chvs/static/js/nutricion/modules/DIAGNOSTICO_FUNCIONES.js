/**
 * SCRIPT DE DIAGNÓSTICO - Verificar Funciones Globales
 * Copia y pega este código en la consola del navegador
 */

console.log('═══════════════════════════════════════════════════════════');
console.log('🔍 DIAGNÓSTICO COMPLETO DE FUNCIONES GLOBALES');
console.log('═══════════════════════════════════════════════════════════\n');

// 1. Verificar MenusController
console.log('1️⃣ CONTROLADOR PRINCIPAL:');
console.log('   window.menusController:', typeof window.menusController);
console.log('   Es instancia correcta:', window.menusController instanceof MenusAvanzadosController);
console.log('');

// 2. Verificar Managers
console.log('2️⃣ MANAGERS INSTANCIADOS:');
const managers = {
    'filtrosManager': FiltrosManager,
    'modalidadesManager': ModalidadesManager,
    'preparacionesManager': PreparacionesManager,
    'ingredientesManager': IngredientesManager,
    'modalesManager': ModalesManager,
    'analisisNutricionalManager': AnalisisNutricionalManager,
    'menusEspecialesManager': MenusEspecialesManager
};

Object.entries(managers).forEach(([propName, className]) => {
    const instance = window.menusController?.[propName];
    const isCorrect = instance instanceof className;
    console.log(`   ${isCorrect ? '✅' : '❌'} ${propName}: ${typeof instance} (${isCorrect ? 'OK' : 'ERROR'})`);
});
console.log('');

// 3. Verificar Funciones Globales
console.log('3️⃣ FUNCIONES GLOBALES DISPONIBLES:');

const funcionesEsperadas = {
    // Gestión de menús
    'abrirGestionPreparaciones': 'function',
    
    // Análisis nutricional
    'abrirModalAnalisisNutricional': 'function',
    
    // Menús especiales
    'abrirModalMenuEspecial': 'function',
    'crearMenuEspecial': 'function',
    'abrirEditarMenuEspecial': 'function',
    'guardarEdicionMenuEspecial': 'function',
    'eliminarMenuEspecial': 'function',
    
    // Ingredientes
    'abrirAgregarIngrediente': 'function',
    'agregarFilaIngrediente': 'function',
    'guardarIngredientes': 'function',
    'eliminarIngrediente': 'function',
    'eliminarFilaIngrediente': 'function',
    
    // Cerrar modales
    'cerrarModalPreparacion': 'function',
    'cerrarModalIngredientes': 'function',
    'cerrarModalAnalisisNutricional': 'function'
};

let funcionesOK = 0;
let funcionesERROR = 0;

Object.entries(funcionesEsperadas).forEach(([nombreFuncion, tipoEsperado]) => {
    const tipoActual = typeof window[nombreFuncion];
    const isCorrect = tipoActual === tipoEsperado;
    
    if (isCorrect) {
        funcionesOK++;
        console.log(`   ✅ window.${nombreFuncion}`);
    } else {
        funcionesERROR++;
        console.log(`   ❌ window.${nombreFuncion} (esperado: ${tipoEsperado}, actual: ${tipoActual})`);
    }
});

console.log('');
console.log(`   Total: ${funcionesOK} OK, ${funcionesERROR} ERROR`);
console.log('');

// 4. Verificar Modales en DOM
console.log('4️⃣ MODALES EN EL DOM:');
const modales = [
    'modalPreparaciones',
    'modalNuevaPreparacion',
    'modalAgregarIngredientes',
    'modalAnalisisNutricional',
    'modalMenuEspecial',
    'modalEditarMenuEspecial'
];

modales.forEach(modalId => {
    const modal = document.getElementById(modalId);
    console.log(`   ${modal ? '✅' : '❌'} #${modalId}`);
});
console.log('');

// 5. Verificar Event Listeners
console.log('5️⃣ EVENT LISTENERS (Botones sin onclick):');
const botonesConEventListener = [
    { id: 'btnAplicarFiltros', descripcion: 'Aplicar Filtros' },
    { id: 'btnAgregarPreparacion', descripcion: 'Agregar Preparación' },
    { id: 'btnAnalisisNutricional', descripcion: 'Análisis Nutricional' },
    { id: 'btnMostrarOpcionesCopia', descripcion: 'Mostrar Opciones Copia' },
    { id: 'btnEjecutarCopia', descripcion: 'Ejecutar Copia' }
];

botonesConEventListener.forEach(({ id, descripcion }) => {
    const btn = document.getElementById(id);
    console.log(`   ${btn ? '✅' : '⚠️'} #${id} (${descripcion})`);
});
console.log('');

// 6. Test de Funciones Críticas
console.log('6️⃣ TEST DE FUNCIONES CRÍTICAS:');

// Test abrirModalMenuEspecial
try {
    const testModalEspecial = typeof window.abrirModalMenuEspecial === 'function';
    console.log(`   ${testModalEspecial ? '✅' : '❌'} abrirModalMenuEspecial está definida`);
    
    if (testModalEspecial && window.menusController?.menusEspecialesManager) {
        console.log('   ✅ menusEspecialesManager está disponible');
    } else {
        console.log('   ❌ menusEspecialesManager NO está disponible');
    }
} catch (error) {
    console.log('   ❌ Error al verificar abrirModalMenuEspecial:', error.message);
}

// Test abrirAgregarIngrediente
try {
    const testIngredientes = typeof window.abrirAgregarIngrediente === 'function';
    console.log(`   ${testIngredientes ? '✅' : '❌'} abrirAgregarIngrediente está definida`);
    
    if (testIngredientes && window.menusController?.ingredientesManager) {
        console.log('   ✅ ingredientesManager está disponible');
    } else {
        console.log('   ❌ ingredientesManager NO está disponible');
    }
} catch (error) {
    console.log('   ❌ Error al verificar abrirAgregarIngrediente:', error.message);
}

console.log('');

// RESULTADO FINAL
console.log('═══════════════════════════════════════════════════════════');
const todoOK = funcionesERROR === 0;
if (todoOK) {
    console.log('✅ ¡TODAS LAS FUNCIONES ESTÁN CORRECTAMENTE DEFINIDAS!');
} else {
    console.log('❌ HAY ERRORES - Revisar arriba para detalles');
}
console.log('═══════════════════════════════════════════════════════════\n');

// INSTRUCCIONES
console.log('📋 SIGUIENTE PASO:');
console.log('   Si todo está OK, prueba manualmente:');
console.log('   1. Click en tarjeta "Crear Menú Especial" → window.abrirModalMenuEspecial()');
console.log('   2. Click en menú → Agregar Preparación → Modal correcto?');
console.log('   3. Click en Agregar Ingredientes → Modal correcto?');
console.log('');

