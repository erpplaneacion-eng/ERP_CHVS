/**
 * Gestor centralizado de modales para el módulo de nutrición
 * Unifica el manejo de modales que se repite en múltiples archivos
 */

// Namespace para gestión de modales
window.NutricionModals = window.NutricionModals || {};

/**
 * Clase para gestionar modales de forma centralizada
 */
class ModalManager {
    constructor() {
        this.modalesActivos = new Map();
        this.inicializarEventosGlobales();
    }

    /**
     * Inicializa eventos globales para todos los modales
     */
    inicializarEventosGlobales() {
        // Cerrar modal al hacer click fuera
        document.addEventListener('click', (event) => {
            this.modalesActivos.forEach((config, modal) => {
                if (event.target === modal && config.cerrarAlClickFuera !== false) {
                    this.cerrar(modal.id);
                }
            });
        });

        // Cerrar modal con tecla Escape
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                const modalActivo = this.obtenerModalActivo();
                if (modalActivo) {
                    this.cerrar(modalActivo.id);
                }
            }
        });
    }

    /**
     * Abre un modal existente
     * @param {string} modalId - ID del modal a abrir
     * @param {Object} opciones - Opciones de configuración
     */
    abrir(modalId, opciones = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal con ID "${modalId}" no encontrado`);
            return;
        }

        // Configuración por defecto
        const config = {
            cerrarAlClickFuera: true,
            mostrarOverlay: true,
            callback: null,
            ...opciones
        };

        // Agregar clases y estilos
        modal.style.display = 'block';
        modal.classList.add('modal-activo');
        
        if (config.mostrarOverlay) {
            document.body.classList.add('modal-abierto');
        }

        // Registrar modal activo
        this.modalesActivos.set(modal, config);

        // Enfocar primer input si existe
        setTimeout(() => {
            const primerInput = modal.querySelector('input, textarea, select');
            if (primerInput) {
                primerInput.focus();
            }
        }, 100);

        // Ejecutar callback si existe
        if (config.callback) {
            config.callback(modal);
        }

        return modal;
    }

    /**
     * Cierra un modal
     * @param {string} modalId - ID del modal a cerrar
     */
    cerrar(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal con ID "${modalId}" no encontrado`);
            return;
        }

        // Remover del registro
        this.modalesActivos.delete(modal);

        // Ocultar modal
        modal.style.display = 'none';
        modal.classList.remove('modal-activo');

        // Si no hay más modales abiertos, quitar overlay
        if (this.modalesActivos.size === 0) {
            document.body.classList.remove('modal-abierto');
        }

        // Limpiar formularios si existen
        const formularios = modal.querySelectorAll('form');
        formularios.forEach(form => {
            if (form.reset) {
                form.reset();
            }
        });

        // Limpiar campos hidden de ID si existen
        const camposId = modal.querySelectorAll('input[type="hidden"][id*="Id"]');
        camposId.forEach(campo => {
            campo.value = '';
        });
    }

    /**
     * Obtiene el modal actualmente activo
     * @returns {HTMLElement|null} - Modal activo o null
     */
    obtenerModalActivo() {
        for (const modal of this.modalesActivos.keys()) {
            if (modal.style.display === 'block') {
                return modal;
            }
        }
        return null;
    }

    /**
     * Crea un modal dinámicamente
     * @param {Object} config - Configuración del modal
     * @returns {HTMLElement} - Elemento modal creado
     */
    crear(config) {
        const {
            id,
            titulo,
            contenido,
            botones = [],
            clase = '',
            ancho = 'auto'
        } = config;

        // Verificar si ya existe
        if (document.getElementById(id)) {
            console.warn(`Modal con ID "${id}" ya existe`);
            return document.getElementById(id);
        }

        // Crear estructura del modal
        const modal = NutricionUtils.crearElemento('div', {
            id: id,
            className: `modal ${clase}`,
            style: {
                display: 'none',
                position: 'fixed',
                zIndex: '1000',
                left: '0',
                top: '0',
                width: '100%',
                height: '100%',
                backgroundColor: 'rgba(0,0,0,0.5)'
            }
        });

        const contenidoModal = NutricionUtils.crearElemento('div', {
            className: 'modal-content',
            style: {
                backgroundColor: '#fefefe',
                margin: '15% auto',
                padding: '0',
                border: 'none',
                borderRadius: '8px',
                width: ancho,
                maxWidth: '90%',
                boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
            }
        });

        // Header del modal
        const header = NutricionUtils.crearElemento('div', {
            className: 'modal-header',
            style: {
                padding: '20px',
                borderBottom: '1px solid #eee'
            }
        }, `
            <h4 style="margin: 0;">${titulo}</h4>
            <span class="close" style="
                position: absolute;
                right: 20px;
                top: 20px;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                color: #aaa;
            ">&times;</span>
        `);

        // Body del modal
        const body = NutricionUtils.crearElemento('div', {
            className: 'modal-body',
            style: {
                padding: '20px'
            }
        }, contenido);

        // Footer del modal si hay botones
        let footer = null;
        if (botones.length > 0) {
            footer = NutricionUtils.crearElemento('div', {
                className: 'modal-footer',
                style: {
                    padding: '20px',
                    borderTop: '1px solid #eee',
                    textAlign: 'right'
                }
            });

            botones.forEach(boton => {
                const btn = NutricionUtils.crearElemento('button', {
                    type: boton.tipo || 'button',
                    className: boton.clase || 'btn btn-secondary',
                    style: {
                        marginLeft: '10px'
                    }
                }, boton.texto);

                if (boton.onclick) {
                    btn.addEventListener('click', boton.onclick);
                }

                footer.appendChild(btn);
            });
        }

        // Ensamblar modal
        contenidoModal.appendChild(header);
        contenidoModal.appendChild(body);
        if (footer) {
            contenidoModal.appendChild(footer);
        }
        modal.appendChild(contenidoModal);

        // Agregar eventos
        header.querySelector('.close').addEventListener('click', () => {
            this.cerrar(id);
        });

        // Agregar al DOM
        document.body.appendChild(modal);

        return modal;
    }

    /**
     * Confirma una acción con modal
     * @param {string} mensaje - Mensaje de confirmación
     * @param {Function} onConfirm - Callback de confirmación
     * @param {Function} onCancel - Callback de cancelación
     */
    confirmar(mensaje, onConfirm, onCancel = null) {
        const modalId = 'modal-confirmacion-' + Date.now();
        
        const modal = this.crear({
            id: modalId,
            titulo: 'Confirmación',
            contenido: `<p>${mensaje}</p>`,
            ancho: '400px',
            botones: [
                {
                    texto: 'Cancelar',
                    clase: 'btn btn-secondary',
                    onclick: () => {
                        this.cerrar(modalId);
                        if (onCancel) onCancel();
                    }
                },
                {
                    texto: 'Confirmar',
                    clase: 'btn btn-danger',
                    onclick: () => {
                        this.cerrar(modalId);
                        if (onConfirm) onConfirm();
                    }
                }
            ]
        });

        this.abrir(modalId);

        // Auto-remover después de cerrar
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 500);
    }

    /**
     * Muestra un modal de alerta
     * @param {string} mensaje - Mensaje de alerta
     * @param {string} titulo - Título del modal
     * @param {Function} callback - Callback al cerrar
     */
    alerta(mensaje, titulo = 'Información', callback = null) {
        const modalId = 'modal-alerta-' + Date.now();
        
        const modal = this.crear({
            id: modalId,
            titulo: titulo,
            contenido: `<p>${mensaje}</p>`,
            ancho: '400px',
            botones: [
                {
                    texto: 'Aceptar',
                    clase: 'btn btn-primary',
                    onclick: () => {
                        this.cerrar(modalId);
                        if (callback) callback();
                    }
                }
            ]
        });

        this.abrir(modalId);

        // Auto-remover después de cerrar
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 500);
    }

    /**
     * Configura un formulario dentro de un modal
     * @param {string} modalId - ID del modal
     * @param {Object} config - Configuración del formulario
     */
    configurarFormulario(modalId, config) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        const form = modal.querySelector('form');
        if (!form) return;

        // Prevenir submit por defecto
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            if (config.onSubmit) {
                config.onSubmit(e, form);
            }
        });

        // Validación en tiempo real si se especifica
        if (config.validacion) {
            Object.keys(config.validacion).forEach(campoId => {
                const campo = form.querySelector(`#${campoId}`);
                if (campo) {
                    campo.addEventListener('blur', () => {
                        config.validacion[campoId](campo);
                    });
                }
            });
        }
    }
}

// Instancia global del gestor de modales
const modalManager = new ModalManager();

// Funciones de compatibilidad para código existente
function abrirModalNuevo(modalId = 'modalForm') {
    modalManager.abrir(modalId, {
        callback: (modal) => {
            // Limpiar título para modales de creación
            const titulo = modal.querySelector('.modal-title, h4');
            if (titulo && titulo.textContent.includes('Editar')) {
                titulo.textContent = titulo.textContent.replace('Editar', 'Nuevo');
            }
        }
    });
}

function cerrarModal(modalId = 'modalForm') {
    modalManager.cerrar(modalId);
}

function abrirModal(modalId) {
    modalManager.abrir(modalId);
}

// Exportar al namespace global
Object.assign(window.NutricionModals, {
    ModalManager,
    modalManager,
    abrirModalNuevo,
    cerrarModal,
    abrirModal
});

// Exportar funciones directamente para compatibilidad
window.abrirModalNuevo = abrirModalNuevo;
window.cerrarModal = cerrarModal;
window.abrirModal = abrirModal;
window.modalManager = modalManager;