/**
 * MenusAvanzadosController.js - ARCHIVO PRINCIPAL REFACTORIZADO
 * Coordinador principal que integra todos los módulos del sistema de menús avanzados
 * 
 * MÓDULOS INTEGRADOS:
 * - PreparacionesManager: Gestión de preparaciones
 * - IngredientesManager: Gestión de ingredientes
 * - ModalesManager: Gestión centralizada de modales
 * - [Pendientes] FiltrosManager, ModalidadesManager, etc.
 */

class MenusAvanzadosController {
    constructor() {
        // Variables globales del sistema
        this.programaActual = null;
        this.municipioActual = null;
        this.modalidadesData = [];
        this.menusData = {};
        this.menuActualId = null;
        this.menuActualAnalisis = null;

        // Managers de módulos
        this.filtrosManager = null;
        this.modalidadesManager = null;
        this.preparacionesManager = null;
        this.ingredientesManager = null;
        this.analisisNutricionalManager = null;
        this.menusEspecialesManager = null;
        this.modalesManager = null;

        this.init();
    }

    /**
     * Inicializar el controlador principal
     */
    async init() {
        try {
            // Inicializar managers en orden de dependencia
            this.modalesManager = new ModalesManager();
            this.filtrosManager = new FiltrosManager();
            this.modalidadesManager = new ModalidadesManager();
            this.preparacionesManager = new PreparacionesManager();
            this.ingredientesManager = new IngredientesManager();
            this.analisisNutricionalManager = new AnalisisNutricionalManager();
            this.menusEspecialesManager = new MenusEspecialesManager();

            // Configurar integración entre módulos
            this.configurarIntegracion();

            // Si hay municipio preseleccionado, cargar programas
            if (typeof MUNICIPIO_ACTUAL !== 'undefined' && MUNICIPIO_ACTUAL) {
                await this.filtrosManager.cargarProgramasPorMunicipio(MUNICIPIO_ACTUAL);
            }
        } catch (error) {
            console.error('❌ Error al inicializar MenusAvanzadosController:', error);
        }
    }

    /**
     * Configurar integración entre módulos
     */
    configurarIntegracion() {
        // Configurar callbacks entre managers
        if (this.filtrosManager) {
            this.filtrosManager.setOnFiltrosAplicados((programaId) => {
                this.cargarModalidadesPorPrograma(programaId);
            });
        }

        if (this.modalidadesManager) {
            this.modalidadesManager.setOnModalidadesRecargadas((programaId) => {
                this.cargarModalidadesPorPrograma(programaId);
            });
        }

        if (this.menusEspecialesManager) {
            this.menusEspecialesManager.setProgramaActual(this.programaActual);
            this.menusEspecialesManager.setOnModalidadesRecargadas((programaId) => {
                this.cargarModalidadesPorPrograma(programaId);
            });
        }

        // Configurar integración entre PreparacionesManager e IngredientesManager
        if (this.preparacionesManager && this.ingredientesManager) {
            this.preparacionesManager.setIngredientesManager(this.ingredientesManager);
        }

        // Todos los managers pueden usar el ModalesManager
        if (this.preparacionesManager && this.modalesManager) {
            this.preparacionesManager.setModalesManager(this.modalesManager);
        }
        
        if (this.ingredientesManager && this.modalesManager) {
            this.ingredientesManager.setModalesManager(this.modalesManager);
        }

        if (this.menusEspecialesManager && this.modalesManager) {
            this.menusEspecialesManager.setModalesManager(this.modalesManager);
        }
    }

    /**
     * Configurar event listeners principales
     */
    setupEventListeners() {
        // Los event listeners ahora están manejados por cada manager individual
        // Solo mantenemos los event listeners específicos del controlador principal
        
        // Event listener para análisis nutricional
        const btnAnalisis = document.getElementById('btnAnalisisNutricional');
        if (btnAnalisis) {
            btnAnalisis.addEventListener('click', (e) => this.handleAnalisisNutricional(e));
        }
    }

    // =================== MÉTODOS DE COORDINACIÓN ===================

    /**
     * Manejar análisis nutricional
     * @param {Event} e - Evento del botón
     */
    handleAnalisisNutricional(e) {
        if (this.menuActualAnalisis) {
            this.abrirModalAnalisisNutricional(this.menuActualAnalisis);
        }
    }

    // =================== MÉTODOS DE CARGA DE DATOS ===================

