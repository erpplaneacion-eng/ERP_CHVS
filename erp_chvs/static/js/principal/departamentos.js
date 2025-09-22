// departamentos.js - Funcionalidad para gestión de departamentos

class DepartamentosManager {
    constructor() {
        this.baseUrl = '/principal/api/departamentos/';
        this.editingCodigo = null;
        this.deleteCode = null;
        this.saving = false; // Flag para prevenir doble envío
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDepartamentosTable();
    }

    setupEventListeners() {
        // Botón nuevo departamento
        const newBtn = document.getElementById('btn-nuevo-departamento');
        if (newBtn) {
            newBtn.addEventListener('click', () => this.showCreateModal());
        }

        // Formulario departamento
        const form = document.getElementById('departamentoForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveDepartamento();
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
            const modal = document.getElementById('departamentoModal');
            const confirmModal = document.getElementById('confirmModal');

            if (event.target === modal) {
                this.closeModal();
            }
            if (event.target === confirmModal) {
                this.closeConfirmModal();
            }
        });

        // Botones del modal
        const cancelBtn = document.querySelector('#departamentoModal .btn-secondary');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }

        const saveBtn = document.querySelector('#departamentoModal .btn-primary');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveDepartamento());
        }
    }

    async loadDepartamentosTable() {
        try {
            const response = await fetch(this.baseUrl);
            const data = await response.json();
            this.updateTable(data.departamentos);
        } catch (error) {
            console.error('Error loading departamentos:', error);
            this.showAlert('Error al cargar los departamentos', 'error');
        }
    }

    updateTable(departamentos) {
        const tbody = document.querySelector('#departamentosTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (departamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">No hay departamentos registrados</td></tr>';
            return;
        }

        departamentos.forEach(dept => {
            const row = document.createElement('tr');
            row.setAttribute('data-codigo', dept.codigo_departamento);
            row.innerHTML = `
                <td>${dept.codigo_departamento}</td>
                <td>${dept.nombre_departamento}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="departamentosManager.editDepartamento('${dept.codigo_departamento}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="departamentosManager.deleteDepartamento('${dept.codigo_departamento}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    showCreateModal() {
        this.editingCodigo = null;
        const modal = document.getElementById('departamentoModal');
        const title = document.getElementById('modalTitle');
        const form = document.getElementById('departamentoForm');
        const codigoField = document.getElementById('codigo_departamento');

        if (title) title.textContent = 'Nuevo Departamento';
        if (form) form.reset();
        if (codigoField) codigoField.disabled = false;
        if (modal) modal.style.display = 'block';
    }

    async editDepartamento(codigo) {
        this.editingCodigo = codigo;

        try {
            const response = await fetch(`${this.baseUrl}${codigo}/`);
            const data = await response.json();

            const modal = document.getElementById('departamentoModal');
            const title = document.getElementById('modalTitle');
            const codigoField = document.getElementById('codigo_departamento');
            const nombreField = document.getElementById('nombre_departamento');

            if (title) title.textContent = 'Editar Departamento';
            if (codigoField) {
                codigoField.value = data.codigo_departamento;
                codigoField.disabled = true;
            }
            if (nombreField) nombreField.value = data.nombre_departamento;
            if (modal) modal.style.display = 'block';

        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al cargar los datos del departamento', 'error');
        }
    }

    deleteDepartamento(codigo) {
        this.deleteCode = codigo;
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) confirmModal.style.display = 'block';
    }

    async saveDepartamento() {
        // Prevenir doble ejecución
        if (this.saving) {
            return;
        }

        this.saving = true;

        // Deshabilitar botón de guardar
        const saveBtn = document.querySelector('#municipioModal .btn-primary, #departamentoModal .btn-primary');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Guardando...';
        }

        const codigoField = document.getElementById('codigo_departamento');
        const nombreField = document.getElementById('nombre_departamento');

        if (!codigoField || !nombreField) {
            this.saving = false;
            this.showAlert('Error: campos del formulario no encontrados', 'error');
            return;
        }

        const formData = {
            codigo_departamento: codigoField.value.trim(),
            nombre_departamento: nombreField.value.trim()
        };

        // Validaciones
        if (!formData.codigo_departamento || !formData.nombre_departamento) {
            this.saving = false;
            this.showAlert('Por favor complete todos los campos', 'warning');
            return;
        }

        // Validar que el código no tenga espacios y sea un formato válido
        formData.codigo_departamento = formData.codigo_departamento.replace(/\s+/g, '').toUpperCase();

        const url = this.editingCodigo ?
            `${this.baseUrl}${this.editingCodigo}/` :
            this.baseUrl;
        const method = this.editingCodigo ? 'PUT' : 'POST';

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
                    this.editingCodigo ? 'Departamento actualizado exitosamente' : 'Departamento creado exitosamente',
                    'success'
                );
                this.loadDepartamentosTable();
            } else {
                this.showAlert('Error: ' + (data.error || 'No se pudo guardar el departamento'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al guardar el departamento', 'error');
        } finally {
            // Resetear el flag independientemente del resultado
            this.saving = false;

            // Rehabilitar botón de guardar
            const saveBtn = document.querySelector('#municipioModal .btn-primary, #departamentoModal .btn-primary');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = this.editingCodigo ? 'Actualizar' : 'Guardar';
            }
        }
    }

    async confirmDelete() {
        if (!this.deleteCode) return;

        try {
            const response = await fetch(`${this.baseUrl}${this.deleteCode}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                this.closeConfirmModal();
                this.showAlert('Departamento eliminado exitosamente', 'success');
                this.loadDepartamentosTable();
            } else {
                this.showAlert('Error: ' + (data.error || 'No se pudo eliminar el departamento'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al eliminar el departamento', 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('departamentoModal');
        if (modal) modal.style.display = 'none';
        this.editingCodigo = null;
    }

    closeConfirmModal() {
        const confirmModal = document.getElementById('confirmModal');
        if (confirmModal) confirmModal.style.display = 'none';
        this.deleteCode = null;
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
let departamentosManager;

// Funciones para usar en el HTML
function showCreateModal() {
    if (departamentosManager) {
        departamentosManager.showCreateModal();
    }
}

function editDepartamento(codigo) {
    if (departamentosManager) {
        departamentosManager.editDepartamento(codigo);
    }
}

function deleteDepartamento(codigo) {
    if (departamentosManager) {
        departamentosManager.deleteDepartamento(codigo);
    }
}

function closeModal() {
    if (departamentosManager) {
        departamentosManager.closeModal();
    }
}

function closeConfirmModal() {
    if (departamentosManager) {
        departamentosManager.closeConfirmModal();
    }
}

function saveDepartamento() {
    if (departamentosManager) {
        departamentosManager.saveDepartamento();
    }
}

function confirmDelete() {
    if (departamentosManager) {
        departamentosManager.confirmDelete();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la página de departamentos
    if (window.location.pathname.includes('departamentos') || document.getElementById('departamentosTable')) {
        departamentosManager = new DepartamentosManager();
    }
});

// CSS para animaciones
const style = document.createElement('style');
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
`;
document.head.appendChild(style);