// tipos_genero.js - JavaScript para gestión de tipos de género
let currentTipoGeneroId = null;
let isEditMode = false;

function showCreateModal() {
    isEditMode = false;
    currentTipoGeneroId = null;
    document.getElementById('modalTitle').textContent = 'Nuevo Tipo de Género';
    document.getElementById('tipoGeneroForm').reset();
    document.getElementById('id_genero').disabled = false;
    document.getElementById('tipoGeneroModal').style.display = 'block';
}

function editTipoGenero(id) {
    isEditMode = true;
    currentTipoGeneroId = id;
    document.getElementById('modalTitle').textContent = 'Editar Tipo de Género';
    document.getElementById('id_genero').disabled = true;
    
    fetch(`/principal/api/tipos-genero/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('id_genero').value = data.id_genero;
            document.getElementById('genero').value = data.genero;
            document.getElementById('codigo_genero').value = data.codigo_genero;
            document.getElementById('tipoGeneroModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos del tipo de género');
        });
}

function saveTipoGenero() {
    const formData = {
        id_genero: document.getElementById('id_genero').value,
        genero: document.getElementById('genero').value,
        codigo_genero: parseInt(document.getElementById('codigo_genero').value)
    };

    const url = isEditMode ? 
        `/principal/api/tipos-genero/${currentTipoGeneroId}/` : 
        '/principal/api/tipos-genero/';
    
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
        alert('Error al guardar el tipo de género');
    });
}

function deleteTipoGenero(id) {
    currentTipoGeneroId = id;
    document.getElementById('confirmModal').style.display = 'block';
}

function confirmDelete() {
    if (currentTipoGeneroId) {
        fetch(`/principal/api/tipos-genero/${currentTipoGeneroId}/`, {
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
            alert('Error al eliminar el tipo de género');
        });
    }
    closeConfirmModal();
}

function closeModal() {
    document.getElementById('tipoGeneroModal').style.display = 'none';
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

// Cerrar modales al hacer clic fuera de ellos
window.onclick = function(event) {
    const tipoGeneroModal = document.getElementById('tipoGeneroModal');
    const confirmModal = document.getElementById('confirmModal');
    
    if (event.target === tipoGeneroModal) {
        closeModal();
    }
    if (event.target === confirmModal) {
        closeConfirmModal();
    }
}