    /**
     * Cargar programas por municipio
     * @param {string} municipioId - ID del municipio
     */
    async cargarProgramasPorMunicipio(municipioId) {
        try {
            const url = `/nutricion/api/programas-por-municipio/?municipio_id=${municipioId}`;
            const response = await fetch(url);
            const data = await response.json();
            const selectPrograma = document.getElementById('filtroPrograma');
            
            if (!selectPrograma) return;

            selectPrograma.innerHTML = '<option value="">Seleccione un programa...</option>';
            
            if (data.programas && data.programas.length > 0) {
                data.programas.forEach(programa => {
                    const option = document.createElement('option');
                    option.value = programa.id;
                    option.textContent = `${programa.programa} (${programa.contrato})`;
                    selectPrograma.appendChild(option);
                });
                
                selectPrograma.disabled = false;
                
                // Si solo hay un programa, seleccionarlo automáticamente
                if (data.programas.length === 1) {
                    selectPrograma.value = data.programas[0].id;
                    document.getElementById('btnAplicarFiltros').disabled = false;
                }
            } else {
                selectPrograma.innerHTML = '<option value="">No hay programas activos en este municipio</option>';
                selectPrograma.disabled = true;
            }
        } catch (error) {
            console.error('Error al cargar programas:', error);
            alert('Error al cargar programas del municipio');
        }
    }

    /**
     * Cargar modalidades por programa
     * @param {string} programaId - ID del programa
     */
    async cargarModalidadesPorPrograma(programaId) {
        try {
            const data = await this.modalidadesManager.cargarModalidadesPorPrograma(programaId);
            
            this.programaActual = data.programa;
            this.modalidadesData = data.modalidades;
            this.menusData = data.menus;
            
            this.mostrarInfoPrograma(data.programa);
            document.getElementById('mensajeInicial').style.display = 'none';
            this.generarAcordeones(data.modalidades);
            
            // Actualizar programa actual en otros managers
            if (this.menusEspecialesManager) {
                this.menusEspecialesManager.setProgramaActual(data.programa);
            }
            
        } catch (error) {
            console.error('Error al cargar modalidades:', error);
            alert('Error al cargar modalidades del programa');
        }
    }


    /**
     * Mostrar información del programa
     * @param {Object} programa - Datos del programa
     */
    mostrarInfoPrograma(programa) {
        const container = document.getElementById('infoProgramaContainer');
        document.getElementById('infoProgramaNombre').querySelector('span').textContent = programa.nombre;
        document.getElementById('infoProgramaContrato').querySelector('span').textContent = programa.contrato;
        
        const municipioSelect = document.getElementById('filtroMunicipio');
        const municipioNombre = municipioSelect.options[municipioSelect.selectedIndex].text;
        document.getElementById('infoProgramaMunicipio').querySelector('span').textContent = municipioNombre;
        
        container.style.display = 'block';
    }

    /**
     * Generar acordeones de modalidades
     * @param {Array} modalidades - Array de modalidades
     */
    generarAcordeones(modalidades) {
        this.modalidadesManager.generarAcordeones(modalidades);
    }


    // =================== MÉTODOS DE GESTIÓN DE PREPARACIONES ===================

    /**
     * Abrir gestión de preparaciones
     * @param {number} menuId - ID del menú
     * @param {string} menuNumero - Número del menú
     */
    abrirGestionPreparaciones(menuId, menuNumero) {
        this.menuActualId = menuId;
        this.menuActualAnalisis = menuId;
        
        document.getElementById('menuNumeroModal').textContent = menuNumero;
        this.modalesManager.abrirModal(this.modalesManager.modales.preparaciones);

        // Encontrar la modalidad del menú actual
        for (const modId in this.menusData) {
            if (this.menusData[modId].some(menu => menu.id_menu === menuId)) {
                if (this.preparacionesManager) {
                    this.preparacionesManager.setModalidadActual(modId);
                }
                break;
            }
        }

        // Configurar botón de agregar preparación
        this.configurarBotonAgregarPreparacion(menuId);
        
        // Cargar preparaciones
        this.cargarPreparacionesMenu(menuId);
    }

    /**
     * Configurar botón de agregar preparación
     * @param {number} menuId - ID del menú
     */
    configurarBotonAgregarPreparacion(menuId) {
        const btnAgregar = document.getElementById('btnAgregarPreparacion');
        if (btnAgregar) {
            // Remover todos los event listeners anteriores
            const newBtn = btnAgregar.cloneNode(true);
            btnAgregar.parentNode.replaceChild(newBtn, btnAgregar);
            
            // Asignar el evento al nuevo botón
            newBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (this.preparacionesManager) {
                    this.preparacionesManager.abrirModalNuevaPreparacion(menuId);
                }
            };
        }
    }

    /**
     * Cargar preparaciones de un menú
     * @param {number} menuId - ID del menú
     */
    async cargarPreparacionesMenu(menuId) {
        if (this.preparacionesManager) {
            await this.preparacionesManager.cargarPreparacionesMenu(menuId);
        }
    }

    /**
     * Cargar ingredientes de una preparación
     * @param {number} preparacionId - ID de la preparación
     */
    async cargarIngredientesPreparacion(preparacionId) {
        if (this.ingredientesManager) {
            await this.ingredientesManager.cargarIngredientesPreparacion(preparacionId);
        }
    }

    // =================== MÉTODOS DE ANÁLISIS NUTRICIONAL ===================

    /**
     * Abrir modal de análisis nutricional
     * @param {number} menuId - ID del menú
     */
    abrirModalAnalisisNutricional(menuId) {
        this.modalesManager.abrirModal(this.modalesManager.modales.analisisNutricional);

        const menuNumero = document.getElementById('menuNumeroModal').textContent;
        document.getElementById('menuNombreAnalisis').textContent = menuNumero;

        this.cargarAnalisisNutricional(menuId);
    }

    /**
     * Cargar análisis nutricional
     * @param {number} menuId - ID del menú
     */
    async cargarAnalisisNutricional(menuId) {
        if (this.analisisNutricionalManager) {
            await this.analisisNutricionalManager.cargarAnalisisNutricional(menuId);
        }
    }

    // =================== MÉTODOS DE UTILIDAD ===================

    /**
     * Generar menús automáticos
     * @param {string} modalidadId - ID de la modalidad
     * @param {string} modalidadNombre - Nombre de la modalidad
     */
    async generarMenusAutomaticos(modalidadId, modalidadNombre) {
        if (this.modalidadesManager) {
            await this.modalidadesManager.generarMenusAutomaticos(modalidadId, modalidadNombre);
        }
    }

    /**
     * Resetear filtros
     */
    resetearFiltros() {
        if (this.filtrosManager) {
            this.filtrosManager.resetearFiltros();
        }
    }
}

