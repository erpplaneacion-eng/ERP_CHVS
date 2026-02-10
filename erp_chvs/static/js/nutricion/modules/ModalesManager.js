/**
 * ModalesManager.js
 * Maneja centralizadamente todos los modales del sistema
 * - Configuración de botones de cerrar
 * - Manejo de z-index para modales anidados
 * - Event listeners para cierre de modales
 * - Funciones globales para compatibilidad con onclick
 */

class ModalesManager {
    constructor() {
        this.modales = {
            preparaciones: 'modalPreparaciones',
            nuevaPreparacion: 'modalNuevaPreparacion',
            agregarIngredientes: 'modalAgregarIngredientes',
            analisisNutricional: 'modalAnalisisNutricional',
            menuEspecial: 'modalMenuEspecial',
            editarMenuEspecial: 'modalEditarMenuEspecial',
            menuIA: 'modalMenuIA'
        };
        
        this.init();
    }

    init() {
        this.setupGlobalFunctions();
        this.ocultarTodosLosModales();
        this.configurarBotonesCerrar();
        this.configurarEventListeners();
    }

    /**
     * Configurar funciones globales para compatibilidad con onclick
     */
    setupGlobalFunctions() {
        // Función para cerrar modal de preparación
        window.cerrarModalPreparacion = () => {
            this.cerrarModalPreparacion();
        };

        // Función para cerrar modal de ingredientes
        window.cerrarModalIngredientes = () => {
            this.cerrarModalIngredientes();
        };

        // Función para cerrar modal de análisis nutricional
        window.cerrarModalAnalisisNutricional = () => {
            this.cerrarModalAnalisisNutricional();
        };
    }

