/**
 * MenusEspecialesManager.js
 * Maneja toda la lógica relacionada con menús especiales
 * - Creación de menús especiales
 * - Edición de menús especiales
 * - Eliminación de menús especiales
 * - Gestión de modales de menús especiales
 */

class MenusEspecialesManager {
    constructor() {
        this.programaActual = null;
        this.modalesManager = null;
        
        this.init();
    }

    init() {
        // Inicialización del manager
    }

    /**
     * Establecer ModalesManager
     * @param {ModalesManager} manager - Instancia de ModalesManager
     */
    setModalesManager(manager) {
        this.modalesManager = manager;
    }

    /**
     * Abrir modal de menú especial
     * @param {string} modalidadId - ID de la modalidad
     */
    abrirModalMenuEspecial(modalidadId) {
        document.getElementById('modalidadIdEspecial').value = modalidadId;
        document.getElementById('nombreMenuEspecial').value = '';
        
        const modal = document.getElementById('modalMenuEspecial');
        
        // Mover modal al body para evitar problemas de z-index
        document.body.appendChild(modal);
        
        // Forzar estilos para visibilidad
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.zIndex = '1100';
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    }

    /**
     * Crear menú especial
     */
    async crearMenuEspecial() {
        const modalidadId = document.getElementById('modalidadIdEspecial').value;
        const nombreMenu = document.getElementById('nombreMenuEspecial').value.trim();
        
        if (!nombreMenu) {
            alert('Por favor ingrese un nombre para el menú especial');
            return;
        }

        try {
            const response = await fetch('/nutricion/api/crear-menu-especial/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    programa_id: this.programaActual.id,
                    modalidad_id: modalidadId,
                    nombre_menu: nombreMenu
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert(`✓ Menú especial "${nombreMenu}" creado exitosamente`);
                document.getElementById('modalMenuEspecial').style.display = 'none';
                
                // Notificar al sistema principal para recargar modalidades
                if (this.onModalidadesRecargadas) {
                    this.onModalidadesRecargadas(this.programaActual.id);
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo crear el menú especial'));
            }
        } catch (error) {
            console.error('Error al crear menú especial:', error);
            alert('Error al crear menú especial');
        }
    }

    /**
     * Abrir modal de editar menú especial
     * @param {number} menuId - ID del menú
     * @param {string} nombreActual - Nombre actual del menú
     */
    abrirEditarMenuEspecial(menuId, nombreActual) {
        document.getElementById('menuIdEditar').value = menuId;
        document.getElementById('nombreMenuEditado').value = nombreActual;
        
        const modal = document.getElementById('modalEditarMenuEspecial');
        
        // Mover modal al body para evitar problemas de z-index
        document.body.appendChild(modal);
        
        // Forzar estilos para visibilidad
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.zIndex = '1100';
        modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    }

    /**
     * Guardar edición de menú especial
     */
    async guardarEdicionMenuEspecial() {
        const menuId = document.getElementById('menuIdEditar').value;
        const nuevoNombre = document.getElementById('nombreMenuEditado').value.trim();

        if (!nuevoNombre) {
            alert('Por favor ingrese un nombre para el menú');
            return;
        }

        try {
            const response = await fetch(`/nutricion/api/menus/${menuId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    menu: nuevoNombre
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`✓ Menú actualizado a "${nuevoNombre}" exitosamente`);
                document.getElementById('modalEditarMenuEspecial').style.display = 'none';
                
                // Notificar al sistema principal para recargar modalidades
                if (this.onModalidadesRecargadas) {
                    this.onModalidadesRecargadas(this.programaActual.id);
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo actualizar el menú'));
            }
        } catch (error) {
            console.error('Error al actualizar menú especial:', error);
            alert('Error al actualizar el menú especial');
        }
    }

    /**
     * Eliminar menú especial
     * @param {number} menuId - ID del menú
     * @param {string} nombreMenu - Nombre del menú
     */
    async eliminarMenuEspecial(menuId, nombreMenu) {
        if (!confirm(`¿Está seguro de eliminar el menú especial "${nombreMenu}"?\n\nEsta acción también eliminará todas las preparaciones asociadas.`)) {
            return;
        }

        try {
            const response = await fetch(`/nutricion/api/menus/${menuId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                alert(`✓ Menú especial "${nombreMenu}" eliminado exitosamente`);
                
                // Notificar al sistema principal para recargar modalidades
                if (this.onModalidadesRecargadas) {
                    this.onModalidadesRecargadas(this.programaActual.id);
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo eliminar el menú'));
            }
        } catch (error) {
            console.error('Error al eliminar menú especial:', error);
            alert('Error al eliminar el menú especial');
        }
    }

    /**
     * Establecer programa actual
     * @param {Object} programa - Datos del programa
     */
    setProgramaActual(programa) {
        this.programaActual = programa;
    }

    /**
     * Establecer callback para cuando se recargan modalidades
     * @param {Function} callback - Función a ejecutar
     */
    setOnModalidadesRecargadas(callback) {
        this.onModalidadesRecargadas = callback;
    }

    /**
     * Cerrar modal de menú especial
     */
    cerrarModalMenuEspecial() {
        const modal = document.getElementById('modalMenuEspecial');
        if (modal) {
            modal.style.display = 'none';
            
            // Limpiar formulario
            document.getElementById('modalidadIdEspecial').value = '';
            document.getElementById('nombreMenuEspecial').value = '';
        }
    }

    /**
     * Cerrar modal de editar menú especial
     */
    cerrarModalEditarMenuEspecial() {
        const modal = document.getElementById('modalEditarMenuEspecial');
        if (modal) {
            modal.style.display = 'none';
            
            // Limpiar formulario
            document.getElementById('menuIdEditar').value = '';
            document.getElementById('nombreMenuEditado').value = '';
        }
    }

    /**
     * Validar nombre de menú especial
     * @param {string} nombre - Nombre del menú
     * @returns {Object} Resultado de la validación
     */
    validarNombreMenu(nombre) {
        const nombreTrimmed = nombre.trim();
        
        if (!nombreTrimmed) {
            return {
                valido: false,
                mensaje: 'El nombre del menú no puede estar vacío'
            };
        }
        
        if (nombreTrimmed.length < 3) {
            return {
                valido: false,
                mensaje: 'El nombre del menú debe tener al menos 3 caracteres'
            };
        }
        
        if (nombreTrimmed.length > 100) {
            return {
                valido: false,
                mensaje: 'El nombre del menú no puede exceder 100 caracteres'
            };
        }
        
        // Verificar caracteres especiales
        const caracteresEspeciales = /[<>:"/\\|?*]/;
        if (caracteresEspeciales.test(nombreTrimmed)) {
            return {
                valido: false,
                mensaje: 'El nombre del menú contiene caracteres no permitidos'
            };
        }
        
        return {
            valido: true,
            mensaje: 'Nombre válido'
        };
    }

    /**
     * Verificar si un nombre de menú ya existe en la modalidad
     * @param {string} nombre - Nombre del menú
     * @param {string} modalidadId - ID de la modalidad
     * @returns {Promise<boolean>} True si ya existe
     */
    async verificarNombreExistente(nombre, modalidadId) {
        try {
            // TODO: Implementar verificación en el backend
            // Por ahora retornamos false
            return false;
        } catch (error) {
            console.error('Error al verificar nombre existente:', error);
            return false;
        }
    }

    /**
     * Obtener estadísticas de menús especiales
     * @param {string} modalidadId - ID de la modalidad
     * @returns {Object} Estadísticas
     */
    getEstadisticasMenusEspeciales(modalidadId) {
        // TODO: Implementar estadísticas
        return {
            totalMenusEspeciales: 0,
            menusConPreparaciones: 0,
            menusSinPreparaciones: 0
        };
    }

    /**
     * Duplicar menú especial
     * @param {number} menuId - ID del menú a duplicar
     * @param {string} nuevoNombre - Nombre para el menú duplicado
     */
    async duplicarMenuEspecial(menuId, nuevoNombre) {
        try {
            const response = await fetch('/nutricion/api/duplicar-menu-especial/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    menu_id: menuId,
                    nuevo_nombre: nuevoNombre
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`✓ Menú especial "${nuevoNombre}" duplicado exitosamente`);
                
                // Notificar al sistema principal para recargar modalidades
                if (this.onModalidadesRecargadas) {
                    this.onModalidadesRecargadas(this.programaActual.id);
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo duplicar el menú'));
            }
        } catch (error) {
            console.error('Error al duplicar menú especial:', error);
            alert('Error al duplicar el menú especial');
        }
    }

    /**
     * Exportar menú especial a Excel
     * @param {number} menuId - ID del menú
     * @param {string} nombreMenu - Nombre del menú
     */
    exportarMenuEspecial(menuId, nombreMenu) {
        const url = `/nutricion/exportar-excel/${menuId}/`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `Menu_Especial_${nombreMenu.replace(/[^a-zA-Z0-9]/g, '_')}.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Exportar para uso global
window.MenusEspecialesManager = MenusEspecialesManager;
