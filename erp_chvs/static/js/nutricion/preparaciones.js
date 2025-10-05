// Gestión de Preparaciones - Módulo de Nutrición

// Elementos del DOM
let modal, formPreparacion, modalTitle;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos
    modal = document.getElementById('modalPreparacion');
    formPreparacion = document.getElementById('formPreparacion');
    modalTitle = document.getElementById('modalTitle');

    // Event listeners
    document.getElementById('btnNuevaPreparacion').addEventListener('click', abrirModalNuevo);
    document.querySelector('.close').addEventListener('click', cerrarModal);
    formPreparacion.addEventListener('submit', guardarPreparacion);

    // Cerrar modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            cerrarModal();
        }
    });
});

function abrirModalNuevo() {
    modalTitle.textContent = 'Nueva Preparación';
    formPreparacion.reset();
    document.getElementById('preparacionId').value = '';
    modal.style.display = 'block';
}

function cerrarModal() {
    modal.style.display = 'none';
    formPreparacion.reset();
}

async function editarPreparacion(id) {
    try {
        const data = await nutricionAPI.obtenerPreparacion(id);

        if (response.ok) {
            modalTitle.textContent = 'Editar Preparación';
            document.getElementById('preparacionId').value = data.id_preparacion;
            document.getElementById('preparacionNombre').value = data.preparacion;
            document.getElementById('preparacionMenu').value = data.id_menu;
            modal.style.display = 'block';
        } else {
            alert('Error al cargar la preparación');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar la preparación');
    }
}

async function guardarPreparacion(event) {
    event.preventDefault();

    const id = document.getElementById('preparacionId').value;
    const data = {
        preparacion: document.getElementById('preparacionNombre').value,
        id_menu: document.getElementById('preparacionMenu').value
    };

    try {
        const result = id ? 
            await nutricionAPI.editarPreparacion(id, data) :
            await nutricionAPI.crearPreparacion(data);

        if (result.success) {
            alert(id ? 'Preparación actualizada exitosamente' : 'Preparación creada exitosamente');
            cerrarModal();
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar la preparación');
    }
}

async function eliminarPreparacion(id) {
    if (!confirm('¿Está seguro de eliminar esta preparación? Se eliminarán también todos sus ingredientes asociados.')) {
        return;
    }

    try {
        const result = await nutricionAPI.eliminarPreparacion(id);

        if (result.success) {
            alert('Preparación eliminada exitosamente');
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error al eliminar'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar la preparación');
    }
}

// Función auxiliar para obtener el token CSRF
// Función getCookie ahora disponible desde utils.js
