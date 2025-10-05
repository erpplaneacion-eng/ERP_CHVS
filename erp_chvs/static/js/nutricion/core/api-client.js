/**
 * Cliente API centralizado para el módulo de nutrición
 * Centraliza todas las llamadas fetch con manejo consistente de errores y CSRF
 */

// Namespace para API
window.NutricionAPI = window.NutricionAPI || {};

/**
 * Cliente API centralizado
 */
class APIClient {
    constructor() {
        this.baseURL = '/nutricion/api/';
        this.requestsActivas = new Set();
    }

    /**
     * Realiza una petición HTTP
     * @param {string} endpoint - Endpoint de la API
     * @param {Object} opciones - Opciones de la petición
     * @returns {Promise} - Promesa con la respuesta
     */
    async request(endpoint, opciones = {}) {
        const url = this.construirURL(endpoint);
        const requestId = `${opciones.method || 'GET'}-${url}-${Date.now()}`;
        
        try {
            // Configuración por defecto
            const config = {
                method: 'GET',
                headers: {
                    ...NutricionUtils.getDefaultHeaders(),
                    ...opciones.headers
                },
                ...opciones
            };

            // Registrar request activa
            this.requestsActivas.add(requestId);

            // Realizar petición
            const response = await fetch(url, config);
            
            // Manejar respuesta
            return await this.manejarRespuesta(response);
            
        } catch (error) {
            throw this.manejarError(error, endpoint);
        } finally {
            // Remover request activa
            this.requestsActivas.delete(requestId);
        }
    }

    /**
     * Construye la URL completa
     * @param {string} endpoint - Endpoint relativo
     * @returns {string} - URL completa
     */
    construirURL(endpoint) {
        // Si el endpoint ya es una URL completa, devolverla
        if (endpoint.startsWith('http') || endpoint.startsWith('/')) {
            return endpoint;
        }
        
        // Construir URL relativa
        return this.baseURL + endpoint.replace(/^\//, '');
    }

    /**
     * Maneja la respuesta de la API
     * @param {Response} response - Objeto Response
     * @returns {Promise} - Datos de la respuesta
     */
    async manejarRespuesta(response) {
        const contentType = response.headers.get('content-type');
        
        if (!response.ok) {
            let error;
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                error = new Error(data.error || data.message || `Error ${response.status}`);
                error.data = data;
            } else {
                error = new Error(`Error HTTP ${response.status}: ${response.statusText}`);
            }
            error.status = response.status;
            throw error;
        }

        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    }

    /**
     * Maneja errores de la API
     * @param {Error} error - Error ocurrido
     * @param {string} endpoint - Endpoint donde ocurrió el error
     * @returns {Error} - Error procesado
     */
    manejarError(error, endpoint) {
        console.error(`Error en API (${endpoint}):`, error);
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            error.message = 'Error de conexión. Verifique su conexión a internet.';
        }
        
        return error;
    }

    // Métodos HTTP específicos

    /**
     * Petición GET
     * @param {string} endpoint - Endpoint
     * @param {Object} params - Parámetros de consulta
     * @returns {Promise} - Respuesta de la API
     */
    async get(endpoint, params = {}) {
        let url = endpoint;
        if (Object.keys(params).length > 0) {
            const searchParams = new URLSearchParams(params);
            url += (endpoint.includes('?') ? '&' : '?') + searchParams.toString();
        }
        
        return this.request(url, { method: 'GET' });
    }

    /**
     * Petición POST
     * @param {string} endpoint - Endpoint
     * @param {Object} data - Datos a enviar
     * @returns {Promise} - Respuesta de la API
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Petición PUT
     * @param {string} endpoint - Endpoint
     * @param {Object} data - Datos a enviar
     * @returns {Promise} - Respuesta de la API
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Petición PATCH
     * @param {string} endpoint - Endpoint
     * @param {Object} data - Datos a enviar
     * @returns {Promise} - Respuesta de la API
     */
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    /**
     * Petición DELETE
     * @param {string} endpoint - Endpoint
     * @returns {Promise} - Respuesta de la API
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Subida de archivos
     * @param {string} endpoint - Endpoint
     * @param {FormData} formData - Datos del formulario
     * @returns {Promise} - Respuesta de la API
     */
    async upload(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            headers: {
                'X-CSRFToken': NutricionUtils.getCsrfToken()
                // No agregar Content-Type para FormData
            },
            body: formData
        });
    }

    /**
     * Verifica si hay requests activas
     * @returns {boolean} - True si hay requests activas
     */
    tieneRequestsActivas() {
        return this.requestsActivas.size > 0;
    }

    /**
     * Cancela todas las requests activas (si es posible)
     */
    cancelarTodas() {
        this.requestsActivas.clear();
    }
}

/**
 * Servicio específico para endpoints de nutrición
 */
class NutricionService extends APIClient {
    constructor() {
        super();
        this.baseURL = '/nutricion/api/';
    }

