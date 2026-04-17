class GestionListadosManager {
    constructor() {
        this.modal = document.getElementById('modalEliminar');
        this.pendiente = null;
        this.eliminando = false;
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
            || this._getCsrfFromCookie();
        this.init();
    }

    init() {
        document.querySelectorAll('.btn-eliminar').forEach(btn => {
            btn.addEventListener('click', (e) => this.abrirModal(e.currentTarget));
        });

        document.getElementById('btnCancelarEliminar')
            .addEventListener('click', () => this.cerrarModal());

        document.getElementById('btnConfirmarEliminar')
            .addEventListener('click', () => this.confirmarEliminar());

        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.cerrarModal();
        });
    }

    abrirModal(btn) {
        this.pendiente = {
            programaId: btn.dataset.programaId,
            programaNombre: btn.dataset.programaNombre,
            focalizacion: btn.dataset.focalizacion,
            registros: btn.dataset.registros,
        };
        document.getElementById('modalPrograma').textContent = this.pendiente.programaNombre;
        document.getElementById('modalFocalizacion').textContent = this.pendiente.focalizacion;
        document.getElementById('modalRegistros').textContent = this.pendiente.registros;
        this.modal.style.display = 'flex';
    }

    cerrarModal() {
        this.modal.style.display = 'none';
        this.pendiente = null;
    }

    async confirmarEliminar() {
        if (this.eliminando || !this.pendiente) return;
        this.eliminando = true;

        const btnConfirmar = document.getElementById('btnConfirmarEliminar');
        btnConfirmar.disabled = true;
        btnConfirmar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Eliminando...';

        try {
            const { programaId, programaNombre, focalizacion } = this.pendiente;

            const resp = await fetch('/facturacion/api/eliminar-carga-listados/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({
                    programa_id: programaId,
                    focalizacion: focalizacion,
                }),
            });

            const data = await resp.json();
            this.cerrarModal();

            if (data.success) {
                const fila = document.getElementById(
                    `fila-${programaId}-${focalizacion}`
                );
                if (fila) fila.remove();

                const total = document.getElementById('totalCargas');
                if (total) total.textContent = parseInt(total.textContent) - 1;

                Swal.fire({
                    icon: 'success',
                    title: 'Eliminado',
                    text: data.message,
                    timer: 3000,
                    showConfirmButton: false,
                });
            } else {
                Swal.fire({ icon: 'error', title: 'Error', text: data.error });
            }
        } catch (err) {
            this.cerrarModal();
            Swal.fire({ icon: 'error', title: 'Error de conexión', text: err.message });
        } finally {
            this.eliminando = false;
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = '<i class="fas fa-trash-alt"></i> Eliminar';
        }
    }

    _getCsrfFromCookie() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }
}

document.addEventListener('DOMContentLoaded', () => new GestionListadosManager());
