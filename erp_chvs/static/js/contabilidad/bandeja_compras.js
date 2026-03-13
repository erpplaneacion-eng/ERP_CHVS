// bandeja_compras.js — Bandeja de Compras

class BandejaComprasManager {
    constructor() {
        this.allRegistros = [];
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

        if (filtroTipo) filtroTipo.addEventListener('change', () => this.applyFilters());
        if (filtroEstado) filtroEstado.addEventListener('change', () => this.applyFilters());
        if (btnLimpiar) btnLimpiar.addEventListener('click', () => {
            if (filtroTipo) filtroTipo.value = '';
            if (filtroEstado) filtroEstado.value = '';
            this.applyFilters();
        });
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
            const matchTipo = !tipo || r.tipo === tipo;
            const matchEstado = !estado || r.estado === estado;
            return matchTipo && matchEstado;
        });

        this.renderTabla(filtrados);
    }

    renderTabla(registros) {
        const tbody = document.getElementById('bandeja-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!registros.length) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No hay registros en la bandeja.</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        registros.forEach(r => {
            const tr = document.createElement('tr');
            const valorFmt = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(r.valor_total);
            const fechaEnvio = r.fecha_envio ? new Date(r.fecha_envio).toLocaleDateString('es-CO') : '—';
            const tiempoMs = r.fecha_envio ? Date.now() - new Date(r.fecha_envio).getTime() : 0;
            const tiempoDias = r.fecha_envio ? Math.floor(tiempoMs / 86400000) : '—';

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
                    <a href="${REVISION_BASE_URL}${r.id}/" class="btn btn-sm btn-primary">
                        <i class="fas fa-search"></i> Revisar
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
