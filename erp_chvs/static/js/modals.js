document.addEventListener('DOMContentLoaded', function () {
    // ===== MODAL PARA COMEDORES =====
    const comedorModal = document.getElementById('comedor-modal');
    if (comedorModal) {
        const comedorModalForm = document.getElementById('comedor-form');
        const comedorModalTitle = document.getElementById('modal-title');
        const comedorModalSubmitBtn = document.getElementById('modal-submit-btn');

        const openAddComedorBtn = document.getElementById('add-comedor-btn');
        const editComedorBtns = document.querySelectorAll('.edit-comedor-btn');

        const comedorCloseBtn = comedorModal.querySelector('.modal-close-btn');
        const comedorCancelBtn = comedorModal.querySelector('.modal-cancel-btn');

        function openComedorModal() {
            comedorModal.style.display = 'flex';
        }

        function closeComedorModal() {
            comedorModal.style.display = 'none';
        }

        // Configurar modal para "Añadir Sede"
        if (openAddComedorBtn) {
            openAddComedorBtn.addEventListener('click', function() {
                comedorModalTitle.textContent = 'Añadir Nueva Sede / Comedor';
                comedorModalSubmitBtn.textContent = 'Guardar Sede';
                comedorModalForm.action = this.dataset.createUrl;
                comedorModalForm.reset();
                openComedorModal();
            });
        }

        // Configurar modal para "Editar Sede"
        editComedorBtns.forEach(button => {
            button.addEventListener('click', function() {
                const data = this.dataset;

                comedorModalTitle.textContent = 'Editar Sede / Comedor';
                comedorModalSubmitBtn.textContent = 'Actualizar Sede';
                comedorModalForm.action = `/planeacion/sedes/editar/${data.id}/`;

                // Poblar los campos del formulario con los datos existentes
                const fields = [
                    'institucion', 'sede', 'direccion', 'telefono', 'contacto',
                    'estado', 'departamento', 'municipio', 'tipo_comedor', 'dane',
                    'cod_interface'
                ];

                fields.forEach(field => {
                    const input = comedorModalForm.querySelector(`[name="${field}"]`);
                    if (input && data[field]) {
                        if (input.type === 'select-one') {
                            // Para campos select, buscar la opción correcta
                            for (let option of input.options) {
                                if (option.value === data[field]) {
                                    option.selected = true;
                                    break;
                                }
                            }
                        } else {
                            input.value = data[field];
                        }
                    }
                });
                
                openComedorModal();
            });
        });

        // Eventos para cerrar el modal de comedores
        if (comedorCloseBtn) {
            comedorCloseBtn.addEventListener('click', closeComedorModal);
        }
        if (comedorCancelBtn) {
            comedorCancelBtn.addEventListener('click', closeComedorModal);
        }
        comedorModal.addEventListener('click', function(event) {
            if (event.target === comedorModal) {
                closeComedorModal();
            }
        });
    }

    // ===== MODAL PARA PROGRAMAS (código original) =====
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
                modalForm.querySelector('[name="fecha_inicial"]').value = data.fechaInicial;
                modalForm.querySelector('[name="fecha_final"]').value = data.fechaFinal;
                modalForm.querySelector('[name="estado"]').value = data.estado;
                
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

        // Eventos para cerrar el modal de programas
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
    }
});