    /**
     * Ocultar todos los modales al inicializar
     */
    ocultarTodosLosModales() {
        Object.values(this.modales).forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'none';
            }
        });
    }

    /**
     * Configurar botones de cerrar (X) para cada modal
     */
    configurarBotonesCerrar() {
        const configuraciones = [
            { modalId: this.modales.preparaciones, funcion: () => this.cerrarModal(this.modales.preparaciones) },
            { modalId: this.modales.nuevaPreparacion, funcion: () => this.cerrarModalPreparacion() },
            { modalId: this.modales.agregarIngredientes, funcion: () => this.cerrarModalIngredientes() },
            { modalId: this.modales.analisisNutricional, funcion: () => this.cerrarModalAnalisisNutricional() },
            { modalId: this.modales.menuEspecial, funcion: () => this.cerrarModal(this.modales.menuEspecial) },
            { modalId: this.modales.editarMenuEspecial, funcion: () => this.cerrarModal(this.modales.editarMenuEspecial) }
        ];

        configuraciones.forEach(({ modalId, funcion }) => {
            const modal = document.getElementById(modalId);
            if (modal) {
                const closeBtn = modal.querySelector('.close');
                if (closeBtn) {
                    closeBtn.onclick = funcion;
                }
            }
        });
    }

    /**
     * Configurar event listeners globales para modales
     */
    configurarEventListeners() {
        // Event listener para cerrar modal al hacer click en el fondo
        document.addEventListener('click', (event) => {
            // Cerrar modal solo si se hace clic en el botón X
            if (event.target.classList.contains('close') && event.target.closest('.modal')) {
                event.target.closest('.modal').style.display = 'none';
                return;
            }

            // Cerrar modal solo si se hace clic DIRECTAMENTE en el fondo del modal
            // NO si se hace clic en elementos internos (como acordeones, botones, etc.)
            if (event.target.classList.contains('modal') && !event.target.classList.contains('modal-content')) {
                // Verificar que no sea un clic dentro del contenido del modal
                const modalContent = event.target.querySelector('.modal-content');
                if (modalContent && !modalContent.contains(event.target)) {
                    event.target.style.display = 'none';
                }
            }
        });
    }

    /**
     * Abrir un modal específico
     * @param {string} modalId - ID del modal
     * @param {Object} options - Opciones adicionales
     */
    abrirModal(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`❌ Modal ${modalId} no encontrado`);
            return;
        }

        // Configurar z-index según el tipo de modal
        const zIndexMap = {
            [this.modales.preparaciones]: 1000,
            [this.modales.nuevaPreparacion]: 1100,
            [this.modales.agregarIngredientes]: 1150,
            [this.modales.analisisNutricional]: 1200,
            [this.modales.menuEspecial]: 1100,
            [this.modales.editarMenuEspecial]: 1100
        };

        // Mover modal al body para evitar problemas de z-index con elementos anidados
        document.body.appendChild(modal);

        // Aplicar estilos para asegurar visibilidad
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.zIndex = options.zIndex || zIndexMap[modalId] || 1000;
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';

        // Si es el modal de ingredientes, aplicar estilos especiales
        if (modalId === this.modales.agregarIngredientes) {
            this.configurarModalIngredientes(modal);
        }
    }

    /**
     * Cerrar un modal específico
     * @param {string} modalId - ID del modal
     */
    cerrarModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Configurar estilos especiales para el modal de ingredientes
     * @param {HTMLElement} modal - Elemento del modal
     */
    configurarModalIngredientes(modal) {
        const modalContent = modal.querySelector('.modal-content');
        
        if (modalContent) {
            modalContent.style.width = '90vw';
            modalContent.style.maxWidth = '1200px';
            modalContent.style.height = '80vh';
            modalContent.style.maxHeight = '700px';
            modalContent.style.backgroundColor = 'white';
            modalContent.style.borderRadius = '12px';
            modalContent.style.padding = '25px';
            modalContent.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
            modalContent.style.overflow = 'hidden';
            modalContent.style.display = 'flex';
            modalContent.style.flexDirection = 'column';
        }
    }

    /**
     * Cerrar modal de preparación
     */
    cerrarModalPreparacion() {
        const modal = document.getElementById(this.modales.nuevaPreparacion);
        if (modal) {
            modal.style.display = 'none';
            
            // Limpiar formulario
            const nombrePrep = document.getElementById('nombrePreparacion');
            const componenteAlim = document.getElementById('componenteAlimento');
            const menuIdPrep = document.getElementById('menuIdPrep');
            
            if (nombrePrep) nombrePrep.value = '';
            if (componenteAlim) componenteAlim.value = '';
            if (menuIdPrep) menuIdPrep.value = '';
        }
    }

    /**
     * Cerrar modal de ingredientes
     */
    cerrarModalIngredientes() {
        const modal = document.getElementById(this.modales.agregarIngredientes);
        if (modal) {
            modal.style.display = 'none';
            
            // Limpiar tabla de ingredientes
            const tbody = document.getElementById('tbodyIngredientes');
            if (tbody) {
                tbody.innerHTML = '';
            }
            
            // Destruir instancias de Select2
            $('.select-ingrediente').each(function() {
                if ($(this).hasClass('select2-hidden-accessible')) {
                    $(this).select2('destroy');
                }
            });
        }
    }

    /**
     * Cerrar modal de análisis nutricional
     */
    cerrarModalAnalisisNutricional() {
        const modal = document.getElementById(this.modales.analisisNutricional);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Obtener el z-index apropiado para un modal
     * @param {string} modalId - ID del modal
     * @returns {number} Z-index
     */
    getZIndex(modalId) {
        const zIndexMap = {
            [this.modales.preparaciones]: 1000,
            [this.modales.nuevaPreparacion]: 1100,
            [this.modales.agregarIngredientes]: 1150,
            [this.modales.analisisNutricional]: 1200,
            [this.modales.menuEspecial]: 1100,
            [this.modales.editarMenuEspecial]: 1100
        };
        
        return zIndexMap[modalId] || 1000;
    }

    /**
     * Verificar si un modal está abierto
     * @param {string} modalId - ID del modal
     * @returns {boolean} True si está abierto
     */
    isModalOpen(modalId) {
        const modal = document.getElementById(modalId);
        return modal && modal.style.display !== 'none';
    }

    /**
     * Obtener lista de modales abiertos
     * @returns {Array} Lista de IDs de modales abiertos
     */
    getOpenModals() {
        return Object.values(this.modales).filter(modalId => this.isModalOpen(modalId));
    }

    /**
     * Cerrar todos los modales
     */
    cerrarTodosLosModales() {
        Object.values(this.modales).forEach(modalId => {
            this.cerrarModal(modalId);
        });
    }

    /**
     * Configurar modal para que aparezca sobre otros
     * @param {string} modalId - ID del modal
     * @param {number} zIndex - Z-index personalizado
     */
    traerAlFrente(modalId, zIndex = null) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.zIndex = zIndex || (this.getZIndex(modalId) + 1000);
        }
    }
}

// Exportar para uso global
window.ModalesManager = ModalesManager;
