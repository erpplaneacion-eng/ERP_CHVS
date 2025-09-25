/**
 * JavaScript para el módulo de facturación.
 * Maneja la validación de archivos y la interacción del usuario.
 */

class FacturacionManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeFormValidation();
    }

    bindEvents() {
        // Validación de archivos en tiempo real
        const fileInputs = document.querySelectorAll('input[type="file"][name="archivo_excel"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => this.handleFileChange(e));
        });

        // Validación de formularios
        const forms = document.querySelectorAll('form[method="post"]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });

        // Cambio de tipo de procesamiento
        const tipoProcesamientoInputs = document.querySelectorAll('input[name="tipo_procesamiento"]');
        tipoProcesamientoInputs.forEach(input => {
            input.addEventListener('change', (e) => this.handleTipoProcesamientoChange(e));
        });
    }

    initializeFormValidation() {
        // Configurar validación de Bootstrap si está disponible
        if (typeof bootstrap !== 'undefined') {
            const forms = document.querySelectorAll('.needs-validation');
            forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!form.checkValidity()) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    form.classList.add('was-validated');
                });
            });
        }
    }

    handleFileChange(event) {
        const file = event.target.files[0];
        const form = event.target.closest('form');
        const tipoProcesamiento = form.querySelector('input[name="tipo_procesamiento"]')?.value || 'original';
        
        if (file) {
            this.validateFile(file, tipoProcesamiento)
                .then(result => {
                    this.showFileValidationResult(result, event.target);
                })
                .catch(error => {
                    this.showError('Error al validar el archivo: ' + error.message);
                });
        }
    }

    async validateFile(file, tipoProcesamiento) {
        const formData = new FormData();
        formData.append('archivo_excel', file);
        formData.append('tipo_procesamiento', tipoProcesamiento);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
            const response = await fetch('/facturacion/validar-archivo/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error validating file:', error);
            throw error;
        }
    }

    showFileValidationResult(result, inputElement) {
        const feedbackElement = this.getOrCreateFeedbackElement(inputElement);
        
        if (result.success) {
            feedbackElement.className = 'valid-feedback';
            feedbackElement.textContent = `✓ Archivo válido (${result.total_filas} filas, ${result.total_columnas} columnas)`;
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
        } else {
            feedbackElement.className = 'invalid-feedback';
            feedbackElement.textContent = `✗ ${result.error}`;
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
        }
    }

    getOrCreateFeedbackElement(inputElement) {
        let feedbackElement = inputElement.parentNode.querySelector('.valid-feedback, .invalid-feedback');
        
        if (!feedbackElement) {
            feedbackElement = document.createElement('div');
            feedbackElement.className = 'feedback';
            inputElement.parentNode.appendChild(feedbackElement);
        }
        
        return feedbackElement;
    }

    handleFormSubmit(event) {
        const form = event.target;
        const fileInput = form.querySelector('input[type="file"][name="archivo_excel"]');
        const focalizacionSelect = form.querySelector('select[name="focalizacion"]');
        
        // Validaciones básicas
        if (fileInput && !fileInput.files[0]) {
            event.preventDefault();
            this.showError('Por favor seleccione un archivo Excel.');
            return;
        }
        
        if (focalizacionSelect && !focalizacionSelect.value) {
            event.preventDefault();
            this.showError('Por favor seleccione una focalización.');
            return;
        }

        // Mostrar indicador de carga
        this.showLoadingIndicator(form);
    }

    handleTipoProcesamientoChange(event) {
        const tipoProcesamiento = event.target.value;
        const form = event.target.closest('form');
        const fileInput = form.querySelector('input[type="file"][name="archivo_excel"]');
        
        // Limpiar validaciones previas
        if (fileInput) {
            fileInput.classList.remove('is-valid', 'is-invalid');
            const feedbackElement = form.querySelector('.valid-feedback, .invalid-feedback');
            if (feedbackElement) {
                feedbackElement.remove();
            }
        }
        
        // Actualizar información de columnas requeridas
        this.updateColumnRequirements(tipoProcesamiento, form);
    }

    updateColumnRequirements(tipoProcesamiento, form) {
        const infoElement = form.querySelector('.column-requirements');
        if (!infoElement) return;

        const requirements = {
            'nuevo': 'LOTE, NOMBRE INSTITUCION, NOMBRE SEDE, ZONA, TIPO_DOCUMENTO, NRO_DOCUMENTO, APELLIDO1, APELLIDO2, NOMBRE1, NOMBRE2, FECHA_NACIMIENTO, GENERO, TIPO_JORNADA, GRADO, GRUPO',
            'original': 'ESTADO, SECTOR, MODELO, SEDE'
        };

        infoElement.textContent = `Columnas requeridas: ${requirements[tipoProcesamiento] || requirements['original']}`;
    }

    showLoadingIndicator(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Procesando...';
            
            // Restaurar después de 30 segundos como fallback
            setTimeout(() => {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }, 30000);
        }
    }

    showError(message) {
        // Crear o actualizar elemento de error
        let errorElement = document.querySelector('.alert-danger');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger alert-dismissible fade show';
            errorElement.innerHTML = `
                <span class="error-message"></span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.querySelector('.container').insertBefore(errorElement, document.querySelector('.container').firstChild);
        }
        
        errorElement.querySelector('.error-message').textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            if (errorElement) {
                errorElement.style.display = 'none';
            }
        }, 5000);
    }

    showSuccess(message) {
        // Crear o actualizar elemento de éxito
        let successElement = document.querySelector('.alert-success');
        if (!successElement) {
            successElement = document.createElement('div');
            successElement.className = 'alert alert-success alert-dismissible fade show';
            successElement.innerHTML = `
                <span class="success-message"></span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.querySelector('.container').insertBefore(successElement, document.querySelector('.container').firstChild);
        }
        
        successElement.querySelector('.success-message').textContent = message;
        successElement.style.display = 'block';
        
        // Auto-ocultar después de 3 segundos
        setTimeout(() => {
            if (successElement) {
                successElement.style.display = 'none';
            }
        }, 3000);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // Método para obtener estadísticas de sedes
    async getSedesEstadisticas(municipio = 'CALI') {
        try {
            const response = await fetch(`/facturacion/estadisticas-sedes/?municipio=${municipio}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo estadísticas de sedes:', error);
            throw error;
        }
    }

    // Método para mostrar estadísticas en la interfaz
    async displaySedesEstadisticas(municipio = 'CALI') {
        try {
            const result = await this.getSedesEstadisticas(municipio);
            if (result.success) {
                console.log('Estadísticas de sedes:', result.estadisticas);
                // Aquí puedes actualizar la interfaz con las estadísticas
            }
        } catch (error) {
            console.error('Error mostrando estadísticas:', error);
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.facturacionManager = new FacturacionManager();
});

// Funciones de utilidad globales
window.FacturacionUtils = {
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    validateExcelFile: function(file) {
        const validTypes = [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];
        const validExtensions = ['.xls', '.xlsx'];
        
        const isValidType = validTypes.includes(file.type);
        const isValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        
        return isValidType || isValidExtension;
    },
    
    showToast: function(message, type = 'info') {
        // Implementación simple de toast notification
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Mostrar toast
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
        
        // Remover del DOM después de 5 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
};
