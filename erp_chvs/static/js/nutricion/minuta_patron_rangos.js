class MinutaPatronRangosManager {
    constructor() {
        this.modal = null;
        this.form = null;
        this.modalTitle = null;
        this.submitBtn = null;
        this.validationSummary = null;
        this.isEditing = false;
        this.currentSearchTerm = '';
        this.init();
    }

    init() {
        this.modal = document.getElementById('minuta-rango-modal');
        this.form = document.getElementById('minuta-rango-form');
        this.modalTitle = document.getElementById('modal-title');
        this.submitBtn = document.getElementById('modal-submit-btn');
        this.validationSummary = document.getElementById('formValidationSummary');

        if (!this.modal || !this.form) {
            return;
        }

        this.setupEventListeners();
        this.setupSearch();
    }

    setupEventListeners() {
        const addBtn = document.getElementById('add-rango-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showCreateModal());
        }

        document.querySelectorAll('.edit-rango-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showEditModal(e.currentTarget);
            });
        });

        document.querySelectorAll('.delete-rango-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteRango(e.currentTarget);
            });
        });

        this.modal.querySelectorAll('.modal-close-btn, .modal-cancel-btn').forEach((btn) => {
            btn.addEventListener('click', () => this.closeModal());
        });

        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'flex') {
                this.closeModal();
            }
        });

        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const clearButton = document.getElementById('clearSearch');
        if (!searchInput || !clearButton) return;

        const urlParams = new URLSearchParams(window.location.search);
        const currentQuery = urlParams.get('q') || '';
        this.currentSearchTerm = currentQuery;

        searchInput.addEventListener('input', () => {
            this.currentSearchTerm = searchInput.value.trim();
            this.updateClearButton();
        });

        clearButton.addEventListener('click', () => {
            window.location.href = window.location.pathname;
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.submitSearch();
            }
        });
    }

    updateClearButton() {
        const clearButton = document.getElementById('clearSearch');
        if (!clearButton) return;
        if (this.currentSearchTerm) {
            clearButton.classList.add('show');
            return;
        }
        clearButton.classList.remove('show');
    }

    submitSearch() {
        const searchTerm = this.currentSearchTerm.trim();
        if (searchTerm) {
            window.location.href = `${window.location.pathname}?q=${encodeURIComponent(searchTerm)}`;
            return;
        }
        window.location.href = window.location.pathname;
    }

    showCreateModal() {
        this.isEditing = false;
        this.clearForm();
        this.modalTitle.textContent = 'Añadir Registro';
        this.submitBtn.textContent = 'Guardar Registro';
        this.form.action = document.getElementById('add-rango-btn')?.dataset.createUrl || window.location.pathname;
        this.openModal();
    }

    showEditModal(button) {
        this.isEditing = true;
        const data = button.dataset;
        this.clearForm();
        this.modalTitle.textContent = 'Editar Registro';
        this.submitBtn.textContent = 'Actualizar Registro';
        this.form.action = `/nutricion/minuta-patron-rangos/editar/${data.id}/`;

        document.getElementById('id_id_modalidad').value = data.idModalidad || '';
        document.getElementById('id_id_grado_escolar_uapa').value = data.idGrado || '';
        document.getElementById('id_id_componente').value = data.idComponente || '';
        document.getElementById('id_id_grupo_alimentos').value = data.idGrupo || '';
        document.getElementById('id_peso_neto_minimo').value = data.pesoMin || '';
        document.getElementById('id_peso_neto_maximo').value = data.pesoMax || '';

        this.openModal();
    }

    openModal() {
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.clearForm();
    }

    clearForm() {
        this.form.reset();
        if (this.validationSummary) {
            this.validationSummary.style.display = 'none';
            this.validationSummary.innerHTML = '';
        }
    }

    renderErrors(errorsByField = {}, genericMessage = '') {
        const allErrors = [];
        Object.values(errorsByField).forEach((errors) => {
            if (Array.isArray(errors)) {
                allErrors.push(...errors);
            }
        });
        if (!allErrors.length && genericMessage) {
            allErrors.push(genericMessage);
        }

        if (!this.validationSummary) return;
        if (!allErrors.length) {
            this.validationSummary.style.display = 'none';
            this.validationSummary.innerHTML = '';
            return;
        }

        const items = allErrors.map((err) => `<li>${err}</li>`).join('');
        this.validationSummary.innerHTML = `<strong>Corrige lo siguiente:</strong><ul style="margin:8px 0 0 18px; padding:0;">${items}</ul>`;
        this.validationSummary.style.display = 'block';
    }

    async handleSubmit(event) {
        event.preventDefault();
        const submitOriginal = this.submitBtn ? this.submitBtn.innerHTML : '';
        if (this.submitBtn) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = 'Guardando...';
        }

        try {
            const response = await fetch(this.form.action || window.location.pathname, {
                method: 'POST',
                body: new FormData(this.form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                this.renderErrors(data.errors || {}, data.message || 'No se pudo guardar el registro.');
                if (typeof Swal !== 'undefined') {
                    Swal.fire('No se guardó', data.message || 'Hay validaciones pendientes.', 'warning');
                }
                return;
            }

            if (typeof Swal !== 'undefined') {
                await Swal.fire('Éxito', data.message || 'Registro guardado correctamente.', 'success');
            }
            window.location.reload();
        } catch (error) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', 'Error de conexión al guardar el registro.', 'error');
            }
        } finally {
            if (this.submitBtn) {
                this.submitBtn.disabled = false;
                this.submitBtn.innerHTML = submitOriginal || (this.isEditing ? 'Actualizar Registro' : 'Guardar Registro');
            }
        }
    }

    async deleteRango(button) {
        const id = button.dataset.id;
        const nombre = button.dataset.nombre || `Registro ${id}`;

        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title: '¿Eliminar registro?',
                text: `¿Está seguro de eliminar "${nombre}"?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            });
            if (!result.isConfirmed) return;
        } else if (!confirm(`¿Está seguro de eliminar "${nombre}"?`)) {
            return;
        }

        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
            const response = await fetch(`/nutricion/minuta-patron-rangos/eliminar/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            const result = await response.json();

            if (result.success) {
                if (typeof Swal !== 'undefined') {
                    await Swal.fire({
                        title: 'Eliminado',
                        text: result.message || 'Registro eliminado correctamente.',
                        icon: 'success',
                        timer: 1400,
                        showConfirmButton: false
                    });
                }
                window.location.reload();
                return;
            }

            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', result.error || 'No se pudo eliminar el registro.', 'error');
            }
        } catch (error) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', 'Error de conexión al eliminar el registro.', 'error');
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('minuta-rango-modal')) {
        window.minutaPatronRangosManager = new MinutaPatronRangosManager();
    }
});
