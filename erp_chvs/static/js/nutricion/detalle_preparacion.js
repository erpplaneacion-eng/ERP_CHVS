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
        if (event.target === modal) {
            cerrarModal();
        }
    });
});

function abrirModal() {
    modal.style.display = 'block';
}

function cerrarModal() {
    modal.style.display = 'none';
    formAgregarIngrediente.reset();
}

async function agregarIngrediente(event) {
    event.preventDefault();
    
    const preparacionId = document.getElementById('preparacionId').value;
    const data = {
        ingrediente_id: document.getElementById('ingredienteSelect').value,
        cantidad: document.getElementById('cantidad').value,
        unidad_medida: document.getElementById('unidadMedida').value
    };

    try {
        const response = await fetch(`/nutricion/api/detalle-preparacion/${preparacionId}/agregar/`, {
            method: 'POST',
            headers: NutricionUtils.getDefaultHeaders(),
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        if (response.ok) {
            NutricionUtils.mostrarNotificacion('success', 'Ingrediente agregado exitosamente');
            cerrarModal();
            location.reload(); // Recargar para mostrar el nuevo ingrediente
        } else {
            NutricionUtils.mostrarNotificacion('error', result.error || 'Error al agregar ingrediente');
        }
    } catch (error) {
        NutricionUtils.manejarError(error, 'Agregar ingrediente');
    }
}

async function eliminarIngrediente(idIngrediente) {
    modalManager.confirmar(
        '¿Está seguro de que desea eliminar este ingrediente?',
        async () => {
            try {
                const response = await fetch(`/nutricion/api/detalle-preparacion/${idIngrediente}/eliminar/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': NutricionUtils.getCsrfToken()
                    }
                });

                const result = await response.json();
                
                if (response.ok) {
                    NutricionUtils.mostrarNotificacion('success', 'Ingrediente eliminado exitosamente');
                    location.reload(); // Recargar para actualizar la lista
                } else {
                    NutricionUtils.mostrarNotificacion('error', result.error || 'Error al eliminar');
                }
            } catch (error) {
                NutricionUtils.manejarError(error, 'Eliminar ingrediente');
            }
        }
    );
}

// Función getCookie ahora disponible desde utils.js