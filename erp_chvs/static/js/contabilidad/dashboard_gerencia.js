// dashboard_gerencia.js — Vista unificada: historial de líderes

class DashboardLideresManager {
    constructor() {
        this.allData = null;
        this.lideresPopulados = false;
        this.init();
    }

    init() {
        this.cargar();
        document.getElementById('btn-actualizar')?.addEventListener('click', () => this.cargar());
        document.getElementById('btn-filtrar')?.addEventListener('click', () => this.cargar());
        document.getElementById('btn-limpiar')?.addEventListener('click', () => this.limpiarYRecargar());
    }

    limpiarYRecargar() {
        ['filtro-lider', 'filtro-mes', 'filtro-tipo'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        const ano = document.getElementById('filtro-ano');
        if (ano) ano.value = '';
        this.cargar();
    }

    getFiltros() {
        const filtros = {};
        const lider = document.getElementById('filtro-lider')?.value;
        const mes = document.getElementById('filtro-mes')?.value;
        const ano = document.getElementById('filtro-ano')?.value;
        const tipo = document.getElementById('filtro-tipo')?.value;
        if (lider) filtros.lider_id = lider;
        if (mes) filtros.periodo_mes = mes;
        if (ano) filtros.periodo_ano = ano;
        if (tipo) filtros.tipo = tipo;
        return filtros;
    }

    async cargar() {
        document.getElementById('cargando').style.display = '';
        document.getElementById('tabla-container').style.display = 'none';

        const params = new URLSearchParams(this.getFiltros()).toString();
        const url = params ? `${DASHBOARD_URL}?${params}` : DASHBOARD_URL;

        try {
            const response = await fetch(url);
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Error del servidor');

            this.allData = data.data;
            this.renderKPIs(data.data.kpis);
            this.renderTabla(data.data.lideres);
            if (!this.lideresPopulados) this.poblarSelectLideres(data.data.lideres);
        } catch (error) {
            console.error('Error al cargar dashboard:', error);
            document.getElementById('cargando').innerHTML =
                `<div class="text-danger py-4"><i class="fas fa-exclamation-circle"></i> Error al cargar: ${error.message}</div>`;
        }
    }

    renderKPIs(conteos) {
        const container = document.getElementById('kpi-container');
        if (!container) return;

        const cfg = [
            { key: 'BORRADOR',               label: 'Borrador',         color: '#6c757d' },
            { key: 'ENVIADO',                 label: 'Enviados',         color: '#1e3a8a' },
            { key: 'EN_REVISION_COMPRAS',     label: 'En Revisión',      color: '#0ea5e9' },
            { key: 'DEVUELTO_COMPRAS',        label: 'Devueltos',        color: '#d97706' },
            { key: 'APROBADO_COMPRAS',        label: 'Aprobado Compras', color: '#0d9488' },
            { key: 'OBSERVADO_CONTABILIDAD',  label: 'Observados',       color: '#ca8a04' },
            { key: 'CERRADO',                 label: 'Cerrados',         color: '#14532d' },
        ];

        const fragment = document.createDocumentFragment();
        cfg.forEach(c => {
            const count = conteos[c.key] || 0;
            const card = document.createElement('div');
            card.style.cssText = `background:#fff;border-radius:8px;padding:14px 18px;box-shadow:0 2px 6px rgba(0,0,0,.08);
                min-width:120px;border-top:4px solid ${c.color};text-align:center;flex:1;`;
            card.innerHTML = `
                <div style="font-size:26px;font-weight:700;color:${c.color};">${count}</div>
                <div style="font-size:12px;color:#6c757d;margin-top:3px;">${c.label}</div>
            `;
            fragment.appendChild(card);
        });
        container.innerHTML = '';
        container.appendChild(fragment);
    }

    renderTabla(lideres) {
        document.getElementById('cargando').style.display = 'none';
        document.getElementById('tabla-container').style.display = '';

        const tbody = document.getElementById('tbody-lideres');
        const sinDatos = document.getElementById('sin-datos');
        const tabla = document.getElementById('tabla-lideres');

        if (!lideres.length) {
            tabla.style.display = 'none';
            sinDatos.style.display = '';
            return;
        }
        tabla.style.display = '';
        sinDatos.style.display = 'none';
        tbody.innerHTML = '';

        const fmt = v => new Intl.NumberFormat('es-CO', {
            style: 'currency', currency: 'COP', minimumFractionDigits: 0
        }).format(v);

        const dias = v => v !== null && v !== undefined ? `${v}d` : '—';

        const fragment = document.createDocumentFragment();

        lideres.forEach(lider => {
            const inicial = (lider.lider_nombre[0] || '?').toUpperCase();
            const estadoCritico = lider.estado_critico || '';

            // ---- Fila principal del líder ----
            const trLider = document.createElement('tr');
            trLider.className = 'fila-lider';
            trLider.dataset.liderId = lider.lider_id;
            trLider.style.cursor = 'pointer';

            const badgeCritico = estadoCritico
                ? `<span class="estado-badge estado-badge-${estadoCritico.toLowerCase().replace(/_/g,'')}" style="font-size:11px;">${this._estadoLabel(estadoCritico)}</span>`
                : '<span style="color:#999;font-size:12px;">Sin activos</span>';

            const devBadge = lider.total_devoluciones > 0
                ? `<span style="color:#d97706;font-weight:700;">${lider.total_devoluciones}</span>`
                : '0';

            trLider.innerHTML = `
                <td style="text-align:center;">
                    <i class="fas fa-chevron-right icono-toggle" style="font-size:11px;color:#888;transition:transform 0.2s;"></i>
                </td>
                <td>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="width:34px;height:34px;border-radius:50%;background:#1e3a8a;color:#fff;
                            display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;">
                            ${inicial}
                        </div>
                        <div>
                            <div style="font-weight:600;color:#1e3a8a;">${lider.lider_nombre}</div>
                            <div style="font-size:11px;color:#999;">@${lider.lider_username}</div>
                        </div>
                    </div>
                </td>
                <td>${badgeCritico}</td>
                <td style="text-align:center;font-weight:600;">${lider.total_registros}</td>
                <td style="text-align:center;">
                    ${lider.total_activos > 0
                        ? `<span style="color:#1e3a8a;font-weight:700;">${lider.total_activos}</span>`
                        : '0'}
                </td>
                <td style="text-align:center;">
                    <span style="color:#14532d;font-weight:600;">${lider.total_cerrados}</span>
                </td>
                <td style="text-align:center;">${devBadge}</td>
                <td style="text-align:right;font-size:13px;">${fmt(lider.valor_total_cerrado)}</td>
                <td style="text-align:center;">${dias(lider.promedio_dias_cierre)}</td>
                <td style="text-align:center;${lider.max_dias_cierre > 10 ? 'color:#c0392b;font-weight:700;' : ''}">${dias(lider.max_dias_cierre)}</td>
                <td style="text-align:center;">${dias(lider.promedio_dias_reentrega)}</td>
                <td style="text-align:center;${lider.max_dias_reentrega > 5 ? 'color:#d97706;font-weight:700;' : ''}">${dias(lider.max_dias_reentrega)}</td>
            `;
            fragment.appendChild(trLider);

            // ---- Fila detalle (colapsada) ----
            const trDetalle = document.createElement('tr');
            trDetalle.className = 'fila-detalle';
            trDetalle.dataset.liderId = lider.lider_id;
            trDetalle.style.display = 'none';

            const td = document.createElement('td');
            td.colSpan = 12;
            td.style.cssText = 'padding:0;background:#f8f9ff;border-bottom:2px solid #e0e0e0;';
            td.appendChild(this._crearSubTabla(lider.registros));
            trDetalle.appendChild(td);
            fragment.appendChild(trDetalle);

            // Toggle al hacer click en la fila líder
            trLider.addEventListener('click', () => this._toggleDetalle(lider.lider_id));
        });

        tbody.appendChild(fragment);
    }

    _crearSubTabla(registros) {
        const meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
        const fmt = v => new Intl.NumberFormat('es-CO', {
            style: 'currency', currency: 'COP', minimumFractionDigits: 0
        }).format(v);

        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'padding:12px 20px 16px 52px;';

        if (!registros.length) {
            wrapper.innerHTML = '<p class="text-muted" style="font-size:13px;">Sin registros.</p>';
            return wrapper;
        }

        const tabla = document.createElement('table');
        tabla.className = 'sub-detalle-tabla';
        tabla.style.cssText = 'width:100%;border-collapse:collapse;font-size:13px;';
        tabla.innerHTML = `
            <thead>
                <tr>
                    <th style="padding:7px 10px;text-align:left;">RC</th>
                    <th style="padding:7px 10px;text-align:left;">Tipo</th>
                    <th style="padding:7px 10px;text-align:left;">Período</th>
                    <th style="padding:7px 10px;text-align:left;">Estado</th>
                    <th style="padding:7px 10px;text-align:center;" title="Días en el estado actual">Días estado</th>
                    <th style="padding:7px 10px;text-align:center;">Devoluciones</th>
                    <th style="padding:7px 10px;text-align:center;" title="Días desde envío hasta cierre">Días cierre</th>
                    <th style="padding:7px 10px;text-align:center;" title="Días desde devolución hasta reenvío">Días reentrega</th>
                    <th style="padding:7px 10px;text-align:center;">Docs</th>
                    <th style="padding:7px 10px;text-align:right;">Valor</th>
                </tr>
            </thead>
        `;
        const tbody = document.createElement('tbody');

        registros.forEach(r => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid #eee';

            const derivadoTag = r.es_derivado
                ? `<span style="font-size:10px;background:#e3f2fd;color:#1565c0;border-radius:3px;padding:1px 5px;margin-left:4px;">derivado</span>`
                : '';

            const diasEstadoStyle = r.dias_en_estado > 5 && r.estado !== 'CERRADO'
                ? 'color:#c0392b;font-weight:700;'
                : '';

            const diasCierreVal = r.dias_cierre !== null && r.dias_cierre !== undefined
                ? `<span style="${r.dias_cierre > 10 ? 'color:#c0392b;font-weight:700;' : ''}">${r.dias_cierre}d</span>`
                : '—';

            const diasReentregaVal = r.dias_reentrega !== null && r.dias_reentrega !== undefined
                ? `<span style="${r.dias_reentrega > 5 ? 'color:#d97706;font-weight:700;' : ''}">${r.dias_reentrega}d</span>`
                : '—';

            tr.innerHTML = `
                <td style="padding:7px 10px;">
                    <a href="/contabilidad/registro/${r.id}/" style="font-weight:600;color:#1e3a8a;">
                        RC-${r.id}
                    </a>${derivadoTag}
                </td>
                <td style="padding:7px 10px;">${r.tipo_display}</td>
                <td style="padding:7px 10px;">${meses[r.periodo_mes - 1]} ${r.periodo_ano}</td>
                <td style="padding:7px 10px;">
                    <span class="estado-badge estado-badge-${r.estado.toLowerCase().replace(/_/g,'')}">${r.estado_display}</span>
                </td>
                <td style="padding:7px 10px;text-align:center;${diasEstadoStyle}">${r.dias_en_estado}d</td>
                <td style="padding:7px 10px;text-align:center;">
                    ${r.num_devoluciones > 0
                        ? `<span style="color:#d97706;font-weight:700;"><i class="fas fa-undo" style="font-size:10px;"></i> ${r.num_devoluciones}</span>`
                        : '—'}
                </td>
                <td style="padding:7px 10px;text-align:center;">${diasCierreVal}</td>
                <td style="padding:7px 10px;text-align:center;">${diasReentregaVal}</td>
                <td style="padding:7px 10px;text-align:center;">${r.total_documentos}</td>
                <td style="padding:7px 10px;text-align:right;">${fmt(r.valor_total)}</td>
            `;
            tbody.appendChild(tr);
        });

        tabla.appendChild(tbody);
        wrapper.appendChild(tabla);
        return wrapper;
    }

