// Variables globales
let editingMode = false;
let currentSedeId = null;
let instituciones = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadInstituciones();
    updateStats();
    setupModalEventListeners(); // Configurar event listeners globales para modales
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

    const data = {
        cod_interprise: formData.get('cod_interprise'),
        cod_dane: formData.get('cod_dane'),
        nombre_sede_educativa: formData.get('nombre_sede_educativa'),
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
            location.reload(); // Recargar la página para mostrar los cambios
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
        document.getElementById('codigo_ie').value = sede.codigo_ie;
        document.getElementById('direccion').value = sede.direccion || '';
        document.getElementById('zona').value = sede.zona;
        document.getElementById('preparado').value = sede.preparado;
        document.getElementById('industrializado').value = sede.industrializado;

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
            location.reload(); // Recargar la página para mostrar los cambios
        } else {
            showNotification(result.error || 'Error al eliminar la sede', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', 'error');
    }
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

// Función showNotification y event listeners para modales ahora están disponibles globalmente desde main.js