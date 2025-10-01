// niveles_grado.js - JavaScript para gestión de niveles grado escolar
let currentNivelGradoId = null;
let isEditMode = false;

function showCreateModal() {
    isEditMode = false;
    currentNivelGradoId = null;
    document.getElementById('modalTitle').textContent = 'Nuevo Nivel Grado Escolar';
    document.getElementById('nivelGradoForm').reset();
    document.getElementById('id_grado_escolar').disabled = false;
    document.getElementById('nivelGradoModal').style.display = 'block';
}

function editNivelGrado(id) {
    isEditMode = true;
    currentNivelGradoId = id;
    document.getElementById('modalTitle').textContent = 'Editar Nivel Grado Escolar';
    document.getElementById('id_grado_escolar').disabled = true;

    fetch(`/principal/api/niveles-grado/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('id_grado_escolar').value = data.id_grado_escolar;
            document.getElementById('grados_sedes').value = data.grados_sedes;
            document.getElementById('nivel_escolar_uapa').value = data.nivel_escolar_uapa;
            document.getElementById('nivelGradoModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos del nivel grado');
        });
}

function saveNivelGrado() {
    const formData = {
        id_grado_escolar: document.getElementById('id_grado_escolar').value,
        grados_sedes: document.getElementById('grados_sedes').value,
        nivel_escolar_uapa: document.getElementById('nivel_escolar_uapa').value
    };

    const url = isEditMode ?
        `/principal/api/niveles-grado/${currentNivelGradoId}/` :
        '/principal/api/niveles-grado/';

    const method = isEditMode ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
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
        alert('Error al guardar el nivel grado');
    });
}

function deleteNivelGrado(id, nombre) {
    currentNivelGradoId = id;
    document.getElementById('deleteItemName').textContent = `${id} - ${nombre}`;
    document.getElementById('deleteModal').style.display = 'block';
}

function confirmDelete() {
    if (currentNivelGradoId) {
        fetch(`/principal/api/niveles-grado/${currentNivelGradoId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCsrfToken()
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
            alert('Error al eliminar el nivel grado');
        });
    }
    closeDeleteModal();
}

function closeModal() {
    document.getElementById('nivelGradoModal').style.display = 'none';
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Cerrar modales al hacer clic fuera de ellos
window.onclick = function(event) {
    const nivelGradoModal = document.getElementById('nivelGradoModal');
    const deleteModal = document.getElementById('deleteModal');

    if (event.target === nivelGradoModal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}