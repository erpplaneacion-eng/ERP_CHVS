/**
 * Archivo principal de inicialización del módulo de nutrición
 * Coordina la carga y configuración de todos los componentes
 */

// Configuración global del módulo
const NutricionConfig = {
    version: '2.0.0',
    debug: false,
    autoInit: true,
    modules: {
        utils: true,
        modals: true,
        api: true,
        menus: true
    }
};

/**
 * Sistema de carga de dependencias
 */
class DependencyLoader {
    constructor() {
        this.loadedModules = new Set();
        this.loadingPromises = new Map();
    }

    /**
     * Carga un script dinámicamente
     * @param {string} src - Ruta del script
     * @param {string} moduleName - Nombre del módulo
     * @returns {Promise} - Promesa que se resuelve cuando el script se carga
     */
    loadScript(src, moduleName) {
        if (this.loadedModules.has(moduleName)) {
            return Promise.resolve();
        }

        if (this.loadingPromises.has(moduleName)) {
            return this.loadingPromises.get(moduleName);
        }

        const promise = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = () => {
                this.loadedModules.add(moduleName);
                if (NutricionConfig.debug) {
                    console.log(`✅ Módulo cargado: ${moduleName}`);
                }
                resolve();
            };
            script.onerror = () => {
                console.error(`❌ Error cargando módulo: ${moduleName}`);
                reject(new Error(`Failed to load ${moduleName}`));
            };
            document.head.appendChild(script);
        });

        this.loadingPromises.set(moduleName, promise);
        return promise;
    }

    /**
     * Verifica si un módulo está disponible
     * @param {string} moduleName - Nombre del módulo
     * @returns {boolean} - True si está disponible
     */
    isModuleAvailable(moduleName) {
        return this.loadedModules.has(moduleName);
    }
}

/**
 * Gestor principal del módulo de nutrición
 */
class NutricionManager {
    constructor() {
        this.loader = new DependencyLoader();
        this.initialized = false;
        this.baseJSPath = '/static/js/nutricion/';
    }

    /**
     * Inicializa el módulo completo
     */
    async init() {
        if (this.initialized) {
            console.warn('Nutrición Manager ya está inicializado');
            return;
        }

        try {
            console.log('🚀 Inicializando módulo de nutrición v' + NutricionConfig.version);
            
            // Cargar módulos core en orden
            await this.cargarModulosCore();
            
            // Cargar módulos específicos según la página
            await this.cargarModulosEspecificos();
            
            // Configurar eventos globales
            this.configurarEventosGlobales();
            
            this.initialized = true;
            console.log('✅ Módulo de nutrición inicializado correctamente');
            
            // Emitir evento de inicialización completa
            this.emitirEvento('nutricion:ready');
            
        } catch (error) {
            console.error('❌ Error inicializando módulo de nutrición:', error);
            throw error;
        }
    }

    /**
     * Carga los módulos core necesarios
     */
    async cargarModulosCore() {
        const coreModules = [
            { name: 'utils', file: 'core/utils.js' },
            { name: 'modals', file: 'core/modal-manager.js' },
            { name: 'api', file: 'core/api-client.js' }
        ];

        for (const module of coreModules) {
            if (NutricionConfig.modules[module.name]) {
                await this.loader.loadScript(this.baseJSPath + module.file, module.name);
            }
        }
    }

    /**
     * Carga módulos específicos según la página actual
     */
    async cargarModulosEspecificos() {
        const currentPage = this.detectarPaginaActual();
        
        const pageModules = {
            'lista_menus': [], // Los módulos ya se cargan en el HTML
            'lista_alimentos': ['alimentos.js'],
            'menus_basicos': ['menus.js']
        };

        if (pageModules[currentPage]) {
            for (const moduleFile of pageModules[currentPage]) {
                await this.loader.loadScript(this.baseJSPath + moduleFile, moduleFile);
            }
        }
    }

