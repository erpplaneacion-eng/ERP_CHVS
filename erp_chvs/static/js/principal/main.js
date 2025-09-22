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
 * Carga las estadísticas para la página principal del módulo
 */
function loadPrincipalStats() {
    // Cargar total de departamentos
    fetch('/principal/api/departamentos/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-departamentos');
            if (element) {
                element.textContent = data.departamentos.length;
            }
        })
        .catch(error => {
            console.error('Error loading departamentos:', error);
            const element = document.getElementById('total-departamentos');
            if (element) {
                element.textContent = '0';
            }
        });

    // Cargar total de municipios
    fetch('/principal/api/municipios/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-municipios');
            if (element) {
                element.textContent = data.municipios.length;
            }
        })
        .catch(error => {
            console.error('Error loading municipios:', error);
            const element = document.getElementById('total-municipios');
            if (element) {
                element.textContent = '0';
            }
        });

    // Cargar total de tipos de documento
    fetch('/principal/api/tipos-documento/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-tipos-documento');
            if (element) {
                element.textContent = data.tipos_documento.length;
            }
        })
        .catch(error => {
            console.error('Error loading tipos documento:', error);
            const element = document.getElementById('total-tipos-documento');
            if (element) {
                element.textContent = '0';
            }
        });

    // Cargar total de tipos de género
    fetch('/principal/api/tipos-genero/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-tipos-genero');
            if (element) {
                element.textContent = data.tipos_genero.length;
            }
        })
        .catch(error => {
            console.error('Error loading tipos genero:', error);
            const element = document.getElementById('total-tipos-genero');
            if (element) {
                element.textContent = '0';
            }
        });

    // Cargar total de modalidades de consumo
    fetch('/principal/api/modalidades-consumo/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-modalidades');
            if (element) {
                element.textContent = data.modalidades.length;
            }
        })
        .catch(error => {
            console.error('Error loading modalidades:', error);
            const element = document.getElementById('total-modalidades');
            if (element) {
                element.textContent = '0';
            }
        });

    // Cargar total de instituciones educativas
    fetch('/principal/api/instituciones/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-instituciones');
            if (element) {
                element.textContent = data.instituciones.length;
            }
        })
        .catch(error => {
            console.error('Error loading instituciones:', error);
            const element = document.getElementById('total-instituciones');
            if (element) {
                element.textContent = '0';
            }
        });

    // Cargar total de sedes educativas
    fetch('/principal/api/sedes/')
        .then(response => response.json())
        .then(data => {
            const element = document.getElementById('total-sedes');
            if (element) {
                element.textContent = data.sedes.length;
            }
        })
        .catch(error => {
            console.error('Error loading sedes:', error);
            const element = document.getElementById('total-sedes');
            if (element) {
                element.textContent = '0';
            }
        });
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
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">&times;</button>
    `;

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
