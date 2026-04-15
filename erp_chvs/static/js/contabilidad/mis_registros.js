// mis_registros.js — Gestión de registros contables del líder

function estadoDisplayEfectivo(r) {
    if (r.tipo === 'MATERIAS_PRIMAS' && r.estado === 'APROBADO_COMPRAS') {
        return 'Enviado a Contabilidad';
    }
    return r.estado_display;
}

class MisRegistrosManager {
    constructor() {
        this.saving = false;
        this.allRegistros = [];
        this.init();
    }

    init() {
        this.cargarRegistros();
        this.setupModalNuevo();
        this.setupFiltros();
    }

    setupModalNuevo() {
        const btnNuevo = document.getElementById('btn-nuevo-registro');
        const modal = document.getElementById('nuevoRegistroModal');
        const closeBtn = document.getElementById('close-nuevo-modal');
        const cancelBtn = document.getElementById('cancel-nuevo-modal');
        const guardarBtn = document.getElementById('btn-guardar-registro');

        if (btnNuevo) btnNuevo.addEventListener('click', () => this.abrirModal());
        if (closeBtn) closeBtn.addEventListener('click', () => this.cerrarModal());
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.cerrarModal());
        if (guardarBtn) guardarBtn.addEventListener('click', () => this.guardarRegistro());

        window.addEventListener('click', (e) => {
            if (e.target === modal) this.cerrarModal();
        });
    }

    setupFiltros() {
        const filtroTipo = document.getElementById('filtro-tipo');
        const filtroEstado = document.getElementById('filtro-estado');
        const btnLimpiar = document.getElementById('btn-limpiar-filtros');

        if (filtroTipo) filtroTipo.addEventListener('change', () => this.applyFilters());
        if (filtroEstado) filtroEstado.addEventListener('change', () => this.applyFilters());
        if (btnLimpiar) btnLimpiar.addEventListener('click', () => this.limpiarFiltros());
    }

    abrirModal() {
        const modal = document.getElementById('nuevoRegistroModal');
        const form = document.getElementById('nuevo-tipo');
        if (form) {
            document.getElementById('nuevo-tipo').value = '';
            document.getElementById('nuevo-mes').value = '';
            document.getElementById('nuevo-ano').value = '';
            document.getElementById('nuevo-descripcion').value = '';
        }
        if (modal) modal.style.display = 'block';
    }

    cerrarModal() {
        const modal = document.getElementById('nuevoRegistroModal');
        if (modal) modal.style.display = 'none';
    }

    async cargarRegistros() {
        try {
            const response = await fetch(MIS_REGISTROS_URL);
            const data = await response.json();
            if (data.success) {
                this.allRegistros = data.data;
                this.applyFilters();
            } else {
                this.mostrarError('Error al cargar registros: ' + (data.error || ''));
            }
        } catch (error) {
            console.error('Error al cargar registros:', error);
            this.mostrarError('Error de conexión al cargar registros.');
        }
    }

    applyFilters() {
        const tipo = document.getElementById('filtro-tipo')?.value || '';
        const estado = document.getElementById('filtro-estado')?.value || '';

        const filtrados = this.allRegistros.filter(r => {
            const matchTipo = !tipo || r.tipo === tipo;
            const matchEstado = !estado || r.estado === estado;
            return matchTipo && matchEstado;
        });

        this.renderTabla(filtrados);
    }

    limpiarFiltros() {
        const filtroTipo = document.getElementById('filtro-tipo');
        const filtroEstado = document.getElementById('filtro-estado');
        if (filtroTipo) filtroTipo.value = '';
        if (filtroEstado) filtroEstado.value = '';
        this.applyFilters();
    }

    renderTabla(registros) {
        const tbody = document.getElementById('registros-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!registros.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center">No se encontraron registros.</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        registros.forEach((r, idx) => {
            const tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.dataset.id = r.id;

            const valorFormateado = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(r.valor_total);
            const fechaEnvio = r.fecha_envio ? new Date(r.fecha_envio).toLocaleDateString('es-CO') : '—';

            tr.innerHTML = `
                <td>${r.id}</td>
                <td>${r.lider || '<span class="text-muted">—</span>'}</td>
                <td>${r.periodo_mes}/${r.periodo_ano}</td>
                <td>${r.tipo_display}</td>
                <td>${r.descripcion || '<span class="text-muted">—</span>'}</td>
                <td>${r.total_documentos}</td>
                <td>${valorFormateado}</td>
                <td><span class="estado-badge estado-badge-${r.estado.toLowerCase().replace(/_/g, '')}">${estadoDisplayEfectivo(r)}</span></td>
                <td>${fechaEnvio}</td>
                <td>
                    <a href="/contabilidad/registro/${r.id}/" class="btn btn-sm btn-primary">
                        <i class="fas fa-eye"></i> Ver
                    </a>
                </td>
            `;
            fragment.appendChild(tr);
        });
        tbody.appendChild(fragment);
    }

    async guardarRegistro() {
        if (this.saving) return;
        this.saving = true;

        const btn = document.getElementById('btn-guardar-registro');
        if (btn) { btn.disabled = true; btn.textContent = 'Creando...'; }

        const tipo = document.getElementById('nuevo-tipo')?.value;
        const periodo_mes = document.getElementById('nuevo-mes')?.value;
        const periodo_ano = document.getElementById('nuevo-ano')?.value;
        const descripcion = document.getElementById('nuevo-descripcion')?.value?.trim() || '';

        if (!tipo || !periodo_mes || !periodo_ano) {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-save"></i> Crear Registro'; }
            this.mostrarAlerta('Tipo, mes y año son obligatorios.', 'warning');
            return;
        }

        try {
            const response = await fetch(CREAR_REGISTRO_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ tipo, periodo_mes: parseInt(periodo_mes), periodo_ano: parseInt(periodo_ano), descripcion }),
            });
            const data = await response.json();
            if (data.success) {
                this.cerrarModal();
                this.mostrarAlerta('Registro creado exitosamente.', 'success');
                // Redirigir al detalle del nuevo registro
                window.location.href = `/contabilidad/registro/${data.id}/`;
            } else {
                this.mostrarAlerta(data.error || 'Error al crear el registro.', 'error');
            }
        } catch (error) {
            console.error('Error al crear registro:', error);
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-save"></i> Crear Registro'; }
        }
    }

    mostrarAlerta(mensaje, tipo) {
        const colores = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const iconos = { success: 'check-circle', error: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle' };

        const alerta = document.createElement('div');
        alerta.style.cssText = `
            position:fixed; top:20px; right:20px; z-index:10000;
            padding:15px 20px; border-radius:5px; color:white; font-weight:500;
            min-width:300px; box-shadow:0 4px 6px rgba(0,0,0,.1);
            display:flex; align-items:center; gap:10px;
            background-color:${colores[tipo] || colores.info};
            animation: slideInRight 0.3s ease;
        `;
        alerta.innerHTML = `
            <i class="fas fa-${iconos[tipo] || iconos.info}"></i>
            <span>${mensaje}</span>
            <button style="background:none;border:none;color:white;font-size:18px;cursor:pointer;margin-left:auto;" onclick="this.parentElement.remove()">×</button>
        `;
        document.body.appendChild(alerta);
        setTimeout(() => { if (alerta.parentElement) alerta.remove(); }, 5000);
    }

    mostrarError(msg) {
        const tbody = document.getElementById('registros-tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="10" class="text-center" style="color:#e74c3c;">${msg}</td></tr>`;
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

let misRegistrosManager;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('registrosTable')) {
        misRegistrosManager = new MisRegistrosManager();
    }
});
