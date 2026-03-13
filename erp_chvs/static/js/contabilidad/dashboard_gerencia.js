// dashboard_gerencia.js — Dashboard de Gerencia

class DashboardGerenciaManager {
    constructor() {
        this.init();
    }

    init() {
        this.cargarDashboard();
        this.setupFiltros();
    }

    setupFiltros() {
        const btnAplicar = document.getElementById('btn-aplicar-filtros');
        const btnLimpiar = document.getElementById('btn-limpiar-filtros');
        const btnActualizar = document.getElementById('btn-actualizar');

        if (btnAplicar) btnAplicar.addEventListener('click', () => this.cargarDashboard());
        if (btnLimpiar) btnLimpiar.addEventListener('click', () => this.limpiarYRecargar());
        if (btnActualizar) btnActualizar.addEventListener('click', () => this.cargarDashboard());
    }

    limpiarYRecargar() {
        const ids = ['filtro-lider', 'filtro-mes', 'filtro-ano', 'filtro-tipo', 'filtro-estado'];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        this.cargarDashboard();
    }

    getFiltros() {
        const filtros = {};
        const lider = document.getElementById('filtro-lider')?.value;
        const mes = document.getElementById('filtro-mes')?.value;
        const ano = document.getElementById('filtro-ano')?.value;
        const tipo = document.getElementById('filtro-tipo')?.value;
        const estado = document.getElementById('filtro-estado')?.value;

        if (lider) filtros.lider_id = lider;
        if (mes) filtros.periodo_mes = mes;
        if (ano) filtros.periodo_ano = ano;
        if (tipo) filtros.tipo = tipo;
        if (estado) filtros.estado = estado;

        return filtros;
    }

    async cargarDashboard() {
        const filtros = this.getFiltros();
        const params = new URLSearchParams(filtros).toString();
        const url = params ? `${DASHBOARD_URL}?${params}` : DASHBOARD_URL;

        try {
            const response = await fetch(url);
            const data = await response.json();
            if (data.success) {
                this.renderKPIs(data.data.conteos);
                this.renderTabla(data.data.registros);
                this.poblarLideres(data.data.lideres);
            } else {
                console.error('Error en dashboard:', data.error);
            }
        } catch (error) {
            console.error('Error al cargar dashboard:', error);
        }
    }

    renderKPIs(conteos) {
        const container = document.getElementById('kpi-container');
        if (!container) return;

        const estadosConfig = [
            { key: 'BORRADOR', label: 'Borrador', color: '#6c757d' },
            { key: 'ENVIADO', label: 'Enviado', color: '#1e3a8a' },
            { key: 'EN_REVISION_COMPRAS', label: 'En Revisión', color: '#0ea5e9' },
            { key: 'DEVUELTO_COMPRAS', label: 'Devueltos', color: '#d97706' },
            { key: 'APROBADO_COMPRAS', label: 'Aprobado Compras', color: '#0d9488' },
            { key: 'OBSERVADO_CONTABILIDAD', label: 'Observados', color: '#ca8a04' },
            { key: 'CERRADO', label: 'Cerrados', color: '#14532d' },
        ];

        container.innerHTML = '';
        const fragment = document.createDocumentFragment();

        estadosConfig.forEach(cfg => {
            const count = conteos[cfg.key] || 0;
            const card = document.createElement('div');
            card.style.cssText = `
                background: white;
                border-radius: 8px;
                padding: 16px 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                min-width: 140px;
                border-top: 4px solid ${cfg.color};
                text-align: center;
                flex: 1;
            `;
            card.innerHTML = `
                <div style="font-size:28px; font-weight:700; color:${cfg.color};">${count}</div>
                <div style="font-size:13px; color:#6c757d; margin-top:4px;">${cfg.label}</div>
            `;
            fragment.appendChild(card);
        });

        container.appendChild(fragment);
    }

    renderTabla(registros) {
        const tbody = document.getElementById('dashboard-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!registros.length) {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No hay registros con los filtros aplicados.</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        registros.forEach(r => {
            const tr = document.createElement('tr');
            const valorFmt = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(r.valor_total);
            const fechaEnvio = r.fecha_envio ? new Date(r.fecha_envio).toLocaleDateString('es-CO') : '—';
            const fechaCierre = r.fecha_cierre ? new Date(r.fecha_cierre).toLocaleDateString('es-CO') : '—';

            tr.innerHTML = `
                <td>${r.id}</td>
                <td>${r.lider}</td>
                <td>${r.periodo_mes}/${r.periodo_ano}</td>
                <td>${r.tipo_display}</td>
                <td><span class="estado-badge estado-badge-${r.estado.toLowerCase().replace(/_/g, '')}">${r.estado_display}</span></td>
                <td>${r.total_documentos}</td>
                <td>${valorFmt}</td>
                <td>${fechaEnvio}</td>
                <td>${fechaCierre}</td>
                <td>${r.duracion_dias}</td>
                <td>${r.num_devoluciones}</td>
            `;
            fragment.appendChild(tr);
        });
        tbody.appendChild(fragment);
    }

    poblarLideres(lideres) {
        const select = document.getElementById('filtro-lider');
        if (!select || select.options.length > 1) return;

        lideres.forEach(l => {
            const opt = document.createElement('option');
            opt.value = l.id;
            opt.textContent = (l.first_name && l.last_name)
                ? `${l.first_name} ${l.last_name}`
                : l.username;
            select.appendChild(opt);
        });
    }
}

let dashboardGerenciaManager;
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboardTable')) {
        dashboardGerenciaManager = new DashboardGerenciaManager();
    }
});
