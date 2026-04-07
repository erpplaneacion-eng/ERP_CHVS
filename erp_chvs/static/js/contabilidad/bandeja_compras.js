// bandeja_compras.js — Bandeja de Compras

const ESTADOS_ACTIVOS_COMPRAS = ['ENVIADO', 'EN_REVISION_COMPRAS', 'OBSERVADO_CONTABILIDAD'];

class BandejaComprasManager {
    constructor() {
        this.allRegistros = [];
        this.modoHistorial = false;
        this.init();
    }

    init() {
        this.cargarRegistros();
        this.setupFiltros();
    }

    setupFiltros() {
        const filtroTipo = document.getElementById('filtro-tipo');
        const filtroEstado = document.getElementById('filtro-estado');
        const btnLimpiar = document.getElementById('btn-limpiar-filtros');
        const btnToggle = document.getElementById('btn-toggle-historial');

        if (filtroTipo) filtroTipo.addEventListener('change', () => this.applyFilters());
        if (filtroEstado) filtroEstado.addEventListener('change', () => this.applyFilters());
        if (btnLimpiar) btnLimpiar.addEventListener('click', () => {
            if (filtroTipo) filtroTipo.value = '';
            if (filtroEstado) filtroEstado.value = '';
            this.applyFilters();
        });
        if (btnToggle) btnToggle.addEventListener('click', () => this.toggleHistorial());
    }

    async toggleHistorial() {
        this.modoHistorial = !this.modoHistorial;
        const btn = document.getElementById('btn-toggle-historial');
        if (btn) {
            btn.innerHTML = this.modoHistorial
                ? '<i class="fas fa-inbox"></i> Solo pendientes'
                : '<i class="fas fa-history"></i> Ver historial';
            btn.classList.toggle('btn-primary', this.modoHistorial);
            btn.classList.toggle('btn-outline-secondary', !this.modoHistorial);
        }
        // Mostrar/ocultar opciones históricas en el select de estado
        document.querySelectorAll('#filtro-estado .opt-historial').forEach(opt => {
            opt.style.display = this.modoHistorial ? '' : 'none';
        });
        // Si estaba filtrado por un estado histórico, limpiarlo
        const filtroEstado = document.getElementById('filtro-estado');
        if (!this.modoHistorial && filtroEstado &&
            !ESTADOS_ACTIVOS_COMPRAS.includes(filtroEstado.value)) {
            filtroEstado.value = '';
        }

        const tbody = document.getElementById('bandeja-tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="10" class="text-center text-muted">Cargando...</td></tr>`;

        const url = BANDEJA_URL + (this.modoHistorial ? '?todos=1' : '');
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (data.success) {
                this.allRegistros = data.data;
                this.applyFilters();
            } else {
                if (tbody) tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error al cargar datos.</td></tr>`;
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
            if (tbody) tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error de conexión: ${error.message}</td></tr>`;
        }
    }

    async cargarRegistros() {
        try {
            const response = await fetch(BANDEJA_URL);
            const data = await response.json();
            if (data.success) {
                this.allRegistros = data.data;
                this.applyFilters();
            }
        } catch (error) {
            console.error('Error al cargar bandeja:', error);
        }
    }

    applyFilters() {
        const tipo = document.getElementById('filtro-tipo')?.value || '';
        const estado = document.getElementById('filtro-estado')?.value || '';

        const filtrados = this.allRegistros.filter(r => {
            return (!tipo || r.tipo === tipo) && (!estado || r.estado === estado);
        });

        this.renderTabla(filtrados);
    }

    renderTabla(registros) {
        const tbody = document.getElementById('bandeja-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!registros.length) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center text-muted">${
                this.modoHistorial ? 'No hay registros en el historial.' : 'No hay registros pendientes.'
            }</td></tr>`;
            return;
        }

        const fragment = document.createDocumentFragment();
        registros.forEach(r => {
            const tr = document.createElement('tr');
            if (r.estado === 'CERRADO') tr.style.opacity = '0.75';

            const valorFmt = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(r.valor_total);
            const fechaEnvio = r.fecha_envio ? new Date(r.fecha_envio).toLocaleDateString('es-CO') : '—';
            const tiempoMs = r.fecha_envio ? Date.now() - new Date(r.fecha_envio).getTime() : 0;
            const tiempoDias = r.fecha_envio ? Math.floor(tiempoMs / 86400000) : '—';
            const esActivo = ESTADOS_ACTIVOS_COMPRAS.includes(r.estado);

            tr.innerHTML = `
                <td>${r.id}</td>
                <td>${r.lider}</td>
                <td>${r.periodo_mes}/${r.periodo_ano}</td>
                <td>${r.tipo_display}</td>
                <td>${r.total_documentos}</td>
                <td>${valorFmt}</td>
                <td><span class="estado-badge estado-badge-${r.estado.toLowerCase().replace(/_/g, '')}">${r.estado_display}</span></td>
                <td>${fechaEnvio}</td>
                <td>${tiempoDias !== '—' ? tiempoDias + ' día(s)' : '—'}</td>
                <td>
                    <a href="${REVISION_BASE_URL}${r.id}/" class="btn btn-sm ${esActivo ? 'btn-primary' : 'btn-outline-secondary'}">
                        <i class="fas fa-${esActivo ? 'search' : 'eye'}"></i> ${esActivo ? 'Revisar' : 'Ver'}
                    </a>
                </td>
            `;
            fragment.appendChild(tr);
        });
        tbody.appendChild(fragment);
    }
}

let bandejaComprasManager;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('bandejaTable')) {
        bandejaComprasManager = new BandejaComprasManager();
    }
});
