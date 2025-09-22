// tipos_documento.js - JavaScript para gestión de tipos de documento
let currentTipoDocumentoId = null;
let isEditMode = false;

function showCreateModal() {
    isEditMode = false;
    currentTipoDocumentoId = null;
    document.getElementById('modalTitle').textContent = 'Nuevo Tipo de Documento';
    document.getElementById('tipoDocumentoForm').reset();
    document.getElementById('id_documento').disabled = false;
    document.getElementById('tipoDocumentoModal').style.display = 'block';
}

function editTipoDocumento(id) {
    isEditMode = true;
    currentTipoDocumentoId = id;
    document.getElementById('modalTitle').textContent = 'Editar Tipo de Documento';
    document.getElementById('id_documento').disabled = true;
    
    fetch(`/principal/api/tipos-documento/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('id_documento').value = data.id_documento;
            document.getElementById('tipo_documento').value = data.tipo_documento;
            document.getElementById('codigo_documento').value = data.codigo_documento;
            document.getElementById('tipoDocumentoModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos del tipo de documento');
        });
}

function saveTipoDocumento() {
    const formData = {
        id_documento: document.getElementById('id_documento').value,
        tipo_documento: document.getElementById('tipo_documento').value,
        codigo_documento: parseInt(document.getElementById('codigo_documento').value)
    };

    const url = isEditMode ? 
        `/principal/api/tipos-documento/${currentTipoDocumentoId}/` : 
        '/principal/api/tipos-documento/';
    
    const method = isEditMode ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al guardar el tipo de documento');
    });
}

function deleteTipoDocumento(id) {
    currentTipoDocumentoId = id;
    document.getElementById('confirmModal').style.display = 'block';
}

function confirmDelete() {
    if (currentTipoDocumentoId) {
        fetch(`/principal/api/tipos-documento/${currentTipoDocumentoId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al eliminar el tipo de documento');
        });
    }
    closeConfirmModal();
}

function closeModal() {
    document.getElementById('tipoDocumentoModal').style.display = 'none';
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

// Cerrar modales al hacer clic fuera de ellos
window.onclick = function(event) {
    const tipoDocumentoModal = document.getElementById('tipoDocumentoModal');
    const confirmModal = document.getElementById('confirmModal');
    
    if (event.target === tipoDocumentoModal) {
        closeModal();
    }
    if (event.target === confirmModal) {
        closeConfirmModal();
    }
}
