// Variables globales
let editingMode = false;
let currentInstitucionId = null;
let municipios = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Verificar que las funciones globales estén disponibles
    if (typeof window.showNotification !== 'function') {
        console.error('showNotification no está disponible desde main.js');
    }

    loadMunicipios();
    updateStats();
    setupSearch();
});

// Funciones para cargar datos de referencia
async function loadMunicipios() {
    try {
        const response = await fetch('/principal/api/municipios/');
        const data = await response.json();
        municipios = data.municipios;

        const select = document.getElementById('id_municipios');
        select.innerHTML = '<option value="">Seleccione un municipio</option>';

        municipios.forEach(mun => {
            select.innerHTML += `<option value="${mun.id}">${mun.nombre_municipio}</option>`;
        });
    } catch (error) {
        console.error('Error al cargar municipios:', error);
        showNotification('Error al cargar municipios', 'error');
    }
}


// Funciones del modal
function showCreateModal() {
    editingMode = false;
    currentInstitucionId = null;

    document.getElementById('modalTitle').textContent = 'Nueva Institución Educativa';
    document.getElementById('institucionForm').reset();
    document.getElementById('codigo_ie').readOnly = false;

    document.getElementById('institucionModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('institucionModal').style.display = 'none';
}

function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Función para guardar institución
async function saveInstitucion() {
    const form = document.getElementById('institucionForm');
    const formData = new FormData(form);

    // Validar campos requeridos
    if (!formData.get('codigo_ie') || !formData.get('nombre_institucion') ||
        !formData.get('id_municipios')) {
        showNotification('Por favor complete todos los campos requeridos', 'error');
        return;
    }

    const data = {
        codigo_ie: formData.get('codigo_ie'),
        nombre_institucion: formData.get('nombre_institucion'),
        id_municipios: parseInt(formData.get('id_municipios'))
    };

    try {
        let url, method;

        if (editingMode) {
            url = `/principal/api/instituciones/${currentInstitucionId}/`;
            method = 'PUT';
        } else {
            url = '/principal/api/instituciones/';
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
                editingMode ? 'Institución actualizada exitosamente' : 'Institución creada exitosamente',
                'success'
            );
            closeModal();
            loadInstitucionesTable(); // Actualizar solo la tabla
        } else {
            showNotification(result.error || 'Error al guardar la institución', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Función para editar institución
async function editInstitucion(codigoIe) {
    try {
        const response = await fetch(`/principal/api/instituciones/${codigoIe}/`);
        const institucion = await response.json();

        editingMode = true;
        currentInstitucionId = codigoIe;

        document.getElementById('modalTitle').textContent = 'Editar Institución Educativa';
        document.getElementById('codigo_ie').value = institucion.codigo_ie;
        document.getElementById('codigo_ie').readOnly = true;
        document.getElementById('nombre_institucion').value = institucion.nombre_institucion;
        document.getElementById('id_municipios').value = institucion.id_municipios;

        document.getElementById('institucionModal').style.display = 'flex';
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar la institución', 'error');
    }
}

// Función para ver detalles
async function viewInstitucion(codigoIe) {
    try {
        const response = await fetch(`/principal/api/instituciones/${codigoIe}/`);
        const institucion = await response.json();

        // Obtener nombre del municipio
        const municipio = municipios.find(m => m.id === institucion.id_municipios);

        const detailContent = `
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Código IE:</label>
                    <span>${institucion.codigo_ie}</span>
                </div>
                <div class="detail-item">
                    <label>Nombre:</label>
                    <span>${institucion.nombre_institucion}</span>
                </div>
                <div class="detail-item">
                    <label>Municipio:</label>
                    <span>${municipio ? municipio.nombre_municipio : 'N/A'}</span>
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

// Función para eliminar institución
async function deleteInstitucion(codigoIe) {
    if (!confirm('¿Está seguro de que desea eliminar esta institución? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const response = await fetch(`/principal/api/instituciones/${codigoIe}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Institución eliminada exitosamente', 'success');
            loadInstitucionesTable(); // Actualizar solo la tabla
        } else {
            showNotification(result.error || 'Error al eliminar la institución', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    }
}

// Función para cargar y actualizar la tabla de instituciones
async function loadInstitucionesTable() {
    try {
        const response = await fetch('/principal/api/instituciones/');
        const data = await response.json();
        updateInstitucionesTable(data.instituciones);
        updateStats(); // También actualizar estadísticas
    } catch (error) {
        console.error('Error al cargar instituciones:', error);
        showNotification('Error al cargar instituciones', 'error');
    }
}

// Función para actualizar la tabla dinámicamente
function updateInstitucionesTable(instituciones) {
    const tbody = document.querySelector('#institucionesTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (instituciones.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay instituciones registradas</td></tr>';
        return;
    }

    instituciones.forEach(institucion => {
        const row = document.createElement('tr');
        row.setAttribute('data-codigo', institucion.codigo_ie);
        row.innerHTML = `
            <td>${institucion.codigo_ie}</td>
            <td>${institucion.nombre_institucion}</td>
            <td>${institucion.id_municipios__nombre_municipio || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewInstitucion('${institucion.codigo_ie}')" title="Ver detalles">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-warning" onclick="editInstitucion('${institucion.codigo_ie}')" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteInstitucion('${institucion.codigo_ie}')" title="Eliminar">
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
        const response = await fetch('/principal/api/instituciones/');
        const data = await response.json();

        // Actualizar el contador en el template si existe
        const totalElement = document.querySelector('.header-left p strong');
        if (totalElement) {
            totalElement.textContent = data.instituciones.length;
        }

        // Actualizar estadísticas en la página principal si existe
        const statsElement = document.getElementById('total-instituciones');
        if (statsElement) {
            statsElement.textContent = data.instituciones.length;
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
    if (!document.querySelector('#instituciones-notification-styles')) {
        const style = document.createElement('style');
        style.id = 'instituciones-notification-styles';
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

let allInstituciones = []; // Almacenar todas las instituciones para búsqueda
let currentSearchTerm = '';

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearButton = document.getElementById('clearSearch');
    const resultsCount = document.getElementById('searchResultsCount');

    if (!searchInput || !clearButton || !resultsCount) {
        console.error('Elementos de búsqueda no encontrados');
        return;
    }

    // Cargar todas las instituciones para búsqueda
    loadAllInstitucionesForSearch();

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

async function loadAllInstitucionesForSearch() {
    try {
        const response = await fetch('/principal/api/instituciones/');
        const data = await response.json();
        allInstituciones = data.instituciones;
    } catch (error) {
        console.error('Error al cargar instituciones para búsqueda:', error);
        showNotification('Error al cargar datos para búsqueda', 'error');
    }
}

function performSearch() {
    const searchTerm = currentSearchTerm.toLowerCase();
    const tbody = document.querySelector('#institucionesTable tbody');
    const resultsCount = document.getElementById('searchResultsCount');

    if (!tbody || !resultsCount) return;

    // Si no hay término de búsqueda, mostrar todas las instituciones
    if (!searchTerm) {
        showAllInstituciones();
        resultsCount.textContent = 'Mostrando todas las instituciones';
        return;
    }

    // Filtrar instituciones
    const filteredInstituciones = allInstituciones.filter(institucion => {
        return (
            institucion.codigo_ie.toLowerCase().includes(searchTerm) ||
            institucion.nombre_institucion.toLowerCase().includes(searchTerm) ||
            (institucion.id_municipios__nombre_municipio && institucion.id_municipios__nombre_municipio.toLowerCase().includes(searchTerm))
        );
    });

    // Actualizar tabla
    updateInstitucionesTable(filteredInstituciones);
    
    // Actualizar contador de resultados
    if (filteredInstituciones.length === 0) {
        resultsCount.innerHTML = `No se encontraron instituciones que coincidan con "<span class="highlight">${searchTerm}</span>"`;
    } else {
        resultsCount.innerHTML = `Mostrando <span class="highlight">${filteredInstituciones.length}</span> de ${allInstituciones.length} instituciones`;
    }
}

function showAllInstituciones() {
    updateInstitucionesTable(allInstituciones);
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