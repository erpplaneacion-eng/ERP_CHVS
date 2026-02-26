// rutas.js - Gestión de rutas de entrega

class RutasManager {
    constructor() {
        this.baseUrl = '/logistica/api/rutas/';
        this.tiposUrl = '/logistica/api/tipos-ruta/';
        this.programasUrl = '/logistica/api/programas/';
        this.editingId = null;
        this.deleteId = null;
        this.saving = false;
        this.allRutas = [];  // cache completo para filtrado en cliente
        this.init();
    }

    init() {
        this.setupModalEvents();
        this.loadTable();
        this.loadSelects();
    }

    setupModalEvents() {
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('rutaModal');
            const confirmModal = document.getElementById('rutaConfirmModal');
            if (event.target === modal) this.closeModal();
            if (event.target === confirmModal) this.closeConfirmModal();
        });
    }

    async loadSelects() {
        try {
            const [tiposResp, programasResp] = await Promise.all([
                fetch(this.tiposUrl),
                fetch(this.programasUrl)
            ]);
            const tiposData = await tiposResp.json();
            const programasData = await programasResp.json();

            // Selects del modal
            const tipoSelect = document.getElementById('ruta_tipo');
            const progSelect = document.getElementById('ruta_programa');

            // Selects de filtro
            const filtroTipo = document.getElementById('filtro-tipo');
            const filtroPrograma = document.getElementById('filtro-programa');

            tiposData.tipos_ruta.forEach(t => {
                const opt = () => {
                    const o = document.createElement('option');
                    o.value = t.id;
                    o.textContent = t.tipo;
                    return o;
                };
                if (tipoSelect) tipoSelect.appendChild(opt());
                if (filtroTipo) filtroTipo.appendChild(opt());
            });

            programasData.programas.forEach(p => {
                const label = `${p.programa}${p.contrato ? ' (' + p.contrato + ')' : ''}`;
                const opt = () => {
                    const o = document.createElement('option');
                    o.value = p.id;
                    o.textContent = label;
                    return o;
                };
                if (progSelect) progSelect.appendChild(opt());
                if (filtroPrograma) filtroPrograma.appendChild(opt());
            });

        } catch (error) {
            console.error('Error al cargar selects:', error);
        }
    }

    async loadTable() {
        try {
            const response = await fetch(this.baseUrl);
            const data = await response.json();
            this.allRutas = data.rutas;
            this.applyFilters();
        } catch (error) {
            console.error('Error al cargar rutas:', error);
            this.showAlert('Error al cargar los datos', 'error');
        }
    }

    applyFilters() {
        const nombre = (document.getElementById('filtro-nombre')?.value || '').toLowerCase().trim();
        const tipoId = document.getElementById('filtro-tipo')?.value || '';
        const programaId = document.getElementById('filtro-programa')?.value || '';
        const estado = document.getElementById('filtro-estado')?.value || '';

        const filtradas = this.allRutas.filter(r => {
            const matchNombre  = !nombre    || r.nombre_ruta.toLowerCase().includes(nombre);
            const matchTipo    = !tipoId    || String(r.id_tipo_ruta) === tipoId;
            const matchPrograma= !programaId|| String(r.id_programa) === programaId;
            const matchEstado  = !estado    || String(r.activa) === estado;
            return matchNombre && matchTipo && matchPrograma && matchEstado;
        });

        this.updateTable(filtradas);
    }

    clearFilters() {
        const ids = ['filtro-nombre', 'filtro-tipo', 'filtro-programa', 'filtro-estado'];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        this.applyFilters();
    }

    updateTable(rutas) {
        const tbody = document.querySelector('#rutasTable tbody');
        if (!tbody) return;

        const totalEl = document.getElementById('total-rutas');
        if (totalEl) totalEl.textContent = rutas.length;

        tbody.innerHTML = '';

        if (!rutas.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No se encontraron rutas</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        rutas.forEach(r => {
            const estadoBadge = r.activa
                ? '<span class="badge badge-success">Activa</span>'
                : '<span class="badge badge-secondary">Inactiva</span>';
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${r.id}</td>
                <td>${r.nombre_ruta}</td>
                <td>${r.tipo_ruta_nombre}</td>
                <td>${r.programa_nombre}</td>
                <td>${estadoBadge}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="rutasManager.editRuta(${r.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="rutasManager.deleteRuta(${r.id})">
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
        const modal = document.getElementById('rutaModal');
        const title = document.getElementById('rutaModalTitle');
        const form = document.getElementById('rutaForm');
        const saveBtn = document.getElementById('rutaSaveBtn');

        if (title) title.textContent = 'Nueva Ruta';
        if (form) form.reset();
        document.getElementById('ruta_activa').checked = true;
        if (saveBtn) saveBtn.textContent = 'Guardar';
        if (modal) modal.style.display = 'block';
    }

    async editRuta(id) {
        this.editingId = id;
        try {
            const response = await fetch(`${this.baseUrl}${id}/`);
            const data = await response.json();

            const modal = document.getElementById('rutaModal');
            const title = document.getElementById('rutaModalTitle');
            const saveBtn = document.getElementById('rutaSaveBtn');

            if (title) title.textContent = 'Editar Ruta';
            document.getElementById('ruta_nombre').value = data.nombre_ruta;
            document.getElementById('ruta_tipo').value = data.id_tipo_ruta;
            document.getElementById('ruta_programa').value = data.id_programa;
            document.getElementById('ruta_activa').checked = data.activa;
            if (saveBtn) saveBtn.textContent = 'Actualizar';
            if (modal) modal.style.display = 'block';

        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al cargar los datos de la ruta', 'error');
        }
    }

    deleteRuta(id) {
        this.deleteId = id;
        const confirmModal = document.getElementById('rutaConfirmModal');
        if (confirmModal) confirmModal.style.display = 'block';
    }

    async saveRuta() {
        if (this.saving) return;
        this.saving = true;

        const saveBtn = document.getElementById('rutaSaveBtn');
        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Guardando...'; }

        const nombre = document.getElementById('ruta_nombre').value.trim();
        const id_tipo_ruta = document.getElementById('ruta_tipo').value;
        const id_programa = document.getElementById('ruta_programa').value;
        const activa = document.getElementById('ruta_activa').checked;

        if (!nombre || !id_tipo_ruta || !id_programa) {
            this.saving = false;
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = this.editingId ? 'Actualizar' : 'Guardar'; }
            this.showAlert('Nombre, tipo de ruta y programa son obligatorios', 'warning');
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
                body: JSON.stringify({ nombre_ruta: nombre, id_tipo_ruta, id_programa, activa })
            });

            const data = await response.json();

            if (data.success) {
                this.closeModal();
                this.showAlert(
                    this.editingId ? 'Ruta actualizada exitosamente' : 'Ruta creada exitosamente',
                    'success'
                );
                this.loadTable();
            } else {
                this.showAlert(data.error || 'No se pudo guardar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al guardar la ruta', 'error');
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
                this.showAlert('Ruta eliminada exitosamente', 'success');
                this.loadTable();
            } else {
                this.closeConfirmModal();
                this.showAlert(data.error || 'No se pudo eliminar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al eliminar la ruta', 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('rutaModal');
        if (modal) modal.style.display = 'none';
        this.editingId = null;
    }

    closeConfirmModal() {
        const confirmModal = document.getElementById('rutaConfirmModal');
        if (confirmModal) confirmModal.style.display = 'none';
        this.deleteId = null;
    }

    showAlert(message, type = 'info') {
        const colors = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const icons = { success: 'check-circle', error: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle' };

        const alert = document.createElement('div');
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

let rutasManager;

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('rutasTable')) {
        rutasManager = new RutasManager();
    }
});
