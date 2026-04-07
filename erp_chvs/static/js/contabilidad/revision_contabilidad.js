// revision_contabilidad.js — Revisión de Contabilidad (con decisión por factura)

function horasLaboralesEntre(inicioISO, finISO) {
    if (!inicioISO || !finISO) return 0;
    const OFFSET_MS = 5 * 60 * 60 * 1000; // Colombia UTC-5
    const H_INI = 7, H_FIN = 15;
    function toLocal(iso) {
        return new Date(new Date(iso).getTime() - OFFSET_MS);
    }
    const inicio = toLocal(inicioISO);
    const fin = toLocal(finISO);
    if (fin <= inicio) return 0;
    let total = 0;
    let cur = new Date(Date.UTC(inicio.getUTCFullYear(), inicio.getUTCMonth(), inicio.getUTCDate(), inicio.getUTCHours(), inicio.getUTCMinutes(), inicio.getUTCSeconds()));
    const finLocal = new Date(Date.UTC(fin.getUTCFullYear(), fin.getUTCMonth(), fin.getUTCDate(), fin.getUTCHours(), fin.getUTCMinutes(), fin.getUTCSeconds()));
    while (cur < finLocal) {
        const dow = cur.getUTCDay();
        if (dow === 0 || dow === 6) {
            const add = dow === 0 ? 1 : 2;
            cur = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth(), cur.getUTCDate() + add, H_INI, 0, 0));
            continue;
        }
        const iniHoy = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth(), cur.getUTCDate(), H_INI, 0, 0));
        const finHoy = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth(), cur.getUTCDate(), H_FIN, 0, 0));
        if (cur < iniHoy) cur = iniHoy;
        if (cur >= finHoy) {
            cur = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth(), cur.getUTCDate() + 1, H_INI, 0, 0));
            continue;
        }
        const finEf = new Date(Math.min(finHoy.getTime(), finLocal.getTime()));
        total += (finEf - cur) / 3600000;
        cur = new Date(Date.UTC(cur.getUTCFullYear(), cur.getUTCMonth(), cur.getUTCDate() + 1, H_INI, 0, 0));
    }
    return Math.round(total * 10) / 10;
}

class RevisionContabilidadManager {
    constructor() {
        this.saving = false;
        this.facturasPendienteDev = null; // id de factura que está siendo devuelta
        this.init();
    }

    init() {
        this.cargarDetalle();
        this.cargarChecklist();
        this.cargarHistorial();
        this.setupBotones();
        this.setupModal();
    }

    setupBotones() {
        const btnFinalizar = document.getElementById('btn-finalizar-revision');
        if (btnFinalizar) btnFinalizar.addEventListener('click', () => this.finalizarRevision());
    }

