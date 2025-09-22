// Variables globales
let editingMode = false;
let currentSedeId = null;
let instituciones = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadInstituciones();
    updateStats();
});

// Funciones para cargar datos de referencia
async function loadInstituciones() {
    try {
        const response = await fetch('/principal/api/instituciones/');
        const data = await response.json();
        instituciones = data.instituciones;

        const select = document.getElementById('institucion_id');
        select.innerHTML = '<option value="">Seleccione una institución</option>';

        instituciones.forEach(inst => {
            select.innerHTML += `<option value="${inst.codigo_dane}">${inst.nombre_institucion} - ${inst.municipio__nombre_municipio}</option>`;
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
    document.getElementById('codigo_sede').readOnly = false;

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
    if (!formData.get('codigo_sede') || !formData.get('nombre_sede') ||
        !formData.get('institucion_id') || !formData.get('direccion') || !formData.get('zona')) {
        showNotification('Por favor complete todos los campos requeridos', 'error');
        return;
    }

    const data = {
        codigo_sede: formData.get('codigo_sede'),
        nombre_sede: formData.get('nombre_sede'),
        institucion_id: formData.get('institucion_id'),
        direccion: formData.get('direccion'),
        zona: formData.get('zona'),
        telefono: formData.get('telefono') || '',
        coordinador: formData.get('coordinador') || '',
        tiene_comedor: formData.has('tiene_comedor'),
        tipo_atencion: formData.get('tipo_atencion') || '',
        capacidad_beneficiarios: formData.get('capacidad_beneficiarios') ? parseInt(formData.get('capacidad_beneficiarios')) : null,
        jornada_manana: formData.has('jornada_manana'),
        jornada_tarde: formData.has('jornada_tarde'),
        jornada_nocturna: formData.has('jornada_nocturna'),
        jornada_unica: formData.has('jornada_unica'),
        estado: formData.get('estado') || 'ACTIVO'
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
async function editSede(codigoSede) {
    try {
        const response = await fetch(`/principal/api/sedes/${codigoSede}/`);
        const sede = await response.json();

        editingMode = true;
        currentSedeId = codigoSede;

        document.getElementById('modalTitle').textContent = 'Editar Sede Educativa';
        document.getElementById('codigo_sede').value = sede.codigo_sede;
        document.getElementById('codigo_sede').readOnly = true;
        document.getElementById('nombre_sede').value = sede.nombre_sede;
        document.getElementById('institucion_id').value = sede.institucion_id;
        document.getElementById('direccion').value = sede.direccion;
        document.getElementById('zona').value = sede.zona;
        document.getElementById('telefono').value = sede.telefono || '';
        document.getElementById('coordinador').value = sede.coordinador || '';
        document.getElementById('tiene_comedor').checked = sede.tiene_comedor;
        document.getElementById('tipo_atencion').value = sede.tipo_atencion || '';
        document.getElementById('capacidad_beneficiarios').value = sede.capacidad_beneficiarios || '';
        document.getElementById('jornada_manana').checked = sede.jornada_manana;
        document.getElementById('jornada_tarde').checked = sede.jornada_tarde;
        document.getElementById('jornada_nocturna').checked = sede.jornada_nocturna;
        document.getElementById('jornada_unica').checked = sede.jornada_unica;
        document.getElementById('estado').value = sede.estado;

        document.getElementById('sedeModal').style.display = 'flex';
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar la sede', 'error');
    }
}

// Función para ver detalles
async function viewSede(codigoSede) {
    try {
        const response = await fetch(`/principal/api/sedes/${codigoSede}/`);
        const sede = await response.json();

        // Obtener información de la institución
        const institucion = instituciones.find(i => i.codigo_dane === sede.institucion_id);

        // Generar lista de jornadas
        const jornadas = [];
        if (sede.jornada_manana) jornadas.push('Mañana');
        if (sede.jornada_tarde) jornadas.push('Tarde');
        if (sede.jornada_nocturna) jornadas.push('Nocturna');
        if (sede.jornada_unica) jornadas.push('Única');

        const detailContent = `
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Código Sede:</label>
                    <span>${sede.codigo_sede}</span>
                </div>
                <div class="detail-item">
                    <label>Nombre:</label>
                    <span>${sede.nombre_sede}</span>
                </div>
                <div class="detail-item full-width">
                    <label>Institución:</label>
                    <span>${institucion ? institucion.nombre_institucion : 'N/A'}</span>
                </div>
                <div class="detail-item full-width">
                    <label>Dirección:</label>
                    <span>${sede.direccion}</span>
                </div>
                <div class="detail-item">
                    <label>Zona:</label>
                    <span class="badge badge-${sede.zona.toLowerCase()}">${sede.zona}</span>
                </div>
                <div class="detail-item">
                    <label>Estado:</label>
                    <span class="badge badge-${sede.estado.toLowerCase()}">${sede.estado}</span>
                </div>
                <div class="detail-item">
                    <label>Teléfono:</label>
                    <span>${sede.telefono || 'No especificado'}</span>
                </div>
                <div class="detail-item">
                    <label>Coordinador:</label>
                    <span>${sede.coordinador || 'No especificado'}</span>
                </div>
                <div class="detail-section">
                    <h4><i class="fas fa-utensils"></i> Información del Comedor</h4>
                    <div class="detail-item">
                        <label>Tiene Comedor:</label>
                        <span class="badge ${sede.tiene_comedor ? 'badge-success' : 'badge-secondary'}">
                            ${sede.tiene_comedor ? 'Sí' : 'No'}
                        </span>
                    </div>
                    <div class="detail-item">
                        <label>Tipo de Atención:</label>
                        <span>${sede.tipo_atencion || 'No especificado'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Capacidad:</label>
                        <span>${sede.capacidad_beneficiarios || 'No especificada'} beneficiarios</span>
                    </div>
                </div>
                <div class="detail-section">
                    <h4><i class="fas fa-clock"></i> Jornadas Disponibles</h4>
                    <div class="detail-item full-width">
                        <label>Jornadas:</label>
                        <span>${jornadas.length > 0 ? jornadas.join(', ') : 'No especificadas'}</span>
                    </div>
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
async function deleteSede(codigoSede) {
    if (!confirm('¿Está seguro de que desea eliminar esta sede? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const response = await fetch(`/principal/api/sedes/${codigoSede}/`, {
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