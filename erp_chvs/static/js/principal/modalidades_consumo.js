// modalidades_consumo.js - Gestión de modalidades de consumo
let currentModalidadId = null;
let isEditMode = false;
let centrosCostoLoaded = false;

function loadCentrosCosto() {
    if (centrosCostoLoaded) return Promise.resolve();

    return fetch('/principal/api/siesa/centros-costo/')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('modalidad_select');
            data.centros.forEach(c => {
                const option = document.createElement('option');
                option.value = c.f284_descripcion;
                option.dataset.id = c.f284_id;
                option.textContent = c.f284_descripcion;
                select.appendChild(option);
            });
            centrosCostoLoaded = true;
        });
}

function showCreateModal() {
    isEditMode = false;
    currentModalidadId = null;
    document.getElementById('modalTitle').textContent = 'Nueva Modalidad';
    document.getElementById('modalidadForm').reset();

    // Mostrar select, ocultar input de texto
    document.getElementById('modalidad_select').style.display = '';
    document.getElementById('modalidad_select').required = true;
    document.getElementById('modalidad_input').style.display = 'none';
    document.getElementById('modalidad_input').required = false;

    // ID Modalidad readonly y vacío — se autocompleta al seleccionar
    document.getElementById('id_modalidades').readOnly = true;
    document.getElementById('id_modalidades').value = '';

    loadCentrosCosto().then(() => {
        document.getElementById('modalidad_select').value = '';
        document.getElementById('modalidadModal').style.display = 'block';
    });
}

function editModalidad(id) {
    isEditMode = true;
    currentModalidadId = id;
    document.getElementById('modalTitle').textContent = 'Editar Modalidad';

    // Ocultar select, mostrar input de texto
    document.getElementById('modalidad_select').style.display = 'none';
    document.getElementById('modalidad_select').required = false;
    document.getElementById('modalidad_input').style.display = '';
    document.getElementById('modalidad_input').required = true;

    // ID Modalidad readonly en edición
    document.getElementById('id_modalidades').readOnly = true;

    fetch(`/principal/api/modalidades-consumo/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('id_modalidades').value = data.id_modalidades;
            document.getElementById('modalidad_input').value = data.modalidad;
            document.getElementById('cod_modalidad').value = data.cod_modalidad;
            document.getElementById('modalidadModal').style.display = 'block';
        })
        .catch(() => alert('Error al cargar los datos de la modalidad'));
}

// Autocompleta ID Modalidad al seleccionar del maestro SIESA
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('modalidad_select').addEventListener('change', function () {
        const selected = this.options[this.selectedIndex];
        document.getElementById('id_modalidades').value = selected.dataset.id || '';
    });
});

function saveModalidad() {
    const modalidadValor = isEditMode
        ? document.getElementById('modalidad_input').value.trim().toUpperCase()
        : document.getElementById('modalidad_select').value.trim().toUpperCase();

    if (!modalidadValor) {
        alert('Debe seleccionar o ingresar una modalidad.');
        return;
    }

    const formData = {
        id_modalidades: document.getElementById('id_modalidades').value,
        modalidad: modalidadValor,
        cod_modalidad: document.getElementById('cod_modalidad').value.trim().toUpperCase()
    };

    if (!formData.id_modalidades || !formData.cod_modalidad) {
        alert('Complete todos los campos requeridos.');
        return;
    }

    const url = isEditMode
        ? `/principal/api/modalidades-consumo/${currentModalidadId}/`
        : '/principal/api/modalidades-consumo/';
    const method = isEditMode ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
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
    .catch(() => alert('Error al guardar la modalidad'));
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
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
        })
        .then(async response => {
            const data = await response.json().catch(() => ({}));
            return { ok: response.ok, data };
        })
        .then(({ ok, data }) => {
            if (ok && data.success) {
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'No fue posible eliminar la modalidad'));
            }
        })
        .catch(() => alert('Error al eliminar la modalidad'));
    }
    closeConfirmModal();
}

function closeModal() {
    document.getElementById('modalidadModal').style.display = 'none';
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

window.onclick = function (event) {
    if (event.target === document.getElementById('modalidadModal')) closeModal();
    if (event.target === document.getElementById('confirmModal')) closeConfirmModal();
};
