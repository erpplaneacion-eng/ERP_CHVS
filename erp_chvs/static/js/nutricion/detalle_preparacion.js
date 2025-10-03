// Gestión de Ingredientes de Preparación - Módulo de Nutrición

// Elementos del DOM
let modal, formAgregarIngrediente;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos
    modal = document.getElementById('modalIngrediente');
    formAgregarIngrediente = document.getElementById('formAgregarIngrediente');

    // Event listeners
    document.getElementById('btnAgregarIngrediente').addEventListener('click', abrirModal);
    document.querySelector('.close').addEventListener('click', cerrarModal);
    formAgregarIngrediente.addEventListener('submit', agregarIngrediente);

    // Cerrar modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            cerrarModal();
        }
    });
});

function abrirModal() {
    formAgregarIngrediente.reset();
    modal.style.display = 'block';
}

function cerrarModal() {
    modal.style.display = 'none';
    formAgregarIngrediente.reset();
}

async function agregarIngrediente(event) {
    event.preventDefault();

    const data = {
        id_ingrediente_siesa: document.getElementById('ingredienteSelect').value,
        cantidad: document.getElementById('ingredienteCantidad').value
    };

    try {
        const response = await fetch(`/nutricion/api/preparaciones/${PREPARACION_ID}/ingredientes/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('Ingrediente agregado exitosamente');
            cerrarModal();
            location.reload();
        } else {
            alert('Error: ' + (result.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al agregar el ingrediente');
    }
}

async function eliminarIngrediente(idIngrediente) {
    if (!confirm('¿Está seguro de eliminar este ingrediente de la preparación?')) {
        return;
    }

    try {
        const response = await fetch(`/nutricion/api/preparaciones/${PREPARACION_ID}/ingredientes/${idIngrediente}/`, {
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
