// JavaScript para la bandeja de contabilidad
const ESTADOS_ACTIVOS_CONTA = ['APROBADO_COMPRAS'];

function estadoDisplayEfectivo(r) {
    if (r.tipo === 'MATERIAS_PRIMAS' && r.estado === 'APROBADO_COMPRAS') {
        return 'Enviado a Contabilidad';
    }
    return r.estado_display;
}

class BandejaContabilidadManager {
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

        // Al entrar en historial, limpiar filtros para asegurar visibilidad
        const filtroEstado = document.getElementById('filtro-estado');
        if (this.modoHistorial && filtroEstado) filtroEstado.value = '';
        const filtroTipo = document.getElementById('filtro-tipo');
        if (this.modoHistorial && filtroTipo) filtroTipo.value = '';

        const tbody = document.getElementById('bandeja-contabilidad-tbody');
        if (tbody) tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">Cargando...</td></tr>`;

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
                if (tbody) tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Error al cargar datos.</td></tr>`;
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
            if (tbody) tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Error de conexión: ${error.message}</td></tr>`;
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
            console.error('Error al cargar bandeja de contabilidad:', error);
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
        const tbody = document.getElementById('bandeja-contabilidad-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!registros.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">${
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
            const puedeRevisar = r.estado === 'APROBADO_COMPRAS';

            tr.innerHTML = `
                <td>${r.id}</td>
                <td>${r.lider}</td>
                <td>${r.periodo_mes}/${r.periodo_ano}</td>
                <td>${r.tipo_display}</td>
                <td>${r.total_documentos}</td>
                <td>${valorFmt}</td>
                <td><span class="estado-badge estado-badge-${r.estado.toLowerCase().replace(/_/g, '')}">${estadoDisplayEfectivo(r)}</span></td>
                <td>${fechaEnvio}</td>
                <td>
                    ${puedeRevisar
                        ? `<a href="${REVISION_BASE_URL}${r.id}/" class="btn btn-sm btn-primary"><i class="fas fa-search"></i> Revisar</a>`
                        : `<a href="${REVISION_BASE_URL}${r.id}/" class="btn btn-sm btn-outline-secondary"><i class="fas fa-eye"></i> Ver</a>`}
                </td>
            `;
            fragment.appendChild(tr);
        });
        tbody.appendChild(fragment);
    }
}

let bandejaContabilidadManager;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('bandejaContabilidadTable')) {
        bandejaContabilidadManager = new BandejaContabilidadManager();
    }
});
