/**
 * common.js - Funcionalidad JavaScript común para todo el proyecto
 * Este archivo contiene utilidades y funciones compartidas entre múltiples aplicaciones
 */

// Objeto para almacenar todas las utilidades comunes
const ERPUtils = {
    /**
     * Formatea un número como moneda (COP)
     * @param {number} amount - El monto a formatear
     * @return {string} El monto formateado como moneda
     */
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    },
    
    /**
     * Formatea una fecha en formato DD/MM/YYYY
     * @param {string|Date} date - La fecha a formatear
     * @return {string} La fecha formateada
     */
    formatDate: function(date) {
        if (!date) return '';
        
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        
        return `${day}/${month}/${year}`;
    },
    
    /**
     * Valida que un string tenga un formato de correo electrónico válido
     * @param {string} email - El correo a validar
     * @return {boolean} true si es válido, false si no
     */
    isValidEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
    },
    
    /**
     * Muestra un mensaje de alerta personalizado
     * @param {string} message - El mensaje a mostrar
     * @param {string} type - El tipo de alerta (success, error, warning, info)
     */
    showAlert: function(message, type = 'info') {
        // Si existe la biblioteca SweetAlert2, usarla
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                text: message,
                icon: type,
                confirmButtonText: 'Aceptar'
            });
        } else {
            // Si no, usar alert nativo
            alert(message);
        }
    },
    
    /**
     * Función para validar campos requeridos en un formulario
     * @param {HTMLFormElement} form - El formulario a validar
     * @param {Array} fieldNames - Lista de nombres de campos requeridos
     * @return {boolean} true si todos los campos requeridos están completos
     */
    validateRequiredFields: function(form, fieldNames) {
        let isValid = true;
        let errorMessage = '';
        
        fieldNames.forEach(function(fieldName) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field && !field.value.trim()) {
                isValid = false;
                errorMessage += `- El campo ${fieldName} es obligatorio\n`;
                field.style.borderColor = '#e74c3c';
            } else if (field) {
                field.style.borderColor = '';
            }
        });
        
        if (!isValid) {
            this.showAlert('Por favor complete los siguientes campos:\n\n' + errorMessage, 'error');
        }
        
        return isValid;
    }
};

// Extender los prototipos nativos con métodos útiles (usar con precaución)
if (!String.prototype.capitalize) {
    String.prototype.capitalize = function() {
        return this.charAt(0).toUpperCase() + this.slice(1).toLowerCase();
    };
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Código de inicialización global aquí, si es necesario
});
