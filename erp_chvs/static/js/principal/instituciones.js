// Variables globales
let editingMode = false;
let currentInstitucionId = null;
let departamentos = [];
let municipios = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadDepartamentos();
    updateStats();
});

// Funciones para cargar datos de referencia
async function loadDepartamentos() {
    try {
        const response = await fetch('/principal/api/departamentos/');
        const data = await response.json();
        departamentos = data.departamentos;

        const select = document.getElementById('departamento_id');
        select.innerHTML = '<option value="">Seleccione un departamento</option>';

        departamentos.forEach(dept => {
            select.innerHTML += `<option value="${dept.codigo_departamento}">${dept.nombre_departamento}</option>`;
        });
    } catch (error) {
        console.error('Error al cargar departamentos:', error);
        showNotification('Error al cargar departamentos', 'error');
    }
}

async function loadMunicipios(departamentoId) {
    try {
        const response = await fetch('/principal/api/municipios/');
        const data = await response.json();
        municipios = data.municipios.filter(m => m.codigo_departamento === departamentoId);

        const select = document.getElementById('municipio_id');
        select.innerHTML = '<option value="">Seleccione un municipio</option>';

        municipios.forEach(mun => {
            select.innerHTML += `<option value="${mun.id}">${mun.nombre_municipio}</option>`;
        });
    } catch (error) {
        console.error('Error al cargar municipios:', error);
        showNotification('Error al cargar municipios', 'error');
    }
}

// Event listener para cambio de departamento
document.addEventListener('DOMContentLoaded', function() {
    const departamentoSelect = document.getElementById('departamento_id');
    if (departamentoSelect) {
        departamentoSelect.addEventListener('change', function() {
            const departamentoId = this.value;
            if (departamentoId) {
                loadMunicipios(departamentoId);
            } else {
                document.getElementById('municipio_id').innerHTML = '<option value="">Seleccione un municipio</option>';
            }
        });
    }
});

// Funciones del modal
function showCreateModal() {
    editingMode = false;
    currentInstitucionId = null;

    document.getElementById('modalTitle').textContent = 'Nueva Institución Educativa';
    document.getElementById('institucionForm').reset();
    document.getElementById('codigo_dane').readOnly = false;

    // Limpiar municipios
    document.getElementById('municipio_id').innerHTML = '<option value="">Seleccione un municipio</option>';

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
    if (!formData.get('codigo_dane') || !formData.get('nombre_institucion') ||
        !formData.get('departamento_id') || !formData.get('municipio_id')) {
        showNotification('Por favor complete todos los campos requeridos', 'error');
        return;
    }

    const data = {
        codigo_dane: formData.get('codigo_dane'),
        nombre_institucion: formData.get('nombre_institucion'),
        departamento_id: formData.get('departamento_id'),
        municipio_id: parseInt(formData.get('municipio_id')),
        direccion: formData.get('direccion') || '',
        telefono: formData.get('telefono') || '',
        email: formData.get('email') || '',
        sector: formData.get('sector') || 'OFICIAL',
        rector: formData.get('rector') || '',
        estado: formData.get('estado') || 'ACTIVO'
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
async function editInstitucion(codigoDane) {
    try {
        const response = await fetch(`/principal/api/instituciones/${codigoDane}/`);
        const institucion = await response.json();

        editingMode = true;
        currentInstitucionId = codigoDane;

        document.getElementById('modalTitle').textContent = 'Editar Institución Educativa';
        document.getElementById('codigo_dane').value = institucion.codigo_dane;
        document.getElementById('codigo_dane').readOnly = true;
        document.getElementById('nombre_institucion').value = institucion.nombre_institucion;
        document.getElementById('departamento_id').value = institucion.departamento_id;

        // Cargar municipios del departamento y seleccionar el municipio
        await loadMunicipios(institucion.departamento_id);
        document.getElementById('municipio_id').value = institucion.municipio_id;

        document.getElementById('direccion').value = institucion.direccion || '';
        document.getElementById('telefono').value = institucion.telefono || '';
        document.getElementById('email').value = institucion.email || '';
        document.getElementById('sector').value = institucion.sector;
        document.getElementById('rector').value = institucion.rector || '';
        document.getElementById('estado').value = institucion.estado;

        document.getElementById('institucionModal').style.display = 'flex';
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar la institución', 'error');
    }
}

// Función para ver detalles
async function viewInstitucion(codigoDane) {
    try {
        const response = await fetch(`/principal/api/instituciones/${codigoDane}/`);
        const institucion = await response.json();

        // Obtener nombres de departamento y municipio
        const departamento = departamentos.find(d => d.codigo_departamento === institucion.departamento_id);
        const municipio = municipios.find(m => m.id === institucion.municipio_id);

        const detailContent = `
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Código DANE:</label>
                    <span>${institucion.codigo_dane}</span>
                </div>
                <div class="detail-item">
                    <label>Nombre:</label>
                    <span>${institucion.nombre_institucion}</span>
                </div>
                <div class="detail-item">
                    <label>Departamento:</label>
                    <span>${departamento ? departamento.nombre_departamento : 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <label>Municipio:</label>
                    <span>${municipio ? municipio.nombre_municipio : 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <label>Sector:</label>
                    <span class="badge badge-${institucion.sector.toLowerCase()}">${institucion.sector}</span>
                </div>
                <div class="detail-item">
                    <label>Estado:</label>
                    <span class="badge badge-${institucion.estado.toLowerCase()}">${institucion.estado}</span>
                </div>
                <div class="detail-item full-width">
                    <label>Dirección:</label>
                    <span>${institucion.direccion || 'No especificada'}</span>
                </div>
                <div class="detail-item">
                    <label>Teléfono:</label>
                    <span>${institucion.telefono || 'No especificado'}</span>
                </div>
                <div class="detail-item">
                    <label>Email:</label>
                    <span>${institucion.email || 'No especificado'}</span>
                </div>
                <div class="detail-item full-width">
                    <label>Rector/Director:</label>
                    <span>${institucion.rector || 'No especificado'}</span>
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
async function deleteInstitucion(codigoDane) {
    if (!confirm('¿Está seguro de que desea eliminar esta institución? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const response = await fetch(`/principal/api/instituciones/${codigoDane}/`, {
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

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;

    // Agregar al DOM
    document.body.appendChild(notification);

    // Remover automáticamente después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Event listeners para cerrar modales con ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
        closeDetailModal();
    }
});

// Event listeners para cerrar modales haciendo clic fuera
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal();
        closeDetailModal();
    }
});