    // Métodos específicos para entidades

    // PROGRAMAS
    async obtenerProgramasPorMunicipio(municipioId) {
        return this.get('programas-por-municipio/', { municipio_id: municipioId });
    }

    // MODALIDADES
    async obtenerModalidadesPorPrograma(programaId) {
        return this.get('modalidades-por-programa/', { programa_id: programaId });
    }

    // MENÚS
    async obtenerMenus(programaId) {
        return this.get('menus/', { programa_id: programaId });
    }

    async generarMenusAutomaticos(modalidadId, modalidadNombre) {
        return this.post('generar-menus/', { 
            modalidad_id: modalidadId, 
            modalidad_nombre: modalidadNombre 
        });
    }

    async crearMenuEspecial(data) {
        return this.post('menu-especial/', data);
    }

    async editarMenuEspecial(menuId, data) {
        return this.put(`menu-especial/${menuId}/`, data);
    }

    async eliminarMenuEspecial(menuId) {
        return this.delete(`menu-especial/${menuId}/`);
    }

    // PREPARACIONES
    async obtenerPreparaciones() {
        return this.get('preparaciones/');
    }

    async obtenerPreparacion(id) {
        return this.get(`preparaciones/${id}/`);
    }

    async crearPreparacion(data) {
        return this.post('preparaciones/', data);
    }

    async editarPreparacion(id, data) {
        return this.put(`preparaciones/${id}/`, data);
    }

    async eliminarPreparacion(id) {
        return this.delete(`preparaciones/${id}/`);
    }

    async obtenerPreparacionesMenu(menuId) {
        return this.get(`preparaciones-menu/${menuId}/`);
    }

    // INGREDIENTES
    async obtenerIngredientes() {
        return this.get('ingredientes/');
    }

    async obtenerIngrediente(id) {
        return this.get(`ingredientes/${id}/`);
    }

    async crearIngrediente(data) {
        return this.post('ingredientes/', data);
    }

    async editarIngrediente(id, data) {
        return this.put(`ingredientes/${id}/`, data);
    }

    async eliminarIngrediente(id) {
        return this.delete(`ingredientes/${id}/`);
    }

    async obtenerIngredientesSiesa() {
        return this.get('ingredientes-siesa/');
    }

    async obtenerIngredientesPreparacion(preparacionId) {
        return this.get(`ingredientes-preparacion/${preparacionId}/`);
    }

    async guardarIngredientes(preparacionId, ingredientes) {
        return this.post(`ingredientes-preparacion/${preparacionId}/`, { ingredientes });
    }

    async eliminarIngredientePreparacion(preparacionId, ingredienteId) {
        return this.delete(`ingredientes-preparacion/${preparacionId}/${ingredienteId}/`);
    }

    // ANÁLISIS NUTRICIONAL
    async obtenerAnalisisNutricional(menuId) {
        return this.get(`analisis-nutricional/${menuId}/`);
    }

    async guardarAnalisisNutricional(data) {
        return this.post('guardar-analisis-nutricional/', data);
    }

    async obtenerOCrearAnalisis(menuId, nivelId) {
        return this.post('obtener-crear-analisis/', { menu_id: menuId, nivel_id: nivelId });
    }

    async ajustarPorcentaje(data) {
        return this.post('ajustar-porcentaje/', data);
    }

    async ajustarPeso(data) {
        return this.post('ajustar-peso/', data);
    }
}

/**
 * Wrapper para manejo de errores con UI
 */
class NutricionAPIWithUI extends NutricionService {
    async request(endpoint, opciones = {}) {
        const mostrarLoading = opciones.mostrarLoading !== false;
        const mostrarErrores = opciones.mostrarErrores !== false;
        
        try {
            if (mostrarLoading) {
                NutricionUtils.LoadingManager.mostrar();
            }
            
            const resultado = await super.request(endpoint, opciones);
            
            // Mostrar mensaje de éxito si se especifica
            if (opciones.mensajeExito) {
                NutricionUtils.mostrarNotificacion('success', opciones.mensajeExito);
            }
            
            return resultado;
            
        } catch (error) {
            if (mostrarErrores) {
                NutricionUtils.manejarError(error, `API ${endpoint}`);
            }
            throw error;
        } finally {
            if (mostrarLoading) {
                NutricionUtils.LoadingManager.ocultar();
            }
        }
    }
}

// Instancia global del servicio
const nutricionAPI = new NutricionAPIWithUI();

// Funciones de compatibilidad para código existente
async function realizarPeticionAPI(url, opciones = {}) {
    return nutricionAPI.request(url, opciones);
}

// Exportar al namespace global
Object.assign(window.NutricionAPI, {
    APIClient,
    NutricionService,
    NutricionAPIWithUI,
    nutricionAPI,
    realizarPeticionAPI
});

// Exportar instancia principal para uso directo
window.nutricionAPI = nutricionAPI;