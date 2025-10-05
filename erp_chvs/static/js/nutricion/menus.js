/**
 * Gestión de Menús - Módulo de Nutrición
 * ✨ REFACTORIZADO: Usa módulos core (ModalManager, ApiClient)
 */

// Configuración del módulo
const MENU_CONFIG = {
    modalId: 'modalMenu',
    formId: 'formMenu',
    apiEndpoint: '/nutricion/api/menus/'
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
});

function inicializarEventos() {
    // Botón nuevo menú
    const btnNuevo = document.getElementById('btnNuevoMenu');
    if (btnNuevo) {
        btnNuevo.addEventListener('click', () => abrirModalNuevo());
    }

    // Formulario
    const form = document.getElementById(MENU_CONFIG.formId);
    if (form) {
        form.addEventListener('submit', guardarMenu);
    }

    // Cerrar modal con X
    const closeBtn = document.querySelector(`#${MENU_CONFIG.modalId} .close`);
    if (closeBtn) {
        closeBtn.addEventListener('click', () => cerrarModal());
    }

    // Cerrar modal al hacer clic fuera
    const modal = document.getElementById(MENU_CONFIG.modalId);
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
    const form = document.getElementById(MENU_CONFIG.formId);

    if (modalTitle) modalTitle.textContent = 'Nuevo Menú';
    if (form) form.reset();

    document.getElementById('menuId').value = '';
    ModalManager.abrir(MENU_CONFIG.modalId);
}

function cerrarModal() {
    const form = document.getElementById(MENU_CONFIG.formId);
    if (form) form.reset();

    ModalManager.cerrar(MENU_CONFIG.modalId);
}

async function editarMenu(id) {
    try {
        const data = await ApiClient.get(`${MENU_CONFIG.apiEndpoint}${id}/`);

        // Llenar formulario
        document.getElementById('modalTitle').textContent = 'Editar Menú';
        document.getElementById('menuId').value = data.id_menu;
        document.getElementById('menuNombre').value = data.menu;
        document.getElementById('menuModalidad').value = data.id_modalidad;
        document.getElementById('menuPrograma').value = data.id_contrato;

        ModalManager.abrir(MENU_CONFIG.modalId);

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al cargar el menú');
        console.error('Error:', error);
    }
}

// =================== FUNCIONES CRUD ===================

async function guardarMenu(event) {
    event.preventDefault();

    const id = document.getElementById('menuId').value;
    const data = {
        menu: document.getElementById('menuNombre').value,
        id_modalidad: document.getElementById('menuModalidad').value,
        id_contrato: document.getElementById('menuPrograma').value
    };

    try {
        let result;

        if (id) {
            // Actualizar
            result = await ApiClient.put(`${MENU_CONFIG.apiEndpoint}${id}/`, data);
        } else {
            // Crear
            result = await ApiClient.post(MENU_CONFIG.apiEndpoint, data);
        }

        if (result.success) {
            NutricionUtils.mostrarNotificacion(
                'success',
                id ? 'Menú actualizado exitosamente' : 'Menú creado exitosamente'
            );
            cerrarModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al guardar');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al guardar el menú');
        console.error('Error:', error);
    }
}

async function eliminarMenu(id) {
    const confirmado = await ModalManager.confirmar(
        '¿Está seguro de eliminar este menú?',
        'Esta acción eliminará también todas las preparaciones asociadas.'
    );

    if (!confirmado) return;

    try {
        const result = await ApiClient.delete(`${MENU_CONFIG.apiEndpoint}${id}/`);

        if (result.success) {
            NutricionUtils.mostrarNotificacion('success', 'Menú eliminado exitosamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al eliminar');
        }

    } catch (error) {
        NutricionUtils.mostrarNotificacion('error', 'Error al eliminar el menú');
        console.error('Error:', error);
    }
}

// Exponer funciones globales necesarias
window.editarMenu = editarMenu;
window.eliminarMenu = eliminarMenu;
