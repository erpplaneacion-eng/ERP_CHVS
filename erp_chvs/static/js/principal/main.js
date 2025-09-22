/**
 * main.js - Funcionalidad JavaScript principal del sitio
 * Este archivo maneja las interacciones comunes a todo el sitio como menú, notificaciones, etc.
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===== NAVEGACIÓN Y MENÚ LATERAL =====
    initializeSidebar();

    // ===== NOTIFICACIONES =====
    setupNotifications();

    // ===== TEMAS Y PREFERENCIAS =====
    setupThemePreferences();

    // ===== MENSAJES DE ALERTA =====
    setupAlertMessages();

    // ===== ESTADÍSTICAS PARA PÁGINA PRINCIPAL =====
    if (window.location.pathname.includes('/principal/') && window.location.pathname.endsWith('/principal/')) {
        loadPrincipalStats();
    }
});

/**
 * Inicializa la funcionalidad del sidebar/menú lateral
 */
function initializeSidebar() {
    // Toggle para el menú lateral en móviles
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            document.body.classList.toggle('sidebar-open');
        });
        
        // Cerrar sidebar al hacer clic fuera en dispositivos móviles
        document.addEventListener('click', function(event) {
            const isMobile = window.innerWidth < 992;
            const clickedOutsideSidebar = !sidebar.contains(event.target) && event.target !== sidebarToggle;
            
            if (isMobile && sidebar.classList.contains('active') && clickedOutsideSidebar) {
                sidebar.classList.remove('active');
                document.body.classList.remove('sidebar-open');
            }
        });
    }
    
    // Expandir/colapsar submenús
    const menuItems = document.querySelectorAll('.sidebar-menu .has-submenu');
    menuItems.forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            link.addEventListener('click', function(e) {
                if (this.nextElementSibling && this.nextElementSibling.classList.contains('submenu')) {
                    e.preventDefault();
                    this.parentElement.classList.toggle('open');
                    
                    const submenu = this.nextElementSibling;
                    if (submenu.style.maxHeight) {
                        submenu.style.maxHeight = null;
                    } else {
                        submenu.style.maxHeight = submenu.scrollHeight + 'px';
                    }
                }
            });
        }
    });
    
    // Resaltar elemento de menú activo
    highlightActiveMenuItem();
}

/**
 * Resalta el elemento de menú correspondiente a la página actual
 */
function highlightActiveMenuItem() {
    const currentPath = window.location.pathname;
    
    // Buscar enlaces que coincidan con la ruta actual
    const menuLinks = document.querySelectorAll('.sidebar-menu a');
    menuLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            
            // Si está en un submenú, expandir el padre
            const parentMenu = link.closest('.submenu');
            if (parentMenu) {
                parentMenu.style.maxHeight = parentMenu.scrollHeight + 'px';
                parentMenu.parentElement.classList.add('open');
            }
        }
    });
}

/**
 * Configura el sistema de notificaciones
 */
function setupNotifications() {
    const notificationToggle = document.getElementById('notification-toggle');
    const notificationDropdown = document.getElementById('notification-dropdown');
    
    if (notificationToggle && notificationDropdown) {
        notificationToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            notificationDropdown.classList.toggle('show');
            
            // Marcar como leídas
            if (notificationDropdown.classList.contains('show')) {
                markNotificationsAsRead();
            }
        });
        
        // Cerrar al hacer clic fuera
        document.addEventListener('click', function(event) {
            if (notificationDropdown.classList.contains('show') && 
                !notificationDropdown.contains(event.target) && 
                event.target !== notificationToggle) {
                notificationDropdown.classList.remove('show');
            }
        });
    }
    
    // TODO: Cargar notificaciones cuando se implemente el endpoint
    // setInterval(loadNotifications, 60000); // Cada minuto
}

/**
 * Carga las notificaciones del usuario
 * TODO: Implementar cuando se cree el endpoint de notificaciones
 */
function loadNotifications() {
    // fetch('/api/notifications/')
    //     .then(response => response.json())
    //     .then(data => {
    //         updateNotificationUI(data);
    //     })
    //     .catch(error => {
    //         console.error('Error cargando notificaciones:', error);
    //     });
    console.log('Sistema de notificaciones no implementado aún');
}

/**
 * Actualiza la UI con las notificaciones recibidas
 * @param {Object} data - Datos de notificaciones
 */
function updateNotificationUI(data) {
    const notificationContainer = document.getElementById('notification-list');
    const notificationBadge = document.getElementById('notification-badge');
    
    if (!notificationContainer) return;
    
    // Actualizar contador
    if (notificationBadge) {
        const unreadCount = data.unreadCount || 0;
        notificationBadge.textContent = unreadCount;
        notificationBadge.style.display = unreadCount > 0 ? 'block' : 'none';
    }
    
    // Actualizar lista
    if (data.notifications && data.notifications.length > 0) {
        notificationContainer.innerHTML = '';
        
        data.notifications.forEach(notification => {
            const notificationItem = document.createElement('div');
            notificationItem.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
            notificationItem.innerHTML = `
                <div class="notification-icon">
                    <i class="fa fa-${notification.icon || 'bell'}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${notification.timeAgo}</div>
                </div>
            `;
            
            notificationContainer.appendChild(notificationItem);
        });
    } else {
        notificationContainer.innerHTML = '<div class="no-notifications">No hay notificaciones</div>';
    }
}

