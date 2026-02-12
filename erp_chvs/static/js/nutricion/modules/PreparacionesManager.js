/**
 * PreparacionesManager.js
 * Maneja toda la lógica relacionada con preparaciones
 * - CRUD de preparaciones
 * - Gestión de modal de nueva preparación
 * - Carga de preparaciones por menú
 * - Eliminación de preparaciones
 */

class PreparacionesManager {
    constructor() {
        this.apiClient = window.nutricionAPI || window.ApiClient;
        this.modalManager = window.modalManager;
        this.componentesAlimentos = [];
        this.modalidadActualId = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadComponentesAlimentos();
    }

    /**
     * Establecer IngredientesManager
     * @param {IngredientesManager} manager - Instancia de IngredientesManager
     */
    setIngredientesManager(manager) {
        this.ingredientesManager = manager;
    }

    /**
     * Establecer ModalesManager
     * @param {ModalesManager} manager - Instancia de ModalesManager
     */
    setModalesManager(manager) {
        this.modalesManager = manager;
    }

    /**
     * Establecer modalidad actual
     * @param {string} modalidadId - ID de la modalidad
     */
    setModalidadActual(modalidadId) {
        this.modalidadActualId = modalidadId;
    }

    /**
     * Configurar event listeners para el módulo de preparaciones
     */
    setupEventListeners() {
        // Event listener para el formulario de nueva preparación
        const formNuevaPrep = document.getElementById('formNuevaPreparacion');
        if (formNuevaPrep) {
            formNuevaPrep.addEventListener('submit', (e) => this.handleSubmitNuevaPreparacion(e));
        }

        // Event listener para mostrar opciones de copia
        const btnMostrarOpciones = document.getElementById('btnMostrarOpcionesCopia');
        if (btnMostrarOpciones) {
            btnMostrarOpciones.addEventListener('click', (e) => this.handleMostrarOpcionesCopia(e));
        }

        // Event listener para ejecutar copia
        const btnEjecutarCopia = document.getElementById('btnEjecutarCopia');
        if (btnEjecutarCopia) {
            btnEjecutarCopia.addEventListener('click', (e) => this.handleEjecutarCopia(e));
        }
    }

    /**
     * Cargar componentes de alimentos desde la API
     */
    async loadComponentesAlimentos() {
        try {
            const response = await fetch('/nutricion/api/componentes-alimentos/');
            const data = await response.json();
            if (data.componentes) {
                this.componentesAlimentos = data.componentes;
            }
        } catch (error) {
            console.error('Error al cargar componentes:', error);
            alert('Error al cargar componentes de alimentos');
        }
    }

    /**
     * Abrir modal de nueva preparación
     * @param {number} menuId - ID del menú
     */
    async abrirModalNuevaPreparacion(menuId) {
        document.getElementById('menuIdPrep').value = menuId;
        document.getElementById('nombrePreparacion').value = '';

        // Resetear y ocultar la sección de copia
        document.getElementById('opcionesCopiaContainer').style.display = 'none';
        document.getElementById('selectPreparacionCopia').innerHTML = '';

        if (this.componentesAlimentos.length === 0) {
            await this.loadComponentesAlimentos();
        }

        this.populateComponentesSelect();

        const modal = document.getElementById('modalNuevaPreparacion');
        
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
     * Poblar el select de componentes de alimentos
     */
    populateComponentesSelect() {
        const selectComponente = document.getElementById('componenteAlimento');
        selectComponente.innerHTML = '<option value="">Seleccione un componente...</option>';

        this.componentesAlimentos.forEach(comp => {
            const option = document.createElement('option');
            option.value = comp.id_componente;
            option.textContent = `${comp.componente} (${comp.id_grupo_alimentos__grupo_alimentos})`;
            selectComponente.appendChild(option);
        });
    }

    /**
     * Manejar envío del formulario de nueva preparación
     * @param {Event} e - Evento del formulario
     */
    async handleSubmitNuevaPreparacion(e) {
        e.preventDefault();
        
        const menuId = document.getElementById('menuIdPrep').value;
        const nombrePrep = document.getElementById('nombrePreparacion').value.trim();
        const componenteId = document.getElementById('componenteAlimento').value;

        if (!nombrePrep) {
            alert('Por favor ingrese un nombre para la preparación');
            return;
        }

        if (!componenteId) {
            alert('Por favor seleccione un componente de alimento');
            return;
        }

        try {
            const response = await fetch('/nutricion/api/preparaciones/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    id_menu: menuId,
                    preparacion: nombrePrep,
                    id_componente: componenteId
                })
            });

            const data = await response.json();
            
