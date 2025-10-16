/**
 * FiltrosManager.js
 * Maneja toda la lógica relacionada con filtros
 * - Filtro de municipio
 * - Filtro de programa
 * - Aplicación de filtros
 * - Reset de filtros
 */

class FiltrosManager {
    constructor() {
        this.municipioActual = null;
        this.programaActual = null;
        this.onFiltrosAplicados = null; // Callback cuando se aplican filtros
        
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    /**
     * Configurar event listeners para filtros
     */
    setupEventListeners() {
        // Filtro de municipio
        const filtroMunicipio = document.getElementById('filtroMunicipio');
        if (filtroMunicipio) {
            filtroMunicipio.addEventListener('change', (e) => this.handleFiltroMunicipio(e));
        }

        // Filtro de programa
        const filtroPrograma = document.getElementById('filtroPrograma');
        if (filtroPrograma) {
            filtroPrograma.addEventListener('change', (e) => this.handleFiltroPrograma(e));
        }

        // Botón aplicar filtros
        const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
        if (btnAplicarFiltros) {
            btnAplicarFiltros.addEventListener('click', (e) => this.handleAplicarFiltros(e));
        }
    }

    /**
     * Manejar cambio en filtro de municipio
     * @param {Event} e - Evento del select
     */
    async handleFiltroMunicipio(e) {
        const municipioId = e.target.value;
        this.municipioActual = municipioId;
        
        if (municipioId) {
            await this.cargarProgramasPorMunicipio(municipioId);
        } else {
            this.resetearFiltros();
        }
    }

    /**
     * Manejar cambio en filtro de programa
     * @param {Event} e - Evento del select
     */
    handleFiltroPrograma(e) {
        const programaId = e.target.value;
        this.programaActual = programaId;
        document.getElementById('btnAplicarFiltros').disabled = !programaId;
    }

    /**
     * Manejar aplicar filtros
     * @param {Event} e - Evento del botón
     */
    handleAplicarFiltros(e) {
        const programaId = document.getElementById('filtroPrograma').value;
        if (programaId && this.onFiltrosAplicados) {
            this.onFiltrosAplicados(programaId);
        }
    }

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
     * Resetear todos los filtros
     */
    resetearFiltros() {
        document.getElementById('filtroPrograma').innerHTML = '<option value="">Primero seleccione un municipio...</option>';
        document.getElementById('filtroPrograma').disabled = true;
        document.getElementById('btnAplicarFiltros').disabled = true;
        document.getElementById('infoProgramaContainer').style.display = 'none';
        document.getElementById('modalidadesContainer').innerHTML = '';
        document.getElementById('mensajeInicial').style.display = 'block';
        
        this.programaActual = null;
    }

    /**
     * Establecer callback para cuando se aplican filtros
     * @param {Function} callback - Función a ejecutar cuando se aplican filtros
     */
    setOnFiltrosAplicados(callback) {
        this.onFiltrosAplicados = callback;
    }

    /**
     * Obtener municipio actual
     * @returns {string|null} ID del municipio actual
     */
    getMunicipioActual() {
        return this.municipioActual;
    }

    /**
     * Obtener programa actual
     * @returns {string|null} ID del programa actual
     */
    getProgramaActual() {
        return this.programaActual;
    }

    /**
     * Establecer municipio actual
     * @param {string} municipioId - ID del municipio
     */
    setMunicipioActual(municipioId) {
        this.municipioActual = municipioId;
        const filtroMunicipio = document.getElementById('filtroMunicipio');
        if (filtroMunicipio) {
            filtroMunicipio.value = municipioId;
        }
    }

    /**
     * Establecer programa actual
     * @param {string} programaId - ID del programa
     */
    setProgramaActual(programaId) {
        this.programaActual = programaId;
        const filtroPrograma = document.getElementById('filtroPrograma');
        if (filtroPrograma) {
            filtroPrograma.value = programaId;
            document.getElementById('btnAplicarFiltros').disabled = false;
        }
    }

    /**
     * Verificar si hay filtros aplicados
     * @returns {boolean} True si hay filtros aplicados
     */
    tieneFiltrosAplicados() {
        return this.municipioActual && this.programaActual;
    }

    /**
     * Obtener nombre del municipio seleccionado
     * @returns {string} Nombre del municipio
     */
    getNombreMunicipio() {
        const filtroMunicipio = document.getElementById('filtroMunicipio');
        if (filtroMunicipio && filtroMunicipio.selectedIndex >= 0) {
            return filtroMunicipio.options[filtroMunicipio.selectedIndex].text;
        }
        return '';
    }

    /**
     * Obtener nombre del programa seleccionado
     * @returns {string} Nombre del programa
     */
    getNombrePrograma() {
        const filtroPrograma = document.getElementById('filtroPrograma');
        if (filtroPrograma && filtroPrograma.selectedIndex >= 0) {
            return filtroPrograma.options[filtroPrograma.selectedIndex].text;
        }
        return '';
    }

    /**
     * Habilitar/deshabilitar filtros
     * @param {boolean} enabled - True para habilitar
     */
    setFiltrosEnabled(enabled) {
        const filtroMunicipio = document.getElementById('filtroMunicipio');
        const filtroPrograma = document.getElementById('filtroPrograma');
        const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
        
        if (filtroMunicipio) filtroMunicipio.disabled = !enabled;
        if (filtroPrograma) filtroPrograma.disabled = !enabled;
        if (btnAplicarFiltros) btnAplicarFiltros.disabled = !enabled;
    }
}

// Exportar para uso global
window.FiltrosManager = FiltrosManager;