    setupModal() {
        const modal = document.getElementById('modal-devolver-contabilidad');
        if (!modal) return;

        document.getElementById('btn-cerrar-modal-devolver-cont')
            ?.addEventListener('click', () => this.cerrarModalDevolver());
        document.getElementById('btn-cancelar-devolver-cont')
            ?.addEventListener('click', () => this.cerrarModalDevolver());
        document.getElementById('btn-confirmar-devolver-cont')
            ?.addEventListener('click', () => this.confirmarDevolucion());

        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.cerrarModalDevolver();
        });
    }

    // ------------------------------------------------------------------ //
    // Carga de datos                                                       //
    // ------------------------------------------------------------------ //

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

    async cargarChecklist() {
        try {
            const response = await fetch(CHECKLIST_URL);
            const data = await response.json();
            if (data.success) this.renderChecklistPorFactura(data.data);
        } catch (error) {
            console.error('Error al cargar checklist:', error);
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

    // ------------------------------------------------------------------ //
    // Render facturas                                                      //
    // ------------------------------------------------------------------ //

    renderFacturas(facturas, valorTotal) {
        const tbody = document.getElementById('facturas-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        const puedeActuar = REGISTRO_ESTADO === 'APROBADO_COMPRAS';

        if (!facturas.length) {
            tbody.innerHTML = `<tr><td colspan="${puedeActuar ? 7 : 6}" class="text-center text-muted">Sin facturas.</td></tr>`;
        } else {
            const fragment = document.createDocumentFragment();
            let decididas = 0;

            facturas.forEach((f, idx) => {
                const tr = document.createElement('tr');
                const valor = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(f.valor);
                const fecha = f.fecha_factura ? new Date(f.fecha_factura + 'T00:00:00').toLocaleDateString('es-CO') : '—';

                let accionHtml = '';
                if (puedeActuar) {
                    const est = f.estado_contabilidad;
                    if (est === 'APROBADA') {
                        decididas++;
                        accionHtml = `<span class="badge-estado badge-aprobada"><i class="fas fa-check"></i> Aprobada</span>`;
                    } else if (est === 'DEVUELTA') {
                        decididas++;
                        const motivoCont = f.comentario_devolucion_contabilidad
                            ? `<div style="margin-top:6px;padding:6px 8px;background:#fee2e2;border-left:3px solid #c0392b;border-radius:4px;font-size:12px;color:#7f1d1d;text-align:left;max-width:220px;">
                                   <i class="fas fa-exclamation-circle" style="color:#c0392b;"></i>
                                   <em>${f.comentario_devolucion_contabilidad}</em>
                               </div>`
                            : '';
                        accionHtml = `
                            <div>
                                <span class="badge-estado badge-devuelta">
                                    <i class="fas fa-undo-alt"></i> Devuelta a Compras
                                </span>
                                ${motivoCont}
                            </div>`;
                    } else {
                        accionHtml = `
                            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                                <button class="btn btn-sm btn-success btn-aprobar-cont" data-id="${f.id}" data-numero="${f.numero_factura}" title="Aprobar factura">
                                    <i class="fas fa-check"></i>
                                </button>
                                <button class="btn btn-sm btn-danger btn-devolver-cont" data-id="${f.id}" data-numero="${f.numero_factura}" title="Devolver a Compras">
                                    <i class="fas fa-undo-alt"></i>
                                </button>
                            </div>`;
                    }

                }

                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td>${f.numero_factura}</td>
                    <td>${f.proveedor}</td>
                    <td>${f.concepto}</td>
                    <td>${valor}</td>
                    <td>${fecha}</td>
                    ${puedeActuar ? `<td style="text-align:center;">${accionHtml}</td>` : ''}
                `;
                fragment.appendChild(tr);
            });
            tbody.appendChild(fragment);

            if (puedeActuar) {
                this._actualizarContador(decididas, facturas.length);

                tbody.querySelectorAll('.btn-aprobar-cont').forEach(btn => {
                    btn.addEventListener('click', () => this.aprobarFactura(
                        parseInt(btn.dataset.id), btn.dataset.numero
                    ));
                });
                tbody.querySelectorAll('.btn-devolver-cont').forEach(btn => {
                    btn.addEventListener('click', () => this.abrirModalDevolver(
                        parseInt(btn.dataset.id), btn.dataset.numero
                    ));
                });
            }
        }

        const totalEl = document.getElementById('valor-total');
        if (totalEl) {
            totalEl.textContent = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(valorTotal);
        }
    }

    _actualizarContador(decididas, total) {
        const el = document.getElementById('contador-facturas');
        if (!el) return;
        const pendientes = total - decididas;
        if (pendientes === 0) {
            el.innerHTML = `<span style="color:#16a34a;"><i class="fas fa-check-circle"></i> Todas decididas (${total}/${total})</span>`;
        } else {
            el.innerHTML = `${decididas}/${total} decididas — <span style="color:#dc2626;">${pendientes} pendiente${pendientes > 1 ? 's' : ''}</span>`;
        }
    }

    // ------------------------------------------------------------------ //
    // Aprobar factura individual                                           //
    // ------------------------------------------------------------------ //

    async aprobarFactura(facturaId, numeroFactura) {
        if (this.saving) return;
        const result = await Swal.fire({
            title: '¿Aprobar factura?',
            text: `Factura ${numeroFactura} — quedará marcada como aprobada por Contabilidad.`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, aprobar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#16a34a',
        });
        if (!result.isConfirmed) return;

        this.saving = true;
        try {
            const response = await fetch(`${APROBAR_FACTURA_CONT_BASE}${facturaId}/aprobar-contabilidad/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (data.success) {
                await this.cargarDetalle();
            } else {
                this.mostrarAlerta(data.error || 'Error al aprobar.', 'error');
            }
        } catch {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
        }
    }

    // ------------------------------------------------------------------ //
    // Devolver factura individual                                          //
    // ------------------------------------------------------------------ //

    abrirModalDevolver(facturaId, numeroFactura) {
        this.facturasPendienteDev = facturaId;
        const modal = document.getElementById('modal-devolver-contabilidad');
        const desc = document.getElementById('modal-devolver-cont-desc');
        const motivo = document.getElementById('motivo-devolucion-contabilidad');
        if (desc) desc.textContent = `Factura: ${numeroFactura}`;
        if (motivo) motivo.value = '';
        if (modal) modal.style.display = 'flex';
    }

    cerrarModalDevolver() {
        const modal = document.getElementById('modal-devolver-contabilidad');
        if (modal) modal.style.display = 'none';
        this.facturasPendienteDev = null;
    }

    async confirmarDevolucion() {
        const motivo = document.getElementById('motivo-devolucion-contabilidad')?.value?.trim();
        if (!motivo) {
            this.mostrarAlerta('El motivo de devolución es obligatorio.', 'warning');
            return;
        }
        if (this.saving || !this.facturasPendienteDev) return;

        this.saving = true;
        try {
            const response = await fetch(`${DEVOLVER_FACTURA_CONT_BASE}${this.facturasPendienteDev}/devolver-contabilidad/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                body: JSON.stringify({ comentario: motivo }),
            });
            const data = await response.json();
            if (data.success) {
                this.cerrarModalDevolver();
                await this.cargarDetalle();
            } else {
                this.mostrarAlerta(data.error || 'Error al devolver.', 'error');
            }
        } catch {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
        }
    }

    // ------------------------------------------------------------------ //
    // Finalizar revisión (con posible split)                              //
    // ------------------------------------------------------------------ //

    async finalizarRevision() {
        if (this.saving) return;

        const horas = horasLaboralesEntre(
            typeof FECHA_APROBACION_COMPRAS !== 'undefined' ? FECHA_APROBACION_COMPRAS : null,
            new Date().toISOString()
        );
        const superaLimite = horas > 5;

        const swalConfig = {
            title: '¿Finalizar revisión de Contabilidad?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, finalizar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#16a34a',
        };

        if (superaLimite) {
            swalConfig.html = `Las facturas aprobadas se cerrarán y las devueltas regresarán a Compras.<br><br>
                <strong style="color:#c0392b;">&#9888; Ha superado las 5 horas laborales (${horas}h transcurridas).<br>
                Debe justificar el motivo de la demora.</strong>`;
            swalConfig.input = 'textarea';
            swalConfig.inputPlaceholder = 'Explique el motivo de la demora...';
            swalConfig.inputValidator = (v) => { if (!v || !v.trim()) return 'La justificación es obligatoria.'; };
        } else {
            swalConfig.text = 'Las facturas aprobadas se cerrarán. Las devueltas regresarán a Compras para corrección.';
        }

        const result = await Swal.fire(swalConfig);
        if (!result.isConfirmed) return;

        const justificacion_demora = superaLimite ? result.value : '';
        this.saving = true;

        try {
            const response = await fetch(FINALIZAR_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                body: JSON.stringify({ justificacion_demora }),
            });
            const data = await response.json();
            if (data.success) {
                let msg = 'Revisión finalizada correctamente.';
                if (data.nuevo_registro_id) {
                    msg = `Revisión finalizada. Facturas aprobadas trasladadas al RC-${data.nuevo_registro_id} y cerradas. Las devueltas regresan a Compras.`;
                } else if (data.estado === 'CERRADO') {
                    msg = 'Todas las facturas aprobadas. Registro cerrado exitosamente.';
                } else if (data.estado === 'OBSERVADO_CONTABILIDAD') {
                    msg = 'Todas las facturas devueltas a Compras para corrección.';
                }
                await Swal.fire({ title: 'Listo', text: msg, icon: 'success', confirmButtonColor: '#16a34a' });
                window.location.href = '/contabilidad/bandeja-contabilidad/';
            } else {
                this.mostrarAlerta(data.error || 'Error al finalizar.', 'error');
            }
        } catch {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
        }
    }

    // ------------------------------------------------------------------ //
    // Checklist (solo lectura)                                            //
    // ------------------------------------------------------------------ //

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
        facturas.forEach((factura) => {
            const pendientes = factura.verificaciones.filter(v => v.estado === 'PENDIENTE').length;
            const todos_ok = factura.verificaciones.length > 0 && pendientes === 0;
            const badge = pendientes > 0
                ? `<span class="checklist-badge-pendientes">${pendientes} pendiente${pendientes > 1 ? 's' : ''}</span>`
                : (todos_ok ? '<span class="checklist-badge-ok">Completo</span>' : '');

            const bloque = document.createElement('div');
            bloque.className = 'checklist-factura-bloque';

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

    // ------------------------------------------------------------------ //
    // Historial                                                            //
    // ------------------------------------------------------------------ //

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

    // ------------------------------------------------------------------ //
    // Utilidades                                                           //
    // ------------------------------------------------------------------ //

    mostrarAlerta(mensaje, tipo) {
        const colores = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const alerta = document.createElement('div');
        alerta.style.cssText = `
            position:fixed; top:20px; right:20px; z-index:10000;
            padding:15px 20px; border-radius:5px; color:white; font-weight:500;
            min-width:300px; box-shadow:0 4px 6px rgba(0,0,0,.1);
            display:flex; align-items:center; gap:10px;
            background-color:${colores[tipo] || colores.info};
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
