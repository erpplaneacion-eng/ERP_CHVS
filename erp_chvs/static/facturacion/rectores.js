class RectoresManager {
    constructor() {
        this.saving = false;
        this.modal = document.getElementById('modal-rector');
        this.inputRector = document.getElementById('input-rector');
        this.inputCodigoIe = document.getElementById('input-codigo-ie');
        this.modalTitulo = document.getElementById('modal-titulo');
        this.modalNombreIe = document.getElementById('modal-nombre-ie');

        this._bindEvents();
    }

    _bindEvents() {
        // Abrir modal editar/agregar
        document.querySelectorAll('.btn-editar-rector').forEach(btn => {
            btn.addEventListener('click', () => this._abrirModal(btn));
        });

        // Eliminar rector
        document.querySelectorAll('.btn-eliminar-rector').forEach(btn => {
            btn.addEventListener('click', () => this._confirmarEliminar(btn));
        });

        // Cerrar modal
        document.getElementById('btn-cerrar-modal').addEventListener('click', () => this._cerrarModal());
        document.getElementById('btn-cancelar-modal').addEventListener('click', () => this._cerrarModal());
        this.modal.addEventListener('click', e => { if (e.target === this.modal) this._cerrarModal(); });

        // Guardar
        document.getElementById('btn-guardar-rector').addEventListener('click', () => this._guardar());

        // Enter en el input
        this.inputRector.addEventListener('keydown', e => { if (e.key === 'Enter') this._guardar(); });

        // Búsqueda rápida
        const busqueda = document.getElementById('busqueda-ie');
        if (busqueda) {
            busqueda.addEventListener('input', () => this._filtrar(busqueda.value));
        }
    }

    _abrirModal(btn) {
        const codigo = btn.dataset.codigo;
        const nombreIe = btn.dataset.nombreIe;
        const rectorActual = btn.dataset.rector || '';

        this.inputCodigoIe.value = codigo;
        this.inputRector.value = rectorActual;
        this.modalNombreIe.textContent = nombreIe;
        this.modalTitulo.textContent = rectorActual ? 'Editar Rector' : 'Registrar Rector';

        this.modal.style.display = 'flex';
        setTimeout(() => this.inputRector.focus(), 100);
    }

    _cerrarModal() {
        this.modal.style.display = 'none';
        this.inputRector.value = '';
        this.inputCodigoIe.value = '';
    }

    async _guardar() {
        if (this.saving) return;

        const nombre = this.inputRector.value.trim();
        const codigo = this.inputCodigoIe.value.trim();

        if (!nombre) {
            this.inputRector.focus();
            return;
        }

        this.saving = true;
        const btnGuardar = document.getElementById('btn-guardar-rector');
        btnGuardar.disabled = true;
        btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

        try {
            const resp = await fetch('/facturacion/api/guardar-rector/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrf(),
                },
                body: JSON.stringify({ codigo_ie: codigo, nombre_rector: nombre }),
            });

            const data = await resp.json();

            if (data.success) {
                const fila = document.querySelector(`tr[data-codigo-ie="${codigo}"]`);
                if (fila) {
                    const celdaRector = fila.querySelector('.celda-rector');
                    celdaRector.innerHTML = `<span class="rector-nombre">${data.nombre_rector}</span>`;

                    const celdaAcciones = fila.querySelector('.celda-acciones');
                    const btnEditar = celdaAcciones.querySelector('.btn-editar-rector');
                    btnEditar.dataset.rector = data.nombre_rector;
                    btnEditar.innerHTML = '<i class="fas fa-edit"></i> Editar';

                    if (!celdaAcciones.querySelector('.btn-eliminar-rector')) {
                        const btnEliminar = document.createElement('button');
                        btnEliminar.className = 'btn btn-sm btn-danger btn-eliminar-rector';
                        btnEliminar.dataset.codigo = codigo;
                        btnEliminar.dataset.nombreIe = fila.dataset.nombreIe;
                        btnEliminar.innerHTML = '<i class="fas fa-trash"></i>';
                        btnEliminar.addEventListener('click', () => this._confirmarEliminar(btnEliminar));
                        celdaAcciones.appendChild(btnEliminar);
                    }
                }

                this._cerrarModal();
                Swal.fire({ icon: 'success', title: 'Guardado', text: 'Rector registrado correctamente.', timer: 1800, showConfirmButton: false });
            } else {
                Swal.fire({ icon: 'error', title: 'Error', text: data.error || 'No se pudo guardar.' });
            }
        } catch (err) {
            Swal.fire({ icon: 'error', title: 'Error de red', text: 'No se pudo conectar con el servidor.' });
        } finally {
            this.saving = false;
            btnGuardar.disabled = false;
            btnGuardar.innerHTML = '<i class="fas fa-save"></i> Guardar';
        }
    }

    _confirmarEliminar(btn) {
        const codigo = btn.dataset.codigo;
        const nombreIe = btn.dataset.nombreIe;

        Swal.fire({
            title: '¿Eliminar rector?',
            html: `Se eliminará el rector registrado para:<br><strong>${nombreIe}</strong>`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#c0392b',
            cancelButtonText: 'Cancelar',
            confirmButtonText: 'Sí, eliminar',
        }).then(async result => {
            if (!result.isConfirmed) return;

            try {
                const resp = await fetch('/facturacion/api/eliminar-rector/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this._getCsrf(),
                    },
                    body: JSON.stringify({ codigo_ie: codigo }),
                });

                const data = await resp.json();

                if (data.success) {
                    const fila = document.querySelector(`tr[data-codigo-ie="${codigo}"]`);
                    if (fila) {
                        fila.querySelector('.celda-rector').innerHTML = '<span class="rector-vacio text-muted"><em>Sin registrar</em></span>';
                        const celdaAcciones = fila.querySelector('.celda-acciones');
                        const btnEditar = celdaAcciones.querySelector('.btn-editar-rector');
                        btnEditar.dataset.rector = '';
                        btnEditar.innerHTML = '<i class="fas fa-edit"></i> Agregar';
                        const btnEliminar = celdaAcciones.querySelector('.btn-eliminar-rector');
                        if (btnEliminar) btnEliminar.remove();
                    }
                    Swal.fire({ icon: 'success', title: 'Eliminado', timer: 1500, showConfirmButton: false });
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: data.error });
                }
            } catch (err) {
                Swal.fire({ icon: 'error', title: 'Error de red', text: 'No se pudo conectar con el servidor.' });
            }
        });
    }

    _filtrar(texto) {
        const termino = texto.toLowerCase();
        document.querySelectorAll('#tabla-ies tbody tr').forEach(fila => {
            const nombreIe = (fila.querySelector('td:nth-child(2)')?.textContent || '').toLowerCase();
            const municipio = (fila.querySelector('td:nth-child(1)')?.textContent || '').toLowerCase();
            fila.style.display = (nombreIe.includes(termino) || municipio.includes(termino)) ? '' : 'none';
        });
    }

    _getCsrf() {
        return document.cookie.split(';').map(c => c.trim())
            .find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
    }
}

document.addEventListener('DOMContentLoaded', () => new RectoresManager());
