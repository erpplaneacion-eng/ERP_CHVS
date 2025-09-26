/**
 * JavaScript para el módulo de facturación.
 * Maneja la validación de archivos y la interacción del usuario.
 */

// Variables globales para transferencia de grados
let sedeDestinoActual = '';
let sedeOrigenActual = '';
let etcActual = '';
let gradosSeleccionados = [];
let gradosDisponiblesData = [];

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

// ===== FUNCIONES PARA GESTIÓN DE LISTADOS FOCALIZACIÓN =====

// Funciones para gestión de listados focalización
function viewListado(idListado) {
    fetch(`/facturacion/api/listados/${idListado}/`)
        .then(response => response.json())
        .then(data => {
            let content = `
                <div class="detail-grid">
                    <div class="detail-row"><strong>ID Listado:</strong> ${data.id_listados}</div>
                    <div class="detail-row"><strong>Año:</strong> ${data.ano}</div>
                    <div class="detail-row"><strong>ETC:</strong> ${data.etc}</div>
                    <div class="detail-row"><strong>Institución:</strong> ${data.institucion}</div>
                    <div class="detail-row"><strong>Sede:</strong> ${data.sede}</div>
                    <div class="detail-row"><strong>Documento:</strong> ${data.tipodoc} ${data.doc}</div>
                    <div class="detail-row"><strong>Nombre Completo:</strong> ${data.nombre1} ${data.nombre2} ${data.apellido1} ${data.apellido2}</div>
                    <div class="detail-row"><strong>Fecha Nacimiento:</strong> ${data.fecha_nacimiento}</div>
                    <div class="detail-row"><strong>Edad:</strong> ${data.edad}</div>
                    <div class="detail-row"><strong>Género:</strong> ${data.genero}</div>
                    <div class="detail-row"><strong>Etnia:</strong> ${data.etnia || 'No especificada'}</div>
                    <div class="detail-row"><strong>Grado:</strong> ${data.grado_grupos}</div>
                    <div class="detail-row"><strong>Focalización:</strong> ${data.focalizacion}</div>
                    <div class="detail-row"><strong>Complementos Alimentarios:</strong></div>
                    <div class="detail-row">
                        <ul>
                            <li>AM: ${data.complemento_alimentario_preparado_am || 'No'}</li>
                            <li>PM: ${data.complemento_alimentario_preparado_pm || 'No'}</li>
                            <li>Almuerzo JU: ${data.almuerzo_jornada_unica || 'No'}</li>
                            <li>Refuerzo: ${data.refuerzo_complemento_am_pm || 'No'}</li>
                        </ul>
                    </div>
                </div>
            `;
            document.getElementById('detailContent').innerHTML = content;
            document.getElementById('detailModal').style.display = 'flex';
        })
        .catch(error => {
            alert('Error al cargar los detalles: ' + error);
        });
}

function editListado(idListado) {
    fetch(`/facturacion/api/listados/${idListado}/`)
        .then(response => response.json())
        .then(data => {
            // Llenar el formulario con los datos
            Object.keys(data).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = data[key] || '';
                }
            });
            document.getElementById('listadoModal').style.display = 'flex';
        })
        .catch(error => {
            alert('Error al cargar los datos para editar: ' + error);
        });
}

function saveListado() {
    const formData = new FormData(document.getElementById('listadoForm'));
    const idListado = document.getElementById('id_listados').value;
    const data = {};

    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }

    // Determinar si es creación (POST) o actualización (PUT)
    // Si el ID contiene "MANUAL_", es un nuevo registro
    const isNewRecord = idListado.startsWith('MANUAL_');
    const method = isNewRecord ? 'POST' : 'PUT';
    const url = isNewRecord ? '/facturacion/api/listados/' : `/facturacion/api/listados/${idListado}/`;

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const message = isNewRecord ? 'Registro creado exitosamente' : 'Registro actualizado exitosamente';
            alert(message);
            closeModal();
            location.reload();
        } else {
            alert('Error al guardar: ' + data.error);
        }
    })
    .catch(error => {
        alert('Error al guardar: ' + error);
    });
}

