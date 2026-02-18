/**
 * programas.js - Funcionalidad JavaScript para la gestión de programas
 * Este archivo maneja las interacciones de usuario en la página de programas
 */

document.addEventListener('DOMContentLoaded', function() {

    // ===== BÚSQUEDA DE MUNICIPIO (input + datalist sobre select oculto) =====
    const municipioSelect = document.querySelector('[name="municipio"]');
    const municipioSearch = document.getElementById('municipio-search');
    const municipioDatalist = document.getElementById('municipios-datalist');

    function initMunicipioDatalist() {
        if (!municipioSelect || !municipioSearch || !municipioDatalist) return;

        // Poblar datalist con los nombres de los municipios del select oculto
        municipioDatalist.innerHTML = '';
        Array.from(municipioSelect.options).forEach(function(option) {
            if (option.value) {
                const dataOption = document.createElement('option');
                dataOption.value = option.text.trim();
                municipioDatalist.appendChild(dataOption);
            }
        });

        // Si el select ya tiene valor (error de validación backend), pre-llenar el input
        if (municipioSelect.value) {
            const selectedOpt = municipioSelect.options[municipioSelect.selectedIndex];
            if (selectedOpt && selectedOpt.value) {
                municipioSearch.value = selectedOpt.text.trim();
            }
        }
    }

    /**
     * Sincroniza el texto ingresado en el input con el select oculto.
     * Retorna true si encontró un municipio válido, false en caso contrario.
     */
    function syncMunicipioToSelect(searchValue) {
        if (!municipioSelect) return false;
        const texto = searchValue.trim().toUpperCase();
        let found = false;

        Array.from(municipioSelect.options).forEach(function(option) {
            if (option.text.trim().toUpperCase() === texto) {
                municipioSelect.value = option.value;
                found = true;
            }
        });

        if (!found) {
            municipioSelect.value = '';
        }
        return found;
    }

    /**
     * Establece el municipio seleccionado en el input de búsqueda a partir del PK.
     * Se usa al abrir el modal de edición.
     */
    function setMunicipioSearchByPk(pk) {
        if (!municipioSelect || !municipioSearch) return;
        municipioSelect.value = pk;
        const selectedOpt = municipioSelect.options[municipioSelect.selectedIndex];
        if (selectedOpt && selectedOpt.value) {
            municipioSearch.value = selectedOpt.text.trim();
            municipioSearch.style.borderColor = '#ced4da';
        }
    }

    if (municipioSearch) {
        municipioSearch.addEventListener('input', function() {
            syncMunicipioToSelect(this.value);
        });
        municipioSearch.addEventListener('change', function() {
            const found = syncMunicipioToSelect(this.value);
            if (this.value && !found) {
                this.style.borderColor = '#e74c3c';
            } else {
                this.style.borderColor = '#ced4da';
            }
        });
    }

    initMunicipioDatalist();


    // ===== MODAL PARA PROGRAMAS =====
    const programModal = document.getElementById('program-modal');
    if (programModal) {
        const modalForm = document.getElementById('program-form');
        const modalTitle = document.getElementById('modal-title');
        const modalSubmitBtn = document.getElementById('modal-submit-btn');

        const openAddBtn = document.getElementById('add-program-btn');
        const editBtns = document.querySelectorAll('.edit-program-btn');

        const closeBtn = programModal.querySelector('.modal-close-btn');
        const cancelBtn = programModal.querySelector('.modal-cancel-btn');

        const currentImageContainer = document.getElementById('current-image-container');
        const currentImageLink = document.getElementById('current-image-link');

        function openModal() {
            programModal.style.display = 'flex';
        }

        function closeModal() {
            programModal.style.display = 'none';
        }

        // Configurar modal para "Añadir"
        if (openAddBtn) {
            openAddBtn.addEventListener('click', function() {
                modalTitle.textContent = 'Añadir Nuevo Programa';
                modalSubmitBtn.textContent = 'Guardar Programa';
                modalForm.action = this.dataset.createUrl;
                modalForm.reset();
                // Limpiar estilos del campo de municipio (form.reset() no resetea CSS)
                if (municipioSearch) {
                    municipioSearch.style.borderColor = '#ced4da';
                }
                if (currentImageContainer) currentImageContainer.style.display = 'none';
                openModal();
            });
        }

        // Configurar modal para "Editar"
        editBtns.forEach(button => {
            button.addEventListener('click', function() {
                const data = this.dataset;

                modalTitle.textContent = 'Editar Programa';
                modalSubmitBtn.textContent = 'Actualizar Programa';
                modalForm.action = `/planeacion/programas/editar/${data.id}/`;

                modalForm.querySelector('[name="programa"]').value = data.programa;
                setMunicipioSearchByPk(data.municipio);
                modalForm.querySelector('[name="fecha_inicial"]').value = data.fechaInicial;
                modalForm.querySelector('[name="fecha_final"]').value = data.fechaFinal;
                modalForm.querySelector('[name="estado"]').value = data.estado;
                modalForm.querySelector('[name="contrato"]').value = data.contrato;

                if (data.imagenUrl && currentImageContainer && currentImageLink) {
                    currentImageLink.href = data.imagenUrl;
                    currentImageContainer.style.display = 'block';
                } else if (currentImageContainer) {
                    currentImageContainer.style.display = 'none';
                }
                modalForm.querySelector('[name="imagen"]').value = '';

                openModal();
            });
        });

        // Eventos para cerrar el modal
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }
        if (cancelBtn) {
            cancelBtn.addEventListener('click', closeModal);
        }
        programModal.addEventListener('click', function(event) {
            if (event.target === programModal) {
                closeModal();
            }
        });

        // ===== ELIMINAR PROGRAMA =====
        const deleteBtns = document.querySelectorAll('.btn-delete-program');
        deleteBtns.forEach(button => {
            button.addEventListener('click', function() {
                const programId = this.dataset.id;
                const programNombre = this.dataset.nombre;

                Swal.fire({
                    title: '¿Estás seguro?',
                    text: `Vas a eliminar el programa "${programNombre}". Esta acción no se puede deshacer y también eliminará la imagen asociada.`,
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#3085d6',
                    confirmButtonText: 'Sí, eliminar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = `/planeacion/programas/eliminar/${programId}/`;

                        const csrfInput = document.createElement('input');
                        csrfInput.type = 'hidden';
                        csrfInput.name = 'csrfmiddlewaretoken';
                        csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;

                        form.appendChild(csrfInput);
                        document.body.appendChild(form);
                        form.submit();
                    }
                });
            });
        });

        // ===== VALIDACIÓN ANTES DE ENVIAR =====
        modalForm.addEventListener('submit', function(e) {
            let isValid = true;
            let errorMessage = '';

            // Campos de texto/fecha obligatorios
            const requiredFields = [
                {name: 'programa', label: 'Nombre del Programa'},
                {name: 'fecha_inicial', label: 'Fecha Inicial'},
                {name: 'fecha_final', label: 'Fecha Final'},
                {name: 'contrato', label: 'Número de Contrato'}
            ];

            requiredFields.forEach(function(field) {
                const element = modalForm.querySelector(`[name="${field.name}"]`);
                if (element && !element.value.trim()) {
                    isValid = false;
                    errorMessage += `- ${field.label} es obligatorio\n`;
                    element.style.borderColor = '#e74c3c';
                } else if (element) {
                    element.style.borderColor = '#ced4da';
                }
            });

            // Validar municipio (a través del select oculto sincronizado)
            if (!municipioSelect || !municipioSelect.value) {
                isValid = false;
                errorMessage += '- Municipio es obligatorio\n';
                if (municipioSearch) municipioSearch.style.borderColor = '#e74c3c';
            }

            // Validar que la fecha final sea posterior a la inicial
            const fechaInicial = new Date(modalForm.querySelector('[name="fecha_inicial"]').value);
            const fechaFinal = new Date(modalForm.querySelector('[name="fecha_final"]').value);

            if (fechaInicial && fechaFinal && fechaFinal <= fechaInicial) {
                isValid = false;
                errorMessage += '- La fecha final debe ser posterior a la fecha inicial\n';
                modalForm.querySelector('[name="fecha_final"]').style.borderColor = '#e74c3c';
            }

            if (!isValid) {
                e.preventDefault();
                alert('Por favor corrige los siguientes errores:\n\n' + errorMessage);
            }
        });
    }
});
