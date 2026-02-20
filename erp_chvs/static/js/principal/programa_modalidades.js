/**
 * programa_modalidades.js
 * Gestión de modalidades por programa
 */

// Objeto para almacenar los cambios pendientes
let cambiosPendientes = {};

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    inicializarEventListeners();
});

/**
 * Inicializar todos los event listeners
 */
function inicializarEventListeners() {
    // Acordeones de programas
    document.querySelectorAll('.municipio-card-header').forEach(header => {
        header.addEventListener('click', function() {
            toggleCard(this);
        });
    });

    // Toggles de modalidades
    document.querySelectorAll('.modalidad-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(event) {
            event.stopPropagation();
            const programaId = this.getAttribute('data-programa-id');
            const modalidadId = this.getAttribute('data-modalidad-id');
            toggleModalidad(programaId, modalidadId, this);
        });
    });

    // Botón guardar
    const btnGuardar = document.getElementById('btnGuardarCambios');
    if (btnGuardar) {
        btnGuardar.addEventListener('click', guardarTodosLosCambios);
    }

    // Búsqueda
    const searchInput = document.getElementById('searchPrograma');
    if (searchInput) {
        searchInput.addEventListener('keyup', filtrarProgramas);
    }
}

/**
 * Toggle del acordeón de programa
 */
function toggleCard(header) {
    const card = header.parentElement;
    const body = card.querySelector('.municipio-card-body');

    // Cerrar otros acordeones
    document.querySelectorAll('.municipio-card-header').forEach(h => {
        if (h !== header) {
            h.classList.remove('active');
            h.parentElement.querySelector('.municipio-card-body').classList.remove('active');
        }
    });

    header.classList.toggle('active');
    body.classList.toggle('active');
}

/**
 * Toggle de una modalidad para un programa
 */
function toggleModalidad(programaId, modalidadId, toggleElement) {
    const modalidadItem = toggleElement.closest('.modalidad-item');
    const isActive = toggleElement.classList.contains('active');

    if (isActive) {
        toggleElement.classList.remove('active');
        modalidadItem.classList.remove('active');
    } else {
        toggleElement.classList.add('active');
        modalidadItem.classList.add('active');
    }

    if (!cambiosPendientes[programaId]) {
        cambiosPendientes[programaId] = { agregar: [], eliminar: [] };
    }

    if (isActive) {
        const addIndex = cambiosPendientes[programaId].agregar.indexOf(modalidadId);
        if (addIndex > -1) {
            cambiosPendientes[programaId].agregar.splice(addIndex, 1);
        } else if (!cambiosPendientes[programaId].eliminar.includes(modalidadId)) {
            cambiosPendientes[programaId].eliminar.push(modalidadId);
        }
    } else {
        const delIndex = cambiosPendientes[programaId].eliminar.indexOf(modalidadId);
        if (delIndex > -1) {
            cambiosPendientes[programaId].eliminar.splice(delIndex, 1);
        } else if (!cambiosPendientes[programaId].agregar.includes(modalidadId)) {
            cambiosPendientes[programaId].agregar.push(modalidadId);
        }
    }

    actualizarContador(programaId);
    mostrarIndicadorCambios();
}

/**
 * Actualizar el contador de modalidades activas del programa
 */
function actualizarContador(programaId) {
    const card = document.querySelector(`.municipio-card[data-programa-id="${programaId}"]`);
    const modalidadesActivas = card.querySelectorAll('.modalidad-item.active').length;
    const contador = card.querySelector('.modalidades-activas-count');

    if (contador) {
        contador.textContent = modalidadesActivas;
        contador.style.transform = 'scale(1.3)';
        setTimeout(() => { contador.style.transform = 'scale(1)'; }, 200);
    }
}

/**
 * Mostrar indicador de cambios pendientes en el botón
 */
function mostrarIndicadorCambios() {
    const totalCambios = Object.values(cambiosPendientes).reduce((total, acciones) => {
        return total + acciones.agregar.length + acciones.eliminar.length;
    }, 0);

    const botonGuardar = document.getElementById('btnGuardarCambios');
    if (totalCambios > 0) {
        botonGuardar.innerHTML = `<i class="fas fa-save"></i> Guardar Cambios (${totalCambios})`;
        botonGuardar.classList.add('pulse');
    } else {
        botonGuardar.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
        botonGuardar.classList.remove('pulse');
    }
}

/**
 * Guardar todos los cambios via API
 */
async function guardarTodosLosCambios() {
    const totalCambios = Object.values(cambiosPendientes).reduce((total, acciones) => {
        return total + acciones.agregar.length + acciones.eliminar.length;
    }, 0);

    if (totalCambios === 0) {
        alert('No hay cambios pendientes para guardar.');
        return;
    }

    if (!confirm(`¿Guardar ${totalCambios} cambio(s)?`)) {
        return;
    }

    const botonGuardar = document.getElementById('btnGuardarCambios');
    botonGuardar.disabled = true;
    botonGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

    try {
        const response = await fetch('/principal/api/programa-modalidades/guardar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(cambiosPendientes)
        });

        const data = await response.json();

        if (data.success) {
            mostrarNotificacion('Cambios guardados exitosamente', 'success');
            cambiosPendientes = {};
            mostrarIndicadorCambios();
            setTimeout(() => { window.location.reload(); }, 1000);
        } else {
            throw new Error(data.error || 'Error al guardar cambios');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarNotificacion('Error al guardar cambios: ' + error.message, 'error');
        botonGuardar.disabled = false;
        botonGuardar.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
    }
}

/**
 * Filtrar programas por búsqueda
 */
function filtrarProgramas() {
    const searchTerm = document.getElementById('searchPrograma').value.toLowerCase();
    const cards = document.querySelectorAll('.municipio-card');

    cards.forEach(card => {
        const nombrePrograma = card.getAttribute('data-programa-nombre').toLowerCase();
        const detalle = card.querySelector('.municipio-details p').textContent.toLowerCase();

        if (nombrePrograma.includes(searchTerm) || detalle.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Mostrar notificación temporal
 */
function mostrarNotificacion(mensaje, tipo = 'info') {
    const notif = document.createElement('div');
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${tipo === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    notif.textContent = mensaje;
    document.body.appendChild(notif);

    setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => { notif.remove(); }, 300);
    }, 3000);
}

/**
 * Obtener cookie por nombre (CSRF token)
 */
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
