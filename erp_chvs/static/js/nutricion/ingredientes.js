/**
 * Gestión de Ingredientes - Módulo de Nutrición
 * ✨ REFACTORIZADO: Usa módulos core (ModalManager, ApiClient)
 */

// Configuración del módulo
const INGREDIENTE_CONFIG = {
    modalId: 'modalIngrediente',
    formId: 'formIngrediente',
    apiEndpoint: '/nutricion/api/ingredientes/'
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
});

function inicializarEventos() {
    // Botón nuevo ingrediente
    const btnNuevo = document.getElementById('btnNuevoIngrediente');
    if (btnNuevo) {
        btnNuevo.addEventListener('click', () => abrirModalNuevo());
    }

    // Formulario
    const form = document.getElementById(INGREDIENTE_CONFIG.formId);
    if (form) {
        form.addEventListener('submit', guardarIngrediente);
    }

    // Cerrar modal con X
    const closeBtn = document.querySelector(`#${INGREDIENTE_CONFIG.modalId} .close`);
    if (closeBtn) {
        closeBtn.addEventListener('click', () => cerrarModal());
    }

    // Cerrar modal al hacer clic fuera
    const modal = document.getElementById(INGREDIENTE_CONFIG.modalId);
    if (modal) {
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                cerrarModal();
            }
        });
    }
}

// =================== FUNCIONES DE MODAL ===================

function abrirModalNuevo() {
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById(INGREDIENTE_CONFIG.formId);
    const codigoInput = document.getElementById('ingredienteCodigo');

    if (modalTitle) modalTitle.textContent = 'Nuevo Ingrediente';
    if (form) form.reset();

    document.getElementById('ingredienteIdOriginal').value = '';
    if (codigoInput) codigoInput.disabled = false;

    ModalManager.abrir(INGREDIENTE_CONFIG.modalId);
}

function cerrarModal() {
    const form = document.getElementById(INGREDIENTE_CONFIG.formId);
    if (form) form.reset();

    ModalManager.cerrar(INGREDIENTE_CONFIG.modalId);
}

async function editarIngrediente(id) {
    try {
        const data = await ApiClient.get(`${INGREDIENTE_CONFIG.apiEndpoint}${id}/`);

        // Llenar formulario
        document.getElementById('modalTitle').textContent = 'Editar Ingrediente';
        document.getElementById('ingredienteIdOriginal').value = data.id_ingrediente_siesa;
        document.getElementById('ingredienteCodigo').value = data.id_ingrediente_siesa;
        document.getElementById('ingredienteCodigo').disabled = true; // No permitir cambiar código
        document.getElementById('ingredienteNombre').value = data.nombre_ingrediente;

        ModalManager.abrir(INGREDIENTE_CONFIG.modalId);

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al cargar el ingrediente');
        console.error('Error:', error);
    }
}

// =================== FUNCIONES CRUD ===================

async function guardarIngrediente(event) {
    event.preventDefault();

    const idOriginal = document.getElementById('ingredienteIdOriginal').value;
    const data = {
        id_ingrediente_siesa: document.getElementById('ingredienteCodigo').value.trim(),
        nombre_ingrediente: document.getElementById('ingredienteNombre').value.trim()
    };

    try {
        let result;

        if (idOriginal) {
            // Actualizar
            result = await ApiClient.put(`${INGREDIENTE_CONFIG.apiEndpoint}${idOriginal}/`, data);
        } else {
            // Crear
            result = await ApiClient.post(INGREDIENTE_CONFIG.apiEndpoint, data);
        }

        if (result.success) {
            NutricionUtils.mostrarNotificacion(
                'success',
                idOriginal ? 'Ingrediente actualizado exitosamente' : 'Ingrediente creado exitosamente'
            );
            cerrarModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al guardar');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al guardar el ingrediente');
        console.error('Error:', error);
    }
}

async function eliminarIngrediente(id) {
    const confirmado = await ModalManager.confirmar(
        '¿Está seguro de eliminar este ingrediente?',
        'Esta acción no se puede deshacer.'
    );

    if (!confirmado) return;

    try {
        const result = await ApiClient.delete(`${INGREDIENTE_CONFIG.apiEndpoint}${id}/`);

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
window.editarIngrediente = editarIngrediente;
window.eliminarIngrediente = eliminarIngrediente;
