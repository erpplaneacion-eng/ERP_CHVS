/**
 * Gestión de Preparaciones - Módulo de Nutrición
 * ✨ REFACTORIZADO: Usa módulos core (ModalManager, ApiClient)
 */

// Configuración del módulo
const PREPARACION_CONFIG = {
    modalId: 'modalPreparacion',
    formId: 'formPreparacion',
    apiEndpoint: '/nutricion/api/preparaciones/'
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
});

function inicializarEventos() {
    // Botón nueva preparación
    const btnNuevo = document.getElementById('btnNuevaPreparacion');
    if (btnNuevo) {
        btnNuevo.addEventListener('click', () => abrirModalNuevo());
    }

    // Formulario
    const form = document.getElementById(PREPARACION_CONFIG.formId);
    if (form) {
        form.addEventListener('submit', guardarPreparacion);
    }

    // Cerrar modal con X
    const closeBtn = document.querySelector(`#${PREPARACION_CONFIG.modalId} .close`);
    if (closeBtn) {
        closeBtn.addEventListener('click', () => cerrarModal());
    }

    // Cerrar modal al hacer clic fuera
    const modal = document.getElementById(PREPARACION_CONFIG.modalId);
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
    const form = document.getElementById(PREPARACION_CONFIG.formId);

    if (modalTitle) modalTitle.textContent = 'Nueva Preparación';
    if (form) form.reset();

    document.getElementById('preparacionId').value = '';
    ModalManager.abrir(PREPARACION_CONFIG.modalId);
}

function cerrarModal() {
    const form = document.getElementById(PREPARACION_CONFIG.formId);
    if (form) form.reset();

    ModalManager.cerrar(PREPARACION_CONFIG.modalId);
}

async function editarPreparacion(id) {
    try {
        const data = await ApiClient.get(`${PREPARACION_CONFIG.apiEndpoint}${id}/`);

        // Llenar formulario
        document.getElementById('modalTitle').textContent = 'Editar Preparación';
        document.getElementById('preparacionId').value = data.id_preparacion;
        document.getElementById('preparacionNombre').value = data.preparacion;
        document.getElementById('preparacionMenu').value = data.id_menu;

        ModalManager.abrir(PREPARACION_CONFIG.modalId);

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al cargar la preparación');
        console.error('Error:', error);
    }
}

// =================== FUNCIONES CRUD ===================

async function guardarPreparacion(event) {
    event.preventDefault();

    const id = document.getElementById('preparacionId').value;
    const data = {
        preparacion: document.getElementById('preparacionNombre').value,
        id_menu: document.getElementById('preparacionMenu').value
    };

    try {
        let result;

        if (id) {
            // Actualizar
            result = await ApiClient.put(`${PREPARACION_CONFIG.apiEndpoint}${id}/`, data);
        } else {
            // Crear
            result = await ApiClient.post(PREPARACION_CONFIG.apiEndpoint, data);
        }

        if (result.success) {
            NutricionUtils.mostrarNotificacion(
                'success',
                id ? 'Preparación actualizada exitosamente' : 'Preparación creada exitosamente'
            );
            cerrarModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al guardar');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al guardar la preparación');
        console.error('Error:', error);
    }
}

async function eliminarPreparacion(id) {
    const confirmado = await ModalManager.confirmar(
        '¿Está seguro de eliminar esta preparación?',
        'Se eliminarán también todos sus ingredientes asociados.'
    );

    if (!confirmado) return;

    try {
        const result = await ApiClient.delete(`${PREPARACION_CONFIG.apiEndpoint}${id}/`);

        if (result.success) {
            NutricionUtils.mostrarNotificacion('success', 'Preparación eliminada exitosamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al eliminar');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al eliminar la preparación');
        console.error('Error:', error);
    }
}

// Exponer funciones globales necesarias
window.editarPreparacion = editarPreparacion;
window.eliminarPreparacion = eliminarPreparacion;
