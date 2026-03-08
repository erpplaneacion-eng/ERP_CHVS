// alimentos.js - Funcionalidad para gestión de alimentos ICBF

class AlimentosManager {
    // Constructor: define estado de UI y arranca la inicialización del módulo.
    constructor() {
        this.modal = null;
        this.modalTitle = null;
        this.alimentoForm = null;
        this.submitBtn = null;
        this.validationSummary = null;
        this.macroBalanceIndicator = null;
        this.isEditing = false;
        this.currentSearchTerm = '';
        this.init();
    }

    // Inicializa referencias del DOM y activa listeners, validaciones y búsqueda.
    init() {
        // Inicializar elementos del DOM
        this.modal = document.getElementById('alimento-modal');
        this.modalTitle = document.getElementById('modal-title');
        this.alimentoForm = document.getElementById('alimento-form');
        this.submitBtn = document.getElementById('modal-submit-btn');
        this.validationSummary = document.getElementById('formValidationSummary');
        this.macroBalanceIndicator = document.getElementById('macroBalanceIndicator');

        if (!this.modal || !this.alimentoForm) {
            console.warn('AlimentosManager: Elementos del modal no encontrados');
            return;
        }

        this.setupEventListeners();
        this.setupValidations();
        this.setupSearch();
    }

    // Conecta eventos de botones, modales y teclado para todo el ciclo CRUD.
    setupEventListeners() {
        // Botón añadir alimento
        const addBtn = document.getElementById('add-alimento-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showCreateModal());
        }

        // Botones de ver detalles
        const viewBtns = document.querySelectorAll('.view-alimento-btn');
        viewBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const button = e.target.closest('.view-alimento-btn');
                this.showDetailModal(button);
            });
        });

        // Botones de editar
        const editBtns = document.querySelectorAll('.edit-alimento-btn');
        editBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const button = e.target.closest('.edit-alimento-btn');
                this.showEditModal(button);
            });
        });

        // Botones de eliminar
        const deleteBtns = document.querySelectorAll('.delete-alimento-btn');
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const button = e.target.closest('.delete-alimento-btn');
                this.deleteAlimento(button);
            });
        });

        // Botones de cerrar del modal principal (crear/editar)
        const closeBtns = this.modal.querySelectorAll('.modal-close-btn, .modal-cancel-btn');
        closeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Cerrar modal al hacer click fuera
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Cerrar modal de detalles al hacer click fuera
        const detailModal = document.getElementById('detailModal');
        if (detailModal) {
            detailModal.addEventListener('click', (e) => {
                if (e.target === detailModal) {
                    this.closeDetailModal();
                }
            });
        }

        // Botones de cierre del modal de detalle (X y botón "Cancelar")
        if (detailModal) {
            detailModal.querySelectorAll('.modal-close-btn, .modal-cancel-btn, .modal-detail-close-btn').forEach(btn => {
                btn.addEventListener('click', () => this.closeDetailModal());
            });
        }

        // Cerrar modal con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.modal.style.display === 'flex') {
                    this.closeModal();
                }
                const detailModal = document.getElementById('detailModal');
                if (detailModal && detailModal.style.display === 'flex') {
                    this.closeDetailModal();
                }
            }
        });

        // ⭐ IMPORTANTE: Interceptar el submit del formulario
        // Convertir punto a coma antes de enviar (Django espera coma con locale español)
        this.alimentoForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }

    // Configura validaciones de campos (formato de código y rangos numéricos).
    setupValidations() {
        if (!this.alimentoForm) return;

        // Validar código - convertir a mayúsculas y filtrar caracteres
        const codigoInput = this.alimentoForm.querySelector('#id_codigo');
        if (codigoInput) {
            codigoInput.addEventListener('input', function() {
                this.value = this.value.toUpperCase().replace(/[^A-Z0-9\\-_]/g, '');
            });
        }

        // Validar números positivos para campos numéricos
        const numericInputs = this.alimentoForm.querySelectorAll('input[type="number"]');
        numericInputs.forEach(input => {
            input.addEventListener('input', () => {
                if (parseFloat(input.value) < 0) {
                    input.value = '';
                    input.style.borderColor = '#e74c3c';
                } else {
                    input.style.borderColor = '#ced4da';
                }
                this.validateNumericField(input);
                this.runFormValidation();
            });

            // Validar límites específicos según el campo
            input.addEventListener('blur', (e) => {
                this.validateNumericField(e.target);
                this.runFormValidation();
            });
        });

        // Revalidar también cuando cambian campos no numéricos requeridos.
        const requiredTextInputs = this.alimentoForm.querySelectorAll('input[required]:not([type="number"]), select[required], textarea[required]');
        requiredTextInputs.forEach(input => {
            input.addEventListener('input', () => this.runFormValidation());
            input.addEventListener('change', () => this.runFormValidation());
        });
    }

    // Valida límites esperados por campo numérico y muestra error contextual.
    validateNumericField(input) {
        const fieldName = input.name;
        const rawValue = (input.value || '').trim();

        // Si el campo está vacío, limpiamos estado visual y dejamos que el
        // navegador resuelva la validación de required según corresponda.
        if (rawValue === '') {
            input.style.borderColor = '#ced4da';
            this.removeFieldError(input);
            return true;
        }

        const value = parseFloat(rawValue);
        if (Number.isNaN(value)) {
            input.style.borderColor = '#e74c3c';
            this.showFieldError(input, 'Ingresa un número válido.');
            return false;
        }

        let maxValue = null;
        const fieldLimits = {
            'humedad_g': 100,
            'proteina_g': 100,
            'lipidos_g': 100,
            'carbohidratos_totales_g': 100,
            'carbohidratos_disponibles_g': 100,
            'energia_kcal': 900,
            'energia_kj': 3800,
            'fibra_dietaria_g': 50,
            'cenizas_g': 20,
            'calcio_mg': 2000,
            'hierro_mg': 50,
            'vitamina_c_mg': 1000,
            'parte_comestible_field': 100,
            'factor_coccion': 10
        };

        maxValue = fieldLimits[fieldName];

        if (maxValue && value > maxValue) {
            input.style.borderColor = '#e74c3c';
            this.showFieldError(input, `El valor máximo para ${fieldName} es ${maxValue}`);
            return false;
        } else {
            input.style.borderColor = '#ced4da';
            this.removeFieldError(input);
            return true;
        }
    }

    // Inserta un mensaje de error temporal junto al input.
    showFieldError(input, message) {
        // Remover error anterior
        this.removeFieldError(input);

        // Crear nuevo mensaje de error
        const errorSpan = document.createElement('span');
        errorSpan.classList.add('error-message');
        errorSpan.style.color = '#e74c3c';
        errorSpan.style.fontSize = '0.8em';
        errorSpan.style.marginTop = '4px';
        errorSpan.textContent = message;

        input.parentNode.appendChild(errorSpan);

        // Auto-remover después de 3 segundos
        setTimeout(() => {
            this.removeFieldError(input);
        }, 3000);
    }

    // Elimina el mensaje de error visual asociado a un campo.
    removeFieldError(input) {
        const errorSpan = input.parentNode.querySelector('.error-message');
        if (errorSpan) {
            errorSpan.remove();
        }
    }

    // Prepara y abre el modal en modo creación.
    showCreateModal() {
        this.isEditing = false;
        this.clearForm();
        this.modalTitle.textContent = 'Añadir Nuevo Alimento';
        this.submitBtn.textContent = 'Guardar Alimento';

        // Habilitar código para nuevo alimento
        const codigoInput = document.getElementById('id_codigo');
        if (codigoInput) {
            codigoInput.readOnly = false;
            codigoInput.style.backgroundColor = '';
            codigoInput.style.cursor = '';
        }

        this.openModal();
        this.runFormValidation();
    }

    // Prepara y abre el modal en modo edición usando data-* de la fila.
    showEditModal(button) {
        this.isEditing = true;
        const data = button.dataset;

        this.clearForm();
        this.modalTitle.textContent = 'Editar Alimento';
        this.submitBtn.textContent = 'Actualizar Alimento';

        // Cambiar action del formulario para edición
        const codigo = data.codigo;
        this.alimentoForm.action = `/nutricion/alimentos/editar/${codigo}/`;

        // Poblar formulario con datos existentes
        this.populateForm(data);

        // IMPORTANTE: Usar readonly en lugar de disabled
        // disabled NO envía el valor en el POST
        // readonly sí envía el valor pero no permite edición
        const codigoInput = document.getElementById('id_codigo');
        if (codigoInput) {
            codigoInput.readOnly = true;
            codigoInput.style.backgroundColor = '#e9ecef';
            codigoInput.style.cursor = 'not-allowed';
        }

        this.openModal();
        this.runFormValidation();
    }

    // Mapea dataset -> inputs del formulario para cargar datos existentes.
    populateForm(data) {
        // Mapeo directo: data-attribute en HTML → ID del input en el formulario
        const fieldMappings = {
            'codigo': 'id_codigo',
            'nombre': 'id_nombre_del_alimento',
            'parteAnalizada': 'id_parte_analizada',
            'idComponente': 'id_id_componente',
            'humedad': 'id_humedad_g',
            'energiaKcal': 'id_energia_kcal',
            'energiaKj': 'id_energia_kj',
            'proteina': 'id_proteina_g',
            'lipidos': 'id_lipidos_g',
            'carbohidratosTotales': 'id_carbohidratos_totales_g',
            'carbohidratosDisponibles': 'id_carbohidratos_disponibles_g',
            'fibraDietaria': 'id_fibra_dietaria_g',
            'cenizas': 'id_cenizas_g',
            'calcio': 'id_calcio_mg',
            'hierro': 'id_hierro_mg',
            'sodio': 'id_sodio_mg',
            'fosforo': 'id_fosforo_mg',
            'yodo': 'id_yodo_mg',
            'zinc': 'id_zinc_mg',
            'magnesio': 'id_magnesio_mg',
            'potasio': 'id_potasio_mg',
            'tiamina': 'id_tiamina_mg',
            'riboflavina': 'id_riboflavina_mg',
            'niacina': 'id_niacina_mg',
            'folatos': 'id_folatos_mcg',
            'vitaminaB12': 'id_vitamina_b12_mcg',
            'vitaminaC': 'id_vitamina_c_mg',
            'vitaminaA': 'id_vitamina_a_er',
            'grasaSaturada': 'id_grasa_saturada_g',
            'grasaMonoinsaturada': 'id_grasa_monoinsaturada_g',
            'grasaPoliinsaturada': 'id_grasa_poliinsaturada_g',
            'colesterol': 'id_colesterol_mg',
            'parteComestible': 'id_parte_comestible_field',
            'factorCoccion': 'id_factor_coccion'
        };

        console.log('🔍 DEBUG: Poblando formulario...');
        console.log('📦 Dataset completo:', data);

        // Iterar sobre el mapeo y poblar cada campo
        for (const [dataKey, elementId] of Object.entries(fieldMappings)) {
            const element = document.getElementById(elementId);
            const value = data[dataKey];

            if (!element) {
                console.warn(`⚠️ Elemento no encontrado: ${elementId}`);
                continue;
            }

            // Verificar si el valor existe y no está vacío
            // Nota: Permitimos 0 como valor válido para campos numéricos
            if (value !== undefined && value !== null && value !== '') {
                // Los valores ya vienen con punto decimal (formato estándar)
                // gracias a {% localize off %} en el template
                element.value = value;
                console.log(`✅ ${dataKey} → ${elementId}: "${value}"`);
            } else if (value === '0' || value === 0) {
                // Caso especial: 0 es un valor válido
                element.value = '0';
                console.log(`✅ ${dataKey} → ${elementId}: "0"`);
            } else {
                // Limpiar el campo si no hay valor (undefined, null o string vacío)
                element.value = '';
                console.log(`⭕ ${dataKey} → ${elementId}: (vacío)`);
            }
        }

        console.log('✨ Formulario poblado completamente');
    }

    // Restablece formulario, estilos y estado base del modal.
    clearForm() {
        this.alimentoForm.reset();

        // Resetear action del formulario
        const baseUrl = window.location.pathname;
        this.alimentoForm.action = baseUrl;

        // Limpiar errores de validación
        const errorMessages = this.alimentoForm.querySelectorAll('.error-message');
        errorMessages.forEach(error => error.remove());

        // Resetear estilos de border
        const inputs = this.alimentoForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.style.borderColor = '#ced4da';
        });

        // Resetear campo código a editable
        const codigoInput = document.getElementById('id_codigo');
        if (codigoInput) {
            codigoInput.readOnly = false;
            codigoInput.style.backgroundColor = '';
            codigoInput.style.cursor = '';
        }

        if (this.validationSummary) {
            this.validationSummary.style.display = 'none';
            this.validationSummary.innerHTML = '';
        }
        if (this.macroBalanceIndicator) {
            this.macroBalanceIndicator.style.display = 'none';
            this.macroBalanceIndicator.innerHTML = '';
        }
    }

    // Abre modal principal y bloquea scroll de fondo.
    openModal() {
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Focus en el primer campo
        const firstInput = this.alimentoForm.querySelector('input:not([disabled])');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    // Cierra modal principal, restaura scroll y limpia formulario.
    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.clearForm();
    }

    getNumericFieldValue(fieldId) {
        const el = document.getElementById(fieldId);
        if (!el) return 0;
        const raw = (el.value || '').trim();
        if (!raw) return 0;
        const parsed = parseFloat(raw);
        return Number.isNaN(parsed) ? 0 : parsed;
    }

    validateMacronutrientBalance() {
        const proteina = this.getNumericFieldValue('id_proteina_g');
        const lipidos = this.getNumericFieldValue('id_lipidos_g');
        const carbohidratos = this.getNumericFieldValue('id_carbohidratos_totales_g');
        const humedad = this.getNumericFieldValue('id_humedad_g');
        const cenizas = this.getNumericFieldValue('id_cenizas_g');
        const suma = proteina + lipidos + carbohidratos + humedad + cenizas;
        const limite = 105;
        const esValido = suma <= limite;

        if (this.macroBalanceIndicator) {
            this.macroBalanceIndicator.style.display = 'block';
            this.macroBalanceIndicator.style.borderColor = esValido ? '#b7e4c7' : '#f5c2c7';
            this.macroBalanceIndicator.style.background = esValido ? '#f3fff6' : '#fff5f5';
            this.macroBalanceIndicator.style.color = esValido ? '#1e6b36' : '#842029';
            this.macroBalanceIndicator.innerHTML = `Suma componentes principales: <strong>${suma.toFixed(2)}</strong>/105 (proteína + lípidos + carbohidratos + humedad + cenizas)`;
        }

        return {
            isValid: esValido,
            message: esValido ? '' : 'La suma de proteína + lípidos + carbohidratos + humedad + cenizas no puede exceder 105.'
        };
    }

    renderValidationSummary(errors) {
        if (!this.validationSummary) return;

        if (!errors.length) {
            this.validationSummary.style.display = 'none';
            this.validationSummary.innerHTML = '';
            return;
        }

        const items = errors.map(err => `<li>${err}</li>`).join('');
        this.validationSummary.innerHTML = `<strong>Corrige lo siguiente antes de guardar:</strong><ul style="margin:8px 0 0 18px; padding:0;">${items}</ul>`;
        this.validationSummary.style.display = 'block';
    }

    runFormValidation() {
        const errors = [];
        const numericInputs = this.alimentoForm.querySelectorAll('input[type="number"]');
        let hasNumericErrors = false;

        numericInputs.forEach(input => {
            const isValid = this.validateNumericField(input);
            if (!isValid) {
                hasNumericErrors = true;
            }
        });

        const balance = this.validateMacronutrientBalance();
        if (!balance.isValid) {
            errors.push(balance.message);
        }

        const requiredFields = [
            { id: 'id_codigo', name: 'Código' },
            { id: 'id_nombre_del_alimento', name: 'Nombre del alimento' },
            { id: 'id_humedad_g', name: 'Humedad (g)' },
            { id: 'id_energia_kcal', name: 'Energía (kcal)' },
            { id: 'id_energia_kj', name: 'Energía (kJ)' },
            { id: 'id_proteina_g', name: 'Proteína (g)' },
            { id: 'id_lipidos_g', name: 'Lípidos (g)' },
            { id: 'id_carbohidratos_totales_g', name: 'Carbohidratos Totales (g)' }
        ];

        const missingRequired = requiredFields
            .filter(f => {
                const el = document.getElementById(f.id);
                return el && !(el.value || '').trim();
            })
            .map(f => `Campo requerido: ${f.name}`);

        errors.push(...missingRequired);
        if (hasNumericErrors && !errors.includes('Hay valores fuera de rango.')) {
            errors.unshift('Hay valores fuera de rango.');
        }

        this.renderValidationSummary(errors);
        if (this.submitBtn) {
            const isValid = errors.length === 0;
            this.submitBtn.disabled = !isValid;
            this.submitBtn.title = isValid ? '' : 'Corrige las validaciones antes de guardar.';
        }

        return errors.length === 0;
    }

    markServerErrors(errorsByField = {}) {
        if (!errorsByField || typeof errorsByField !== 'object') return;

        const summaryErrors = [];
        Object.entries(errorsByField).forEach(([field, messages]) => {
            if (field !== '__all__') {
                const input = document.getElementById(`id_${field}`);
                if (input) {
                    input.style.borderColor = '#e74c3c';
                    if (Array.isArray(messages) && messages.length) {
                        this.showFieldError(input, messages[0]);
                    }
                }
            }
            if (Array.isArray(messages)) {
                summaryErrors.push(...messages);
            }
        });

        if (summaryErrors.length) {
            this.renderValidationSummary(summaryErrors);
        }
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        console.log('📤 Preparando envío del formulario...');

        // ESTRATEGIA: Mantener los valores con PUNTO (formato estándar)
        // Los inputs type="number" ya tienen el formato correcto
        // Solo necesitamos asegurar que no haya problemas de envío

        const clientValid = this.runFormValidation();
        if (!clientValid) {
            console.error('❌ El formulario tiene errores de validación.');
            return;
        }

        const formData = new FormData(this.alimentoForm);
        const submitOriginal = this.submitBtn ? this.submitBtn.innerHTML : '';
        if (this.submitBtn) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = 'Guardando...';
        }

        try {
            const response = await fetch(this.alimentoForm.action || window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                this.markServerErrors(data.errors || {});
                if (typeof Swal !== 'undefined') {
                    Swal.fire('No se guardó', data.message || 'Hay validaciones pendientes.', 'warning');
                } else {
                    alert(data.message || 'No se pudo guardar el alimento.');
                }
                this.runFormValidation();
                return;
            }

            if (typeof Swal !== 'undefined') {
                await Swal.fire('Éxito', data.message || 'Alimento guardado correctamente.', 'success');
            }
            window.location.reload();
        } catch (error) {
            console.error('Error al guardar alimento:', error);
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', 'Error de conexión al guardar el alimento.', 'error');
            } else {
                alert('Error de conexión al guardar el alimento.');
            }
        } finally {
            if (this.submitBtn) {
                this.submitBtn.disabled = false;
                this.submitBtn.innerHTML = submitOriginal || (this.isEditing ? 'Actualizar Alimento' : 'Guardar Alimento');
            }
        }
    }

    // Función para validar formulario antes de enviar
    validateForm() {
        const requiredFields = ['id_codigo', 'id_nombre_del_alimento'];
        let isValid = true;

        requiredFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && !field.value.trim()) {
                field.style.borderColor = '#e74c3c';
                this.showFieldError(field, 'Este campo es obligatorio');
                isValid = false;
            }
        });

        return isValid;
    }

    // =====================================
    // FUNCIONALIDAD DE VER DETALLES
    // =====================================

    // Construye y muestra el modal de detalle en modo solo lectura.
    showDetailModal(button) {
        const data = button.dataset;
        const detailContent = document.getElementById('detailContent');

        if (!detailContent) return;

        detailContent.innerHTML = `
            <div class="detail-grid">
                <div class="detail-section">
                    <h4>Información Básica</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <label>Código:</label>
                            <span>${data.codigo}</span>
                        </div>
                        <div class="detail-item">
                            <label>Nombre:</label>
                            <span>${data.nombre}</span>
                        </div>
                        <div class="detail-item">
                            <label>Parte Analizada:</label>
                            <span>${data.parteAnalizada}</span>
                        </div>
                        <div class="detail-item">
                            <label>Componente:</label>
                            <span>${data.componente || 'Sin componente'}</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Macronutrientes</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <label>Energía:</label>
                            <span>${data.energiaKcal} kcal / ${data.energiaKj} kJ</span>
                        </div>
                        <div class="detail-item">
                            <label>Proteína:</label>
                            <span>${data.proteina} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Lípidos:</label>
                            <span>${data.lipidos} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Carbohidratos Totales:</label>
                            <span>${data.carbohidratosTotales} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Fibra Dietaria:</label>
                            <span>${data.fibraDietaria} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Humedad:</label>
                            <span>${data.humedad} g</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Minerales</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <label>Calcio:</label>
                            <span>${data.calcio} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Hierro:</label>
                            <span>${data.hierro} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Sodio:</label>
                            <span>${data.sodio} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Fósforo:</label>
                            <span>${data.fosforo} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Zinc:</label>
                            <span>${data.zinc} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Magnesio:</label>
                            <span>${data.magnesio} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Potasio:</label>
                            <span>${data.potasio} mg</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Vitaminas</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <label>Vitamina A:</label>
                            <span>${data.vitaminaA} ER</span>
                        </div>
                        <div class="detail-item">
                            <label>Vitamina C:</label>
                            <span>${data.vitaminaC} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Vitamina B12:</label>
                            <span>${data.vitaminaB12} mcg</span>
                        </div>
                        <div class="detail-item">
                            <label>Tiamina:</label>
                            <span>${data.tiamina} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Riboflavina:</label>
                            <span>${data.riboflavina} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Niacina:</label>
                            <span>${data.niacina} mg</span>
                        </div>
                        <div class="detail-item">
                            <label>Folatos:</label>
                            <span>${data.folatos} mcg</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Grasas</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <label>Grasa Saturada:</label>
                            <span>${data.grasaSaturada} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Grasa Monoinsaturada:</label>
                            <span>${data.grasaMonoinsaturada} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Grasa Poliinsaturada:</label>
                            <span>${data.grasaPoliinsaturada} g</span>
                        </div>
                        <div class="detail-item">
                            <label>Colesterol:</label>
                            <span>${data.colesterol} mg</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4>Cocción</h4>
                    <div class="detail-row">
                        <div class="detail-item">
                            <label>Parte Comestible:</label>
                            <span>${data.parteComestible} %</span>
                        </div>
                        <div class="detail-item">
                            <label>Factor de Cocción:</label>
                            <span>${data.factorCoccion}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('detailModal').style.display = 'flex';
    }

    // Cierra el modal de detalle.
    closeDetailModal() {
        const detailModal = document.getElementById('detailModal');
        if (detailModal) {
            detailModal.style.display = 'none';
        }
    }

    // =====================================
    // FUNCIONALIDAD DE ELIMINAR
    // =====================================

    // Elimina un alimento vía API DELETE con confirmación previa.
    async deleteAlimento(button) {
        const codigo = button.dataset.codigo;
        const nombre = button.dataset.nombre;

        // Usar SweetAlert2 si está disponible, sino confirm nativo
        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title: '¿Eliminar alimento?',
                text: `¿Está seguro de que desea eliminar "${nombre}"? Esta acción no se puede deshacer.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            });

            if (!result.isConfirmed) return;
        } else {
            if (!confirm(`¿Está seguro de que desea eliminar "${nombre}"? Esta acción no se puede deshacer.`)) {
                return;
            }
        }

        try {
            const response = await fetch(`/nutricion/alimentos/eliminar/${codigo}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                // Mostrar notificación de éxito
                if (typeof Swal !== 'undefined') {
                    await Swal.fire({
                        title: '¡Eliminado!',
                        text: 'El alimento ha sido eliminado.',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    });
                }
                // Recargar la página para reflejar los cambios
                window.location.reload();
            } else {
                const errorMsg = result.error || 'Error al eliminar el alimento';
                if (typeof Swal !== 'undefined') {
                    Swal.fire('Error', errorMsg, 'error');
                } else {
                    alert(errorMsg);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            const errorMsg = 'Error de conexión al eliminar';
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', errorMsg, 'error');
            } else {
                alert(errorMsg);
            }
        }
    }

    // =====================================
    // FUNCIONALIDAD DE BÚSQUEDA (SERVER-SIDE)
    // =====================================

    // Inicializa búsqueda server-side usando el parámetro `q` en URL.
    setupSearch() {
        const searchInput = document.getElementById('searchInput');
        const clearButton = document.getElementById('clearSearch');
        const resultsCount = document.getElementById('searchResultsCount');

        if (!searchInput || !clearButton || !resultsCount) {
            console.warn('AlimentosManager: Elementos de búsqueda no encontrados');
            return;
        }

        // Obtener término de búsqueda actual de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const currentQuery = urlParams.get('q') || '';

        // Establecer valor inicial del input
        if (currentQuery) {
            searchInput.value = currentQuery;
            this.currentSearchTerm = currentQuery;
            this.updateClearButton();
            this.updateResultsInfo(currentQuery);
        }

        // Event listener para mostrar/ocultar botón limpiar mientras escribe
        searchInput.addEventListener('input', () => {
            this.currentSearchTerm = searchInput.value.trim();
            this.updateClearButton();
        });

        // Event listener para limpiar búsqueda
        clearButton.addEventListener('click', () => {
            // Redirigir a la página sin parámetro de búsqueda
            window.location.href = window.location.pathname;
        });

        // Event listener para Enter - enviar búsqueda al servidor
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.submitSearch();
            }
        });
    }

    // Envía búsqueda redirigiendo con querystring para filtrado en backend.
    submitSearch() {
        const searchTerm = this.currentSearchTerm.trim();

        if (searchTerm) {
            // Redirigir con parámetro de búsqueda
            window.location.href = `${window.location.pathname}?q=${encodeURIComponent(searchTerm)}`;
        } else {
            // Si está vacío, quitar el parámetro
            window.location.href = window.location.pathname;
        }
    }

    // Actualiza etiqueta de resultados según término buscado y filas visibles.
    updateResultsInfo(searchTerm) {
        const resultsCount = document.getElementById('searchResultsCount');
        const rows = document.querySelectorAll('.alimentos-table tbody tr');
        const visibleCount = rows.length;

        if (resultsCount && searchTerm) {
            resultsCount.innerHTML = `Resultados para "<span class="highlight">${searchTerm}</span>" - Mostrando <span class="highlight">${visibleCount}</span> alimentos`;
        }
    }

    // Muestra u oculta el botón "limpiar" según el estado del input.
    updateClearButton() {
        const clearButton = document.getElementById('clearSearch');
        if (clearButton) {
            if (this.currentSearchTerm) {
                clearButton.classList.add('show');
            } else {
                clearButton.classList.remove('show');
            }
        }
    }
}

// Punto de entrada: inicializa el manager solo en la vista que contiene el modal.
let alimentosManager;

document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la página de alimentos
    if (document.getElementById('alimento-modal')) {
        alimentosManager = new AlimentosManager();
    }
});

// Exportar para uso global si es necesario
window.AlimentosManager = AlimentosManager;
// Función global para cerrar modal de detalles (usado desde HTML onclick)
function closeDetailModal() {
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        detailModal.style.display = 'none';
    }
}

// Exponer globalmente
window.closeDetailModal = closeDetailModal;
