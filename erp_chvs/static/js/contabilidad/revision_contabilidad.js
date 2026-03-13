// revision_contabilidad.js — Revisión de Contabilidad

class RevisionContabilidadManager {
    constructor() {
        this.saving = false;
        this.init();
    }

    init() {
        this.cargarDetalle();
        this.cargarChecklist();
        this.cargarHistorial();
        this.setupBotones();
    }

    setupBotones() {
        const btnObservar = document.getElementById('btn-observar');
        const btnAprobar = document.getElementById('btn-aprobar-cerrar');

        if (btnObservar) btnObservar.addEventListener('click', () => this.observar());
        if (btnAprobar) btnAprobar.addEventListener('click', () => this.aprobarYCerrar());
    }

    async cargarDetalle() {
        try {
            const response = await fetch(DETALLE_URL);
            const data = await response.json();
            if (data.success) {
                this.renderFacturas(data.data.facturas, data.data.valor_total);
            }
        } catch (error) {
            console.error('Error al cargar detalle:', error);
        }
    }

    renderFacturas(facturas, valorTotal) {
        const tbody = document.getElementById('facturas-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!facturas.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin facturas.</td></tr>';
        } else {
            const fragment = document.createDocumentFragment();
            facturas.forEach((f, idx) => {
                const tr = document.createElement('tr');
                const valor = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(f.valor);
                const fecha = f.fecha_factura ? new Date(f.fecha_factura + 'T00:00:00').toLocaleDateString('es-CO') : '—';
                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td>${f.numero_factura}</td>
                    <td>${f.proveedor}</td>
                    <td>${f.concepto}</td>
                    <td>${valor}</td>
                    <td>${fecha}</td>
                `;
                fragment.appendChild(tr);
            });
            tbody.appendChild(fragment);
        }

        const totalEl = document.getElementById('valor-total');
        if (totalEl) {
            totalEl.textContent = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(valorTotal);
        }
    }

    async cargarChecklist() {
        try {
            const response = await fetch(CHECKLIST_URL);
            const data = await response.json();
            if (data.success) this.renderChecklistPorFactura(data.data);
        } catch (error) {
            console.error('Error al cargar checklist:', error);
        }
    }

    renderChecklistPorFactura(facturas) {
        const container = document.getElementById('checklist-facturas-container');
        if (!container) return;
        container.innerHTML = '';

        if (!facturas.length) {
            container.innerHTML = '<p class="text-center text-muted">Sin facturas con checklist.</p>';
            return;
        }

        const coloresEstado = { OK: '#d1fae5', NO_OK: '#fee2e2', NA: '#f3f4f6', PENDIENTE: '#fef3c7' };
        const etiquetasEstado = { OK: 'OK', NO_OK: 'No OK', NA: 'N/A', PENDIENTE: 'Pendiente' };

        const fragment = document.createDocumentFragment();
        facturas.forEach((factura, idx) => {
            const pendientes = factura.verificaciones.filter(v => v.estado === 'PENDIENTE').length;
            const todos_ok = factura.verificaciones.length > 0 && pendientes === 0;
            const badge = pendientes > 0
                ? `<span class="checklist-badge-pendientes">${pendientes} pendiente${pendientes > 1 ? 's' : ''}</span>`
                : (todos_ok ? '<span class="checklist-badge-ok">Completo</span>' : '');

            const bloque = document.createElement('div');
            bloque.className = `checklist-factura-bloque${idx === 0 ? ' abierto' : ''}`;

            const encabezado = document.createElement('div');
            encabezado.className = 'checklist-factura-header';
            encabezado.innerHTML = `
                <i class="fas fa-file-invoice"></i>
                <strong>${factura.numero_factura}</strong>
                <span class="text-muted" style="font-size:13px;">${factura.proveedor}</span>
                <span class="text-muted" style="font-size:12px;">${factura.concepto}</span>
                ${badge}
                <i class="fas fa-chevron-down chevron"></i>
            `;
            encabezado.addEventListener('click', () => bloque.classList.toggle('abierto'));
            bloque.appendChild(encabezado);

            const body = document.createElement('div');
            body.className = 'checklist-factura-body';

            const tabla = document.createElement('table');
            tabla.className = 'data-table checklist-table';
            tabla.innerHTML = `
                <thead>
                    <tr>
                        <th style="width:36px;">#</th>
                        <th>Ítem</th>
                        <th style="width:90px;">Obligatorio</th>
                        <th style="width:100px;">Estado</th>
                        <th>Observación</th>
                        <th style="width:130px;">Verificado Por</th>
                    </tr>
                </thead>
            `;
            const tbody = document.createElement('tbody');

            if (!factura.verificaciones.length) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Sin ítems.</td></tr>';
            } else {
                const frag = document.createDocumentFragment();
                factura.verificaciones.forEach((v, i) => {
                    const tr = document.createElement('tr');
                    tr.style.background = coloresEstado[v.estado] || '';
                    tr.innerHTML = `
                        <td>${i + 1}</td>
                        <td><strong>${v.item_nombre}</strong>${v.item_descripcion ? '<br><small class="text-muted">' + v.item_descripcion + '</small>' : ''}</td>
                        <td>${v.item_obligatorio ? 'Sí' : 'No'}</td>
                        <td><strong>${etiquetasEstado[v.estado] || v.estado}</strong></td>
                        <td>${v.observacion || '—'}</td>
                        <td>${v.verificado_por || '—'}</td>
                    `;
                    frag.appendChild(tr);
                });
                tbody.appendChild(frag);
            }

            tabla.appendChild(tbody);
            body.appendChild(tabla);
            bloque.appendChild(body);
            fragment.appendChild(bloque);
        });
        container.appendChild(fragment);
    }

    async observar() {
        const comentario = document.getElementById('comentario-contabilidad')?.value?.trim();
        if (!comentario) {
            this.mostrarAlerta('El comentario es obligatorio para observar el registro.', 'warning');
            return;
        }

        const confirmado = await Swal.fire({
            title: '¿Enviar observación a Compras?',
            text: 'Compras deberá responder antes de que el registro pueda ser cerrado.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, observar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#ca8a04',
        });

        if (!confirmado.isConfirmed) return;

        try {
            const response = await fetch(OBSERVAR_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ comentario }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Observación enviada a Compras.', 'success');
                setTimeout(() => window.location.href = '/contabilidad/bandeja-contabilidad/', 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al observar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    async aprobarYCerrar() {
        const comentario = document.getElementById('comentario-contabilidad')?.value?.trim() || '';

        const confirmado = await Swal.fire({
            title: '¿Aprobar y cerrar el registro?',
            text: 'Esta acción es definitiva. El registro quedará cerrado.',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, aprobar y cerrar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#16a34a',
        });

        if (!confirmado.isConfirmed) return;

        try {
            const response = await fetch(APROBAR_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ comentario }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Registro aprobado y cerrado exitosamente.', 'success');
                setTimeout(() => window.location.href = '/contabilidad/bandeja-contabilidad/', 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al aprobar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    async cargarHistorial() {
        try {
            const response = await fetch(HISTORIAL_URL);
            const data = await response.json();
            if (data.success) this.renderHistorial(data.data);
        } catch (error) {
            console.error('Error al cargar historial:', error);
        }
    }

    renderHistorial(historial) {
        const container = document.getElementById('historial-container');
        if (!container) return;
        if (!historial.length) {
            container.innerHTML = '<p class="text-muted">Sin historial.</p>';
            return;
        }
        const fragment = document.createDocumentFragment();
        historial.forEach(h => {
            const item = document.createElement('div');
            item.className = 'historial-item';
            const fecha = h.fecha ? new Date(h.fecha).toLocaleString('es-CO') : '—';
            item.innerHTML = `
                <div class="historial-fecha">${fecha}</div>
                <div class="historial-usuario"><strong>${h.usuario}</strong></div>
                <div class="historial-accion">${h.accion_display}</div>
                ${h.comentario ? `<div class="historial-comentario">${h.comentario}</div>` : ''}
            `;
            fragment.appendChild(item);
        });
        container.innerHTML = '';
        container.appendChild(fragment);
    }

    mostrarAlerta(mensaje, tipo) {
        const colores = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const alerta = document.createElement('div');
        alerta.style.cssText = `
            position:fixed; top:20px; right:20px; z-index:10000;
            padding:15px 20px; border-radius:5px; color:white; font-weight:500;
            min-width:300px; box-shadow:0 4px 6px rgba(0,0,0,.1);
            display:flex; align-items:center; gap:10px;
            background-color:${colores[tipo] || colores.info};
            animation: slideInRight 0.3s ease;
        `;
        alerta.innerHTML = `<span>${mensaje}</span><button style="background:none;border:none;color:white;font-size:18px;cursor:pointer;margin-left:auto;" onclick="this.parentElement.remove()">×</button>`;
        document.body.appendChild(alerta);
        setTimeout(() => { if (alerta.parentElement) alerta.remove(); }, 5000);
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

let revisionContabilidadManager;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof REGISTRO_ID !== 'undefined') {
        revisionContabilidadManager = new RevisionContabilidadManager();
    }
});
