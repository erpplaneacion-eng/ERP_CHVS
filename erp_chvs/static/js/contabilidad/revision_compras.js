// revision_compras.js — Revisión de Compras (por factura)

function horasLaboralesEntre(inicioISO, finISO) {
    if (!inicioISO || !finISO) return 0;
    const OFFSET_MS = 5 * 60 * 60 * 1000; // Colombia UTC-5
    const H_INI = 7, H_FIN = 15;
    function toLocal(iso) {
        const d = new Date(new Date(iso).getTime() - OFFSET_MS);
        return d;
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

class RevisionComprasManager {
    constructor() {
        this.saving = false;
        this.totalFacturas = 0;
        this.decididas = 0;
        this.init();
    }

    init() {
        this.cargarDetalle();
        this.cargarHistorial();
        this.mostrarSeccionSegunEstado();
        this.setupModales();
    }

    mostrarSeccionSegunEstado() {
        const secConfirmar = document.getElementById('seccion-confirmar');
        const secChecklist = document.getElementById('seccion-checklist');
        const secResponder = document.getElementById('seccion-responder-observacion');
        const bannerObs = document.getElementById('banner-observacion');

        if (secConfirmar) secConfirmar.style.display = REGISTRO_ESTADO === 'ENVIADO' ? '' : 'none';
        if (secChecklist) secChecklist.style.display = REGISTRO_ESTADO === 'EN_REVISION_COMPRAS' ? '' : 'none';
        if (secResponder) secResponder.style.display = REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD' ? '' : 'none';

        if (REGISTRO_ESTADO === 'EN_REVISION_COMPRAS') {
            this.cargarChecklist();
        }

        if (REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD') {
            if (bannerObs) bannerObs.style.display = 'flex';
            this.cargarUltimaObservacion();
        }
    }

    setupModales() {
        const btnConfirmar = document.getElementById('btn-confirmar-recepcion');
        const btnFinalizar = document.getElementById('btn-finalizar-revision');
        const btnResponder = document.getElementById('btn-responder-observacion');

        if (btnConfirmar) btnConfirmar.addEventListener('click', () => this.confirmarRecepcion());
        if (btnFinalizar) btnFinalizar.addEventListener('click', () => this.finalizarRevision());
        if (btnResponder) btnResponder.addEventListener('click', () => this.responderObservacion());

        // Modal devolución
        const modal = document.getElementById('devolucionModal');
        const closeBtn = document.getElementById('close-devolucion-modal');
        const cancelBtn = document.getElementById('cancel-devolucion-modal');
        const confirmarBtn = document.getElementById('btn-confirmar-devolucion');

        if (closeBtn) closeBtn.addEventListener('click', () => this.cerrarModalDevolucion());
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.cerrarModalDevolucion());
        if (confirmarBtn) confirmarBtn.addEventListener('click', () => this.confirmarDevolucionFactura());

        window.addEventListener('click', (e) => {
            if (e.target === modal) this.cerrarModalDevolucion();
        });
    }

    abrirModalDevolucion(facturaId, facturaNumero) {
        const modal = document.getElementById('devolucionModal');
        const textarea = document.getElementById('motivo-devolucion');
        if (textarea) textarea.value = '';
        // Guardar la factura actual en el modal
        modal.dataset.facturaId = facturaId;
        const titulo = modal.querySelector('h3');
        if (titulo) titulo.innerHTML = `<i class="fas fa-undo"></i> Devolver Factura ${facturaNumero}`;
        if (modal) modal.style.display = 'block';
    }

    cerrarModalDevolucion() {
        const modal = document.getElementById('devolucionModal');
        if (modal) { modal.style.display = 'none'; delete modal.dataset.facturaId; }
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

    async cargarUltimaObservacion() {
        try {
            const response = await fetch(HISTORIAL_URL);
            const data = await response.json();
            if (data.success) {
                const observaciones = data.data.filter(h => h.accion === 'OBSERVACION_CONTABILIDAD');
                if (observaciones.length) {
                    const ultima = observaciones[observaciones.length - 1];
                    const texto = document.getElementById('texto-observacion');
                    if (texto) texto.textContent = ultima.comentario;
                }
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
        }
    }

    renderFacturas(facturas, valorTotal) {
        const tbody = document.getElementById('facturas-tbody');
        const thead = document.querySelector('#facturasTable thead tr');
        if (!tbody) return;
        tbody.innerHTML = '';

        const esObservado = REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD';

        // Agregar columna de observación de Contabilidad si aplica
        if (esObservado && thead && !thead.querySelector('th[data-col="obs-conta"]')) {
            const th = document.createElement('th');
            th.dataset.col = 'obs-conta';
            th.textContent = 'Obs. Contabilidad';
            th.style.minWidth = '160px';
            thead.appendChild(th);
        }

        if (!facturas.length) {
            tbody.innerHTML = `<tr><td colspan="${esObservado ? 8 : 7}" class="text-center text-muted">Sin facturas.</td></tr>`;
        } else {
            const fragment = document.createDocumentFragment();
            facturas.forEach((f, idx) => {
                const tr = document.createElement('tr');
                const valor = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(f.valor);
                const fecha = f.fecha_factura ? new Date(f.fecha_factura + 'T00:00:00').toLocaleDateString('es-CO') : '—';

                let indicadorEmision = '<span class="text-muted" style="font-size:11px;">—</span>';
                if (f.fecha_factura && f.fecha_recepcion_lider) {
                    const facturaDate = new Date(f.fecha_factura + 'T00:00:00');
                    const recepcionDate = new Date(f.fecha_recepcion_lider + 'T00:00:00');
                    const diasRetraso = Math.max(0, Math.floor((recepcionDate - facturaDate) / 86400000));
                    const obs = f.observacion_retraso
                        ? `<br><small style="color:#6b7280;font-style:italic;">"${f.observacion_retraso}"</small>`
                        : '';
                    if (diasRetraso === 0) {
                        indicadorEmision = `<span style="font-size:11px;color:#16a34a;font-weight:600;" title="Días entre fecha de factura y recepción física">0d</span>`;
                    } else if (diasRetraso <= 2) {
                        indicadorEmision = `<span style="font-size:11px;color:#d97706;font-weight:600;" title="Días entre fecha de factura y recepción física">${diasRetraso}d ⚠️</span>${obs}`;
                    } else {
                        indicadorEmision = `<span style="font-size:11px;color:#dc2626;font-weight:700;" title="Días entre fecha de factura y recepción física">${diasRetraso}d 🔴</span>${obs}`;
                    }
                }

                let obsContaHtml = '';
                if (esObservado) {
                    if (f.estado_contabilidad === 'DEVUELTA' && f.comentario_devolucion_contabilidad) {
                        obsContaHtml = `<td>
                            <div style="padding:6px 8px;background:#fee2e2;border-left:3px solid #c0392b;border-radius:4px;font-size:12px;color:#7f1d1d;">
                                <i class="fas fa-exclamation-circle" style="color:#c0392b;"></i>
                                <em>${f.comentario_devolucion_contabilidad}</em>
                            </div>
                        </td>`;
                    } else if (f.estado_contabilidad === 'DEVUELTA') {
                        obsContaHtml = `<td><span class="badge-estado badge-devuelta" style="font-size:11px;"><i class="fas fa-undo-alt"></i> Devuelta</span></td>`;
                    } else {
                        obsContaHtml = `<td class="text-muted" style="font-size:12px;">—</td>`;
                    }
                }

                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td>${f.numero_factura}</td>
                    <td>${f.proveedor}</td>
                    <td>${f.concepto}</td>
                    <td>${valor}</td>
                    <td>${fecha}</td>
                    <td style="text-align:center;">${indicadorEmision}</td>
                    ${obsContaHtml}
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
            if (data.success) {
                this.renderChecklistPorFactura(data.data);
            }
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

        this.totalFacturas = facturas.length;
        this.decididas = facturas.filter(f => f.estado_compras !== 'PENDIENTE').length;
        this.actualizarBotonFinalizar();

        const fragment = document.createDocumentFragment();
        facturas.forEach(factura => {
            fragment.appendChild(this.crearBloqueFactura(factura));
        });
        container.appendChild(fragment);
    }

    crearBloqueFactura(factura) {
        const estado = factura.estado_compras;
        const badgeMap = {
            APROBADA: '<span class="checklist-badge-ok"><i class="fas fa-check"></i> Aprobada</span>',
            DEVUELTA:  '<span class="checklist-badge-pendientes"><i class="fas fa-undo"></i> Devuelta</span>',
            PENDIENTE: '<span class="checklist-badge-gris">Pendiente</span>',
        };
        const badge = badgeMap[estado] || '';

        const bloque = document.createElement('div');
        bloque.className = 'checklist-factura-bloque';
        bloque.dataset.facturaId = factura.factura_id;
        bloque.dataset.estadoCompras = estado;

        // Encabezado (acordeón) — todos colapsados por defecto
        const encabezado = document.createElement('div');
        encabezado.className = 'checklist-factura-header';
        encabezado.innerHTML = `
            <i class="fas fa-file-invoice"></i>
            <strong>${factura.numero_factura}</strong>
            <span class="text-muted" style="font-size:13px;">${factura.proveedor}</span>
            <span class="text-muted" style="font-size:12px;">${factura.concepto}</span>
            <span class="factura-estado-badge">${badge}</span>
            <i class="fas fa-chevron-down chevron"></i>
        `;
        encabezado.addEventListener('click', () => bloque.classList.toggle('abierto'));
        bloque.appendChild(encabezado);

        // Body
        const body = document.createElement('div');
        body.className = 'checklist-factura-body';

        // Banner si está devuelta
        if (estado === 'DEVUELTA' && factura.comentario_devolucion) {
            const banner = document.createElement('div');
            banner.className = 'banner-devolucion';
            banner.style.cssText = 'margin:12px 16px; border-radius:6px;';
            banner.innerHTML = `<i class="fas fa-exclamation-triangle"></i> <strong>Motivo:</strong> ${factura.comentario_devolucion}`;
            body.appendChild(banner);
        }

        // Tabla checklist
        const tabla = document.createElement('table');
        tabla.className = 'data-table checklist-table';
        tabla.innerHTML = `
            <thead>
                <tr>
                    <th style="width:36px;">#</th>
                    <th>Ítem</th>
                    <th style="width:90px;">Obligatorio</th>
                    <th style="width:140px;">Estado</th>
                    <th>Observación</th>
                </tr>
            </thead>
        `;
        const tbody = document.createElement('tbody');
        const editable = estado === 'PENDIENTE';

        if (!factura.verificaciones.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Sin ítems.</td></tr>';
        } else {
            const frag = document.createDocumentFragment();
            factura.verificaciones.forEach((v, i) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${i + 1}</td>
                    <td>
                        <strong>${v.item_nombre}</strong>
                        ${v.item_descripcion ? `<br><small class="text-muted">${v.item_descripcion}</small>` : ''}
                    </td>
                    <td>${v.item_obligatorio ? '<span class="badge" style="background:#fee2e2;color:#991b1b;">Sí</span>' : '<span class="badge badge-secondary">No</span>'}</td>
                    <td>
                        ${editable
                            ? `<select class="checklist-estado-select" data-id="${v.id}" style="padding:6px;border:1px solid #ddd;border-radius:4px;min-width:100px;">
                                <option value="PENDIENTE" ${v.estado === 'PENDIENTE' ? 'selected' : ''}>Pendiente</option>
                                <option value="OK" ${v.estado === 'OK' ? 'selected' : ''}>OK</option>
                                <option value="NO_OK" ${v.estado === 'NO_OK' ? 'selected' : ''}>No OK</option>
                                <option value="NA" ${v.estado === 'NA' ? 'selected' : ''}>N/A</option>
                               </select>`
                            : `<strong>${{OK:'OK',NO_OK:'No OK',NA:'N/A',PENDIENTE:'Pendiente'}[v.estado]||v.estado}</strong>`
                        }
                    </td>
                    <td>
                        ${editable
                            ? `<textarea class="checklist-obs-textarea" data-id="${v.id}" rows="2"
                                style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;font-size:13px;resize:vertical;"
                                placeholder="Observación opcional...">${v.observacion || ''}</textarea>`
                            : (v.observacion || '—')
                        }
                    </td>
                `;
                frag.appendChild(tr);
            });
            tbody.appendChild(frag);
        }

        tabla.appendChild(tbody);
        body.appendChild(tabla);

        // Botones por factura (solo si PENDIENTE)
        if (editable) {
            const acciones = document.createElement('div');
            acciones.style.cssText = 'display:flex; gap:10px; padding:12px 16px; background:#f8fafc; border-top:1px solid #e2e8f0;';
            acciones.innerHTML = `
                <button class="btn btn-sm btn-success btn-aprobar-factura" data-factura-id="${factura.factura_id}">
                    <i class="fas fa-check"></i> Aprobar Factura
                </button>
                <button class="btn btn-sm btn-danger btn-devolver-factura" data-factura-id="${factura.factura_id}" data-numero="${factura.numero_factura}">
                    <i class="fas fa-undo"></i> Devolver Factura
                </button>
            `;
            // Eventos
            acciones.querySelector('.btn-aprobar-factura').addEventListener('click', () => {
                this.aprobarFactura(factura.factura_id, bloque);
            });
            acciones.querySelector('.btn-devolver-factura').addEventListener('click', () => {
                this.abrirModalDevolucion(factura.factura_id, factura.numero_factura);
            });
            body.appendChild(acciones);
        }

        bloque.appendChild(body);
        return bloque;
    }

    async guardarChecklistFactura(facturaId) {
        const bloque = document.querySelector(`.checklist-factura-bloque[data-factura-id="${facturaId}"]`);
        if (!bloque) return;

        const selects = bloque.querySelectorAll('.checklist-estado-select');
        const items = [];
        selects.forEach(sel => {
            const id = sel.dataset.id;
            const obs = bloque.querySelector(`.checklist-obs-textarea[data-id="${id}"]`);
            items.push({
                verificacion_id: parseInt(id),
                estado: sel.value,
                observacion: obs ? obs.value.trim() : '',
            });
        });

        if (!items.length) return;

        await fetch(GUARDAR_CHECKLIST_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify({ items }),
        });
    }

    async aprobarFactura(facturaId, bloque) {
        if (this.saving) return;
        this.saving = true;

        // Primero guardar el checklist de esta factura
        await this.guardarChecklistFactura(facturaId);

        try {
            const response = await fetch(`/contabilidad/api/facturas/${facturaId}/aprobar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (data.success) {
                this.marcarFacturaDecidida(bloque, 'APROBADA');
                this.mostrarAlerta('Factura aprobada.', 'success');
            } else {
                this.mostrarAlerta(data.error || 'Error al aprobar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
        }
    }

    async confirmarDevolucionFactura() {
        const modal = document.getElementById('devolucionModal');
        const facturaId = modal?.dataset?.facturaId;
        const motivo = document.getElementById('motivo-devolucion')?.value?.trim();

        if (!motivo) {
            this.mostrarAlerta('El motivo es obligatorio.', 'warning');
            return;
        }
        if (!facturaId) return;

        this.cerrarModalDevolucion();

        // Primero guardar el checklist de esta factura
        await this.guardarChecklistFactura(facturaId);

        try {
            const response = await fetch(`/contabilidad/api/facturas/${facturaId}/devolver/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ comentario: motivo }),
            });
            const data = await response.json();
            if (data.success) {
                const bloque = document.querySelector(`.checklist-factura-bloque[data-factura-id="${facturaId}"]`);
                if (bloque) this.marcarFacturaDecidida(bloque, 'DEVUELTA', motivo);
                this.mostrarAlerta('Factura devuelta al líder.', 'success');
            } else {
                this.mostrarAlerta(data.error || 'Error al devolver.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    marcarFacturaDecidida(bloque, nuevoEstado, motivo) {
        bloque.classList.remove('abierto');
        bloque.dataset.estadoCompras = nuevoEstado;

        // Actualizar badge en el encabezado
        const badgeEl = bloque.querySelector('.factura-estado-badge');
        if (badgeEl) {
            badgeEl.innerHTML = nuevoEstado === 'APROBADA'
                ? '<span class="checklist-badge-ok"><i class="fas fa-check"></i> Aprobada</span>'
                : '<span class="checklist-badge-pendientes"><i class="fas fa-undo"></i> Devuelta</span>';
        }

        // Deshabilitar selects y textareas
        bloque.querySelectorAll('.checklist-estado-select, .checklist-obs-textarea').forEach(el => {
            el.disabled = true;
        });

        // Ocultar botones de acción
        const acciones = bloque.querySelector('.btn-aprobar-factura')?.closest('div');
        if (acciones) acciones.style.display = 'none';

        // Actualizar contador y botón finalizar
        this.decididas++;
        this.actualizarBotonFinalizar();
    }

    actualizarBotonFinalizar() {
        const btn = document.getElementById('btn-finalizar-revision');
        const label = document.getElementById('label-pendientes');
        const pendientes = this.totalFacturas - this.decididas;

        if (btn) btn.disabled = pendientes > 0;
        if (label) {
            label.textContent = pendientes > 0
                ? `${pendientes} factura${pendientes > 1 ? 's' : ''} sin decidir`
                : 'Todas las facturas decididas — puedes finalizar';
        }
    }

    async finalizarRevision() {
        const horas = horasLaboralesEntre(
            typeof FECHA_INICIO_COMPRAS !== 'undefined' ? FECHA_INICIO_COMPRAS : null,
            new Date().toISOString()
        );
        const superaLimite = horas > 5;

        const swalConfig = {
            title: '¿Finalizar revisión?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, finalizar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#0d9488',
        };

        if (superaLimite) {
            swalConfig.html = `Las facturas aprobadas pasarán a Contabilidad. Las devueltas regresarán al líder.<br><br>
                <strong>&#9888;&#65039; Asegúrese de haber cargado la información de forma correcta en SIESA antes de continuar.</strong><br><br>
                <strong style="color:#c0392b;">&#9888;&#65039; Ha superado las 5 horas laborales (${horas}h transcurridas).<br>
                Debe justificar el motivo de la demora.</strong>`;
            swalConfig.input = 'textarea';
            swalConfig.inputPlaceholder = 'Explique el motivo de la demora...';
            swalConfig.inputValidator = (v) => { if (!v || !v.trim()) return 'La justificación es obligatoria.'; };
        } else {
            swalConfig.html = `Las facturas aprobadas pasarán a Contabilidad. Las devueltas regresarán al líder.<br><br>
                <strong>&#9888;&#65039; Asegúrese de haber cargado la información de forma correcta en SIESA antes de continuar.</strong>`;
        }

        const result = await Swal.fire(swalConfig);
        if (!result.isConfirmed) return;

        const justificacion_demora = superaLimite ? result.value : '';

        try {
            const response = await fetch(FINALIZAR_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ justificacion_demora }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Revisión finalizada.', 'success');
                setTimeout(() => window.location.href = '/contabilidad/bandeja-compras/', 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al finalizar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    async confirmarRecepcion() {
        if (this.saving) return;
        this.saving = true;
        const btn = document.getElementById('btn-confirmar-recepcion');
        if (btn) { btn.disabled = true; btn.textContent = 'Confirmando...'; }
        try {
            const response = await fetch(CONFIRMAR_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Recepción confirmada. Iniciando revisión.', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al confirmar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-check-circle"></i> Confirmar Recepción'; }
        }
    }

    async responderObservacion() {
        const respuesta = document.getElementById('respuesta-observacion')?.value?.trim();
        if (!respuesta) { this.mostrarAlerta('La respuesta es obligatoria.', 'warning'); return; }
        try {
            const response = await fetch(RESPONDER_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                body: JSON.stringify({ comentario: respuesta }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Respuesta enviada. Registro re-aprobado.', 'success');
                setTimeout(() => window.location.href = '/contabilidad/bandeja-compras/', 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al responder.', 'error');
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
        if (!historial.length) { container.innerHTML = '<p class="text-muted">Sin historial.</p>'; return; }
        const fragment = document.createDocumentFragment();
        historial.forEach(h => {
            const item = document.createElement('div');
            item.className = 'historial-item';
            const fecha = h.fecha ? new Date(h.fecha).toLocaleString('es-CO') : '—';
            item.innerHTML = `
                <div class="historial-fecha">${fecha}</div>
                <div class="historial-usuario"><strong>${h.usuario}</strong></div>
                <div class="historial-accion">${h.accion_display}</div>
                ${h.comentario ? `<div class="historial-comentario">${h.comentario.replace(/\n/g, '<br>')}</div>` : ''}
            `;
            fragment.appendChild(item);
        });
        container.innerHTML = '';
        container.appendChild(fragment);
    }

    mostrarAlerta(mensaje, tipo) {
        const colores = { success: '#27ae60', error: '#e74c3c', warning: '#f39c12', info: '#3498db' };
        const alerta = document.createElement('div');
        alerta.style.cssText = `position:fixed;top:20px;right:20px;z-index:10000;padding:15px 20px;border-radius:5px;color:white;font-weight:500;min-width:300px;box-shadow:0 4px 6px rgba(0,0,0,.1);display:flex;align-items:center;gap:10px;background-color:${colores[tipo]||colores.info};`;
        const closeBtn = document.createElement('button');
        closeBtn.style.cssText = 'background:none;border:none;color:white;font-size:18px;cursor:pointer;margin-left:auto;';
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => alerta.remove());
        alerta.appendChild(document.createTextNode(mensaje));
        alerta.appendChild(closeBtn);
        document.body.appendChild(alerta);
        setTimeout(() => { if (alerta.parentElement) alerta.remove(); }, 5000);
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie) {
            for (const cookie of document.cookie.split(';')) {
                const c = cookie.trim();
                if (c.startsWith(name + '=')) { cookieValue = decodeURIComponent(c.substring(name.length + 1)); break; }
            }
        }
        return cookieValue;
    }
}

let revisionComprasManager;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof REGISTRO_ID !== 'undefined') {
        revisionComprasManager = new RevisionComprasManager();
    }
});
