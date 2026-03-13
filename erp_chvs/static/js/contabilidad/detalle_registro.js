// detalle_registro.js — Detalle de registro contable del líder

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

        // Botón enviar
        const seccionEnviar = document.getElementById('seccion-enviar');
        if (seccionEnviar) {
            seccionEnviar.style.display = (REGISTRO_ESTADO === 'BORRADOR' || REGISTRO_ESTADO === 'DEVUELTO_COMPRAS') ? '' : 'none';
        }

        const btnEnviar = document.getElementById('btn-enviar');
        if (btnEnviar) btnEnviar.addEventListener('click', () => this.enviar());
    }

    abrirModalFactura() {
        const modal = document.getElementById('facturaModal');
        document.getElementById('factura-numero').value = '';
        document.getElementById('factura-proveedor').value = '';
        document.getElementById('factura-concepto').value = '';
        document.getElementById('factura-valor').value = '';
        document.getElementById('factura-fecha').value = '';
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
                // Mostrar banner de devolución si aplica
                if (REGISTRO_ESTADO === 'DEVUELTO_COMPRAS') {
                    this.cargarUltimaDevolucion();
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

    renderFacturas(facturas, valorTotal) {
        const tbody = document.getElementById('facturas-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        const esEditable = this.estadosEditables.includes(REGISTRO_ESTADO);

        if (!facturas.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Sin facturas agregadas aún.</td></tr>';
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
                    <td>
                        ${esEditable ? `<button class="btn btn-sm btn-danger btn-eliminar-factura" data-id="${f.id}"><i class="fas fa-trash"></i></button>` : '—'}
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
                body: JSON.stringify({ numero_factura, proveedor, concepto, valor: parseFloat(valor), fecha_factura }),
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
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (data.success) {
                this.mostrarAlerta('Registro enviado a Compras exitosamente.', 'success');
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
