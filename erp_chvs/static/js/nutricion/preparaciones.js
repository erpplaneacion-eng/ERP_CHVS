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
        const response = await fetch(`/nutricion/api/preparaciones/${id}/`);
        const data = await response.json();

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

    const url = id ? `/nutricion/api/preparaciones/${id}/` : '/nutricion/api/preparaciones/';
    const method = id ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

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
        const response = await fetch(`/nutricion/api/preparaciones/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const result = await response.json();

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
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
