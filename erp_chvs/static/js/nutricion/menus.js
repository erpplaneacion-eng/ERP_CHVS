// Gestión de Menús - Módulo de Nutrición

// Elementos del DOM
let modal, formMenu, modalTitle;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos
    modal = document.getElementById('modalMenu');
    formMenu = document.getElementById('formMenu');
    modalTitle = document.getElementById('modalTitle');

    // Event listeners
    document.getElementById('btnNuevoMenu').addEventListener('click', abrirModalNuevo);
    document.querySelector('.close').addEventListener('click', cerrarModal);
    formMenu.addEventListener('submit', guardarMenu);

    // Cerrar modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            cerrarModal();
        }
    });
});

function abrirModalNuevo() {
    modalTitle.textContent = 'Nuevo Menú';
    formMenu.reset();
    document.getElementById('menuId').value = '';
    modal.style.display = 'block';
}

function cerrarModal() {
    modal.style.display = 'none';
    formMenu.reset();
}

async function editarMenu(id) {
    try {
        const response = await fetch(`/nutricion/api/menus/${id}/`);
        const data = await response.json();

        if (response.ok) {
            modalTitle.textContent = 'Editar Menú';
            document.getElementById('menuId').value = data.id_menu;
            document.getElementById('menuNombre').value = data.menu;
            document.getElementById('menuModalidad').value = data.id_modalidad;
            document.getElementById('menuPrograma').value = data.id_contrato;
            modal.style.display = 'block';
        } else {
            alert('Error al cargar el menú');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar el menú');
    }
}

async function guardarMenu(event) {
    event.preventDefault();

    const id = document.getElementById('menuId').value;
    const data = {
        menu: document.getElementById('menuNombre').value,
        id_modalidad: document.getElementById('menuModalidad').value,
        id_contrato: document.getElementById('menuPrograma').value
    };

    const url = id ? `/nutricion/api/menus/${id}/` : '/nutricion/api/menus/';
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
            alert(id ? 'Menú actualizado exitosamente' : 'Menú creado exitosamente');
            cerrarModal();
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar el menú');
    }
}

async function eliminarMenu(id) {
    if (!confirm('¿Está seguro de eliminar este menú? Esta acción eliminará también todas las preparaciones asociadas.')) {
        return;
    }

    try {
        const response = await fetch(`/nutricion/api/menus/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const result = await response.json();

        if (result.success) {
            alert('Menú eliminado exitosamente');
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error al eliminar'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el menú');
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