    /**
     * Detecta la página actual basándose en la URL o elementos DOM
     */
    detectarPaginaActual() {
        const path = window.location.pathname;
        
        if (path.includes('lista-menus') || path.includes('menus-avanzado')) {
            return 'lista_menus';
        } else if (path.includes('lista-preparaciones')) {
            return 'lista_preparaciones';
        } else if (path.includes('lista-ingredientes')) {
            return 'lista_ingredientes';
        } else if (path.includes('detalle-preparacion')) {
            return 'detalle_preparacion';
        } else if (path.includes('lista-alimentos')) {
            return 'lista_alimentos';
        } else if (path.includes('menus')) {
            return 'menus_basicos';
        }
        
        return 'unknown';
    }

    /**
     * Configura eventos globales del módulo
     */
    configurarEventosGlobales() {
        // Manejo global de errores AJAX
        window.addEventListener('unhandledrejection', (event) => {
            if (event.reason && event.reason.message && 
                event.reason.message.includes('nutricion')) {
                console.error('Error no manejado en módulo nutrición:', event.reason);
                if (window.NutricionUtils) {
                    NutricionUtils.manejarError(event.reason, 'Error global');
                }
            }
        });

        // Teclas de acceso rápido
        document.addEventListener('keydown', (event) => {
            // Ctrl+S para guardar (prevenir save del navegador en formularios)
            if (event.ctrlKey && event.key === 's') {
                const activeForm = document.querySelector('form:focus-within');
                if (activeForm && activeForm.closest('.modal')) {
                    event.preventDefault();
                    const submitBtn = activeForm.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.click();
                    }
                }
            }
        });

        // Auto-save para campos de texto largos
        this.configurarAutoSave();
    }

    /**
     * Configura auto-save para formularios largos
     */
    configurarAutoSave() {
        const textareas = document.querySelectorAll('textarea[data-autosave]');
        textareas.forEach(textarea => {
            const debouncedSave = this.debounce(() => {
                const data = {
                    field: textarea.name,
                    value: textarea.value,
                    timestamp: Date.now()
                };
                localStorage.setItem(`autosave_${textarea.name}`, JSON.stringify(data));
            }, 2000);

            textarea.addEventListener('input', debouncedSave);
            
            // Restaurar al cargar
            const saved = localStorage.getItem(`autosave_${textarea.name}`);
            if (saved && !textarea.value.trim()) {
                const data = JSON.parse(saved);
                if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) { // 24 horas
                    textarea.value = data.value;
                }
            }
        });
    }

    /**
     * Emite un evento personalizado
     * @param {string} eventName - Nombre del evento
     * @param {Object} detail - Datos del evento
     */
    emitirEvento(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Función debounce
     * @param {Function} func - Función a ejecutar
     * @param {number} wait - Tiempo de espera
     * @returns {Function} - Función debounced
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Recarga un módulo específico
     * @param {string} moduleName - Nombre del módulo
     */
    async recargarModulo(moduleName) {
        if (this.loader.loadedModules.has(moduleName)) {
            this.loader.loadedModules.delete(moduleName);
            this.loader.loadingPromises.delete(moduleName);
        }
        
        // Recargar según el tipo de módulo
        const moduleFiles = {
            'utils': 'core/utils.js',
            'modals': 'core/modal-manager.js',
            'api': 'core/api-client.js'
        };
        
        if (moduleFiles[moduleName]) {
            await this.loader.loadScript(this.baseJSPath + moduleFiles[moduleName], moduleName);
        }
    }

    /**
     * Información del estado del sistema
     */
    getInfo() {
        return {
            version: NutricionConfig.version,
            initialized: this.initialized,
            loadedModules: Array.from(this.loader.loadedModules),
            currentPage: this.detectarPaginaActual(),
            config: NutricionConfig
        };
    }
}

// Instancia global del manager
const nutricionManager = new NutricionManager();

// Auto-inicialización
if (NutricionConfig.autoInit) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            nutricionManager.init().catch(console.error);
        });
    } else {
        nutricionManager.init().catch(console.error);
    }
}

// API global para depuración y control manual
window.NutricionManager = nutricionManager;
window.NutricionConfig = NutricionConfig;

// Evento para módulos que dependan de la inicialización
document.addEventListener('nutricion:ready', () => {
    console.log('🎉 Sistema de nutrición listo para usar');
});