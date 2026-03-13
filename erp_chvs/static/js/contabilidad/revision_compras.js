// revision_compras.js — Revisión de Compras

class RevisionComprasManager {
    constructor() {
        this.saving = false;
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
        const btnDevolver = document.getElementById('btn-devolver');
        const btnAprobar = document.getElementById('btn-aprobar-compras');
        const btnGuardarChecklist = document.getElementById('btn-guardar-checklist');
        const btnResponder = document.getElementById('btn-responder-observacion');

        if (btnConfirmar) btnConfirmar.addEventListener('click', () => this.confirmarRecepcion());
        if (btnDevolver) btnDevolver.addEventListener('click', () => this.abrirModalDevolucion());
        if (btnAprobar) btnAprobar.addEventListener('click', () => this.aprobar());
        if (btnGuardarChecklist) btnGuardarChecklist.addEventListener('click', () => this.guardarChecklist());
        if (btnResponder) btnResponder.addEventListener('click', () => this.responderObservacion());

        // Modal devolución
        const modal = document.getElementById('devolucionModal');
        const closeBtn = document.getElementById('close-devolucion-modal');
        const cancelBtn = document.getElementById('cancel-devolucion-modal');
        const confirmarBtn = document.getElementById('btn-confirmar-devolucion');

        if (closeBtn) closeBtn.addEventListener('click', () => this.cerrarModalDevolucion());
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.cerrarModalDevolucion());
        if (confirmarBtn) confirmarBtn.addEventListener('click', () => this.devolver());

        window.addEventListener('click', (e) => {
            if (e.target === modal) this.cerrarModalDevolucion();
        });
    }

    abrirModalDevolucion() {
        const modal = document.getElementById('devolucionModal');
        const textarea = document.getElementById('motivo-devolucion');
        if (textarea) textarea.value = '';
        if (modal) modal.style.display = 'block';
    }

    cerrarModalDevolucion() {
        const modal = document.getElementById('devolucionModal');
        if (modal) modal.style.display = 'none';
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

        const fragment = document.createDocumentFragment();
        facturas.forEach(factura => {
            const bloque = document.createElement('div');
            bloque.className = 'checklist-factura-bloque';

            const encabezado = document.createElement('div');
            encabezado.className = 'checklist-factura-header';
            encabezado.innerHTML = `
                <i class="fas fa-file-invoice"></i>
                <strong>${factura.numero_factura}</strong>
                <span class="text-muted" style="margin-left:8px;">${factura.proveedor}</span>
                <span class="text-muted" style="margin-left:8px; font-size:12px;">${factura.concepto}</span>
            `;
            bloque.appendChild(encabezado);

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

            if (!factura.verificaciones.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Sin ítems.</td></tr>';
            } else {
                const frag = document.createDocumentFragment();
                factura.verificaciones.forEach((v, idx) => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${idx + 1}</td>
                        <td>
                            <strong>${v.item_nombre}</strong>
                            ${v.item_descripcion ? `<br><small class="text-muted">${v.item_descripcion}</small>` : ''}
                        </td>
                        <td>${v.item_obligatorio ? '<span class="badge" style="background:#fee2e2;color:#991b1b;">Sí</span>' : '<span class="badge badge-secondary">No</span>'}</td>
                        <td>
                            <select class="checklist-estado-select" data-id="${v.id}" style="padding:6px; border:1px solid #ddd; border-radius:4px; min-width:100px;">
                                <option value="PENDIENTE" ${v.estado === 'PENDIENTE' ? 'selected' : ''}>Pendiente</option>
                                <option value="OK" ${v.estado === 'OK' ? 'selected' : ''}>OK</option>
                                <option value="NO_OK" ${v.estado === 'NO_OK' ? 'selected' : ''}>No OK</option>
                                <option value="NA" ${v.estado === 'NA' ? 'selected' : ''}>N/A</option>
                            </select>
                        </td>
                        <td>
                            <textarea class="checklist-obs-textarea" data-id="${v.id}" rows="2"
                                style="width:100%; padding:6px; border:1px solid #ddd; border-radius:4px; font-size:13px; resize:vertical;"
                                placeholder="Observación opcional...">${v.observacion || ''}</textarea>
                        </td>
                    `;
                    frag.appendChild(tr);
                });
                tbody.appendChild(frag);
            }

            tabla.appendChild(tbody);
            bloque.appendChild(tabla);
            fragment.appendChild(bloque);
        });
        container.appendChild(fragment);
    }

    async guardarChecklist() {
        if (this.saving) return;
        this.saving = true;

        const btn = document.getElementById('btn-guardar-checklist');
        if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }

        const selects = document.querySelectorAll('.checklist-estado-select');
        const items = [];
        selects.forEach(sel => {
            const id = sel.dataset.id;
            const obs = document.querySelector(`.checklist-obs-textarea[data-id="${id}"]`);
            items.push({
                verificacion_id: parseInt(id),
                estado: sel.value,
                observacion: obs ? obs.value.trim() : '',
            });
        });

        try {
            const response = await fetch(GUARDAR_CHECKLIST_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ items }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Checklist guardado exitosamente.', 'success');
            } else {
                this.mostrarAlerta(data.error || 'Error al guardar checklist.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        } finally {
            this.saving = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-save"></i> Guardar Checklist'; }
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
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
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

    async devolver() {
        const motivo = document.getElementById('motivo-devolucion')?.value?.trim();
        if (!motivo) {
            this.mostrarAlerta('El motivo de devolución es obligatorio.', 'warning');
            return;
        }

        this.cerrarModalDevolucion();

        const confirmado = await Swal.fire({
            title: '¿Devolver el registro?',
            text: 'Se notificará al líder para que corrija y reenvíe.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sí, devolver',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#d97706',
        });

        if (!confirmado.isConfirmed) return;

        try {
            const response = await fetch(DEVOLVER_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({ comentario: motivo }),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Registro devuelto al líder.', 'success');
                setTimeout(() => window.location.href = '/contabilidad/bandeja-compras/', 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al devolver.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    async aprobar() {
        const confirmado = await Swal.fire({
            title: '¿Aprobar el registro?',
            text: 'El registro pasará a revisión de Contabilidad.',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sí, aprobar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#0d9488',
        });

        if (!confirmado.isConfirmed) return;

        try {
            const response = await fetch(APROBAR_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Registro aprobado por Compras.', 'success');
                setTimeout(() => window.location.href = '/contabilidad/bandeja-compras/', 1500);
            } else {
                this.mostrarAlerta(data.error || 'Error al aprobar.', 'error');
            }
        } catch (error) {
            this.mostrarAlerta('Error de conexión.', 'error');
        }
    }

    async responderObservacion() {
        const respuesta = document.getElementById('respuesta-observacion')?.value?.trim();
        if (!respuesta) {
            this.mostrarAlerta('La respuesta es obligatoria.', 'warning');
            return;
        }

        try {
            const response = await fetch(RESPONDER_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
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

let revisionComprasManager;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof REGISTRO_ID !== 'undefined') {
        revisionComprasManager = new RevisionComprasManager();
    }
});
