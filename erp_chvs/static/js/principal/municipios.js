// municipios.js - Funcionalidad para gestión de municipios

class MunicipiosManager {
    constructor() {
        this.baseUrl = '/principal/api/municipios/';
        this.departamentosUrl = '/principal/api/departamentos/';
        this.editingId = null;
        this.deleteId = null;
        this.departamentos = [];
        this.saving = false; // Flag para prevenir doble envío
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDepartamentos();
        this.loadMunicipiosTable();
    }

    setupEventListeners() {
        // Botón nuevo municipio
        const newBtn = document.getElementById('btn-nuevo-municipio');
        if (newBtn) {
            newBtn.addEventListener('click', () => this.showCreateModal());
        }

        // Formulario municipio
        const form = document.getElementById('municipioForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveMunicipio();
            });
        }

        // Modal close events
        this.setupModalEvents();
    }

    setupModalEvents() {
        // Cerrar modal con X
        document.querySelectorAll('.modal .close').forEach(closeBtn => {
            closeBtn.addEventListener('click', () => this.closeModal());
        });

        // Cerrar modal al hacer clic fuera
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('municipioModal');
            const confirmModal = document.getElementById('confirmModal');

            if (event.target === modal) {
                this.closeModal();
            }
            if (event.target === confirmModal) {
                this.closeConfirmModal();
            }
        });

        // Botones del modal
        const cancelBtn = document.querySelector('#municipioModal .btn-secondary');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }

        const saveBtn = document.querySelector('#municipioModal .btn-primary');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveMunicipio());
        }
    }

    async loadDepartamentos() {
        try {
            const response = await fetch(this.departamentosUrl);
            const data = await response.json();
            this.departamentos = data.departamentos;
            this.updateDepartamentosSelect();
        } catch (error) {
            console.error('Error loading departamentos:', error);
            this.showAlert('Error al cargar los departamentos', 'error');
        }
    }

    updateDepartamentosSelect() {
        const select = document.getElementById('codigo_departamento');
        if (!select) return;

        select.innerHTML = '<option value="">Seleccione un departamento</option>';

        this.departamentos.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.codigo_departamento;
            option.textContent = `${dept.codigo_departamento} - ${dept.nombre_departamento}`;
            select.appendChild(option);
        });
    }

    async loadMunicipiosTable() {
        try {
            const response = await fetch(this.baseUrl);
            const data = await response.json();
            this.updateTable(data.municipios);
        } catch (error) {
            console.error('Error loading municipios:', error);
            this.showAlert('Error al cargar los municipios', 'error');
        }
    }

    updateTable(municipios) {
        const tbody = document.querySelector('#municipiosTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (municipios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay municipios registrados</td></tr>';
            return;
        }

        municipios.forEach(municipio => {
            const row = document.createElement('tr');
            row.setAttribute('data-id', municipio.id);
            row.innerHTML = `
                <td>${municipio.id}</td>
                <td>${municipio.codigo_municipio}</td>
                <td>${municipio.nombre_municipio}</td>
                <td>${municipio.codigo_departamento}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="municipiosManager.editMunicipio(${municipio.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="municipiosManager.deleteMunicipio(${municipio.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    showCreateModal() {
        this.editingId = null;
        const modal = document.getElementById('municipioModal');
        const title = document.getElementById('modalTitle');
        const form = document.getElementById('municipioForm');

        if (title) title.textContent = 'Nuevo Municipio';
        if (form) form.reset();
        if (modal) modal.style.display = 'block';

        // Asegurar que los departamentos estén cargados
        if (this.departamentos.length === 0) {
            this.loadDepartamentos();
        }
    }

    async editMunicipio(id) {
        this.editingId = id;

        try {
            const response = await fetch(`${this.baseUrl}${id}/`);
            const data = await response.json();

            const modal = document.getElementById('municipioModal');
            const title = document.getElementById('modalTitle');
            const codigoField = document.getElementById('codigo_municipio');
            const nombreField = document.getElementById('nombre_municipio');
            const departamentoField = document.getElementById('codigo_departamento');

            if (title) title.textContent = 'Editar Municipio';
            if (codigoField) codigoField.value = data.codigo_municipio;
            if (nombreField) nombreField.value = data.nombre_municipio;
            if (departamentoField) departamentoField.value = data.codigo_departamento;
            if (modal) modal.style.display = 'block';

        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al cargar los datos del municipio', 'error');
        }
    }

    deleteMunicipio(id) {
        this.deleteId = id;
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) confirmModal.style.display = 'block';
    }

    async saveMunicipio() {
        // Prevenir doble ejecución
        if (this.saving) {
            return;
        }

        this.saving = true;

        // Deshabilitar botón de guardar
        const saveBtn = document.querySelector('#municipioModal .btn-primary');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Guardando...';
        }

        const codigoField = document.getElementById('codigo_municipio');
        const nombreField = document.getElementById('nombre_municipio');
        const departamentoField = document.getElementById('codigo_departamento');

        if (!codigoField || !nombreField || !departamentoField) {
            this.saving = false;
            this.showAlert('Error: campos del formulario no encontrados', 'error');
            return;
        }

        const formData = {
            codigo_municipio: parseInt(codigoField.value),
            nombre_municipio: nombreField.value.trim(),
            codigo_departamento: departamentoField.value.trim()
        };

        // Validaciones
        if (!formData.codigo_municipio || !formData.nombre_municipio || !formData.codigo_departamento) {
            this.saving = false;
            this.showAlert('Por favor complete todos los campos', 'warning');
            return;
        }

        if (isNaN(formData.codigo_municipio)) {
            this.saving = false;
            this.showAlert('El código del municipio debe ser un número válido', 'warning');
            return;
        }

        const url = this.editingId ?
            `${this.baseUrl}${this.editingId}/` :
            this.baseUrl;
        const method = this.editingId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                this.closeModal();
                this.showAlert(
                    this.editingId ? 'Municipio actualizado exitosamente' : 'Municipio creado exitosamente',
                    'success'
                );
                this.loadMunicipiosTable();
            } else {
                this.showAlert('Error: ' + (data.error || 'No se pudo guardar el municipio'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al guardar el municipio', 'error');
        } finally {
            // Resetear el flag independientemente del resultado
            this.saving = false;

            // Rehabilitar botón de guardar
            const saveBtn = document.querySelector('#municipioModal .btn-primary');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = this.editingId ? 'Actualizar' : 'Guardar';
            }
        }
    }

    async confirmDelete() {
        if (!this.deleteId) return;

        try {
            const response = await fetch(`${this.baseUrl}${this.deleteId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                this.closeConfirmModal();
                this.showAlert('Municipio eliminado exitosamente', 'success');
                this.loadMunicipiosTable();
            } else {
                this.showAlert('Error: ' + (data.error || 'No se pudo eliminar el municipio'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al eliminar el municipio', 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('municipioModal');
        if (modal) modal.style.display = 'none';
        this.editingId = null;
    }

    closeConfirmModal() {
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) confirmModal.style.display = 'none';
        this.deleteId = null;
    }

    getDepartamentoNombre(codigo) {
        const dept = this.departamentos.find(d => d.codigo_departamento === codigo);
        return dept ? dept.nombre_departamento : codigo;
    }

    showAlert(message, type = 'info') {
        // Crear elemento de alerta
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <i class="fas fa-${this.getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Estilos para la alerta
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: 500;
            min-width: 300px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        `;

        // Color según el tipo
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        alert.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(alert);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }

    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Funciones globales para compatibilidad con los templates
let municipiosManager;

// Funciones para usar en el HTML
function showCreateModal() {
    if (municipiosManager) {
        municipiosManager.showCreateModal();
    }
}

function editMunicipio(id) {
    if (municipiosManager) {
        municipiosManager.editMunicipio(id);
    }
}

function deleteMunicipio(id) {
    if (municipiosManager) {
        municipiosManager.deleteMunicipio(id);
    }
}

function closeModal() {
    if (municipiosManager) {
        municipiosManager.closeModal();
    }
}

function closeConfirmModal() {
    if (municipiosManager) {
        municipiosManager.closeConfirmModal();
    }
}

function saveMunicipio() {
    if (municipiosManager) {
        municipiosManager.saveMunicipio();
    }
}

function confirmDelete() {
    if (municipiosManager) {
        municipiosManager.confirmDelete();
    }
}

function loadDepartamentos() {
    if (municipiosManager) {
        municipiosManager.loadDepartamentos();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la página de municipios
    if (window.location.pathname.includes('municipios') || document.getElementById('municipiosTable')) {
        municipiosManager = new MunicipiosManager();
    }
});

// CSS para animaciones (si no está ya incluido)
if (!document.querySelector('#municipios-styles')) {
    const style = document.createElement('style');
    style.id = 'municipios-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .alert-close {
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            margin-left: auto;
        }

        .alert-close:hover {
            opacity: 0.7;
        }

        /* Estilos específicos para la tabla de municipios */
        .municipios-container .data-table {
            font-size: 14px;
        }

        .municipios-container .data-table th:first-child {
            width: 80px;
        }

        .municipios-container .data-table th:nth-child(2) {
            width: 120px;
        }

        .municipios-container .data-table th:nth-child(4) {
            width: 150px;
        }

        .municipios-container .data-table th:last-child {
            width: 120px;
        }
    `;
    document.head.appendChild(style);
}