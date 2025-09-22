/**
 * comedores.js - Funcionalidad JavaScript para la gestión de comedores
 * Este archivo maneja las interacciones de usuario en la página de listado y edición de comedores
 */

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('comedor-modal');
    const modalTitle = document.getElementById('modal-title');
    const comedorForm = document.getElementById('comedor-form');
    const submitBtn = document.getElementById('modal-submit-btn');
    const addBtn = document.getElementById('add-comedor-btn');
    const editBtns = document.querySelectorAll('.edit-comedor-btn');
    const closeBtns = document.querySelectorAll('.modal-close-btn, .modal-cancel-btn');

    // Función para abrir modal
    function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    // Función para cerrar modal
    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        comedorForm.reset();
        // Habilitar todos los campos
        enableAllFields();
    }

    // Función para habilitar todos los campos
    function enableAllFields() {
        document.getElementById('id_id_codindem').disabled = false;
        document.getElementById('id_id_departamento').disabled = false;
        document.getElementById('id_id_municipio').disabled = false;
        document.getElementById('id_id_tipo').disabled = false;
        document.getElementById('id_dane').disabled = false;
        document.getElementById('id_cod_interface').disabled = false;
        
        document.getElementById('id_id_codindem').style.backgroundColor = '';
        document.getElementById('id_id_departamento').style.backgroundColor = '';
        document.getElementById('id_id_municipio').style.backgroundColor = '';
        document.getElementById('id_id_tipo').style.backgroundColor = '';
        document.getElementById('id_dane').style.backgroundColor = '';
        document.getElementById('id_cod_interface').style.backgroundColor = '';
    }

    // Función para generar ID de CODINDEM automáticamente
    function generateCodindemId() {
        const departamentoInput = document.getElementById('id_id_departamento');
        const municipioInput = document.getElementById('id_id_municipio');
        const tipoInput = document.getElementById('id_id_tipo');
        const daneInput = document.getElementById('id_dane');
        const codindemInput = document.getElementById('id_id_codindem');
        
        // Solo generar si todos los campos necesarios tienen valor
        if (departamentoInput.value && municipioInput.value && tipoInput.value && daneInput.value) {
            // Formato: DEP-MUN-TIPO-DANE (ej. 05-001-01-105738000139)
            const codindemValue = `${departamentoInput.value}-${municipioInput.value}-${tipoInput.value}-${daneInput.value}`;
            codindemInput.value = codindemValue;
            
            // Disparar evento de cambio para cualquier validación
            const event = new Event('change');
            codindemInput.dispatchEvent(event);
        }
    }

    // Función para deshabilitar campos únicos en modo edición
    function disableUniqueFields() {
        document.getElementById('id_id_codindem').disabled = true;
        document.getElementById('id_id_departamento').disabled = true;
        document.getElementById('id_id_municipio').disabled = true;
        document.getElementById('id_id_tipo').disabled = true;
        document.getElementById('id_dane').disabled = true;
        document.getElementById('id_cod_interface').disabled = true;
        
        document.getElementById('id_id_codindem').style.backgroundColor = '#e9ecef';
        document.getElementById('id_id_departamento').style.backgroundColor = '#e9ecef';
        document.getElementById('id_id_municipio').style.backgroundColor = '#e9ecef';
        document.getElementById('id_id_tipo').style.backgroundColor = '#e9ecef';
        document.getElementById('id_dane').style.backgroundColor = '#e9ecef';
        document.getElementById('id_cod_interface').style.backgroundColor = '#e9ecef';
    }

    // Función para limpiar formulario
    function clearForm() {
        comedorForm.reset();
        // Usar la URL configurada en data-create-url del botón de añadir
        if (addBtn && addBtn.dataset.createUrl) {
            comedorForm.action = addBtn.dataset.createUrl;
        }
        enableAllFields();
    }

    // Abrir modal para añadir
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            // Limpiar formulario y establecer valores por defecto
            clearForm();
            
            // Configurar título y texto del botón para el caso de añadir
            modalTitle.textContent = 'Añadir Nueva Sede / Comedor';
            submitBtn.textContent = 'Guardar Sede';
            
            // Asegurarse que los campos están habilitados para nueva sede
            enableAllFields();
            
            // Pre-establecer valores por defecto si existen en data-attributes
            if (this.dataset.defaultDepartamento) {
                document.getElementById('id_id_departamento').value = this.dataset.defaultDepartamentoId || '';
                document.getElementById('id_departamento').value = this.dataset.defaultDepartamento || '';
            }
            
            if (this.dataset.defaultEstado) {
                document.getElementById('id_estado').value = this.dataset.defaultEstado || 'Activo';
            }
            
            // Abrir el modal
            openModal();
            
            // Poner el foco en el primer campo
            document.getElementById('id_id_codindem').focus();
        });
    }

    // Abrir modal para editar
    editBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const id_codindem = this.dataset.id_codindem;
            
            clearForm();
            modalTitle.textContent = 'Editar Sede / Comedor';
            submitBtn.textContent = 'Actualizar Sede';
            
            // Cambiar action del formulario para edición
            comedorForm.action = `/planeacion/sedes/editar/${id_codindem}/`;
            
            // Poblar formulario con datos existentes
            document.getElementById('id_id_codindem').value = this.dataset.id_codindem || '';
            document.getElementById('id_id_departamento').value = this.dataset.id_departamento || '';
            document.getElementById('id_departamento').value = this.dataset.departamento || '';
            document.getElementById('id_id_municipio').value = this.dataset.id_municipio || '';
            document.getElementById('id_municipio').value = this.dataset.municipio || '';
            document.getElementById('id_id_tipo').value = this.dataset.id_tipo || '';
            document.getElementById('id_tipo_comedor').value = this.dataset.tipo_comedor || '';
            document.getElementById('id_dane').value = this.dataset.dane || '';
            document.getElementById('id_cod_interface').value = this.dataset.cod_interface || '';
            document.getElementById('id_institucion').value = this.dataset.institucion || '';
            document.getElementById('id_sede').value = this.dataset.sede || '';
            document.getElementById('id_direccion').value = this.dataset.direccion || '';
            document.getElementById('id_telefono').value = this.dataset.telefono || '';
            document.getElementById('id_contacto').value = this.dataset.contacto || '';
            document.getElementById('id_estado').value = this.dataset.estado || '';
            
            // Deshabilitar campos únicos en modo edición
            disableUniqueFields();
            
            openModal();
        });
    });

    // Cerrar modal
    closeBtns.forEach(function(btn) {
        btn.addEventListener('click', closeModal);
    });

    // Cerrar modal al hacer click fuera
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Cerrar modal con Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });

    // Función para buscar códigos DANE basados en la institución y sede
    function searchDaneCodes() {
        const institucionInput = document.getElementById('id_institucion');
        const sedeInput = document.getElementById('id_sede');
        const daneInput = document.getElementById('id_dane');
        
        if (institucionInput.value && sedeInput.value) {
            // Mostrar indicador de búsqueda
            daneInput.placeholder = "Buscando código DANE...";
            
            // En un entorno real, aquí haríamos una petición AJAX para buscar el código DANE
            // Ejemplo simulado:
            fetch(`/planeacion/api/buscar-dane/?institucion=${encodeURIComponent(institucionInput.value)}&sede=${encodeURIComponent(sedeInput.value)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.dane_code) {
                        daneInput.value = data.dane_code;
                        // Generar CODINDEM después de obtener el DANE
                        generateCodindemId();
                    } else {
                        daneInput.placeholder = "Ingrese código DANE manualmente";
                    }
                })
                .catch(error => {
                    console.error('Error buscando código DANE:', error);
                    daneInput.placeholder = "Ingrese código DANE manualmente";
                });
        }
    }

    // Validaciones en tiempo real
    const form = document.getElementById('comedor-form');
    if (form) {
        // Validación para código DANE - solo números
        const daneInput = form.querySelector('#id_dane');
        if (daneInput) {
            daneInput.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9]/g, '');
                if (this.value.length > 12) {
                    this.value = this.value.slice(0, 12);
                }
            });
        }

        // Validación para teléfono - solo números y símbolos permitidos
        const telefonoInput = form.querySelector('#id_telefono');
        if (telefonoInput) {
            telefonoInput.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9+\-\s()]/g, '');
            });
        }

        // Configurar la generación automática del ID CODINDEM
        const idInputs = form.querySelectorAll('#id_id_departamento, #id_id_municipio, #id_id_tipo, #id_dane');
        idInputs.forEach(function(input) {
            input.addEventListener('change', generateCodindemId);
        });

        // Configurar la búsqueda automática de códigos DANE
        const institucionInput = form.querySelector('#id_institucion');
        const sedeInput = form.querySelector('#id_sede');
        if (institucionInput && sedeInput) {
            // Buscar DANE cuando ambos campos estén completos
            sedeInput.addEventListener('blur', function() {
                if (institucionInput.value && this.value) {
                    searchDaneCodes();
                }
            });
            
            institucionInput.addEventListener('blur', function() {
                if (this.value && sedeInput.value) {
                    searchDaneCodes();
                }
            });
            
            // Botón para buscar código DANE manualmente
            const searchDaneBtn = document.getElementById('search-dane-btn');
            if (searchDaneBtn) {
                searchDaneBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    searchDaneCodes();
                });
            }
        }

        // Botón para generar ID CODINDEM manualmente
        const generateIdBtn = document.getElementById('generate-id-btn');
        if (generateIdBtn) {
            generateIdBtn.addEventListener('click', function(e) {
                e.preventDefault();
                generateCodindemId();
            });
        }

        // Validación para nombres propios (departamento, municipio, institución, sede, contacto)
        const textInputs = form.querySelectorAll('#id_departamento, #id_municipio, #id_institucion, #id_sede, #id_contacto');
        textInputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                if (this.value) {
                    // Capitalizar primera letra de cada palabra
                    this.value = this.value.replace(/\b\w+/g, function(word) {
                        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
                    });
                }
            });
        });

        // Validación para códigos (ID, cod_interface) - convertir a mayúsculas
        const codeInputs = form.querySelectorAll('#id_id_codindem, #id_cod_interface');
        codeInputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                if (this.value) {
                    this.value = this.value.toUpperCase().replace(/[^A-Z0-9\-_]/g, '');
                }
            });
        });

        // Validación antes de enviar
        form.addEventListener('submit', function(e) {
            let isValid = true;
            let errorMessage = '';

            // Validar campos requeridos
            const requiredFields = [
                {id: 'id_id_codindem', name: 'ID Único'},
                {id: 'id_departamento', name: 'Departamento'},
                {id: 'id_municipio', name: 'Municipio'},
                {id: 'id_institucion', name: 'Institución'},
                {id: 'id_sede', name: 'Sede'},
                {id: 'id_dane', name: 'Código DANE'},
                {id: 'id_cod_interface', name: 'Código de Interfaz'}
            ];
            
            requiredFields.forEach(function(field) {
                const element = form.querySelector(`#${field.id}`);
                if (element && !element.value.trim()) {
                    isValid = false;
                    errorMessage += `- ${field.name} es obligatorio\n`;
                    element.style.borderColor = '#e74c3c';
                    
                    // Agregar mensaje de error bajo el campo
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'field-error';
                    errorDiv.textContent = `${field.name} es obligatorio`;
                    errorDiv.style.color = '#e74c3c';
                    errorDiv.style.fontSize = '0.8rem';
                    errorDiv.style.marginTop = '0.25rem';
                    
                    // Eliminar error anterior si existe
                    const existingError = element.parentNode.querySelector('.field-error');
                    if (existingError) {
                        element.parentNode.removeChild(existingError);
                    }
                    
                    element.parentNode.appendChild(errorDiv);
                } else if (element) {
                    element.style.borderColor = '#ced4da';
                    
                    // Eliminar mensaje de error si existe
                    const existingError = element.parentNode.querySelector('.field-error');
                    if (existingError) {
                        element.parentNode.removeChild(existingError);
                    }
                }
            });
            
            // Validar formato del ID CODINDEM
            const codindemInput = form.querySelector('#id_id_codindem');
            if (codindemInput && codindemInput.value) {
                const pattern = /^\d{2}-\d{3}-\d{2}-\d+$/;
                if (!pattern.test(codindemInput.value)) {
                    isValid = false;
                    errorMessage += `- El formato del ID Único debe ser: 00-000-00-000000000\n`;
                    codindemInput.style.borderColor = '#e74c3c';
                    
                    // Agregar mensaje de error específico
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'field-error';
                    errorDiv.textContent = `Formato incorrecto. Debe ser: 00-000-00-000000000`;
                    errorDiv.style.color = '#e74c3c';
                    errorDiv.style.fontSize = '0.8rem';
                    errorDiv.style.marginTop = '0.25rem';
                    
                    // Eliminar error anterior si existe
                    const existingError = codindemInput.parentNode.querySelector('.field-error');
                    if (existingError) {
                        codindemInput.parentNode.removeChild(existingError);
                    }
                    
                    codindemInput.parentNode.appendChild(errorDiv);
                }
            }

            if (!isValid) {
                e.preventDefault();
                
                // Mostrar mensaje de error en la parte superior del formulario
                const formErrorDiv = document.createElement('div');
                formErrorDiv.className = 'alert alert-danger';
                formErrorDiv.textContent = 'Por favor corrige los errores marcados:';
                formErrorDiv.style.marginBottom = '1rem';
                
                // Eliminar alerta anterior si existe
                const existingAlert = form.querySelector('.alert-danger');
                if (existingAlert) {
                    form.removeChild(existingAlert);
                }
                
                // Insertar al inicio del formulario
                form.insertBefore(formErrorDiv, form.firstChild);
                
                // Hacer scroll al primer error
                const firstErrorField = form.querySelector('[style*="border-color: #e74c3c"]');
                if (firstErrorField) {
                    firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstErrorField.focus();
                }
            }
        });
    }
});
