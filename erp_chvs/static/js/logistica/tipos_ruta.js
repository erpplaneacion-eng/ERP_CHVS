// tipos_ruta.js - Gestión de tipos de ruta

class TiposRutaManager {
    constructor() {
        this.baseUrl = '/logistica/api/tipos-ruta/';
        this.editingId = null;
        this.deleteId = null;
        this.saving = false;
        this.init();
    }

    init() {
        this.setupModalEvents();
        this.loadTable();
    }

    setupModalEvents() {
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('tipoRutaModal');
            const confirmModal = document.getElementById('tipoRutaConfirmModal');
            if (event.target === modal) this.closeModal();
            if (event.target === confirmModal) this.closeConfirmModal();
        });
    }

    async loadTable() {
        try {
            const response = await fetch(this.baseUrl);
            const data = await response.json();
            this.updateTable(data.tipos_ruta);
        } catch (error) {
            console.error('Error al cargar tipos de ruta:', error);
            this.showAlert('Error al cargar los datos', 'error');
        }
    }

    updateTable(tipos) {
        const tbody = document.querySelector('#tiposRutaTable tbody');
        if (!tbody) return;

        const totalEl = document.getElementById('total-tipos-ruta');
        if (totalEl) totalEl.textContent = tipos.length;

        tbody.innerHTML = '';

        if (!tipos.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">No hay tipos de ruta registrados</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        tipos.forEach(t => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${t.id}</td>
                <td>${t.tipo}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="tiposRutaManager.editTipoRuta(${t.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="tiposRutaManager.deleteTipoRuta(${t.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            fragment.appendChild(row);
        });
        tbody.appendChild(fragment);
    }

    showCreateModal() {
        this.editingId = null;
        const modal = document.getElementById('tipoRutaModal');
        const title = document.getElementById('tipoRutaModalTitle');
        const form = document.getElementById('tipoRutaForm');
        const saveBtn = document.getElementById('tipoRutaSaveBtn');

        if (title) title.textContent = 'Nuevo Tipo de Ruta';
        if (form) form.reset();
        if (saveBtn) saveBtn.textContent = 'Guardar';
        if (modal) modal.style.display = 'block';
    }

    async editTipoRuta(id) {
        this.editingId = id;
        try {
            const response = await fetch(`${this.baseUrl}${id}/`);
            const data = await response.json();

            const modal = document.getElementById('tipoRutaModal');
            const title = document.getElementById('tipoRutaModalTitle');
            const tipoField = document.getElementById('tipo_nombre');
            const saveBtn = document.getElementById('tipoRutaSaveBtn');

            if (title) title.textContent = 'Editar Tipo de Ruta';
            if (tipoField) tipoField.value = data.tipo;
            if (saveBtn) saveBtn.textContent = 'Actualizar';
            if (modal) modal.style.display = 'block';

        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al cargar los datos del tipo de ruta', 'error');
        }
    }

    deleteTipoRuta(id) {
        this.deleteId = id;
        const confirmModal = document.getElementById('tipoRutaConfirmModal');
        if (confirmModal) confirmModal.style.display = 'block';
    }

    async saveTipoRuta() {
        if (this.saving) return;
        this.saving = true;

        const saveBtn = document.getElementById('tipoRutaSaveBtn');
        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Guardando...'; }

        const tipoField = document.getElementById('tipo_nombre');
        const tipo = tipoField ? tipoField.value.trim() : '';

        if (!tipo) {
            this.saving = false;
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = this.editingId ? 'Actualizar' : 'Guardar'; }
            this.showAlert('El nombre del tipo es obligatorio', 'warning');
            return;
        }

        const url = this.editingId ? `${this.baseUrl}${this.editingId}/` : this.baseUrl;
        const method = this.editingId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ tipo })
            });

            const data = await response.json();

            if (data.success) {
                this.closeModal();
                this.showAlert(
                    this.editingId ? 'Tipo de ruta actualizado exitosamente' : 'Tipo de ruta creado exitosamente',
                    'success'
                );
                this.loadTable();
            } else {
                this.showAlert(data.error || 'No se pudo guardar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al guardar el tipo de ruta', 'error');
        } finally {
            this.saving = false;
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
                headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
            });

            const data = await response.json();

            if (data.success) {
                this.closeConfirmModal();
                this.showAlert('Tipo de ruta eliminado exitosamente', 'success');
                this.loadTable();
            } else {
                this.closeConfirmModal();
                this.showAlert(data.error || 'No se pudo eliminar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al eliminar el tipo de ruta', 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('tipoRutaModal');
        if (modal) modal.style.display = 'none';
        this.editingId = null;
    }

    closeConfirmModal() {
        const confirmModal = document.getElementById('tipoRutaConfirmModal');
        if (confirmModal) confirmModal.style.display = 'none';
        this.deleteId = null;
    }

    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        const colors = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const icons = { success: 'check-circle', error: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle' };

        alert.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            padding: 15px 20px; border-radius: 5px; color: white; font-weight: 500;
            min-width: 300px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex; align-items: center; gap: 10px;
            background-color: ${colors[type] || colors.info};
            animation: slideInRight 0.3s ease;
        `;
        alert.innerHTML = `
            <i class="fas fa-${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button style="background:none;border:none;color:white;font-size:18px;cursor:pointer;margin-left:auto;" onclick="this.parentElement.remove()">×</button>
        `;
        document.body.appendChild(alert);
        setTimeout(() => { if (alert.parentElement) alert.remove(); }, 5000);
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie) {
            for (const cookie of document.cookie.split(';')) {
                const c = cookie.trim();
                if (c.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(c.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

let tiposRutaManager;

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('tiposRutaTable')) {
        tiposRutaManager = new TiposRutaManager();
    }
});