            if (data.success || data.id_preparacion) {
                alert(`✓ Preparación "${nombrePrep}" creada exitosamente`);
                document.getElementById('modalNuevaPreparacion').style.display = 'none';
                
                // Notificar al sistema principal para recargar preparaciones
                if (window.menusController && window.menusController.cargarPreparacionesMenu) {
                    window.menusController.cargarPreparacionesMenu(menuId);
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo crear la preparación'));
            }
        } catch (error) {
            console.error('Error al crear preparación:', error);
            alert('Error al crear la preparación');
        }
    }

    /**
     * Manejar mostrar opciones de copia
     * @param {Event} e - Evento del botón
     */
    async handleMostrarOpcionesCopia(e) {
        e.preventDefault();
        
        if (!this.modalidadActualId) {
            alert('No se pudo determinar la modalidad actual.');
            return;
        }

        try {
            const response = await fetch(`/nutricion/api/preparaciones-por-modalidad/${this.modalidadActualId}/`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const select = document.getElementById('selectPreparacionCopia');
            select.innerHTML = '<option value="">-- Seleccione una preparación --</option>';
            
            data.preparaciones.forEach(prep => {
                const option = new Option(prep.nombre, prep.id);
                select.add(option);
            });

            document.getElementById('opcionesCopiaContainer').style.display = 'block';

        } catch (error) {
            console.error('Error al cargar preparaciones para copiar:', error);
            alert(`Error al cargar preparaciones para copiar: ${error.message}`);
        }
    }

    /**
     * Manejar ejecutar copia de preparación
     * @param {Event} e - Evento del botón
     */
    async handleEjecutarCopia(e) {
        const sourceId = document.getElementById('selectPreparacionCopia').value;
        const targetMenuId = document.getElementById('menuIdPrep').value;

        if (!sourceId) {
            alert('Por favor, seleccione una preparación para copiar.');
            return;
        }

        try {
            const response = await fetch('/nutricion/api/preparaciones/copiar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    source_preparacion_id: sourceId,
                    target_menu_id: targetMenuId
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`✓ ${data.message}`);
                document.getElementById('modalNuevaPreparacion').style.display = 'none';
                
                // Notificar al sistema principal para recargar preparaciones
                if (window.menusController && window.menusController.cargarPreparacionesMenu) {
                    window.menusController.cargarPreparacionesMenu(targetMenuId);
                }
            } else {
                throw new Error(data.error || 'Error desconocido al copiar.');
            }

        } catch (error) {
            console.error('Error al copiar preparación:', error);
            alert(`Error: ${error.message}`);
        }
    }

    /**
     * Cargar preparaciones de un menú específico
     * @param {number} menuId - ID del menú
     */
    async cargarPreparacionesMenu(menuId) {
        try {
            const response = await fetch(`/nutricion/api/preparaciones/?menu_id=${menuId}`);
            const data = await response.json();
            const container = document.getElementById('listaPreparacionesAcordeon');
            container.innerHTML = '';

            if (data.preparaciones && data.preparaciones.length > 0) {
                // Cargar todas las cantidades de ingredientes en paralelo
                const cantidadesPromises = data.preparaciones.map(prep =>
                    this.obtenerCantidadIngredientes(prep.id_preparacion)
                );
                const cantidades = await Promise.all(cantidadesPromises);

                // Crear un fragmento de documento para insertar todo de una vez
                const fragment = document.createDocumentFragment();

                data.preparaciones.forEach((prep, index) => {
                    prep.cantidad_ingredientes = cantidades[index];
                    const accordion = this.crearAcordeonPreparacion(prep, menuId);
                    fragment.appendChild(accordion);
                });

                // Insertar todo de una vez
                container.appendChild(fragment);
            } else {
                container.innerHTML = '<div class="no-ingredientes"><i class="fas fa-info-circle"></i> No hay preparaciones asociadas a este menú</div>';
            }
        } catch (error) {
            console.error('Error al cargar preparaciones:', error);
        }
    }

    /**
     * Obtener cantidad de ingredientes de una preparación
     * @param {number} preparacionId - ID de la preparación
     * @returns {Promise<number>} Cantidad de ingredientes
     */
    async obtenerCantidadIngredientes(preparacionId) {
        try {
            const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`);
            const data = await response.json();
            return data.ingredientes ? data.ingredientes.length : 0;
        } catch (error) {
            console.error('Error al obtener cantidad de ingredientes:', error);
            return 0;
        }
    }

    /**
     * Crear acordeón para una preparación
     * @param {Object} preparacion - Datos de la preparación
     * @param {number} menuId - ID del menú
     * @returns {HTMLElement} Elemento del acordeón
     */
    crearAcordeonPreparacion(preparacion, menuId) {
        const accordionDiv = document.createElement('div');
        accordionDiv.className = 'preparacion-accordion';
        
        const header = document.createElement('div');
        header.className = 'preparacion-accordion-header';
        header.innerHTML = `
            <div class="preparacion-info">
                <div class="preparacion-nombre">${preparacion.preparacion}</div>
                <span class="ingredientes-badge">
                    <i class="fas fa-cubes"></i> ${preparacion.cantidad_ingredientes || 0} ingredientes
                </span>
            </div>
            <div class="preparacion-actions">
                <button class="btn btn-icon btn-delete" title="Eliminar preparación">
                    <i class="fas fa-trash"></i>
                </button>
                <i class="fas fa-chevron-down"></i>
            </div>
        `;
        
        header.addEventListener('click', (e) => {
            if (!e.target.closest('.btn-delete')) {
                this.togglePreparacionAccordion(header);
            }
        });
        
        const btnDelete = header.querySelector('.btn-delete');
        btnDelete.addEventListener('click', (e) => {
            e.stopPropagation();
            this.eliminarPreparacion(preparacion.id_preparacion, menuId);
        });
        
        const content = document.createElement('div');
        content.className = 'preparacion-accordion-content';
        content.id = `prep-content-${preparacion.id_preparacion}`;
        
        const container = document.createElement('div');
        container.className = 'ingredientes-container';
        container.innerHTML = `
            <button class="btn-agregar-ingrediente" onclick="abrirAgregarIngrediente(${preparacion.id_preparacion})">
                <i class="fas fa-plus"></i> Agregar Ingrediente
            </button>
            <div id="ingredientes-${preparacion.id_preparacion}" style="margin-top: 15px;">
                <div class="no-ingredientes">Haz clic para cargar ingredientes</div>
            </div>
        `;
        
        content.appendChild(container);
        accordionDiv.appendChild(header);
        accordionDiv.appendChild(content);
        
        return accordionDiv;
    }

    /**
     * Alternar acordeón de preparación
     * @param {HTMLElement} header - Header del acordeón
     */
    togglePreparacionAccordion(header) {
        if (!header) {
            return;
        }

        const content = header.nextElementSibling;
        if (!content) {
            return;
        }

        const isActive = content.classList.contains('active');
        
        document.querySelectorAll('.preparacion-accordion-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.preparacion-accordion-header').forEach(h => h.classList.remove('active'));
        
        if (!isActive) {
            content.classList.add('active');
            header.classList.add('active');
            const prepId = content.id.replace('prep-content-', '');
            const ingredientesDiv = document.getElementById(`ingredientes-${prepId}`);
            
            if (ingredientesDiv && ingredientesDiv.querySelector('.no-ingredientes')) {
                this.cargarIngredientesPreparacion(prepId);
            }
        }
    }

    /**
     * Cargar ingredientes de una preparación
     * @param {number} preparacionId - ID de la preparación
     */
    async cargarIngredientesPreparacion(preparacionId) {
        try {
            const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`);
            const data = await response.json();
            const container = document.getElementById(`ingredientes-${preparacionId}`);
            
            if (data.ingredientes && data.ingredientes.length > 0) {
                container.innerHTML = data.ingredientes.map(ing => `
                    <div class="ingrediente-item">
                        <div class="ingrediente-info">
                            <div class="ingrediente-nombre">
                                <i class="fas fa-carrot"></i> ${ing.id_ingrediente_siesa__id_ingrediente_siesa} - ${ing.id_ingrediente_siesa__nombre_ingrediente}
                            </div>
                        </div>
                        <div class="ingrediente-acciones">
                            <button class="btn-icon btn-delete" onclick="eliminarIngrediente(${preparacionId}, '${ing.id_ingrediente_siesa__id_ingrediente_siesa}')" title="Eliminar">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<div class="no-ingredientes"><i class="fas fa-info-circle"></i> No hay ingredientes agregados</div>';
            }
        } catch (error) {
            console.error('Error al cargar ingredientes:', error);
        }
    }

    /**
     * Eliminar una preparación
     * @param {number} preparacionId - ID de la preparación
     * @param {number} menuId - ID del menú
     */
    async eliminarPreparacion(preparacionId, menuId) {
        if (!confirm('¿Está seguro de eliminar esta preparación?')) {
            return;
        }
        
        try {
            const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('✓ Preparación eliminada exitosamente');
                
                // Notificar al sistema principal para recargar preparaciones
                if (window.menusController && window.menusController.cargarPreparacionesMenu) {
                    window.menusController.cargarPreparacionesMenu(menuId);
                }
            } else {
                alert('Error: ' + (data.error || 'No se pudo eliminar'));
            }
        } catch (error) {
            console.error('Error al eliminar preparación:', error);
            alert('Error al eliminar la preparación');
        }
    }

    /**
     * Cerrar modal de preparación
     */
    cerrarModalPreparacion() {
        document.getElementById('modalNuevaPreparacion').style.display = 'none';
        const nombrePrep = document.getElementById('nombrePreparacion');
        const componenteAlim = document.getElementById('componenteAlimento');
        const menuIdPrep = document.getElementById('menuIdPrep');
        
        if (nombrePrep) nombrePrep.value = '';
        if (componenteAlim) componenteAlim.value = '';
        if (menuIdPrep) menuIdPrep.value = '';
    }

    /**
     * Establecer modalidad actual (para copia de preparaciones)
     * @param {string} modalidadId - ID de la modalidad
     */
    setModalidadActual(modalidadId) {
        this.modalidadActualId = modalidadId;
    }
}

// Exportar para uso global
window.PreparacionesManager = PreparacionesManager;

// Funciones globales para compatibilidad con onclick
window.abrirModalNuevaPreparacion = function(menuId) {
    if (window.preparacionesManager) {
        window.preparacionesManager.abrirModalNuevaPreparacion(menuId);
    }
};

window.cerrarModalPreparacion = function() {
    if (window.preparacionesManager) {
        window.preparacionesManager.cerrarModalPreparacion();
    }
};
