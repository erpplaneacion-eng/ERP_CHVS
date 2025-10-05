/**
 * Utilidades comunes para el módulo de nutrición
 * Funciones reutilizables extraídas de múltiples archivos
 */

// Namespace para utilidades de nutrición
window.NutricionUtils = window.NutricionUtils || {};

/**
 * Obtiene el valor de una cookie por nombre
 * @param {string} name - Nombre de la cookie
 * @returns {string|null} - Valor de la cookie o null si no existe
 */
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

/**
 * Obtiene el token CSRF para requests
 * @returns {string} - Token CSRF
 */
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    if (!token) {
        console.warn('No se pudo obtener el token CSRF');
    }
    return token;
}

/**
 * Configuración de headers por defecto para requests
 * @returns {Object} - Headers con CSRF token
 */
function getDefaultHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
    };
}

/**
 * Muestra una notificación en la UI
 * @param {string} tipo - Tipo de notificación ('success', 'error', 'warning', 'info')
 * @param {string} mensaje - Mensaje a mostrar
 * @param {number} duracion - Duración en milisegundos (default: 3000)
 */
function mostrarNotificacion(tipo, mensaje, duracion = 3000) {
    // Crear contenedor si no existe
    let container = document.getElementById('notificaciones-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificaciones-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }

    // Crear notificación
    const notificacion = document.createElement('div');
    notificacion.className = `notificacion ${tipo}`;
    notificacion.style.cssText = `
        background: ${getNotificationColor(tipo)};
        color: white;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        cursor: pointer;
    `;
    notificacion.textContent = mensaje;

    // Agregar al container
    container.appendChild(notificacion);

    // Animar entrada
    setTimeout(() => {
        notificacion.style.opacity = '1';
        notificacion.style.transform = 'translateX(0)';
    }, 10);

    // Remover automáticamente
    const removeTimeout = setTimeout(() => {
        removeNotification(notificacion);
    }, duracion);

    // Remover al hacer click
    notificacion.addEventListener('click', () => {
        clearTimeout(removeTimeout);
        removeNotification(notificacion);
    });
}

/**
 * Obtiene el color para cada tipo de notificación
 * @param {string} tipo - Tipo de notificación
 * @returns {string} - Color CSS
 */
function getNotificationColor(tipo) {
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    return colors[tipo] || colors.info;
}

/**
 * Remueve una notificación con animación
 * @param {HTMLElement} notificacion - Elemento de notificación
 */
function removeNotification(notificacion) {
    notificacion.style.opacity = '0';
    notificacion.style.transform = 'translateX(100%)';
    setTimeout(() => {
        if (notificacion.parentNode) {
            notificacion.parentNode.removeChild(notificacion);
        }
    }, 300);
}

/**
 * Debounce function para limitar la frecuencia de ejecución
 * @param {Function} func - Función a ejecutar
 * @param {number} wait - Tiempo de espera en ms
 * @returns {Function} - Función debounced
 */
function debounce(func, wait) {
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
 * Formatea números con separadores de miles
 * @param {number} numero - Número a formatear
 * @param {number} decimales - Número de decimales (default: 2)
 * @returns {string} - Número formateado
 */
function formatearNumero(numero, decimales = 2) {
    if (numero === null || numero === undefined || isNaN(numero)) {
        return '0.00';
    }
    return Number(numero).toFixed(decimales).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Valida si un string es un número válido
 * @param {string} valor - Valor a validar
 * @returns {boolean} - True si es número válido
 */
function esNumeroValido(valor) {
    return !isNaN(valor) && !isNaN(parseFloat(valor)) && isFinite(valor);
}

/**
 * Sanitiza texto para prevenir XSS
 * @param {string} texto - Texto a sanitizar
 * @returns {string} - Texto sanitizado
 */
function sanitizarTexto(texto) {
    if (typeof texto !== 'string') return '';
    
    const div = document.createElement('div');
    div.textContent = texto;
    return div.innerHTML;
}

/**
 * Crea un elemento DOM con atributos
 * @param {string} tag - Tag del elemento
 * @param {Object} atributos - Atributos del elemento
 * @param {string} contenido - Contenido del elemento
 * @returns {HTMLElement} - Elemento creado
 */
function crearElemento(tag, atributos = {}, contenido = '') {
    const elemento = document.createElement(tag);
    
    Object.keys(atributos).forEach(attr => {
        if (attr === 'className') {
            elemento.className = atributos[attr];
        } else if (attr === 'style' && typeof atributos[attr] === 'object') {
            Object.assign(elemento.style, atributos[attr]);
        } else {
            elemento.setAttribute(attr, atributos[attr]);
        }
    });
    
    if (contenido) {
        elemento.innerHTML = contenido;
    }
    
    return elemento;
}

/**
 * Manejo centralizado de errores
 * @param {Error} error - Error a manejar
 * @param {string} contexto - Contexto donde ocurrió el error
 */
function manejarError(error, contexto = '') {
    console.error(`Error en ${contexto}:`, error);
    
    let mensaje = 'Ha ocurrido un error inesperado';
    
    if (error.message) {
        mensaje = error.message;
    } else if (typeof error === 'string') {
        mensaje = error;
    }
    
    mostrarNotificacion('error', `${contexto ? contexto + ': ' : ''}${mensaje}`);
}

/**
 * Loading spinner global
 */
const LoadingManager = {
    elemento: null,
    contador: 0,
    
    mostrar(mensaje = 'Cargando...') {
        this.contador++;
        
        if (!this.elemento) {
            this.elemento = crearElemento('div', {
                id: 'loading-global',
                style: {
                    position: 'fixed',
                    top: '0',
                    left: '0',
                    width: '100%',
                    height: '100%',
                    backgroundColor: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    zIndex: '9999'
                }
            }, `
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="margin-bottom: 10px;">
                        <i class="fas fa-spinner fa-spin fa-2x"></i>
                    </div>
                    <div id="loading-mensaje">${mensaje}</div>
                </div>
            `);
            document.body.appendChild(this.elemento);
        } else {
            document.getElementById('loading-mensaje').textContent = mensaje;
            this.elemento.style.display = 'flex';
        }
    },
    
    ocultar() {
        this.contador = Math.max(0, this.contador - 1);
        
        if (this.contador === 0 && this.elemento) {
            this.elemento.style.display = 'none';
        }
    }
};

// Exportar utilidades al namespace global
Object.assign(window.NutricionUtils, {
    getCookie,
    getCsrfToken,
    getDefaultHeaders,
    mostrarNotificacion,
    debounce,
    formatearNumero,
    esNumeroValido,
    sanitizarTexto,
    crearElemento,
    manejarError,
    LoadingManager
});

// También exportar funciones directamente para compatibilidad
window.getCookie = getCookie;
window.getCsrfToken = getCsrfToken;
window.mostrarNotificacionGuardado = mostrarNotificacion; // Alias para compatibilidad