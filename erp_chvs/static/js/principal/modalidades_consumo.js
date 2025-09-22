// modalidades_consumo.js - JavaScript para gestión de modalidades de consumo
let currentModalidadId = null;
let isEditMode = false;

function showCreateModal() {
    isEditMode = false;
    currentModalidadId = null;
    document.getElementById('modalTitle').textContent = 'Nueva Modalidad';
    document.getElementById('modalidadForm').reset();
    document.getElementById('id_modalidades').disabled = false;
    document.getElementById('modalidadModal').style.display = 'block';
}

function editModalidad(id) {
    isEditMode = true;
    currentModalidadId = id;
    document.getElementById('modalTitle').textContent = 'Editar Modalidad';
    document.getElementById('id_modalidades').disabled = true;
    
    fetch(`/principal/api/modalidades-consumo/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('id_modalidades').value = data.id_modalidades;
            document.getElementById('modalidad').value = data.modalidad;
            document.getElementById('cod_modalidad').value = data.cod_modalidad;
            document.getElementById('modalidadModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos de la modalidad');
        });
}

function saveModalidad() {
    const formData = {
        id_modalidades: document.getElementById('id_modalidades').value,
        modalidad: document.getElementById('modalidad').value,
        cod_modalidad: document.getElementById('cod_modalidad').value
    };

    const url = isEditMode ? 
        `/principal/api/modalidades-consumo/${currentModalidadId}/` : 
        '/principal/api/modalidades-consumo/';
    
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
        alert('Error al guardar la modalidad');
    });
}

function deleteModalidad(id) {
    currentModalidadId = id;
    document.getElementById('confirmModal').style.display = 'block';
}

function confirmDelete() {
    if (currentModalidadId) {
        fetch(`/principal/api/modalidades-consumo/${currentModalidadId}/`, {
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
            alert('Error al eliminar la modalidad');
        });
    }
    closeConfirmModal();
}

function closeModal() {
    document.getElementById('modalidadModal').style.display = 'none';
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

// Cerrar modales al hacer clic fuera de ellos
window.onclick = function(event) {
    const modalidadModal = document.getElementById('modalidadModal');
    const confirmModal = document.getElementById('confirmModal');
    
    if (event.target === modalidadModal) {
        closeModal();
    }
    if (event.target === confirmModal) {
        closeConfirmModal();
    }
}
