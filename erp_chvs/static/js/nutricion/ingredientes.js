// Gestión de Ingredientes - Módulo de Nutrición

// Elementos del DOM
let modal, formIngrediente, modalTitle;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos
    modal = document.getElementById('modalIngrediente');
    formIngrediente = document.getElementById('formIngrediente');
    modalTitle = document.getElementById('modalTitle');

    // Event listeners
    document.getElementById('btnNuevoIngrediente').addEventListener('click', abrirModalNuevo);
    document.querySelector('.close').addEventListener('click', cerrarModal);
    formIngrediente.addEventListener('submit', guardarIngrediente);

    // Cerrar modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            cerrarModal();
        }
    });
});

function abrirModalNuevo() {
    modalTitle.textContent = 'Nuevo Ingrediente';
    formIngrediente.reset();
    document.getElementById('ingredienteId').value = '';
    modal.style.display = 'block';
}

function cerrarModal() {
    modal.style.display = 'none';
    formIngrediente.reset();
}

async function editarIngrediente(id) {
    try {
        const response = await fetch(`/nutricion/api/ingredientes/${id}/`);
        const data = await response.json();

        if (response.ok) {
            modalTitle.textContent = 'Editar Ingrediente';
            document.getElementById('ingredienteId').value = data.id_ingrediente_siesa;
            document.getElementById('ingredienteNombre').value = data.nombre_ingrediente;
            document.getElementById('ingredienteUnidades').value = data.unidades || '';
            document.getElementById('ingredientePresentacion').value = data.presentacion || '';
            modal.style.display = 'block';
        } else {
            alert('Error al cargar el ingrediente');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar el ingrediente');
    }
}

async function guardarIngrediente(event) {
    event.preventDefault();

    const id = document.getElementById('ingredienteId').value;
    const data = {
        nombre_ingrediente: document.getElementById('ingredienteNombre').value,
        unidades: document.getElementById('ingredienteUnidades').value,
        presentacion: document.getElementById('ingredientePresentacion').value
    };

    const url = id ? `/nutricion/api/ingredientes/${id}/` : '/nutricion/api/ingredientes/';
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
            alert(id ? 'Ingrediente actualizado exitosamente' : 'Ingrediente creado exitosamente');
            cerrarModal();
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al guardar el ingrediente');
    }
}

async function eliminarIngrediente(id) {
    if (!confirm('¿Está seguro de eliminar este ingrediente?')) {
        return;
    }

    try {
        const response = await fetch(`/nutricion/api/ingredientes/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const result = await response.json();

        if (result.success) {
            alert('Ingrediente eliminado exitosamente');
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error al eliminar'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el ingrediente');
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
