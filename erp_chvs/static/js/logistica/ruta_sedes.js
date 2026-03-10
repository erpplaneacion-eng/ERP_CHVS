// ruta_sedes.js - Gestión de asignación de sedes a rutas

class RutaSedesManager {
    constructor() {
        this.baseUrl = '/logistica/api/ruta-sedes/';
        this.bulkUrl = '/logistica/api/ruta-sedes/bulk/';
        this.rutasUrl = '/logistica/api/rutas-activas/';
        this.sedesUrl = '/logistica/api/sedes/';
        this.editingId = null;
        this.deleteId = null;
        this.saving = false;
        this.allSedes = [];
        this.municipioFiltro = '';
        this.selectedSedes = new Set();
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

        document.getElementById('rutaSedeCloseBtn')
            ?.addEventListener('click', () => this.closeModal());
        document.getElementById('rutaSedeCancelBtn')
            ?.addEventListener('click', () => this.closeModal());
        document.getElementById('rutaSedeSaveBtn')
            ?.addEventListener('click', () => this.saveRutaSede());
        document.getElementById('rsBuscadorSede')
            ?.addEventListener('input', (e) => this.renderSedesCheckboxes(e.target.value.trim()));
        document.getElementById('rsFiltroMunicipio')
            ?.addEventListener('change', (e) => {
                this.municipioFiltro = e.target.value;
                const buscador = document.getElementById('rsBuscadorSede');
                this.renderSedesCheckboxes(buscador ? buscador.value.trim() : '');
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

            this.allSedes = sedesData.sedes || [];

            // Poblar selects de rutas: crear + editar + filtro de página
            const rutaCreate = document.getElementById('rs_ruta');
            const rutaEdit   = document.getElementById('rs_ruta_edit');
            const filtroRuta = document.getElementById('filtroRuta');

            [rutaCreate, rutaEdit, filtroRuta].forEach(sel => {
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

            // Poblar select de sede (modo editar: lista simple)
            const sedeEdit = document.getElementById('rs_sede_edit');
            if (sedeEdit) {
                this.allSedes.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s.cod_interprise;
                    opt.textContent = `${s.nombre_sede_educativa} — ${s['codigo_ie__nombre_institucion'] || ''}`;
                    sedeEdit.appendChild(opt);
                });
            }

            // Poblar select de municipios con los valores únicos de las sedes
            const filtroMun = document.getElementById('rsFiltroMunicipio');
            if (filtroMun) {
                const municipiosMap = new Map();
                this.allSedes.forEach(s => {
                    const id = s['codigo_ie__id_municipios'];
                    const nombre = s['codigo_ie__id_municipios__nombre_municipio'];
                    if (id && nombre && !municipiosMap.has(id)) {
                        municipiosMap.set(id, nombre);
                    }
                });
                const sorted = Array.from(municipiosMap.entries()).sort((a, b) => a[1].localeCompare(b[1]));
                sorted.forEach(([id, nombre]) => {
                    const opt = document.createElement('option');
                    opt.value = id;
                    opt.textContent = nombre;
                    filtroMun.appendChild(opt);
                });
            }

            // Renderizar checkboxes para el panel de creación
            this.renderSedesCheckboxes('');

        } catch (error) {
            console.error('Error al cargar selects:', error);
        }
    }

    renderSedesCheckboxes(filter) {
        const lista = document.getElementById('rsSedesLista');
        if (!lista) return;

        const q = filter.toLowerCase();
        const filtradas = this.allSedes.filter(s => {
            const coincideTexto = !q ||
                s.nombre_sede_educativa.toLowerCase().includes(q) ||
                (s['codigo_ie__nombre_institucion'] || '').toLowerCase().includes(q);
            const coincideMunicipio = !this.municipioFiltro ||
                String(s['codigo_ie__id_municipios']) === String(this.municipioFiltro);
            return coincideTexto && coincideMunicipio;
        });

        lista.innerHTML = '';

        if (!filtradas.length) {
            lista.innerHTML = '<p class="rs-sedes-empty">No hay sedes que coincidan.</p>';
            return;
        }

        const frag = document.createDocumentFragment();
        filtradas.forEach(s => {
            const label = document.createElement('label');
            label.className = 'rs-sede-item';

            const chk = document.createElement('input');
            chk.type = 'checkbox';
            chk.value = s.cod_interprise;
            chk.className = 'rs-sede-chk';
            chk.checked = this.selectedSedes.has(s.cod_interprise);
            chk.addEventListener('change', () => {
                if (chk.checked) {
                    this.selectedSedes.add(s.cod_interprise);
                } else {
                    this.selectedSedes.delete(s.cod_interprise);
                }
                this._actualizarContador();
            });

            const texto = document.createElement('span');
            texto.textContent = `${s.nombre_sede_educativa} — ${s['codigo_ie__nombre_institucion'] || ''}`;

            label.appendChild(chk);
            label.appendChild(texto);
            frag.appendChild(label);
        });
        lista.appendChild(frag);
    }

    _actualizarContador() {
        const total = this.selectedSedes.size;
        const el = document.getElementById('rsSedesContador');
        if (!el) return;
        if (total === 0) {
            el.textContent = '0 seleccionadas';
            el.classList.remove('rs-contador-activo');
        } else {
            el.textContent = total === 1 ? '1 seleccionada' : `${total} seleccionadas`;
            el.classList.add('rs-contador-activo');
        }
        const saveBtn = document.getElementById('rutaSedeSaveBtn');
        if (saveBtn && !this.editingId) {
            saveBtn.textContent = total > 0
                ? `Asignar ${total} sede${total > 1 ? 's' : ''}`
                : 'Asignar sedes';
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

        const totalEl = document.getElementById('total-ruta-sedes');
        if (totalEl) totalEl.textContent = items.length;

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

        document.getElementById('rutaSedeModalTitle').textContent = 'Nueva Asignación';
        document.getElementById('rutaSedeSaveBtn').textContent = 'Asignar sedes';

        // Mostrar panel crear, ocultar panel editar
        document.getElementById('rsCreatePanel').classList.remove('rs-hidden');
        document.getElementById('rsEditPanel').classList.add('rs-hidden');

        // Resetear buscador, filtro de municipio, selección y contador
        document.getElementById('rs_ruta').value = '';
        const buscador = document.getElementById('rsBuscadorSede');
        if (buscador) buscador.value = '';
        const filtroMun = document.getElementById('rsFiltroMunicipio');
        if (filtroMun) filtroMun.value = '';
        this.municipioFiltro = '';
        this.selectedSedes = new Set();
        this._actualizarContador();

        document.getElementById('rutaSedeModal').style.display = 'block';
    }

    async editRutaSede(id) {
        this.editingId = id;
        try {
            const response = await fetch(`${this.baseUrl}${id}/`);
            const data = await response.json();

            document.getElementById('rutaSedeModalTitle').textContent = 'Editar Asignación';
            document.getElementById('rutaSedeSaveBtn').textContent = 'Actualizar';

            // Mostrar panel editar, ocultar panel crear
            document.getElementById('rsCreatePanel').classList.add('rs-hidden');
            document.getElementById('rsEditPanel').classList.remove('rs-hidden');

            document.getElementById('rs_ruta_edit').value = data.id_ruta;
            document.getElementById('rs_sede_edit').value = data.sede_educativa;
            document.getElementById('rs_orden').value = data.orden_visita;

            document.getElementById('rutaSedeModal').style.display = 'block';

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
        if (this.editingId) {
            await this._saveEdit();
        } else {
            await this._saveBulk();
        }
    }

    async _saveBulk() {
        this.saving = true;
        const saveBtn = document.getElementById('rutaSedeSaveBtn');
        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Guardando...'; }

        const id_ruta = document.getElementById('rs_ruta').value;
        const sedes = Array.from(this.selectedSedes);

        if (!id_ruta || sedes.length === 0) {
            this.saving = false;
            this._restoreSaveBtn();
            this.showAlert('Selecciona una ruta y al menos una sede', 'warning');
            return;
        }

        try {
            const response = await fetch(this.bulkUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ id_ruta, sedes })
            });
            const data = await response.json();

            if (data.success) {
                this.closeModal();
                this.showAlert(data.message || 'Sedes asignadas exitosamente', 'success');
                const filtroRuta = document.getElementById('filtroRuta');
                this.loadTable(filtroRuta ? filtroRuta.value : '');
            } else {
                this.showAlert(data.error || 'No se pudo guardar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al guardar las asignaciones', 'error');
        } finally {
            this.saving = false;
            this._restoreSaveBtn();
        }
    }

    async _saveEdit() {
        this.saving = true;
        const saveBtn = document.getElementById('rutaSedeSaveBtn');
        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Guardando...'; }

        const id_ruta = document.getElementById('rs_ruta_edit').value;
        const sede_educativa = document.getElementById('rs_sede_edit').value;
        const orden_visita = parseInt(document.getElementById('rs_orden').value, 10) || 1;

        if (!id_ruta || !sede_educativa) {
            this.saving = false;
            this._restoreSaveBtn();
            this.showAlert('La ruta y la sede son obligatorias', 'warning');
            return;
        }

        try {
            const response = await fetch(`${this.baseUrl}${this.editingId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ id_ruta, sede_educativa, orden_visita })
            });
            const data = await response.json();

            if (data.success) {
                this.closeModal();
                this.showAlert('Asignación actualizada exitosamente', 'success');
                const filtroRuta = document.getElementById('filtroRuta');
                this.loadTable(filtroRuta ? filtroRuta.value : '');
            } else {
                this.showAlert(data.error || 'No se pudo guardar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error al actualizar la asignación', 'error');
        } finally {
            this.saving = false;
            this._restoreSaveBtn();
        }
    }

    _restoreSaveBtn() {
        const saveBtn = document.getElementById('rutaSedeSaveBtn');
        if (!saveBtn) return;
        saveBtn.disabled = false;
        saveBtn.textContent = this.editingId ? 'Actualizar' : 'Asignar sedes';
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
