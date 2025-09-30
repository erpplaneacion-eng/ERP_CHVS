/**
 * JavaScript para procesamiento OCR de PDFs
 */

class OCRProcessor {
    constructor() {
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.form = document.getElementById('pdfUploadForm');
        this.fileInput = document.getElementById('archivo_pdf');
        this.procesarBtn = document.getElementById('procesarBtn');
        this.processingSection = document.getElementById('processingSection');
        this.resultsSection = document.getElementById('resultsSection');
        this.errorsSection = document.getElementById('errorsSection');
        this.progressBar = document.getElementById('progressBar');
        this.processingStatus = document.getElementById('processingStatus');
        this.verDetallesBtn = document.getElementById('verDetallesBtn');
    }

    bindEvents() {
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        }

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
    }

    handleFileSelection(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validar tipo de archivo
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            this.showError('Por favor seleccione un archivo PDF válido');
            return;
        }

        // Validar tamaño (10MB máximo)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('El archivo es demasiado grande. Máximo 10MB permitido');
            return;
        }

        // Mostrar información del archivo
        this.showFilePreview(file);
    }

    showFilePreview(file) {
        const previewNombre = document.getElementById('preview-nombre');
        const previewTamano = document.getElementById('preview-tamano');
        const previewSede = document.getElementById('preview-sede');
        const previewMes = document.getElementById('preview-mes');
        const uploadPreview = document.getElementById('uploadPreview');

        if (previewNombre) previewNombre.textContent = file.name;
        if (previewTamano) previewTamano.textContent = this.formatFileSize(file.size);

        // Extraer información del nombre del archivo
        const fileInfo = this.parseFileName(file.name);
        if (previewSede) previewSede.textContent = fileInfo.sede || 'No detectada';
        if (previewMes) previewMes.textContent = fileInfo.mes || 'No detectado';

        if (uploadPreview) {
            uploadPreview.style.display = 'block';
        }
    }

    parseFileName(fileName) {
        // Ejemplo: "Asistencia_Sede_Educativa_CAJMPS_OCTUBRE_2025.pdf"
        const parts = fileName.replace('.pdf', '').split('_');
        return {
            sede: parts[1] || null,
            complemento: parts[2] || null,
            mes: parts[3] || null,
            ano: parts[4] || null
        };
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async handleFormSubmit(event) {
        event.preventDefault();

        console.log('📤 Iniciando envío de formulario OCR...');
        const formData = new FormData(this.form);

        // Verificar que hay un archivo
        const archivo = formData.get('archivo_pdf');
        if (!archivo) {
            console.error('❌ No se encontró archivo en FormData');
            this.showErrorSection('No se seleccionó ningún archivo');
            return;
        }
        console.log('📄 Archivo a enviar:', archivo.name, 'Tamaño:', archivo.size);

        try {
            // Mostrar sección de procesamiento
            this.showProcessingSection();

            // Actualizar progreso
            this.updateProgress(10, 'Iniciando procesamiento...');

            console.log('🌐 Enviando petición a: /ocr_validation/procesar/');

            // Enviar archivo para procesamiento
            const response = await fetch('/ocr_validation/procesar/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            console.log('📥 Respuesta recibida. Status:', response.status, response.statusText);

            // Verificar si la respuesta es JSON
            const contentType = response.headers.get('content-type');
            console.log('📋 Content-Type:', contentType);

            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('❌ Respuesta no es JSON:', text.substring(0, 500));
                this.showErrorSection('Error: El servidor no devolvió una respuesta JSON válida');
                return;
            }

            const result = await response.json();
            console.log('✅ Resultado parseado:', result);

            if (result.success) {
                console.log('🎉 Procesamiento exitoso');
                this.updateProgress(100, 'Procesamiento completado');
                this.showResultsSection(result);
            } else {
                console.error('❌ Error en procesamiento:', result.error);
                this.showErrorSection(result.error);
            }

        } catch (error) {
            console.error('💥 Error capturado:', error);
            console.error('Stack trace:', error.stack);
            this.showErrorSection('Error interno del servidor: ' + error.message);
        }
    }

    showProcessingSection() {
        if (this.processingSection) {
            this.processingSection.style.display = 'block';
        }

        // Ocultar otras secciones
        this.hideSections(['resultsSection', 'errorsSection']);
    }

    hideSections(sectionIds) {
        sectionIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.style.display = 'none';
            }
        });
    }

    updateProgress(percentage, status) {
        if (this.progressBar) {
            this.progressBar.style.width = percentage + '%';
            this.progressBar.textContent = percentage + '%';
        }

        if (this.processingStatus) {
            this.processingStatus.innerHTML = `<p>${status}</p>`;
        }
    }

    showResultsSection(result) {
        // Ocultar procesamiento
        if (this.processingSection) {
            this.processingSection.style.display = 'none';
        }

        // Mostrar resultados
        if (this.resultsSection) {
            this.resultsSection.style.display = 'block';

            // Actualizar información del resumen
            this.updateResultsSummary(result);

            // Configurar botón de detalles
            if (this.verDetallesBtn) {
                this.verDetallesBtn.href = result.redirect_url;
            }
        }

        // Mostrar errores si existen
        if (result.total_errores > 0) {
            this.showErrorsSection(result);
        }
    }

    updateResultsSummary(result) {
        const summaryArchivo = document.getElementById('summary-archivo');
        const summaryErrores = document.getElementById('summary-errores');
        const summaryTiempo = document.getElementById('summary-tiempo');
        const summaryIconErrores = document.getElementById('summary-icon-errores');

        if (summaryArchivo) {
            summaryArchivo.textContent = this.fileInput.files[0].name;
        }

        if (summaryErrores) {
            const erroresText = result.total_errores > 0 ?
                `${result.total_errores} errores encontrados` :
                'Sin errores detectados';
            summaryErrores.textContent = erroresText;
        }

        if (summaryTiempo) {
            summaryTiempo.textContent = `${result.tiempo_procesamiento.toFixed(2)} segundos`;
        }

        if (summaryIconErrores) {
            if (result.total_errores > 0) {
                summaryIconErrores.className = 'summary-icon error';
                summaryIconErrores.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            } else {
                summaryIconErrores.className = 'summary-icon success';
                summaryIconErrores.innerHTML = '<i class="fas fa-check-circle"></i>';
            }
        }
    }

    showErrorsSection(result) {
        if (this.errorsSection) {
            this.errorsSection.style.display = 'block';

            // Crear preview de errores
            const errorsPreview = document.getElementById('errorsPreview');
            if (errorsPreview) {
                errorsPreview.innerHTML = this.generateErrorsPreview(result);
            }
        }
    }

    generateErrorsPreview(result) {
        let html = `
            <div class="alert alert-info">
                <h6><i class="fas fa-search"></i> Análisis de Errores Detectados</h6>
                <p>El sistema ha identificado posibles problemas en el documento:</p>
            </div>

            <div class="errors-summary">
                <div class="error-category">
                    <h6>Campos que se Validan:</h6>
                    <ul>
                        <li><strong>Raciones Diarias/Mensuales:</strong> Validación numérica y lógica</li>
                        <li><strong>Firmas:</strong> Detección de presencia de firmas legibles</li>
                        <li><strong>Casillas de Asistencia:</strong> Detección de posición correcta de "X"</li>
                        <li><strong>Totales:</strong> Verificación de cálculos matemáticos</li>
                    </ul>
                </div>

                <div class="error-category">
                    <h6>Tipos de Errores Detectados:</h6>
                    <div class="error-types">
                        <span class="badge badge-danger">Campos Obligatorios Vacíos</span>
                        <span class="badge badge-warning">Formatos Incorrectos</span>
                        <span class="badge badge-warning">Inconsistencias Lógicas</span>
                        <span class="badge badge-warning">Firmas Faltantes</span>
                        <span class="badge badge-info">Datos Ilegibles</span>
                    </div>
                </div>
            </div>
        `;

        return html;
    }

    showErrorSection(errorMessage) {
        if (this.processingSection) {
            this.processingSection.style.display = 'none';
        }

        // Crear sección de error dinámica
        const errorSection = document.createElement('div');
        errorSection.className = 'error-section';
        errorSection.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="fas fa-exclamation-circle"></i> Error en el Procesamiento</h5>
                <p>${errorMessage}</p>
                <button class="btn btn-primary" onclick="procesarOtroArchivo()">
                    <i class="fas fa-redo"></i> Intentar de Nuevo
                </button>
            </div>
        `;

        // Insertar después de la sección de procesamiento
        if (this.processingSection) {
            this.processingSection.parentNode.insertBefore(errorSection, this.processingSection.nextSibling);
        }
    }

    showError(message) {
        // Crear notificación de error temporal
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insertar al inicio del formulario
        const form = document.getElementById('pdfUploadForm');
        if (form) {
            form.insertBefore(errorDiv, form.firstChild);

            // Remover después de 5 segundos
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.remove();
                }
            }, 5000);
        }
    }
}

// Funciones globales
function limpiarFormulario() {
    const form = document.getElementById('pdfUploadForm');
    if (form) {
        form.reset();
    }

    // Ocultar preview
    const uploadPreview = document.getElementById('uploadPreview');
    if (uploadPreview) {
        uploadPreview.style.display = 'none';
    }

    // Ocultar otras secciones
    const sectionsToHide = ['processingSection', 'resultsSection', 'errorsSection'];
    sectionsToHide.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = 'none';
        }
    });
}

function procesarOtroArchivo() {
    limpiarFormulario();

    // Scroll al formulario
    const uploadSection = document.querySelector('.upload-section');
    if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.ocrProcessor = new OCRProcessor();
    console.log('✅ OCRProcessor initialized and available as window.ocrProcessor');
});