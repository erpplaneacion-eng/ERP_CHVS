// Variables globales
let editingMode = false;
let currentSedeId = null;
let instituciones = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Verificar que las funciones globales estén disponibles
    if (typeof window.showNotification !== 'function') {
        console.error('showNotification no está disponible desde main.js');
    }

    loadInstituciones();
    updateStats();
    setupSearch();
});

// Funciones para cargar datos de referencia
async function loadInstituciones() {
    try {
        const response = await fetch('/principal/api/instituciones/');
        const data = await response.json();
        instituciones = data.instituciones;

        const select = document.getElementById('codigo_ie');
        select.innerHTML = '<option value="">Seleccione una institución</option>';

        instituciones.forEach(inst => {
            select.innerHTML += `<option value="${inst.codigo_ie}">${inst.nombre_institucion}</option>`;
        });
    } catch (error) {
        console.error('Error al cargar instituciones:', error);
        showNotification('Error al cargar instituciones', 'error');
    }
}

// Funciones del modal
function showCreateModal() {
    editingMode = false;
    currentSedeId = null;

    document.getElementById('modalTitle').textContent = 'Nueva Sede Educativa';
    document.getElementById('sedeForm').reset();
    document.getElementById('cod_interprise').readOnly = false;

    document.getElementById('sedeModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('sedeModal').style.display = 'none';
}

function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Función para guardar sede
async function saveSede() {
    const form = document.getElementById('sedeForm');
    const formData = new FormData(form);

    // Validar campos requeridos
    if (!formData.get('cod_interprise') || !formData.get('cod_dane') ||
        !formData.get('nombre_sede_educativa') || !formData.get('codigo_ie') ||
        !formData.get('zona') || !formData.get('preparado') || !formData.get('industrializado')) {
        showNotification('Por favor complete todos los campos requeridos', 'error');
        return;
    }

    // Validar que se hayan seleccionado opciones válidas para los dropdowns
    if (formData.get('preparado') === '' || formData.get('industrializado') === '') {
        showNotification('Por favor seleccione VERDADERO o FALSO para los campos Preparado e Industrializado', 'error');
        return;
    }

    const data = {
        cod_interprise: formData.get('cod_interprise'),
        cod_dane: formData.get('cod_dane'),
        nombre_sede_educativa: formData.get('nombre_sede_educativa'),
        nombre_generico_sede: formData.get('nombre_generico_sede') || 'Sin especificar',
        codigo_ie: formData.get('codigo_ie'),
        zona: formData.get('zona'),
        direccion: formData.get('direccion') || '',
        preparado: formData.get('preparado'),
        industrializado: formData.get('industrializado')
    };

    try {
        let url, method;

        if (editingMode) {
            url = `/principal/api/sedes/${currentSedeId}/`;
            method = 'PUT';
        } else {
            url = '/principal/api/sedes/';
            method = 'POST';
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification(
                editingMode ? 'Sede actualizada exitosamente' : 'Sede creada exitosamente',
                'success'
            );
            closeModal();
            loadSedesTable(); // Actualizar solo la tabla
        } else {
            showNotification(result.error || 'Error al guardar la sede', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Función para editar sede
async function editSede(codInterprise) {
    try {
        const response = await fetch(`/principal/api/sedes/${codInterprise}/`);
        const sede = await response.json();

        editingMode = true;
        currentSedeId = codInterprise;

        document.getElementById('modalTitle').textContent = 'Editar Sede Educativa';
        document.getElementById('cod_interprise').value = sede.cod_interprise;
        document.getElementById('cod_interprise').readOnly = true;
        document.getElementById('cod_dane').value = sede.cod_dane;
        document.getElementById('nombre_sede_educativa').value = sede.nombre_sede_educativa;
        document.getElementById('nombre_generico_sede').value = sede.nombre_generico_sede || '';
        document.getElementById('codigo_ie').value = sede.codigo_ie;
        document.getElementById('direccion').value = sede.direccion || '';
        document.getElementById('zona').value = sede.zona;
        // Establecer valores de los dropdowns
        document.getElementById('preparado').value = sede.preparado || '';
        document.getElementById('industrializado').value = sede.industrializado || '';

        document.getElementById('sedeModal').style.display = 'flex';
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar la sede', 'error');
    }
}

// Función para ver detalles
async function viewSede(codInterprise) {
    try {
        const response = await fetch(`/principal/api/sedes/${codInterprise}/`);
        const sede = await response.json();

        // Obtener información de la institución
        const institucion = instituciones.find(i => i.codigo_ie === sede.codigo_ie);

        const detailContent = `
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Código Interprise:</label>
                    <span>${sede.cod_interprise}</span>
                </div>
                <div class="detail-item">
                    <label>Código DANE:</label>
                    <span>${sede.cod_dane}</span>
                </div>
                <div class="detail-item">
                    <label>Nombre:</label>
                    <span>${sede.nombre_sede_educativa}</span>
                </div>
                <div class="detail-item">
                    <label>Nombre Genérico:</label>
                    <span>${sede.nombre_generico_sede || 'Sin especificar'}</span>
                </div>
                <div class="detail-item full-width">
                    <label>Institución:</label>
                    <span>${institucion ? institucion.nombre_institucion : 'N/A'}</span>
                </div>
                <div class="detail-item full-width">
                    <label>Dirección:</label>
                    <span>${sede.direccion || 'No especificada'}</span>
                </div>
                <div class="detail-item">
                    <label>Zona:</label>
                    <span class="badge badge-${sede.zona.toLowerCase()}">${sede.zona}</span>
                </div>
                <div class="detail-item">
                    <label>Preparado:</label>
                    <span>${sede.preparado}</span>
                </div>
                <div class="detail-item">
                    <label>Industrializado:</label>
                    <span>${sede.industrializado}</span>
                </div>
            </div>
        `;

        document.getElementById('detailContent').innerHTML = detailContent;
        document.getElementById('detailModal').style.display = 'flex';
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar los detalles', 'error');
    }
}

// Función para eliminar sede
async function deleteSede(codInterprise) {
    if (!confirm('¿Está seguro de que desea eliminar esta sede? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const response = await fetch(`/principal/api/sedes/${codInterprise}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Sede eliminada exitosamente', 'success');
            loadSedesTable(); // Actualizar solo la tabla
        } else {
            showNotification(result.error || 'Error al eliminar la sede', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Función para cargar y actualizar la tabla de sedes
async function loadSedesTable() {
    try {
        const response = await fetch('/principal/api/sedes/');
        const data = await response.json();
        updateSedesTable(data.sedes);
        updateStats(); // También actualizar estadísticas
    } catch (error) {
        console.error('Error al cargar sedes:', error);
        showNotification('Error al cargar sedes', 'error');
    }
}

// Función para actualizar la tabla dinámicamente
function updateSedesTable(sedes) {
    const tbody = document.querySelector('#sedesTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (sedes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">No hay sedes registradas</td></tr>';
        return;
    }

    sedes.forEach(sede => {
        const row = document.createElement('tr');
        row.setAttribute('data-codigo', sede.cod_interprise);
        row.innerHTML = `
            <td>${sede.cod_interprise}</td>
            <td>${sede.cod_dane}</td>
            <td>${sede.nombre_sede_educativa}</td>
            <td>${sede.nombre_generico_sede || 'Sin especificar'}</td>
            <td>${sede.codigo_ie__nombre_institucion || 'N/A'}</td>
            <td>
                <span class="badge badge-${sede.zona.toLowerCase()}">
                    ${sede.zona}
                </span>
            </td>
            <td>
                <span class="badge badge-${sede.preparado.toLowerCase()}">
                    ${sede.preparado}
                </span>
            </td>
            <td>
                <span class="badge badge-${sede.industrializado.toLowerCase()}">
                    ${sede.industrializado}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewSede('${sede.cod_interprise}')" title="Ver detalles">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-warning" onclick="editSede('${sede.cod_interprise}')" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteSede('${sede.cod_interprise}')" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Función para actualizar estadísticas
async function updateStats() {
    try {
        const response = await fetch('/principal/api/sedes/');
        const data = await response.json();

        // Actualizar el contador en el template si existe
        const totalElement = document.querySelector('.header-left p strong');
        if (totalElement) {
            totalElement.textContent = data.sedes.length;
        }

        // Actualizar estadísticas en la página principal si existe
        const statsElement = document.getElementById('total-sedes');
        if (statsElement) {
            statsElement.textContent = data.sedes.length;
        }
    } catch (error) {
        console.error('Error al actualizar estadísticas:', error);
    }
}

// Función showNotification y event listeners para modales están disponibles globalmente desde main.js

// Implementación de respaldo para showNotification si no está disponible desde main.js
if (typeof window.showNotification !== 'function') {
    window.showNotification = function(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Estilos para la alerta
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            min-width: 300px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        `;

        // Color según el tipo
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(notification);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    };

    // Función auxiliar para obtener el icono
    function getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }

    // Agregar estilos CSS para las animaciones si no existen
    if (!document.querySelector('#sedes-notification-styles')) {
        const style = document.createElement('style');
        style.id = 'sedes-notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            .alert-close {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                margin-left: auto;
            }

            .alert-close:hover {
                opacity: 0.7;
            }
        `;
        document.head.appendChild(style);
    }
}

// =====================================
// FUNCIONALIDAD DE BÚSQUEDA
// =====================================

let allSedes = []; // Almacenar todas las sedes para búsqueda
let currentSearchTerm = '';

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearButton = document.getElementById('clearSearch');
    const resultsCount = document.getElementById('searchResultsCount');

    if (!searchInput || !clearButton || !resultsCount) {
        console.error('Elementos de búsqueda no encontrados');
        return;
    }

    // Cargar todas las sedes para búsqueda
    loadAllSedesForSearch();

    // Event listener para búsqueda en tiempo real
    searchInput.addEventListener('input', function() {
        currentSearchTerm = this.value.trim();
        performSearch();
        updateClearButton();
    });

    // Event listener para limpiar búsqueda
    clearButton.addEventListener('click', function() {
        searchInput.value = '';
        currentSearchTerm = '';
        performSearch();
        updateClearButton();
        searchInput.focus();
    });

    // Event listener para Enter
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
}

async function loadAllSedesForSearch() {
    try {
        const response = await fetch('/principal/api/sedes/');
        const data = await response.json();
        allSedes = data.sedes;
    } catch (error) {
        console.error('Error al cargar sedes para búsqueda:', error);
        showNotification('Error al cargar datos para búsqueda', 'error');
    }
}

function performSearch() {
    const searchTerm = currentSearchTerm.toLowerCase();
    const tbody = document.querySelector('#sedesTable tbody');
    const resultsCount = document.getElementById('searchResultsCount');

    if (!tbody || !resultsCount) return;

    // Si no hay término de búsqueda, mostrar todas las sedes
    if (!searchTerm) {
        showAllSedes();
        resultsCount.textContent = 'Mostrando todas las sedes';
        return;
    }

    // Filtrar sedes
    const filteredSedes = allSedes.filter(sede => {
        return (
            sede.cod_interprise.toLowerCase().includes(searchTerm) ||
            sede.cod_dane.toLowerCase().includes(searchTerm) ||
            sede.nombre_sede_educativa.toLowerCase().includes(searchTerm) ||
            (sede.nombre_generico_sede && sede.nombre_generico_sede.toLowerCase().includes(searchTerm)) ||
            (sede.codigo_ie__nombre_institucion && sede.codigo_ie__nombre_institucion.toLowerCase().includes(searchTerm)) ||
            sede.zona.toLowerCase().includes(searchTerm) ||
            sede.preparado.toLowerCase().includes(searchTerm) ||
            sede.industrializado.toLowerCase().includes(searchTerm)
        );
    });

    // Actualizar tabla
    updateSedesTable(filteredSedes);
    
    // Actualizar contador de resultados
    if (filteredSedes.length === 0) {
        resultsCount.innerHTML = `No se encontraron sedes que coincidan con "<span class="highlight">${searchTerm}</span>"`;
    } else {
        resultsCount.innerHTML = `Mostrando <span class="highlight">${filteredSedes.length}</span> de ${allSedes.length} sedes`;
    }
}

function showAllSedes() {
    updateSedesTable(allSedes);
}

function updateClearButton() {
    const clearButton = document.getElementById('clearSearch');
    if (clearButton) {
        if (currentSearchTerm) {
            clearButton.classList.add('show');
        } else {
            clearButton.classList.remove('show');
        }
    }
}

// Función para resaltar texto en los resultados
function highlightText(text, searchTerm) {
    if (!searchTerm) return text;
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}