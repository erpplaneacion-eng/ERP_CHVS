// niveles_grado.js - JavaScript para gestión de niveles grado escolar
let currentNivelGradoId = null;
let isEditMode = false;
let currentPage = 1;
const itemsPerPage = 10;

// Cargar datos al iniciar la página
document.addEventListener('DOMContentLoaded', function() {
    loadNivelesGrado();
});

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
            window.showNotification('Error al cargar los datos del nivel grado', 'error');
        });
}

function saveNivelGrado() {
    const formData = {
        id_grado_escolar: document.getElementById('id_grado_escolar').value,
        grados_sedes: document.getElementById('grados_sedes').value,
        nivel_escolar_uapa: document.getElementById('nivel_escolar_uapa').value
    };

    // Validación básica
    if (!formData.id_grado_escolar || !formData.grados_sedes || !formData.nivel_escolar_uapa) {
        window.showNotification('Por favor complete todos los campos requeridos', 'error');
        return;
    }

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
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Error en la respuesta del servidor');
    })
    .then(data => {
        closeModal();
        loadNivelesGrado();
        const message = isEditMode ? 'Nivel grado actualizado exitosamente' : 'Nivel grado creado exitosamente';
        window.showNotification(message, 'success');
    })
    .catch(error => {
        console.error('Error:', error);
        window.showNotification('Error al guardar el nivel grado', 'error');
    });
}

function deleteNivelGrado(id, nombre) {
    currentNivelGradoId = id;
    document.getElementById('deleteItemName').textContent = `${id} - ${nombre}`;
    document.getElementById('deleteModal').style.display = 'block';
}

function confirmDelete() {
    fetch(`/principal/api/niveles-grado/${currentNivelGradoId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (response.ok) {
            closeDeleteModal();
            loadNivelesGrado();
            window.showNotification('Nivel grado eliminado exitosamente', 'success');
        } else {
            throw new Error('Error al eliminar');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.showNotification('Error al eliminar el nivel grado', 'error');
    });
}

function loadNivelesGrado(page = 1) {
    currentPage = page;
    fetch(`/principal/api/niveles-grado/?page=${page}`)
        .then(response => response.json())
        .then(data => {
            renderNivelesGrado(data.results || data);
            if (data.count !== undefined) {
                renderPagination(data.count, page);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.showNotification('Error al cargar los niveles grado', 'error');
        });
}

function renderNivelesGrado(nivelesGrado) {
    const tbody = document.getElementById('niveles-grado-tbody');
    tbody.innerHTML = '';

    if (!nivelesGrado || nivelesGrado.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">No hay niveles grado registrados</td>
            </tr>
        `;
        return;
    }

    nivelesGrado.forEach(nivel => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${nivel.id_grado_escolar}</td>
            <td>${nivel.grados_sedes}</td>
            <td>${nivel.nivel_escolar_uapa}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editNivelGrado('${nivel.id_grado_escolar}')" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteNivelGrado('${nivel.id_grado_escolar}', '${nivel.nivel_escolar_uapa}')" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function renderPagination(totalItems, currentPage) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const paginationContainer = document.getElementById('pagination-container');

    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    let paginationHTML = '<div class="pagination">';

    // Botón anterior
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="loadNivelesGrado(${currentPage - 1})">Anterior</button>`;
    }

    // Números de página
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            paginationHTML += `<button class="page-btn active">${i}</button>`;
        } else {
            paginationHTML += `<button class="page-btn" onclick="loadNivelesGrado(${i})">${i}</button>`;
        }
    }

    // Botón siguiente
    if (currentPage < totalPages) {
        paginationHTML += `<button class="page-btn" onclick="loadNivelesGrado(${currentPage + 1})">Siguiente</button>`;
    }

    paginationHTML += '</div>';
    paginationContainer.innerHTML = paginationHTML;
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

// Cerrar modales al hacer clic fuera
window.addEventListener('click', function(event) {
    const nivelGradoModal = document.getElementById('nivelGradoModal');
    const deleteModal = document.getElementById('deleteModal');

    if (event.target === nivelGradoModal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
});

// Manejar tecla Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
        closeDeleteModal();
    }
});