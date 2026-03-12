class ProcedimientosManager {
    constructor() {
        this.baseUrl = '/nutricion/api/procedimientos/';
        this.editingId = null;
        this.deleteId = null;
        this.saving = false;
        this.init();
    }

    init() {
        this.setupSearch();
        this.setupEventListeners();
    }

    setupSearch() {
        const input = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearSearch');
        if (!input) return;

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const q = input.value.trim();
                const url = new URL(window.location.href);
                if (q) {
                    url.searchParams.set('q', q);
                } else {
                    url.searchParams.delete('q');
                }
                url.searchParams.delete('page');
                window.location.href = url.toString();
            }
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                const url = new URL(window.location.href);
                url.searchParams.delete('q');
                url.searchParams.delete('page');
                window.location.href = url.toString();
            });
        }
    }

    setupEventListeners() {
        document.getElementById('btn-nuevo-procedimiento')
            ?.addEventListener('click', () => this.showCreateModal());

        document.querySelector('#procedimientoModal .modal-close-btn')
            ?.addEventListener('click', () => this.closeModal());
        document.querySelector('#procedimientoModal .modal-cancel-btn')
            ?.addEventListener('click', () => this.closeModal());
        document.getElementById('modal-submit-btn')
            ?.addEventListener('click', () => this.save());

        document.getElementById('closeConfirm')
            ?.addEventListener('click', () => this.closeConfirmModal());
        document.getElementById('cancelDelete')
            ?.addEventListener('click', () => this.closeConfirmModal());
        document.getElementById('confirmDelete')
            ?.addEventListener('click', () => this.confirmDelete());

        window.addEventListener('click', (e) => {
            if (e.target === document.getElementById('procedimientoModal')) this.closeModal();
            if (e.target === document.getElementById('confirmModal')) this.closeConfirmModal();
        });

        document.querySelector('#procedimientosTable tbody')
            ?.addEventListener('click', (e) => {
                const editBtn = e.target.closest('.edit-btn');
                const deleteBtn = e.target.closest('.delete-btn');
                if (editBtn) this.edit(editBtn.dataset.id);
                if (deleteBtn) this.showDeleteModal(deleteBtn.dataset.id, deleteBtn.dataset.nombre);
            });
    }

    showCreateModal() {
        this.editingId = null;
        document.getElementById('modalTitle').textContent = 'Nuevo Procedimiento';
        document.getElementById('input-nombre').value = '';
        document.getElementById('input-procedimiento').value = '';
        document.getElementById('input-activo').checked = true;
        this.hideSummary();
        const btn = document.getElementById('modal-submit-btn');
        if (btn) btn.textContent = 'Guardar';
        document.getElementById('procedimientoModal').classList.remove('hidden-initially');
        document.getElementById('procedimientoModal').style.display = 'flex';
    }

    async edit(id) {
        try {
            const response = await fetch(`${this.baseUrl}${id}/get/`);
            const data = await response.json();
            this.editingId = id;
            document.getElementById('modalTitle').textContent = 'Editar Procedimiento';
            document.getElementById('input-nombre').value = data.nombre;
            document.getElementById('input-procedimiento').value = data.procedimiento;
            document.getElementById('input-activo').checked = data.activo;
            this.hideSummary();
            const btn = document.getElementById('modal-submit-btn');
            if (btn) btn.textContent = 'Actualizar';
            document.getElementById('procedimientoModal').classList.remove('hidden-initially');
            document.getElementById('procedimientoModal').style.display = 'flex';
        } catch (err) {
            this.showAlert('Error al cargar los datos del procedimiento.', 'error');
        }
    }

    showDeleteModal(id, nombre) {
        this.deleteId = id;
        document.getElementById('confirm-nombre').textContent = nombre || '';
        document.getElementById('confirmModal').classList.remove('hidden-initially');
        document.getElementById('confirmModal').style.display = 'flex';
    }

    async save() {
        if (this.saving) return;

        const nombre = document.getElementById('input-nombre').value.trim();
        const procedimiento = document.getElementById('input-procedimiento').value.trim();
        const activo = document.getElementById('input-activo').checked;

        if (!nombre || !procedimiento) {
            this.showSummary('Complete los campos obligatorios: Nombre y Procedimiento.');
            return;
        }

        this.saving = true;
        const btn = document.getElementById('modal-submit-btn');
        if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }

        try {
            const url = this.editingId ? `${this.baseUrl}${this.editingId}/` : this.baseUrl;
            const method = this.editingId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({ nombre, procedimiento, activo }),
            });

            const data = await response.json();
            if (data.success) {
                this.closeModal();
                this.showAlert(
                    this.editingId ? 'Procedimiento actualizado correctamente.' : 'Procedimiento creado correctamente.',
                    'success'
                );
                setTimeout(() => window.location.reload(), 800);
            } else {
                this.showSummary(data.error || 'No se pudo guardar el procedimiento.');
            }
        } catch (err) {
            this.showSummary('Error de conexión. Intente nuevamente.');
        } finally {
            this.saving = false;
            if (btn) {
                btn.disabled = false;
                btn.textContent = this.editingId ? 'Actualizar' : 'Guardar';
            }
        }
    }

    async confirmDelete() {
        if (!this.deleteId) return;
        try {
            const response = await fetch(`${this.baseUrl}${this.deleteId}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': this.getCsrfToken() },
            });
            const data = await response.json();
            if (data.success) {
                this.closeConfirmModal();
                this.showAlert('Procedimiento eliminado correctamente.', 'success');
                setTimeout(() => window.location.reload(), 800);
            } else {
                this.showAlert('Error: ' + (data.error || 'No se pudo eliminar.'), 'error');
            }
        } catch (err) {
            this.showAlert('Error de conexión.', 'error');
        }
    }

    closeModal() {
        document.getElementById('procedimientoModal').style.display = 'none';
        this.editingId = null;
    }

    closeConfirmModal() {
        document.getElementById('confirmModal').style.display = 'none';
        this.deleteId = null;
    }

    showSummary(msg) {
        const el = document.getElementById('formValidationSummary');
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('hidden-initially');
        el.style.display = 'block';
    }

    hideSummary() {
        const el = document.getElementById('formValidationSummary');
        if (!el) return;
        el.style.display = 'none';
    }

    getCsrfToken() {
        return document.cookie.split(';')
            .find(c => c.trim().startsWith('csrftoken='))
            ?.split('=')[1] ?? '';
    }

    showAlert(message, type = 'info') {
        const colors = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const icons  = { success: 'check-circle', error: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle' };
        const alert = document.createElement('div');
        alert.className = 'proc-alert proc-alert-' + type;
        alert.innerHTML = `<i class="fas fa-${icons[type] || icons.info}"></i><span>${message}</span>
            <button class="proc-alert-close">×</button>`;
        alert.querySelector('.proc-alert-close').addEventListener('click', () => alert.remove());
        document.body.appendChild(alert);
        setTimeout(() => alert.parentElement && alert.remove(), 4000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.procedimientosManager = new ProcedimientosManager();
});
