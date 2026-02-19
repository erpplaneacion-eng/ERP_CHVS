// alimentos.js - Funcionalidad para gestión de alimentos ICBF

class AlimentosManager {
    constructor() {
        this.modal = null;
        this.modalTitle = null;
        this.alimentoForm = null;
        this.submitBtn = null;
        this.isEditing = false;
        this.currentSearchTerm = '';
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
        this.setupSearch();
    }

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

        // Cerrar modal de detalles al hacer click fuera
        const detailModal = document.getElementById('detailModal');
        if (detailModal) {
            detailModal.addEventListener('click', (e) => {
                if (e.target === detailModal) {
                    this.closeDetailModal();
                }
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

    // =====================================
    // FUNCIONALIDAD DE VER DETALLES
    // =====================================

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
            </div>
        `;

        document.getElementById('detailModal').style.display = 'flex';
    }

    closeDetailModal() {
        const detailModal = document.getElementById('detailModal');
        if (detailModal) {
            detailModal.style.display = 'none';
        }
    }

    // =====================================
    // FUNCIONALIDAD DE ELIMINAR
    // =====================================

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

    updateResultsInfo(searchTerm) {
        const resultsCount = document.getElementById('searchResultsCount');
        const rows = document.querySelectorAll('.alimentos-table tbody tr');
        const visibleCount = rows.length;

        if (resultsCount && searchTerm) {
            resultsCount.innerHTML = `Resultados para "<span class="highlight">${searchTerm}</span>" - Mostrando <span class="highlight">${visibleCount}</span> alimentos`;
        }
    }

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
// Función global para cerrar modal de detalles (usado desde HTML onclick)
function closeDetailModal() {
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        detailModal.style.display = 'none';
    }
}

// Exponer globalmente
window.closeDetailModal = closeDetailModal;
