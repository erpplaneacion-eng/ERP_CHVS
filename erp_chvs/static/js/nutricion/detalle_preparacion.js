/**
 * Gestión de Ingredientes de Preparación - Módulo de Nutrición
 * ✨ REFACTORIZADO: Usa módulos core (ModalManager, ApiClient)
 */

// Configuración del módulo
const DETALLE_PREPARACION_CONFIG = {
    modalId: 'modalIngrediente',
    formId: 'formAgregarIngrediente',
    apiEndpoint: '/nutricion/api/detalle-preparacion/'
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
});

function inicializarEventos() {
    // Botón agregar ingrediente
    const btnAgregar = document.getElementById('btnAgregarIngrediente');
    if (btnAgregar) {
        btnAgregar.addEventListener('click', () => abrirModal());
    }

    // Formulario
    const form = document.getElementById(DETALLE_PREPARACION_CONFIG.formId);
    if (form) {
        form.addEventListener('submit', agregarIngrediente);
    }

    // Cerrar modal con X
    const closeBtn = document.querySelector(`#${DETALLE_PREPARACION_CONFIG.modalId} .close`);
    if (closeBtn) {
        closeBtn.addEventListener('click', () => cerrarModal());
    }

    // Cerrar modal al hacer clic fuera
    const modal = document.getElementById(DETALLE_PREPARACION_CONFIG.modalId);
    if (modal) {
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                cerrarModal();
            }
        });
    }
}

// =================== FUNCIONES DE MODAL ===================

function abrirModal() {
    const form = document.getElementById(DETALLE_PREPARACION_CONFIG.formId);
    if (form) form.reset();

    ModalManager.abrir(DETALLE_PREPARACION_CONFIG.modalId);
}

function cerrarModal() {
    const form = document.getElementById(DETALLE_PREPARACION_CONFIG.formId);
    if (form) form.reset();

    ModalManager.cerrar(DETALLE_PREPARACION_CONFIG.modalId);
}

// =================== FUNCIONES CRUD ===================

async function agregarIngrediente(event) {
    event.preventDefault();

    const preparacionId = document.getElementById('preparacionId').value;
    const data = {
        ingrediente_id: document.getElementById('ingredienteSelect').value,
        cantidad: document.getElementById('cantidad').value,
        unidad_medida: document.getElementById('unidadMedida').value
    };

    try {
        const result = await ApiClient.post(
            `${DETALLE_PREPARACION_CONFIG.apiEndpoint}${preparacionId}/agregar/`,
            data
        );

        if (result.success) {
            NutricionUtils.mostrarNotificacion('success', 'Ingrediente agregado exitosamente');
            cerrarModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al agregar ingrediente');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al agregar el ingrediente');
        console.error('Error:', error);
    }
}

async function eliminarIngrediente(idIngrediente) {
    const confirmado = await ModalManager.confirmar(
        '¿Está seguro de eliminar este ingrediente de la preparación?',
        'Esta acción no se puede deshacer.'
    );

    if (!confirmado) return;

    try {
        const result = await ApiClient.delete(
            `${DETALLE_PREPARACION_CONFIG.apiEndpoint}${idIngrediente}/eliminar/`
        );

        if (result.success) {
            NutricionUtils.mostrarNotificacion('success', 'Ingrediente eliminado exitosamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al eliminar');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al eliminar el ingrediente');
        console.error('Error:', error);
    }
}

// Exponer funciones globales necesarias
window.eliminarIngrediente = eliminarIngrediente;