    _toggleDetalle(liderId) {
        const trDetalle = document.querySelector(`.fila-detalle[data-lider-id="${liderId}"]`);
        const trLider = document.querySelector(`.fila-lider[data-lider-id="${liderId}"]`);
        const icono = trLider?.querySelector('.icono-toggle');
        if (!trDetalle) return;

        const abierto = trDetalle.style.display !== 'none';
        trDetalle.style.display = abierto ? 'none' : '';
        if (icono) icono.style.transform = abierto ? '' : 'rotate(90deg)';
    }

    poblarSelectLideres(lideres) {
        const select = document.getElementById('filtro-lider');
        if (!select) return;
        lideres.forEach(l => {
            const opt = document.createElement('option');
            opt.value = l.lider_id;
            opt.textContent = l.lider_nombre;
            select.appendChild(opt);
        });
        this.lideresPopulados = true;
    }

    _estadoLabel(e) {
        const labels = {
            'BORRADOR': 'Borrador',
            'ENVIADO': 'Enviado',
            'EN_REVISION_COMPRAS': 'En revisión',
            'DEVUELTO_COMPRAS': 'Devuelto',
            'APROBADO_COMPRAS': 'Aprobado compras',
            'OBSERVADO_CONTABILIDAD': 'Observado',
            'APROBADO_CONTABILIDAD': 'Aprobado contab.',
            'CERRADO': 'Cerrado',
        };
        return labels[e] || e;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (typeof DASHBOARD_URL !== 'undefined') {
        new DashboardLideresManager();
    }
});