function deleteListado(idListado) {
    if (confirm('¿Está seguro de que desea eliminar este registro?')) {
        fetch(`/facturacion/api/listados/${idListado}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Registro eliminado exitosamente');
                location.reload();
            } else {
                alert('Error al eliminar: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error al eliminar: ' + error);
        });
    }
}

function closeModal() {
    document.getElementById('listadoModal').style.display = 'none';
    document.getElementById('listadoForm').reset();
}

function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Función para agregar registro desde sede faltante
function agregarRegistroDesdeSede(nombreSede, etc) {
    // Limpiar el formulario
    document.getElementById('listadoForm').reset();

    // Pre-llenar campos básicos
    document.getElementById('etc').value = etc;
    document.getElementById('sede').value = nombreSede;

    // Generar ID único para el nuevo registro
    const timestamp = Date.now();
    const randomId = Math.random().toString(36).substr(2, 5);
    const idListado = `MANUAL_${timestamp}_${randomId}`.substring(0, 50);
    document.getElementById('id_listados').value = idListado;

    // Abrir modal
    document.getElementById('listadoModal').style.display = 'flex';

    // Cambiar título del modal
    document.getElementById('modalTitle').textContent = `Agregar Registro - ${nombreSede}`;
}

// Función para transferir grados desde sede
function transferirGradosDesdeSede(nombreSede, etc, sedesDisponibles) {
    sedeDestinoActual = nombreSede;
    etcActual = etc;
    sedeOrigenActual = '';
    gradosSeleccionados = [];
    gradosDisponiblesData = sedesDisponibles || [];

    // Actualizar título
    document.getElementById('transferTitle').textContent = `Transferir grados a: ${nombreSede}`;

    // Cargar sedes disponibles en el selector
    cargarSedesOrigen(sedesDisponibles);

    // Limpiar grados disponibles inicialmente
    document.getElementById('gradosDisponibles').innerHTML = '<p class="empty-message">Selecciona una sede de origen para ver sus grados</p>';
    document.getElementById('gradosSeleccionados').innerHTML = '<p class="empty-message">Ningún grado seleccionado</p>';

    // Deshabilitar botón de transferir
    document.getElementById('transferBtn').disabled = true;

    // Abrir modal
    document.getElementById('transferModal').style.display = 'flex';
}

// Función para cargar grados disponibles
function cargarGradosDisponibles(gradosDisponibles) {

    const container = document.getElementById('gradosDisponibles');
    container.innerHTML = '';

    if (gradosDisponibles && gradosDisponibles.length > 0) {
        gradosDisponibles.forEach(nivelData => {
            const nivelDiv = document.createElement('div');
            nivelDiv.className = 'nivel-group';
            nivelDiv.innerHTML = `<h6 style="margin: 10px 0 5px 0; color: #495057;">${nivelData.nivel}</h6>`;

            nivelData.grados.forEach(grado => {
                const gradoDiv = document.createElement('div');
                gradoDiv.className = 'grado-item';
                gradoDiv.onclick = () => toggleGradoSeleccion(grado.grado);

                gradoDiv.innerHTML = `
                    <input type="checkbox" class="grado-checkbox" id="grado_${grado.grado}" value="${grado.grado}">
                    <div class="grado-info">
                        <div class="grado-nivel">Grado ${grado.grado}</div>
                        <div class="grado-detalle">${grado.descripcion}</div>
                    </div>
                `;

                nivelDiv.appendChild(gradoDiv);
            });

            container.appendChild(nivelDiv);
        });
    } else {
        container.innerHTML = '<p class="empty-message">No hay grados disponibles para transferir</p>';
    }

    actualizarGradosSeleccionados();
}

// Función para alternar selección de grado
function toggleGradoSeleccion(grado) {
    const checkbox = document.getElementById(`grado_${grado}`);
    const item = checkbox.closest('.grado-item');

    if (checkbox.checked) {
        checkbox.checked = false;
        item.classList.remove('selected');
        gradosSeleccionados = gradosSeleccionados.filter(g => g !== grado);
    } else {
        checkbox.checked = true;
        item.classList.add('selected');
        gradosSeleccionados.push(grado);
    }

    actualizarGradosSeleccionados();
}

// Función para actualizar lista de grados seleccionados
function actualizarGradosSeleccionados() {
    const container = document.getElementById('gradosSeleccionados');

    if (gradosSeleccionados.length === 0) {
        container.innerHTML = '<p class="empty-message">Ningún grado seleccionado</p>';
    } else {
        container.innerHTML = '';
        gradosSeleccionados.forEach(grado => {
            const gradoDiv = document.createElement('div');
            gradoDiv.className = 'grado-item selected';
            gradoDiv.innerHTML = `
                <div class="grado-info">
                    <div class="grado-nivel">Grado ${grado}</div>
                    <div class="grado-detalle">Listo para transferir</div>
                </div>
                <button class="transfer-btn" onclick="removerGrado('${grado}')">×</button>
            `;
            container.appendChild(gradoDiv);
        });
    }

    // Habilitar/deshabilitar botón de transferir
    document.getElementById('transferBtn').disabled = gradosSeleccionados.length === 0;
}

// Función para remover grado de la selección
function removerGrado(grado) {
    gradosSeleccionados = gradosSeleccionados.filter(g => g !== grado);
    const checkbox = document.getElementById(`grado_${grado}`);
    if (checkbox) {
        checkbox.checked = false;
        checkbox.closest('.grado-item').classList.remove('selected');
    }
    actualizarGradosSeleccionados();
}

// Función para confirmar transferencia
function confirmarTransferencia() {
    if (gradosSeleccionados.length === 0) {
        alert('Selecciona al menos un grado para transferir');
        return;
    }

    if (confirm(`¿Confirmas transferir ${gradosSeleccionados.length} grado(s) a la sede "${sedeDestinoActual}"?\n\nGrados: ${gradosSeleccionados.join(', ')}`)) {
        // Deshabilitar botón mientras procesa
        document.getElementById('transferBtn').disabled = true;
        document.getElementById('transferBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

        // Enviar petición
        fetch('/facturacion/api/transferir-grados/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                sede_destino: sedeDestinoActual,
                grados_seleccionados: gradosSeleccionados,
                etc: etcActual
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`✅ ${data.mensaje}`);
                closeTransferModal();
                location.reload(); // Recargar para ver los cambios
            } else {
                alert('❌ Error: ' + data.error);
                // Rehabilitar botón
                document.getElementById('transferBtn').disabled = false;
                document.getElementById('transferBtn').innerHTML = '<i class="fas fa-exchange-alt"></i> Transferir Grados';
            }
        })
        .catch(error => {
            alert('❌ Error de conexión: ' + error);
            // Rehabilitar botón
            document.getElementById('transferBtn').disabled = false;
            document.getElementById('transferBtn').innerHTML = '<i class="fas fa-exchange-alt"></i> Transferir Grados';
        });
    }
}

// Función para cerrar modal de transferencia
function closeTransferModal() {
    document.getElementById('transferModal').style.display = 'none';
    sedeDestinoActual = '';
    etcActual = '';
    gradosSeleccionados = [];
}

// ===== FUNCIONES PARA TRANSFERENCIA DE GRADOS =====

// Función para transferir grados desde sede
function transferirGradosDesdeSede(nombreSede, etc, sedesDisponibles) {
    sedeDestinoActual = nombreSede;
    etcActual = etc;
    sedeOrigenActual = '';
    gradosSeleccionados = [];
    gradosDisponiblesData = sedesDisponibles || [];

    // Actualizar título
    document.getElementById('transferTitle').textContent = `Transferir grados a: ${nombreSede}`;

    // Cargar sedes disponibles en el selector
    cargarSedesOrigen(sedesDisponibles);

    // Limpiar grados disponibles inicialmente
    document.getElementById('gradosDisponibles').innerHTML = '<p class="empty-message">Selecciona una sede de origen para ver sus grados</p>';
    document.getElementById('gradosSeleccionados').innerHTML = '<p class="empty-message">Ningún grado seleccionado</p>';

    // Deshabilitar botón de transferir
    document.getElementById('transferBtn').disabled = true;

    // Abrir modal
    document.getElementById('transferModal').style.display = 'flex';
}

// Función para cargar sedes disponibles en el selector
function cargarSedesOrigen(sedesDisponibles) {
    const select = document.getElementById('sedeOrigen');
    select.innerHTML = '<option value="">Selecciona una sede...</option>';

    if (sedesDisponibles && sedesDisponibles.length > 0) {
        sedesDisponibles.forEach(sedeData => {
            const option = document.createElement('option');
            option.value = sedeData.sede;
            option.textContent = `${sedeData.sede} (${sedeData.total_grados} grados)`;
            select.appendChild(option);
        });
    }
}

// Función para cambiar sede de origen
function cambiarSedeOrigen() {
    const select = document.getElementById('sedeOrigen');
    sedeOrigenActual = select.value;
    gradosSeleccionados = [];

    if (sedeOrigenActual) {
        // Buscar los grados de la sede seleccionada
        const sedeSeleccionada = gradosDisponiblesData.find(s => s.sede === sedeOrigenActual);
        if (sedeSeleccionada) {
            cargarGradosDisponibles(sedeSeleccionada.grados);
        }
    } else {
        // Limpiar grados si no hay sede seleccionada
        document.getElementById('gradosDisponibles').innerHTML = '<p class="empty-message">Selecciona una sede de origen para ver sus grados</p>';
        document.getElementById('gradosSeleccionados').innerHTML = '<p class="empty-message">Ningún grado seleccionado</p>';
        document.getElementById('transferBtn').disabled = true;
    }
}

// Función para cargar grados disponibles
function cargarGradosDisponibles(gradosDisponibles) {
    const container = document.getElementById('gradosDisponibles');
    container.innerHTML = '';

    if (gradosDisponibles && gradosDisponibles.length > 0) {
        gradosDisponibles.forEach(nivelData => {
            const nivelDiv = document.createElement('div');
            nivelDiv.className = 'nivel-group';
            nivelDiv.innerHTML = `<h6 style="margin: 10px 0 5px 0; color: #495057;">${nivelData.nivel}</h6>`;

            nivelData.grados.forEach(grado => {
                const gradoDiv = document.createElement('div');
                gradoDiv.className = 'grado-item';
                gradoDiv.onclick = () => toggleGradoSeleccion(grado.grado);

                gradoDiv.innerHTML = `
                    <input type="checkbox" class="grado-checkbox" id="grado_${grado.grado}" value="${grado.grado}">
                    <div class="grado-info">
                        <div class="grado-nivel">Grado ${grado.grado}</div>
                        <div class="grado-detalle">${grado.descripcion}</div>
                    </div>
                `;

                nivelDiv.appendChild(gradoDiv);
            });

            container.appendChild(nivelDiv);
        });
    } else {
        container.innerHTML = '<p class="empty-message">Esta sede no tiene grados disponibles</p>';
    }

    actualizarGradosSeleccionados();
}

// Función para alternar selección de grado
function toggleGradoSeleccion(grado) {
    const checkbox = document.getElementById(`grado_${grado}`);
    const item = checkbox.closest('.grado-item');

    if (checkbox.checked) {
        checkbox.checked = false;
        item.classList.remove('selected');
        gradosSeleccionados = gradosSeleccionados.filter(g => g !== grado);
    } else {
        checkbox.checked = true;
        item.classList.add('selected');
        gradosSeleccionados.push(grado);
    }

    actualizarGradosSeleccionados();
}

// Función para actualizar lista de grados seleccionados
function actualizarGradosSeleccionados() {
    const container = document.getElementById('gradosSeleccionados');

    if (gradosSeleccionados.length === 0) {
        container.innerHTML = '<p class="empty-message">Ningún grado seleccionado</p>';
    } else {
        container.innerHTML = '';
        gradosSeleccionados.forEach(grado => {
            const gradoDiv = document.createElement('div');
            gradoDiv.className = 'grado-item selected';
            gradoDiv.innerHTML = `
                <div class="grado-info">
                    <div class="grado-nivel">Grado ${grado}</div>
                    <div class="grado-detalle">Listo para transferir</div>
                </div>
                <button class="transfer-btn" onclick="removerGrado('${grado}')">×</button>
            `;
            container.appendChild(gradoDiv);
        });
    }

    // Habilitar/deshabilitar botón de transferir
    document.getElementById('transferBtn').disabled = gradosSeleccionados.length === 0;
}

// Función para remover grado de la selección
function removerGrado(grado) {
    gradosSeleccionados = gradosSeleccionados.filter(g => g !== grado);
    const checkbox = document.getElementById(`grado_${grado}`);
    if (checkbox) {
        checkbox.checked = false;
        checkbox.closest('.grado-item').classList.remove('selected');
    }
    actualizarGradosSeleccionados();
}

// Función para confirmar transferencia
function confirmarTransferencia() {
    if (!sedeOrigenActual) {
        alert('Selecciona una sede de origen');
        return;
    }

    if (gradosSeleccionados.length === 0) {
        alert('Selecciona al menos un grado para transferir');
        return;
    }

    if (confirm(`¿Confirmas transferir ${gradosSeleccionados.length} grado(s) desde "${sedeOrigenActual}" a "${sedeDestinoActual}"?\n\nGrados: ${gradosSeleccionados.join(', ')}`)) {
        // Deshabilitar botón mientras procesa
        document.getElementById('transferBtn').disabled = true;
        document.getElementById('transferBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

        // Enviar petición
        fetch('/facturacion/api/transferir-grados/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                sede_destino: sedeDestinoActual,
                sede_origen: sedeOrigenActual,
                grados_seleccionados: gradosSeleccionados,
                etc: etcActual
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`✅ ${data.mensaje}`);
                closeTransferModal();
                location.reload(); // Recargar para ver los cambios
            } else {
                alert('❌ Error: ' + data.error);
                // Rehabilitar botón
                document.getElementById('transferBtn').disabled = false;
                document.getElementById('transferBtn').innerHTML = '<i class="fas fa-exchange-alt"></i> Transferir Grados';
            }
        })
        .catch(error => {
            alert('❌ Error de conexión: ' + error);
            // Rehabilitar botón
            document.getElementById('transferBtn').disabled = false;
            document.getElementById('transferBtn').innerHTML = '<i class="fas fa-exchange-alt"></i> Transferir Grados';
        });
    }
}

// Función para cerrar modal de transferencia
function closeTransferModal() {
    document.getElementById('transferModal').style.display = 'none';
    sedeDestinoActual = '';
    sedeOrigenActual = '';
    etcActual = '';
    gradosSeleccionados = [];
    gradosDisponiblesData = [];
}

// Funcionalidad de búsqueda
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#listadosTable tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const isVisible = text.includes(searchTerm);
                row.style.display = isVisible ? '' : 'none';
                if (isVisible) visibleCount++;
            });

            document.getElementById('searchResultsCount').textContent =
                searchTerm ? `Mostrando ${visibleCount} de ${rows.length} registros` : 'Mostrando todos los registros';

            // Mostrar/ocultar botón de limpiar
            if (clearSearchBtn) {
                if (searchTerm) {
                    clearSearchBtn.classList.add('show');
                } else {
                    clearSearchBtn.classList.remove('show');
                }
            }
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchInput) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        });
    }
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
