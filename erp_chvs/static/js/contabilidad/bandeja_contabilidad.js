// JavaScript para la bandeja de contabilidad
class BandejaContabilidadManager {
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
        const btnLimpiar = document.getElementById('btn-limpiar-filtros');

        if (filtroTipo) filtroTipo.addEventListener('change', () => this.applyFilters());
        if (btnLimpiar) btnLimpiar.addEventListener('click', () => {
            if (filtroTipo) filtroTipo.value = '';
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
            console.error('Error al cargar bandeja de contabilidad:', error);
        }
    }

    applyFilters() {
        const tipo = document.getElementById('filtro-tipo')?.value || '';
        const filtrados = this.allRegistros.filter(r => !tipo || r.tipo === tipo);
        this.renderTabla(filtrados);
    }

    renderTabla(registros) {
        const tbody = document.getElementById('bandeja-contabilidad-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!registros.length) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No hay registros en la bandeja.</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        registros.forEach(r => {
            const tr = document.createElement('tr');
            const valorFmt = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(r.valor_total);
            const fechaEnvio = r.fecha_envio ? new Date(r.fecha_envio).toLocaleDateString('es-CO') : '—';

            tr.innerHTML = `
                <td>${r.id}</td>
                <td>${r.lider}</td>
                <td>${r.periodo_mes}/${r.periodo_ano}</td>
                <td>${r.tipo_display}</td>
                <td>${r.total_documentos}</td>
                <td>${valorFmt}</td>
                <td><span class="estado-badge estado-badge-${r.estado.toLowerCase().replace(/_/g, '')}">${r.estado_display}</span></td>
                <td>${fechaEnvio}</td>
                <td>
                    ${r.estado !== 'DEVUELTO_COMPRAS'
                        ? `<a href="${REVISION_BASE_URL}${r.id}/" class="btn btn-sm btn-primary"><i class="fas fa-search"></i> Revisar</a>`
                        : '—'}
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