// =================== FUNCIONES GLOBALES PARA COMPATIBILIDAD ===================
// TODAS las funciones globales están aquí para evitar duplicaciones
// Los managers NO deben definir funciones globales en setupGlobalFunctions()

// ========== GESTIÓN DE MENÚS ==========
window.abrirGestionPreparaciones = function(menuId, menuNumero) {
    if (window.menusController) {
        window.menusController.abrirGestionPreparaciones(menuId, menuNumero);
    }
};

// ========== ANÁLISIS NUTRICIONAL ==========
window.abrirModalAnalisisNutricional = function(menuId) {
    if (window.menusController) {
        window.menusController.abrirModalAnalisisNutricional(menuId);
    }
};

// ========== MENÚS ESPECIALES ==========
window.abrirModalMenuEspecial = function(modalidadId) {
    if (window.menusController && window.menusController.menusEspecialesManager) {
        window.menusController.menusEspecialesManager.abrirModalMenuEspecial(modalidadId);
    }
};

window.crearMenuEspecial = function() {
    if (window.menusController && window.menusController.menusEspecialesManager) {
        window.menusController.menusEspecialesManager.crearMenuEspecial();
    }
};

window.abrirEditarMenuEspecial = function(menuId, nombreActual) {
    if (window.menusController && window.menusController.menusEspecialesManager) {
        window.menusController.menusEspecialesManager.abrirEditarMenuEspecial(menuId, nombreActual);
    }
};

window.guardarEdicionMenuEspecial = function() {
    if (window.menusController && window.menusController.menusEspecialesManager) {
        window.menusController.menusEspecialesManager.guardarEdicionMenuEspecial();
    }
};

window.eliminarMenuEspecial = function(menuId, nombreMenu) {
    if (window.menusController && window.menusController.menusEspecialesManager) {
        window.menusController.menusEspecialesManager.eliminarMenuEspecial(menuId, nombreMenu);
    }
};

// ========== INGREDIENTES ==========
window.abrirAgregarIngrediente = async function(preparacionId) {
    if (window.menusController && window.menusController.ingredientesManager) {
        await window.menusController.ingredientesManager.abrirModalAgregarIngredientes(preparacionId);
    }
};

window.agregarFilaIngrediente = function() {
    if (window.menusController && window.menusController.ingredientesManager) {
        window.menusController.ingredientesManager.agregarFilaIngrediente();
    }
};

window.guardarIngredientes = function() {
    if (window.menusController && window.menusController.ingredientesManager) {
        window.menusController.ingredientesManager.guardarIngredientes();
    }
};

window.eliminarIngrediente = function(preparacionId, ingredienteId) {
    if (window.menusController && window.menusController.ingredientesManager) {
        window.menusController.ingredientesManager.eliminarIngrediente(preparacionId, ingredienteId);
    }
};

window.eliminarFilaIngrediente = function(index) {
    if (window.menusController && window.menusController.ingredientesManager) {
        window.menusController.ingredientesManager.eliminarFilaIngrediente(index);
    }
};

// ========== CERRAR MODALES ==========
window.cerrarModalPreparacion = function() {
    if (window.menusController && window.menusController.modalesManager) {
        window.menusController.modalesManager.cerrarModalPreparacion();
    }
};

window.cerrarModalIngredientes = function() {
    if (window.menusController && window.menusController.modalesManager) {
        window.menusController.modalesManager.cerrarModalIngredientes();
    }
};

window.cerrarModalAnalisisNutricional = function() {
    if (window.menusController && window.menusController.modalesManager) {
        window.menusController.modalesManager.cerrarModalAnalisisNutricional();
    }
};

// Función para obtener cookie CSRF (necesaria para las APIs)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// =================== INICIALIZACIÓN ===================

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.menusController = new MenusAvanzadosController();
});

// Exportar para uso global
window.MenusAvanzadosController = MenusAvanzadosController;
