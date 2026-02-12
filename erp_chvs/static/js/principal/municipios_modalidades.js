/**
 * municipios_modalidades.js
 * Gestión de modalidades por municipio
 */

// Objeto para almacenar los cambios pendientes
let cambiosPendientes = {};

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Módulo de Modalidades por Municipio cargado correctamente');

    // Event listeners
    inicializarEventListeners();
});

/**
 * Inicializar todos los event listeners
 */
function inicializarEventListeners() {
    // Event listener para acordeones de municipios
    document.querySelectorAll('.municipio-card-header').forEach(header => {
        header.addEventListener('click', function() {
            toggleMunicipioCard(this);
        });
    });

    // Event listener para toggles de modalidades
    document.querySelectorAll('.modalidad-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(event) {
            event.stopPropagation();
            const municipioId = this.getAttribute('data-municipio-id');
            const modalidadId = this.getAttribute('data-modalidad-id');
            toggleModalidad(municipioId, modalidadId, this);
        });
    });

    // Event listener para botón de guardar
    const btnGuardar = document.getElementById('btnGuardarCambios');
    if (btnGuardar) {
        btnGuardar.addEventListener('click', guardarTodosLosCambios);
    }

    // Event listener para búsqueda
    const searchInput = document.getElementById('searchMunicipio');
    if (searchInput) {
        searchInput.addEventListener('keyup', filtrarMunicipios);
    }
}

/**
 * Toggle del acordeón de municipio
 */
function toggleMunicipioCard(header) {
    const card = header.parentElement;
    const body = card.querySelector('.municipio-card-body');

    // Cerrar otros acordeones
    document.querySelectorAll('.municipio-card-header').forEach(h => {
        if (h !== header) {
            h.classList.remove('active');
            h.parentElement.querySelector('.municipio-card-body').classList.remove('active');
        }
    });

    // Toggle del acordeón actual
    header.classList.toggle('active');
    body.classList.toggle('active');
}

/**
 * Toggle de una modalidad para un municipio
 */
function toggleModalidad(municipioId, modalidadId, toggleElement) {
    const modalidadItem = toggleElement.closest('.modalidad-item');
    const isActive = toggleElement.classList.contains('active');

    // Toggle visual
    if (isActive) {
        toggleElement.classList.remove('active');
        modalidadItem.classList.remove('active');
    } else {
        toggleElement.classList.add('active');
        modalidadItem.classList.add('active');
    }

    // Registrar el cambio
    if (!cambiosPendientes[municipioId]) {
        cambiosPendientes[municipioId] = {
            agregar: [],
            eliminar: []
        };
    }

    if (isActive) {
        // Estaba activo, ahora lo desactivamos
        const addIndex = cambiosPendientes[municipioId].agregar.indexOf(modalidadId);
        if (addIndex > -1) {
            // Estaba en la lista de agregar, simplemente lo quitamos
            cambiosPendientes[municipioId].agregar.splice(addIndex, 1);
        } else {
            // No estaba en agregar, lo agregamos a eliminar
            if (!cambiosPendientes[municipioId].eliminar.includes(modalidadId)) {
                cambiosPendientes[municipioId].eliminar.push(modalidadId);
            }
        }
    } else {
        // Estaba inactivo, ahora lo activamos
        const delIndex = cambiosPendientes[municipioId].eliminar.indexOf(modalidadId);
        if (delIndex > -1) {
            // Estaba en la lista de eliminar, simplemente lo quitamos
            cambiosPendientes[municipioId].eliminar.splice(delIndex, 1);
        } else {
            // No estaba en eliminar, lo agregamos a agregar
            if (!cambiosPendientes[municipioId].agregar.includes(modalidadId)) {
                cambiosPendientes[municipioId].agregar.push(modalidadId);
            }
        }
    }

    // Actualizar el contador de modalidades activas
    actualizarContador(municipioId);

    // Mostrar indicador de cambios pendientes
    mostrarIndicadorCambios();
}

/**
 * Actualizar el contador de modalidades activas
 */
function actualizarContador(municipioId) {
    const card = document.querySelector(`.municipio-card[data-municipio-id="${municipioId}"]`);
    const modalidadesActivas = card.querySelectorAll('.modalidad-item.active').length;
    const contador = card.querySelector('.modalidades-activas-count');

    if (contador) {
        contador.textContent = modalidadesActivas;

        // Animación del contador
        contador.style.transform = 'scale(1.3)';
        setTimeout(() => {
            contador.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Mostrar indicador de cambios pendientes
 */
function mostrarIndicadorCambios() {
    const totalCambios = Object.keys(cambiosPendientes).reduce((total, municipioId) => {
        return total +
               cambiosPendientes[municipioId].agregar.length +
               cambiosPendientes[municipioId].eliminar.length;
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
 * Guardar todos los cambios
 */
async function guardarTodosLosCambios() {
    // Verificar si hay cambios pendientes
    const totalCambios = Object.keys(cambiosPendientes).reduce((total, municipioId) => {
        return total +
               cambiosPendientes[municipioId].agregar.length +
               cambiosPendientes[municipioId].eliminar.length;
    }, 0);

    if (totalCambios === 0) {
        alert('No hay cambios pendientes para guardar.');
        return;
    }

    // Confirmar acción
    if (!confirm(`¿Guardar ${totalCambios} cambio(s)?`)) {
        return;
    }

    const botonGuardar = document.getElementById('btnGuardarCambios');
    botonGuardar.disabled = true;
    botonGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

    try {
        const response = await fetch('/principal/api/municipio-modalidades/guardar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(cambiosPendientes)
        });

        const data = await response.json();

        if (data.success) {
            // Mostrar mensaje de éxito
            mostrarNotificacion('Cambios guardados exitosamente', 'success');

            // Limpiar cambios pendientes
            cambiosPendientes = {};
            mostrarIndicadorCambios();

            // Recargar la página después de 1 segundo
            setTimeout(() => {
                window.location.reload();
            }, 1000);
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
 * Filtrar municipios por búsqueda
 */
function filtrarMunicipios() {
    const searchTerm = document.getElementById('searchMunicipio').value.toLowerCase();
    const cards = document.querySelectorAll('.municipio-card');

    cards.forEach(card => {
        const nombreMunicipio = card.getAttribute('data-municipio-nombre').toLowerCase();
        const codigoMunicipio = card.querySelector('.municipio-details p').textContent.toLowerCase();

        if (nombreMunicipio.includes(searchTerm) || codigoMunicipio.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

/**
 * Mostrar notificación
 */
function mostrarNotificacion(mensaje, tipo = 'info') {
    // Crear elemento de notificación
    const notif = document.createElement('div');
    notif.className = `notification notification-${tipo}`;
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${tipo === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    notif.textContent = mensaje;

    document.body.appendChild(notif);

    // Remover después de 3 segundos
    setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notif.remove();
        }, 300);
    }, 3000);
}

/**
 * Obtener cookie (para CSRF token)
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