/**
 * Marca las notificaciones como leídas
 */
function markNotificationsAsRead() {
    fetch('/api/notifications/mark-read/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Actualizar UI
        const notificationBadge = document.getElementById('notification-badge');
        if (notificationBadge) {
            notificationBadge.style.display = 'none';
        }
        
        const unreadItems = document.querySelectorAll('.notification-item.unread');
        unreadItems.forEach(item => {
            item.classList.remove('unread');
            item.classList.add('read');
        });
    })
    .catch(error => {
        console.error('Error marcando notificaciones como leídas:', error);
    });
}

/**
 * Obtiene el token CSRF de Django
 * @returns {string} - Token CSRF
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

/**
 * Configura las preferencias de tema (claro/oscuro)
 */
function setupThemePreferences() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Establecer tema inicial basado en preferencia guardada
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            if (savedTheme === 'dark') {
                themeToggle.classList.add('active');
            }
        }
        
        themeToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            
            // Cambiar tema
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
}

/**
 * Configura los mensajes de alerta temporales
 */
function setupAlertMessages() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    
    alerts.forEach(alert => {
        // Agregar botón de cierre si no existe
        if (!alert.querySelector('.close')) {
            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.className = 'close';
            closeBtn.innerHTML = '&times;';
            closeBtn.addEventListener('click', function() {
                alert.remove();
            });
            
            alert.appendChild(closeBtn);
        }
        
        // Auto-cerrar después de cierto tiempo
        if (alert.classList.contains('alert-auto-dismiss')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, 5000);
        }
    });
}

/**
 * Función helper para cargar estadísticas de una API específica
 * @param {string} url - URL de la API
 * @param {string} elementId - ID del elemento HTML donde mostrar el resultado
 * @param {string} dataKey - Clave del objeto JSON que contiene el array de datos
 */
async function loadStatFromAPI(url, elementId, dataKey) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = data[dataKey]?.length || 0;
        }
    } catch (error) {
        console.error(`Error loading ${dataKey}:`, error);
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = '0';
        }
    }
}

/**
 * Carga las estadísticas para la página principal del módulo
 */
function loadPrincipalStats() {
    // Cargar estadísticas de todas las APIs
    loadStatFromAPI('/principal/api/departamentos/', 'total-departamentos', 'departamentos');
    loadStatFromAPI('/principal/api/municipios/', 'total-municipios', 'municipios');
    loadStatFromAPI('/principal/api/tipos-documento/', 'total-tipos-documento', 'tipos_documento');
    loadStatFromAPI('/principal/api/tipos-genero/', 'total-tipos-genero', 'tipos_genero');
    loadStatFromAPI('/principal/api/modalidades-consumo/', 'total-modalidades', 'modalidades');
    loadStatFromAPI('/principal/api/instituciones/', 'total-instituciones', 'instituciones');
    loadStatFromAPI('/principal/api/sedes/', 'total-sedes', 'sedes');
}

/**
 * ===== FUNCIONES COMUNES REUTILIZABLES =====
 * Estas funciones son utilizadas por múltiples módulos del sistema
 */

/**
 * Muestra una notificación temporal en la pantalla
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación: 'info', 'success', 'error', 'warning'
 */
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)}"></i>
        <span>${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;

    // Estilos para la alerta
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideIn 0.3s ease;
    `;

    // Color según el tipo
    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };
    notification.style.backgroundColor = colors[type] || colors.info;

    // Agregar al DOM
    document.body.appendChild(notification);

    // Remover automáticamente después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Función auxiliar para obtener el icono de la notificación
 * @param {string} type - Tipo de notificación
 * @returns {string} - Nombre del icono
 */
function getAlertIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || icons.info;
}

// Exponer función globalmente para asegurar disponibilidad inmediata
window.showNotification = showNotification;


// Agregar estilos CSS para las animaciones si no existen
if (!document.querySelector('#main-notification-styles')) {
    const style = document.createElement('style');
    style.id = 'main-notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .alert-close {
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            margin-left: auto;
        }

        .alert-close:hover {
            opacity: 0.7;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Configura los event listeners globales para el manejo de modales
 * Esta función debe ser llamada desde cada página que use modales
 */
function setupModalEventListeners() {
    // Event listener para cerrar modales con ESC (solo agregar una vez)
    if (!document.body.hasAttribute('data-modal-listeners-setup')) {
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                // Buscar funciones closeModal y closeDetailModal en el contexto global
                if (typeof closeModal === 'function') closeModal();
                if (typeof closeDetailModal === 'function') closeDetailModal();
            }
        });

        // Event listener para cerrar modales haciendo clic fuera
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal-overlay')) {
                // Buscar funciones closeModal y closeDetailModal en el contexto global
                if (typeof closeModal === 'function') closeModal();
                if (typeof closeDetailModal === 'function') closeDetailModal();
            }
        });

        // Marcar que los listeners ya fueron configurados
        document.body.setAttribute('data-modal-listeners-setup', 'true');
    }
}

// Exponer función globalmente para asegurar disponibilidad
window.setupModalEventListeners = setupModalEventListeners;

// Configurar automáticamente los event listeners de modales cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    setupModalEventListeners();
});
