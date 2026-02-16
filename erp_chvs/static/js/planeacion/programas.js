/**
 * programas.js - Funcionalidad JavaScript para la gestión de programas
 * Este archivo maneja las interacciones de usuario en la página de programas
 */

document.addEventListener('DOMContentLoaded', function() {
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
                modalForm.querySelector('[name="municipio"]').value = data.municipio;
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
                        // Crear un formulario temporal para enviar el POST de eliminación
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

        // Validación antes de enviar
        modalForm.addEventListener('submit', function(e) {
            let isValid = true;
            let errorMessage = '';

            // Validar campos requeridos
            const requiredFields = [
                {name: 'programa', label: 'Nombre del Programa'},
                {name: 'municipio', label: 'Municipio'},
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
