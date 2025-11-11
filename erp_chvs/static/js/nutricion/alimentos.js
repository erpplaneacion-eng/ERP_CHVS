// alimentos.js - Funcionalidad para gestión de alimentos ICBF

class AlimentosManager {
    constructor() {
        this.modal = null;
        this.modalTitle = null;
        this.alimentoForm = null;
        this.submitBtn = null;
        this.isEditing = false;
        this.init();
    }

    init() {
        // Inicializar elementos del DOM
        this.modal = document.getElementById('alimento-modal');
        this.modalTitle = document.getElementById('modal-title');
        this.alimentoForm = document.getElementById('alimento-form');
        this.submitBtn = document.getElementById('modal-submit-btn');

        if (!this.modal || !this.alimentoForm) {
            console.warn('AlimentosManager: Elementos del modal no encontrados');
            return;
        }

        this.setupEventListeners();
        this.setupValidations();
    }

    setupEventListeners() {
        // Botón añadir alimento
        const addBtn = document.getElementById('add-alimento-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showCreateModal());
        }

        // Botones de editar
        const editBtns = document.querySelectorAll('.edit-alimento-btn');
        editBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.showEditModal(e.target));
        });

        // Botones de cerrar modal
        const closeBtns = document.querySelectorAll('.modal-close-btn, .modal-cancel-btn');
        closeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Cerrar modal al hacer click fuera
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Cerrar modal con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'flex') {
                this.closeModal();
            }
        });

        // ⭐ IMPORTANTE: Interceptar el submit del formulario
        // Convertir punto a coma antes de enviar (Django espera coma con locale español)
        this.alimentoForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }

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
            input.addEventListener('input', function() {
                if (parseFloat(this.value) < 0) {
                    this.value = '';
                    this.style.borderColor = '#e74c3c';
                } else {
                    this.style.borderColor = '#ced4da';
                }
            });

            // Validar límites específicos según el campo
            input.addEventListener('blur', (e) => this.validateNumericField(e.target));
        });
    }

    validateNumericField(input) {
        const fieldName = input.name;
        const value = parseFloat(input.value);

        if (!value) return;

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
            'parte_comestible_field': 100
        };

        maxValue = fieldLimits[fieldName];

        if (maxValue && value > maxValue) {
            input.style.borderColor = '#e74c3c';
            this.showFieldError(input, `El valor máximo para ${fieldName} es ${maxValue}`);
        } else {
            input.style.borderColor = '#ced4da';
            this.removeFieldError(input);
        }
    }

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

    removeFieldError(input) {
        const errorSpan = input.parentNode.querySelector('.error-message');
        if (errorSpan) {
            errorSpan.remove();
        }
    }

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
    }

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
    }

    populateForm(data) {
        // Mapeo directo: data-attribute en HTML → ID del input en el formulario
        const fieldMappings = {
            'codigo': 'id_codigo',
            'nombre': 'id_nombre_del_alimento',
            'parteAnalizada': 'id_parte_analizada',
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
            'parteComestible': 'id_parte_comestible_field'
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
    }

    openModal() {
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Focus en el primer campo
        const firstInput = this.alimentoForm.querySelector('input:not([disabled])');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.clearForm();
    }

    handleFormSubmit(event) {
        console.log('📤 Preparando envío del formulario...');

        // ESTRATEGIA: Mantener los valores con PUNTO (formato estándar)
        // Los inputs type="number" ya tienen el formato correcto
        // Solo necesitamos asegurar que no haya problemas de envío

        const numericInputs = this.alimentoForm.querySelectorAll('input[type="number"]');
        let emptyRequiredFields = [];

        numericInputs.forEach(input => {
            if (input.value && input.value.trim() !== '') {
                console.log(`✅ ${input.name}: "${input.value}" (manteniendo punto decimal)`);
            } else if (input.hasAttribute('required')) {
                emptyRequiredFields.push(input.name);
                console.warn(`⚠️ ${input.name}: campo requerido vacío`);
            }
        });

        if (emptyRequiredFields.length > 0) {
            console.error('❌ Campos requeridos vacíos:', emptyRequiredFields);
        }

        console.log('✅ Formulario listo para enviar con formato estándar (punto decimal)');
        // Permitir que el formulario se envíe normalmente con punto decimal
        // Django debe aceptar el formato estándar
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

    // Método para manejar búsqueda/filtrado (si se necesita en el futuro)
    filterAlimentos(searchTerm) {
        const rows = document.querySelectorAll('.alimentos-table tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.style.display = matches ? '' : 'none';
        });
    }
}

// Inicializar manager cuando el DOM esté listo
let alimentosManager;

document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la página de alimentos
    if (document.getElementById('alimento-modal')) {
        alimentosManager = new AlimentosManager();
    }
});

// Exportar para uso global si es necesario
window.AlimentosManager = AlimentosManager;