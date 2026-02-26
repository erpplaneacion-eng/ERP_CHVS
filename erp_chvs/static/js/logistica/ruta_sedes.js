// ruta_sedes.js - Gestión de asignación de sedes a rutas

class RutaSedesManager {
    constructor() {
        this.baseUrl = '/logistica/api/ruta-sedes/';
        this.rutasUrl = '/logistica/api/rutas-activas/';
        this.sedesUrl = '/logistica/api/sedes/';
        this.editingId = null;
        this.deleteId = null;
        this.saving = false;
        this.init();
    }

    init() {
        this.setupModalEvents();
        this.loadTable();
        this.loadSelects();
    }

    setupModalEvents() {
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('rutaSedeModal');
            const confirmModal = document.getElementById('rutaSedeConfirmModal');
            if (event.target === modal) this.closeModal();
            if (event.target === confirmModal) this.closeConfirmModal();
        });
    }

    async loadSelects() {
        try {
            const [rutasResp, sedesResp] = await Promise.all([
                fetch(this.rutasUrl),
                fetch(this.sedesUrl)
            ]);
            const rutasData = await rutasResp.json();
            const sedesData = await sedesResp.json();

            // Poblar select de rutas en modal y filtro
            const rutaSelect = document.getElementById('rs_ruta');
            const filtroRuta = document.getElementById('filtroRuta');

            [rutaSelect, filtroRuta].forEach(sel => {
                if (!sel) return;
                const firstOption = sel.options[0];
                sel.innerHTML = '';
                if (firstOption) sel.appendChild(firstOption);

                rutasData.rutas.forEach(r => {
                    const opt = document.createElement('option');
                    opt.value = r.id;
                    opt.textContent = `${r.nombre_ruta} (${r.id_tipo_ruta__tipo || ''})`;
                    sel.appendChild(opt);
                });
            });

            // Poblar select de sedes
            const sedeSelect = document.getElementById('rs_sede');
            if (sedeSelect) {
                sedesData.sedes.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s.cod_interprise;
                    opt.textContent = `${s.nombre_sede_educativa} — ${s['codigo_ie__nombre_institucion'] || ''}`;
                    sedeSelect.appendChild(opt);
                });
            }

        } catch (error) {
            console.error('Error al cargar selects:', error);
        }
    }

    async loadTable(rutaId = '') {
        try {
            const url = rutaId ? `${this.baseUrl}?ruta_id=${rutaId}` : this.baseUrl;
            const response = await fetch(url);
            const data = await response.json();
            this.updateTable(data.ruta_sedes);
        } catch (error) {
            console.error('Error al cargar asignaciones:', error);
            this.showAlert('Error al cargar los datos', 'error');
        }
    }

    updateTable(items) {
        const tbody = document.querySelector('#rutaSedesTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay asignaciones registradas</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        items.forEach(rs => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${rs.id}</td>
                <td>${rs.ruta_nombre}</td>
                <td>${rs.tipo_ruta_nombre}</td>
                <td>${rs.sede_nombre}</td>
                <td><span class="orden-badge">${rs.orden_visita}</span></td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="rutaSedesManager.editRutaSede(${rs.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="rutaSedesManager.deleteRutaSede(${rs.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            fragment.appendChild(row);
        });
        tbody.appendChild(fragment);
    }

    filtrarPorRuta(rutaId) {
        this.loadTable(rutaId);
    }

    showCreateModal() {
        this.editingId = null;
        const modal = document.getElementById('rutaSedeModal');
        const title = document.getElementById('rutaSedeModalTitle');
        const form = document.getElementById('rutaSedeForm');
        const saveBtn = document.getElementById('rutaSedeSaveBtn');

        if (title) title.textContent = 'Nueva Asignación';
        if (form) form.reset();
        document.getElementById('rs_orden').value = 1;
        if (saveBtn) saveBtn.textContent = 'Guardar';
        if (modal) modal.style.display = 'block';
    }

    async editRutaSede(id) {
        this.editingId = id;
        try {
            const response = await fetch(`${this.baseUrl}${id}/`);
            const data = await response.json();

            const modal = document.getElementById('rutaSedeModal');
            const title = document.getElementById('rutaSedeModalTitle');
            const saveBtn = document.getElementById('rutaSedeSaveBtn');

            if (title) title.textContent = 'Editar Asignación';
            document.getElementById('rs_ruta').value = data.id_ruta;
            document.getElementById('rs_sede').value = data.sede_educativa;
            document.getElementById('rs_orden').value = data.orden_visita;
            if (saveBtn) saveBtn.textContent = 'Actualizar';
            if (modal) modal.style.display = 'block';

        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al cargar los datos de la asignación', 'error');
        }
    }

    deleteRutaSede(id) {
        this.deleteId = id;
        const confirmModal = document.getElementById('rutaSedeConfirmModal');
        if (confirmModal) confirmModal.style.display = 'block';
    }

    async saveRutaSede() {
        if (this.saving) return;
        this.saving = true;

        const saveBtn = document.getElementById('rutaSedeSaveBtn');
        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Guardando...'; }

        const id_ruta = document.getElementById('rs_ruta').value;
        const sede_educativa = document.getElementById('rs_sede').value;
        const orden_visita = parseInt(document.getElementById('rs_orden').value, 10) || 1;

        if (!id_ruta || !sede_educativa) {
            this.saving = false;
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = this.editingId ? 'Actualizar' : 'Guardar'; }
            this.showAlert('La ruta y la sede son obligatorias', 'warning');
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
                body: JSON.stringify({ id_ruta, sede_educativa, orden_visita })
            });

            const data = await response.json();

            if (data.success) {
                this.closeModal();
                this.showAlert(
                    this.editingId ? 'Asignación actualizada exitosamente' : 'Sede asignada exitosamente',
                    'success'
                );
                const filtroRuta = document.getElementById('filtroRuta');
                this.loadTable(filtroRuta ? filtroRuta.value : '');
            } else {
                this.showAlert(data.error || 'No se pudo guardar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al guardar la asignación', 'error');
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
                this.showAlert('Asignación eliminada exitosamente', 'success');
                const filtroRuta = document.getElementById('filtroRuta');
                this.loadTable(filtroRuta ? filtroRuta.value : '');
            } else {
                this.closeConfirmModal();
                this.showAlert(data.error || 'No se pudo eliminar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al eliminar la asignación', 'error');
        }
    }

    closeModal() {
        const modal = document.getElementById('rutaSedeModal');
        if (modal) modal.style.display = 'none';
        this.editingId = null;
    }

    closeConfirmModal() {
        const confirmModal = document.getElementById('rutaSedeConfirmModal');
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

let rutaSedesManager;

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('rutaSedesTable')) {
        rutaSedesManager = new RutaSedesManager();
    }
});
