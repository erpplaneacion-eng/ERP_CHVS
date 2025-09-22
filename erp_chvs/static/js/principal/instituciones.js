// Variables globales
let editingMode = false;
let currentInstitucionId = null;
let municipios = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadMunicipios();
    updateStats();
    setupModalEventListeners(); // Configurar event listeners globales para modales
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
            location.reload(); // Recargar la página para mostrar los cambios
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
            location.reload(); // Recargar la página para mostrar los cambios
        } else {
            showNotification(result.error || 'Error al eliminar la institución', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    }
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

// Función showNotification y event listeners para modales ahora están disponibles globalmente desde main.js