'use strict';

class CertificadosManager {
    constructor() {
        this.empleadoData = null;
        this.saving = false;
        this.init();
    }

    init() {
        document.getElementById('buscarEmpleadoBtn')
            .addEventListener('click', () => this.buscarEmpleado());

        document.getElementById('cedulaBusqueda')
            .addEventListener('keydown', (e) => { if (e.key === 'Enter') this.buscarEmpleado(); });

        document.getElementById('generarCertBtn')
            .addEventListener('click', () => this.generarCertificado());

        document.getElementById('cancelarBtn')
            .addEventListener('click', () => this.resetForm());

        document.getElementById('recargarBtn')
            .addEventListener('click', () => this.loadCertificados());

        this.loadCertificados();
    }

    // ── Búsqueda de empleado ──────────────────────────────────────────────
    async buscarEmpleado() {
        const cedula = document.getElementById('cedulaBusqueda').value.trim();
        if (!cedula) {
            this.showAlert('Ingresa una cédula para buscar.', 'warning');
            return;
        }

        const btn = document.getElementById('buscarEmpleadoBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Buscando...';

        try {
            const res = await fetch(`/calidad/api/buscar-empleado/?cedula=${encodeURIComponent(cedula)}`);
            const data = await res.json();

            if (!res.ok) {
                this.showAlert(data.error || 'Error al buscar el empleado.', 'error');
                this.resetForm();
                return;
            }

            this.mostrarDatosEmpleado(data.empleado);
        } catch {
            this.showAlert('Error de conexión. Inténtalo de nuevo.', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-search"></i> Buscar';
        }
    }

    mostrarDatosEmpleado(emp) {
        this.empleadoData = emp;

        const tipoLabels = {
            manipuladora: 'Manipuladora de Alimentos',
            planta: 'Personal de Planta',
            aprendiz: 'Aprendiz SENA',
        };

        document.getElementById('empNombreHeader').textContent = emp.nombre_completo || '—';
        document.getElementById('empNombre').textContent    = emp.nombre_completo || '—';
        document.getElementById('empCedula').textContent    = emp.cedula || '—';
        document.getElementById('empCargo').textContent     = emp.cargo || '—';
        document.getElementById('empEps').textContent       = emp.eps || '—';
        document.getElementById('empPrograma').textContent  = emp.programa_empresa || '—';

        const badge = document.getElementById('empTipoBadge');
        badge.textContent = tipoLabels[emp.tipo_empleado] || emp.tipo_empleado;
        badge.className = `tipo-badge ${emp.tipo_empleado}`;

        document.getElementById('empleadoPanel').style.display = 'block';
    }

    // ── Generación del certificado ────────────────────────────────────────
    async generarCertificado() {
        if (!this.empleadoData) {
            this.showAlert('Primero busca un empleado.', 'warning');
            return;
        }
        if (this.saving) return;
        this.saving = true;

        const btn = document.getElementById('generarCertBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generando...';

        const observaciones = document.getElementById('observaciones').value.trim();

        try {
            const res = await fetch('/calidad/certificados/generar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    cedula: this.empleadoData.cedula,
                    observaciones,
                }),
            });
            const data = await res.json();

            if (!res.ok) {
                this.showAlert(data.error || 'Error al generar el certificado.', 'error');
                return;
            }

            this.showAlert(
                `Certificado ${data.numero} generado. Descarga en progreso...`,
                'success'
            );

            // Abrir descarga en nueva pestaña
            window.open(data.url_descargar, '_blank');

            this.resetForm();
            this.loadCertificados();
        } catch {
            this.showAlert('Error de conexión. Inténtalo de nuevo.', 'error');
        } finally {
            this.saving = false;
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-file-pdf"></i> Generar y Descargar Certificado';
        }
    }

    // ── Lista de certificados ─────────────────────────────────────────────
    async loadCertificados() {
        const tbody = document.getElementById('certificadosTbody');
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted"><i class="fas fa-spinner fa-spin"></i> Cargando...</td></tr>';

        try {
            const res = await fetch('/calidad/api/certificados/');
            const data = await res.json();

            if (!data.certificados.length) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No hay certificados emitidos aún.</td></tr>';
                return;
            }

            const tipoLabels = {
                manipuladora: 'Manipuladora',
                planta: 'Planta',
                aprendiz: 'Aprendiz',
            };

            const frag = document.createDocumentFragment();
            for (const c of data.certificados) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${c.numero_certificado}</strong></td>
                    <td>${c.cedula}</td>
                    <td>${c.nombre_completo}</td>
                    <td>${c.cargo || '—'}</td>
                    <td><span class="badge-tipo badge-${c.tipo_empleado}">${tipoLabels[c.tipo_empleado] || c.tipo_empleado}</span></td>
                    <td>${c.fecha_emision}</td>
                    <td>${c.creado_por}</td>
                    <td>
                        <a href="/calidad/certificados/${c.id}/descargar/"
                           target="_blank"
                           class="btn btn-sm btn-primary"
                           title="Descargar PDF">
                            <i class="fas fa-download"></i>
                        </a>
                    </td>
                `;
                frag.appendChild(tr);
            }
            tbody.innerHTML = '';
            tbody.appendChild(frag);
        } catch {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Error al cargar los certificados.</td></tr>';
        }
    }

    // ── Utilidades ────────────────────────────────────────────────────────
    resetForm() {
        this.empleadoData = null;
        document.getElementById('cedulaBusqueda').value = '';
        document.getElementById('observaciones').value = '';
        document.getElementById('empleadoPanel').style.display = 'none';
    }

    showAlert(message, type = 'info') {
        const existing = document.querySelector('.calidad-alert');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.className = `calidad-alert ${type}`;
        div.textContent = message;
        document.body.appendChild(div);

        setTimeout(() => div.remove(), 5000);
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('certificadosTable')) {
        window.certificadosManager = new CertificadosManager();
    }
});
