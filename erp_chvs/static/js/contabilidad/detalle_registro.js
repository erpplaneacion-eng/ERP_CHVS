// detalle_registro.js — Detalle de registro contable del líder

function horasLaboralesEntre(inicioISO, finISO) {
    if (!inicioISO || !finISO) return 0;
    const OFFSET_MS = 5 * 60 * 60 * 1000; // Colombia UTC-5
    const H_INI = 7, H_FIN = 15;
    // Convertir a "hora local Colombia" usando UTC corrido
    function toLocal(iso) {
        const d = new Date(new Date(iso).getTime() - OFFSET_MS);
        return d; // ahora getUTCHours() devuelve hora Colombia
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

class DetalleRegistroManager {
    constructor() {
        this.saving = false;
        this.deleteFacturaId = null;
        this.estadosEditables = ['BORRADOR', 'DEVUELTO_COMPRAS'];
        this.init();
    }

    init() {
        this.cargarDetalle();
        this.cargarHistorial();
        this.setupModal();
        this.setupEliminarModal();
        this.configurarBotones();
        this.setupExcelUpload();
    }

    setupModal() {
        const btnAgregar = document.getElementById('btn-agregar-factura');
        const modal = document.getElementById('facturaModal');
        const closeBtn = document.getElementById('close-factura-modal');
        const cancelBtn = document.getElementById('cancel-factura-modal');
        const guardarBtn = document.getElementById('btn-guardar-factura');

        if (btnAgregar) btnAgregar.addEventListener('click', () => this.abrirModalFactura());
        if (closeBtn) closeBtn.addEventListener('click', () => this.cerrarModal('facturaModal'));
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.cerrarModal('facturaModal'));
        if (guardarBtn) guardarBtn.addEventListener('click', () => this.guardarFactura());

        // Mostrar/ocultar campo de observación según retraso entre fecha factura y hoy
        const inputFecha = document.getElementById('factura-fecha');
        if (inputFecha) {
            inputFecha.addEventListener('change', function () {
                const grupo = document.getElementById('grupo-observacion-retraso');
                if (!grupo) return;
                if (!this.value) { grupo.style.display = 'none'; return; }
                const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
                const emision = new Date(this.value + 'T00:00:00');
                const dias = Math.floor((hoy - emision) / 86400000);
                grupo.style.display = dias > 0 ? '' : 'none';
            });
        }

        window.addEventListener('click', (e) => {
            const m = document.getElementById('facturaModal');
            const me = document.getElementById('eliminarFacturaModal');
            if (e.target === m) this.cerrarModal('facturaModal');
            if (e.target === me) this.cerrarModal('eliminarFacturaModal');
        });
    }

    setupEliminarModal() {
        const cancelBtn = document.getElementById('cancel-eliminar-modal');
        const closeBtn = document.getElementById('close-eliminar-modal');
        const confirmarBtn = document.getElementById('btn-confirmar-eliminar');

        if (cancelBtn) cancelBtn.addEventListener('click', () => this.cerrarModal('eliminarFacturaModal'));
        if (closeBtn) closeBtn.addEventListener('click', () => this.cerrarModal('eliminarFacturaModal'));
        if (confirmarBtn) confirmarBtn.addEventListener('click', () => this.eliminarFactura());
    }

    configurarBotones() {
        const esEditable = this.estadosEditables.includes(REGISTRO_ESTADO);

        // Botón agregar factura
        const wrapAgregar = document.getElementById('btn-agregar-factura-wrap');
        if (wrapAgregar) wrapAgregar.style.display = esEditable ? '' : 'none';

        // Botón cargar Excel (solo MATERIAS_PRIMAS)
        const wrapExcel = document.getElementById('btn-cargar-excel-wrap');
        if (wrapExcel) wrapExcel.style.display = esEditable ? '' : 'none';

        // Botón enviar: BORRADOR siempre, DEVUELTO_COMPRAS solo para SERVICIOS
        const puedeEnviar = REGISTRO_ESTADO === 'BORRADOR' ||
            (REGISTRO_ESTADO === 'DEVUELTO_COMPRAS' && REGISTRO_TIPO === 'SERVICIOS');
        const seccionEnviar = document.getElementById('seccion-enviar');
        if (seccionEnviar) seccionEnviar.style.display = puedeEnviar ? '' : 'none';

        const btnEnviar = document.getElementById('btn-enviar');
        if (btnEnviar) btnEnviar.addEventListener('click', () => this.enviar());

        // Sección de respuesta a Contabilidad: solo MATERIAS_PRIMAS en OBSERVADO_CONTABILIDAD
        const seccionResponder = document.getElementById('seccion-responder-conta');
        if (seccionResponder) {
            const visible = REGISTRO_TIPO === 'MATERIAS_PRIMAS' && REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD';
            seccionResponder.style.display = visible ? '' : 'none';
        }

        const btnResponder = document.getElementById('btn-responder-conta');
        if (btnResponder) btnResponder.addEventListener('click', () => this.responderObservacion());
    }

    abrirModalFactura() {
        const modal = document.getElementById('facturaModal');
        document.getElementById('factura-numero').value = '';
        document.getElementById('factura-proveedor').value = '';
        document.getElementById('factura-concepto').value = '';
        document.getElementById('factura-valor').value = '';
        document.getElementById('factura-fecha').value = '';
        document.getElementById('factura-recepcion').value = '';
        const obsRetraso = document.getElementById('factura-observacion-retraso');
        const grupoObs = document.getElementById('grupo-observacion-retraso');
        if (obsRetraso) obsRetraso.value = '';
        if (grupoObs) grupoObs.style.display = 'none';
        const metodoPago = document.getElementById('factura-metodo-pago');
        if (metodoPago) metodoPago.value = '';
        const tipoContrato = document.getElementById('factura-tipo-contrato');
        if (tipoContrato) tipoContrato.value = '';

        if (modal) modal.style.display = 'block';
    }

    cerrarModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
        if (modalId === 'eliminarFacturaModal') this.deleteFacturaId = null;
    }

    async cargarDetalle() {
        try {
            const response = await fetch(DETALLE_URL);
            const data = await response.json();
            if (data.success) {
                this.renderFacturas(data.data.facturas, data.data.valor_total);
                if (REGISTRO_ESTADO === 'DEVUELTO_COMPRAS') {
                    this.cargarUltimaDevolucion();
                }
                // MATERIAS_PRIMAS observado por Contabilidad → mostrar banner de observación
                if (REGISTRO_TIPO === 'MATERIAS_PRIMAS' && REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD') {
                    this.cargarObservacionContabilidad();
                }
            }
        } catch (error) {
            console.error('Error al cargar detalle:', error);
        }
    }

    async cargarUltimaDevolucion() {
        try {
            const response = await fetch(HISTORIAL_URL);
            const data = await response.json();
            if (data.success) {
                const devoluciones = data.data.filter(h => h.accion === 'DEVOLUCION_COMPRAS');
                if (devoluciones.length) {
                    const ultima = devoluciones[devoluciones.length - 1];
                    const banner = document.getElementById('banner-devolucion');
                    const texto = document.getElementById('texto-devolucion');
                    if (banner && texto) {
                        texto.textContent = ultima.comentario;
                        banner.style.display = 'flex';
                    }
                }
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
        }
    }

    async cargarObservacionContabilidad() {
        try {
            const response = await fetch(HISTORIAL_URL);
            const data = await response.json();
            if (data.success) {
                // Buscar la última observación/devolución de Contabilidad
                const observaciones = data.data.filter(h =>
                    h.accion === 'OBSERVACION_CONTABILIDAD' || h.accion === 'DEVOLUCION_CONTABILIDAD'
                );
                if (observaciones.length) {
                    const ultima = observaciones[observaciones.length - 1];
                    const banner = document.getElementById('banner-observacion-conta');
                    const texto = document.getElementById('texto-observacion-conta');
                    if (banner && texto) {
                        texto.textContent = ultima.comentario;
                        banner.style.display = 'flex';
                    }
                }
            }
        } catch (error) {
            console.error('Error al cargar observación de Contabilidad:', error);
        }
    }

    renderFacturas(facturas, valorTotal) {
        const tbody = document.getElementById('facturas-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        const esEditable = this.estadosEditables.includes(REGISTRO_ESTADO);
        const esDevuelto = REGISTRO_ESTADO === 'DEVUELTO_COMPRAS';

        const totalColumnas = REGISTRO_TIPO === 'MATERIAS_PRIMAS' ? 13 : REGISTRO_TIPO === 'SERVICIOS' ? 12 : 10;

        if (!facturas.length) {
            tbody.innerHTML = `<tr><td colspan="${totalColumnas}" class="text-center text-muted">Sin facturas agregadas aún.</td></tr>`;
        } else {
            const fragment = document.createDocumentFragment();
            facturas.forEach((f, idx) => {
                const tr = document.createElement('tr');
                const valor = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(f.valor);
                const fecha = f.fecha_factura ? new Date(f.fecha_factura + 'T00:00:00').toLocaleDateString('es-CO') : '—';

                // Indicador: días entre fecha_factura y fecha_recepcion_lider
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

                const fechaRecepcion = f.fecha_recepcion_lider
                    ? new Date(f.fecha_recepcion_lider + 'T00:00:00').toLocaleDateString('es-CO')
                    : '<span class="text-muted">—</span>';
                // Días retención: si tenemos fecha_recepcion_lider y fecha_envio del registro
                let diasRetencionCell = '<span class="text-muted">—</span>';
                if (f.fecha_recepcion_lider && FECHA_ENVIO) {
                    const rec = new Date(f.fecha_recepcion_lider + 'T00:00:00');
                    const env = new Date(FECHA_ENVIO);
                    const dias = Math.max(0, Math.round((env - rec) / 86400000));
                    const color = dias === 0 ? '#16a34a' : dias <= 2 ? '#d97706' : '#dc2626';
                    diasRetencionCell = `<span style="font-weight:600; color:${color};">${dias}d</span>`;
                }

                // Badge de estado por factura
                let estadoBadge = '';
                if (esDevuelto) {
                    // DEVUELTO_COMPRAS: estado de revisión de Compras
                    if (f.estado_compras === 'APROBADA') {
                        estadoBadge = '<span class="checklist-badge-ok" style="font-size:11px;"><i class="fas fa-check"></i> Aprobada</span>';
                        tr.style.background = '#f0fdf4';
                    } else if (f.estado_compras === 'DEVUELTA') {
                        estadoBadge = '<span class="checklist-badge-pendientes" style="font-size:11px;"><i class="fas fa-undo"></i> Devuelta</span>';
                        tr.style.background = '#fff7ed';
                    }
                } else if (REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD') {
                    // OBSERVADO_CONTABILIDAD: estado de revisión de Contabilidad por factura
                    if (f.estado_contabilidad === 'DEVUELTA') {
                        estadoBadge = '<span class="checklist-badge-pendientes" style="font-size:11px;"><i class="fas fa-undo"></i> Devuelta por Contabilidad</span>';
                        tr.style.background = '#fff7ed';
                    } else if (f.estado_contabilidad === 'APROBADA') {
                        estadoBadge = '<span class="checklist-badge-ok" style="font-size:11px;"><i class="fas fa-check"></i> Aprobada</span>';
                        tr.style.background = '#f0fdf4';
                    }
                }

                // Solo las facturas DEVUELTA pueden eliminarse en estado DEVUELTO_COMPRAS
                const puedeEliminar = esEditable && (REGISTRO_ESTADO === 'BORRADOR' || f.estado_compras === 'DEVUELTA');

                const celdaMetodoPago = REGISTRO_TIPO === 'SERVICIOS'
                    ? `<td style="font-size:12px;">${f.metodo_pago_display || '<span class="text-muted">—</span>'}</td>
                       <td style="font-size:12px;">${f.tipo_contrato || '<span class="text-muted">—</span>'}</td>`
                    : '';

                const celdasMateriasPrimas = REGISTRO_TIPO === 'MATERIAS_PRIMAS' ? `
                    <td style="font-size:12px;">${f.estado_contable || '—'}</td>
                    <td style="font-size:12px;">${f.referencia_appd || '—'}</td>
                    <td style="font-size:12px;">${f.numero_orden_compra || '—'}</td>
                ` : '';

                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td>${f.numero_factura} ${estadoBadge}</td>
                    <td>${f.proveedor}</td>
                    <td>
                        ${f.concepto}
                        ${f.comentario_devolucion ? `<br><small style="color:#c0392b;"><i class="fas fa-exclamation-circle"></i> ${f.comentario_devolucion}</small>` : ''}
                        ${f.comentario_devolucion_contabilidad && REGISTRO_ESTADO === 'OBSERVADO_CONTABILIDAD' ? `<br><small style="color:#7c3aed;"><i class="fas fa-exclamation-circle"></i> <strong>Contabilidad:</strong> ${f.comentario_devolucion_contabilidad}</small>` : ''}
                    </td>
                    <td>${valor}</td>
                    <td>${fecha}</td>
                    <td style="text-align:center;">${indicadorEmision}</td>
                    <td>${fechaRecepcion}</td>
                    <td>${diasRetencionCell}</td>
                    ${celdaMetodoPago}
                    ${celdasMateriasPrimas}
                    <td>
                        ${puedeEliminar ? `<button class="btn btn-sm btn-danger btn-eliminar-factura" data-id="${f.id}"><i class="fas fa-trash"></i></button>` : '—'}
                    </td>
                `;
                fragment.appendChild(tr);
            });
            tbody.appendChild(fragment);

            // Eventos eliminar
            tbody.querySelectorAll('.btn-eliminar-factura').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.deleteFacturaId = parseInt(btn.dataset.id);
                    document.getElementById('eliminarFacturaModal').style.display = 'block';
                });
            });
        }

        const totalEl = document.getElementById('valor-total');
        if (totalEl) {
            totalEl.textContent = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0 }).format(valorTotal);
        }
    }

    setupExcelUpload() {
        const input = document.getElementById('input-excel');
        if (!input) return;
        input.addEventListener('change', (e) => {
            const archivo = e.target.files[0];
            if (archivo) this.cargarExcel(archivo);
            input.value = '';
        });
    }

    async cargarExcel(archivo) {
        if (this.saving) return;
        this.saving = true;

        const label = document.getElementById('btn-cargar-excel-label');
        if (label) {
            label.style.pointerEvents = 'none';
            label.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        }

        const formData = new FormData();
        formData.append('archivo_excel', archivo);
        formData.append('csrfmiddlewaretoken', this.getCookie('csrftoken'));

        try {
            const response = await fetch(CARGAR_EXCEL_URL, { method: 'POST', body: formData });
            const data = await response.json();

            if (!data.success) {
                this.mostrarAlerta(data.error || 'Error al cargar el Excel.', 'error');
                return;
            }

            let msg = `Se crearon <strong>${data.creadas}</strong> factura(s) correctamente.`;
            if (data.errores && data.errores.length) {
                const detalle = data.errores.map(e => `Fila ${e.fila}: ${e.error}`).join('<br>');
                msg += `<br><br>Filas con error (${data.errores.length}):<br><small>${detalle}</small>`;
            }
            Swal.fire({
                icon: data.creadas > 0 ? 'success' : 'warning',
                title: 'Carga completada',
                html: msg,
                confirmButtonColor: '#1e3a8a',
            });
            if (data.creadas > 0) this.cargarDetalle();
        } catch {
            this.mostrarAlerta('Error de conexión al cargar el Excel.', 'error');
        } finally {
            this.saving = false;
            if (label) {
                label.style.pointerEvents = '';
                label.innerHTML = '<i class="fas fa-file-excel"></i> Cargar Excel';
            }
        }
    }

    async guardarFactura() {
        if (this.saving) return;
        this.saving = true;

        const btn = document.getElementById('btn-guardar-factura');
        if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }

        const numero_factura = document.getElementById('factura-numero')?.value?.trim();
        const proveedor = document.getElementById('factura-proveedor')?.value?.trim();
        const concepto = document.getElementById('factura-concepto')?.value?.trim();
        const valor = document.getElementById('factura-valor')?.value;
        const fecha_factura = document.getElementById('factura-fecha')?.value;
        const fecha_recepcion_lider = document.getElementById('factura-recepcion')?.value || null;
        const observacion_retraso = document.getElementById('factura-observacion-retraso')?.value?.trim() || '';
        const metodo_pago = document.getElementById('factura-metodo-pago')?.value || '';
        const tipo_contrato = document.getElementById('factura-tipo-contrato')?.value?.trim() || '';

        if (!numero_factura || !proveedor || !concepto || !valor || !fecha_factura) {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-save"></i> Guardar Factura'; }
            this.mostrarAlerta('Todos los campos son obligatorios.', 'warning');
            return;
        }

        try {
            const response = await fetch(FACTURAS_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ numero_factura, proveedor, concepto, valor: parseFloat(valor), fecha_factura, fecha_recepcion_lider, observacion_retraso, metodo_pago, tipo_contrato }),
            });
            const data = await response.json();
            if (data.success) {
                this.cerrarModal('facturaModal');
                this.mostrarAlerta('Factura agregada exitosamente.', 'success');
                this.cargarDetalle();
            } else {
                this.mostrarAlerta(data.error || 'Error al guardar factura.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-save"></i> Guardar Factura'; }
        }
    }

    async eliminarFactura() {
        if (!this.deleteFacturaId) return;

        const id = this.deleteFacturaId;
        this.cerrarModal('eliminarFacturaModal');

        try {
            const response = await fetch(`/contabilidad/api/facturas/${id}/eliminar/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Factura eliminada.', 'success');
                this.cargarDetalle();
            } else {
                this.mostrarAlerta(data.error || 'Error al eliminar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    async enviar() {
        if (this.saving) return;

        const horas = horasLaboralesEntre(FECHA_CREACION, new Date().toISOString());
        const superaLimite = horas > 5;

        const destino = REGISTRO_TIPO === 'MATERIAS_PRIMAS' ? 'Contabilidad' : 'Compras';
        const swalConfig = {
            title: `¿Enviar registro a ${destino}?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#1e3a8a',
        };

        if (superaLimite) {
            swalConfig.html = `El registro será enviado a ${destino} para revisión.<br><br>
                <strong style="color:#c0392b;">&#9888;&#65039; Ha superado las 5 horas laborales (${horas}h transcurridas).<br>
                Debe justificar el motivo de la demora.</strong>`;
            swalConfig.input = 'textarea';
            swalConfig.inputPlaceholder = 'Explique el motivo de la demora...';
            swalConfig.inputValidator = (v) => { if (!v || !v.trim()) return 'La justificación es obligatoria.'; };
        } else {
            swalConfig.text = `El registro será enviado a ${destino} para revisión. (${horas}h laborales transcurridas)`;
        }

        const result = await Swal.fire(swalConfig);
        if (!result.isConfirmed) return;

        const justificacion_demora = superaLimite ? result.value : '';

        this.saving = true;
        const btn = document.getElementById('btn-enviar');
        if (btn) { btn.disabled = true; btn.textContent = 'Enviando...'; }

        try {
            const response = await fetch(ENVIAR_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ justificacion_demora }),
            });
            const data = await response.json();
            if (data.success) {
                const destino = REGISTRO_TIPO === 'MATERIAS_PRIMAS' ? 'Contabilidad' : 'Compras';
                this.mostrarAlerta(`Registro enviado a ${destino} exitosamente.`, 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al enviar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar a Compras'; }
        }
    }

    async responderObservacion() {
        if (this.saving) return;

        const comentario = document.getElementById('respuesta-conta-comentario')?.value?.trim();
        if (!comentario) {
            this.mostrarAlerta('Debe ingresar una respuesta antes de enviar.', 'warning');
            return;
        }

        const result = await Swal.fire({
            title: '¿Enviar respuesta a Contabilidad?',
            text: 'El registro volverá a la bandeja de Contabilidad para revisión.',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, enviar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#1e3a8a',
        });
        if (!result.isConfirmed) return;

        this.saving = true;
        const btn = document.getElementById('btn-responder-conta');
        if (btn) { btn.disabled = true; btn.textContent = 'Enviando...'; }

        try {
            const response = await fetch(RESPONDER_OBSERVACION_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ comentario }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Respuesta enviada. El registro volvió a Contabilidad.', 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al enviar respuesta.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar respuesta a Contabilidad'; }
        }
    }

    async cargarHistorial() {
        try {
            const response = await fetch(HISTORIAL_URL);
            const data = await response.json();
            if (data.success) {
                this.renderHistorial(data.data);
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
        }
    }

    renderHistorial(historial) {
        const container = document.getElementById('historial-container');
        if (!container) return;

        if (!historial.length) {
            container.innerHTML = '<p class="text-muted">Sin historial aún.</p>';
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
        alerta.style.cssText = `
            position:fixed; top:20px; right:20px; z-index:10000;
            padding:15px 20px; border-radius:5px; color:white; font-weight:500;
            min-width:300px; box-shadow:0 4px 6px rgba(0,0,0,.1);
            display:flex; align-items:center; gap:10px;
            background-color:${colores[tipo] || colores.info};
            animation: slideInRight 0.3s ease;
        `;
        alerta.innerHTML = `
            <span>${mensaje}</span>
            <button style="background:none;border:none;color:white;font-size:18px;cursor:pointer;margin-left:auto;" onclick="this.parentElement.remove()">×</button>
        `;
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

let detalleRegistroManager;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof REGISTRO_ID !== 'undefined') {
        detalleRegistroManager = new DetalleRegistroManager();
    }
});
