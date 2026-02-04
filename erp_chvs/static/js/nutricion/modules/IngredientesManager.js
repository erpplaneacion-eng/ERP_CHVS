/**
 * IngredientesManager.js
 * Maneja toda la lógica relacionada con ingredientes
 * - CRUD de ingredientes
 * - Gestión de modal de agregar ingredientes
 * - Select2 para dropdowns de ingredientes
 * - Carga de ingredientes SIESA
 */

class IngredientesManager {
    constructor() {
        this.apiClient = window.nutricionAPI || window.ApiClient;
        this.ingredientesSiesa = [];
        
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
     * Abrir modal de agregar ingredientes
     * @param {number} preparacionId - ID de la preparación
     */
    async abrirModalAgregarIngredientes(preparacionId) {
        document.getElementById('preparacionIdIngredientes').value = preparacionId;
        document.getElementById('tbodyIngredientes').innerHTML = '';
        
        if (this.ingredientesSiesa.length === 0) {
            await this.cargarIngredientesSiesa();
        }
        
        this.agregarFilaIngrediente();
        const modal = document.getElementById('modalAgregarIngredientes');
        const modalContent = modal.querySelector('.modal-content');
        
        // MOVER MODAL AL BODY Y FORZAR VISIBILIDAD
        document.body.appendChild(modal);
        
        // FORZAR VISIBILIDAD DEL MODAL
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100vw';
        modal.style.height = '100vh';
        modal.style.zIndex = '9999';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        modal.style.visibility = 'visible';
        modal.style.opacity = '1';
        
        // Forzar visibilidad del contenido con mejores dimensiones
        if (modalContent) {
            modalContent.style.display = 'block';
            modalContent.style.visibility = 'visible';
            modalContent.style.opacity = '1';
            modalContent.style.position = 'relative';
            modalContent.style.zIndex = '10000';
            modalContent.style.width = '90vw';
            modalContent.style.maxWidth = '1200px';
            modalContent.style.height = '80vh';
            modalContent.style.maxHeight = '700px';
            modalContent.style.backgroundColor = 'white';
            modalContent.style.borderRadius = '12px';
            modalContent.style.padding = '25px';
            modalContent.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
            modalContent.style.overflow = 'hidden';
            modalContent.style.display = 'flex';
            modalContent.style.flexDirection = 'column';
        }
    }

    /**
     * Cargar ingredientes SIESA desde la API
     */
    async cargarIngredientesSiesa() {
        try {
            const response = await fetch('/nutricion/api/ingredientes/');
            const data = await response.json();
            if (data.ingredientes) {
                this.ingredientesSiesa = data.ingredientes;
            }
        } catch (error) {
            console.error('Error al cargar ingredientes SIESA:', error);
            alert('Error al cargar lista de ingredientes');
        }
    }

    /**
     * Agregar una nueva fila de ingrediente al modal
     */
    agregarFilaIngrediente() {
        const tbody = document.getElementById('tbodyIngredientes');
        const filaIndex = tbody.children.length;
        const tr = document.createElement('tr');
        tr.className = 'fila-ingrediente';
        tr.id = `fila-ing-${filaIndex}`;
        
        const optionsHTML = '<option value="">Seleccione un ingrediente...</option>' +
            this.ingredientesSiesa.map(ing => `<option value="${ing.id_ingrediente_siesa}">${ing.id_ingrediente_siesa} - ${ing.nombre_ingrediente}</option>`).join('');
        
        tr.innerHTML = `
            <td>
                <select class="select-ingrediente" id="ingrediente-${filaIndex}" required>
                    ${optionsHTML}
                </select>
            </td>
            <td style="text-align: center;">
                <button type="button" class="btn-eliminar-fila" onclick="eliminarFilaIngrediente(${filaIndex})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);

        // Inicializar Select2 para el nuevo dropdown
        $(`#ingrediente-${filaIndex}`).select2({
            placeholder: 'Buscar ingrediente...', 
            allowClear: true,
            width: '100%',
            language: {
                noResults: function() {
                    return "No se encontraron ingredientes";
                },
                searching: function() {
                    return "Buscando...";
                }
            },
            dropdownParent: $('#modalAgregarIngredientes .modal-body-ingredientes')
        });
    }

    /**
     * Eliminar una fila de ingrediente
     * @param {number} index - Índice de la fila
     */
    eliminarFilaIngrediente(index) {
        $(`#ingrediente-${index}`).select2('destroy');

        const fila = document.getElementById(`fila-ing-${index}`);
        if (fila) {
            fila.remove();
        }
    }

    /**
     * Guardar ingredientes de una preparación
     */
    async guardarIngredientes() {
        const preparacionId = document.getElementById('preparacionIdIngredientes').value;
        const tbody = document.getElementById('tbodyIngredientes');
        const filas = tbody.querySelectorAll('.fila-ingrediente');

        if (filas.length === 0) {
            alert('Agregue al menos un ingrediente');
            return;
        }

        const ingredientes = [];
        let hayErrores = false;

        filas.forEach((fila, index) => {
            const ingredienteId = document.getElementById(`ingrediente-${index}`)?.value;

            if (!ingredienteId) {
                hayErrores = true;
                return;
            }

            ingredientes.push({
                id_ingrediente_siesa: ingredienteId
            });
        });

        if (hayErrores) {
            alert('Seleccione un ingrediente en cada fila');
            return;
        }

        try {
            const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    ingredientes: ingredientes
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`✓ ${ingredientes.length} ingrediente(s) agregado(s) exitosamente`);
                this.cerrarModalIngredientes();

                // Recargar ingredientes en el acordeón
                this.cargarIngredientesPreparacion(preparacionId);

                // Actualizar el contador de ingredientes en el badge del acordeón
                this.actualizarContadorIngredientes(preparacionId);
            } else {
                alert('Error: ' + (data.error || 'No se pudieron guardar los ingredientes'));
            }
        } catch (error) {
            console.error('Error al guardar ingredientes:', error);
            alert('Error al guardar ingredientes');
        }
    }

    /**
     * Cerrar modal de ingredientes
     */
    cerrarModalIngredientes() {
        $('.select-ingrediente').each(function() {
            if ($(this).hasClass('select2-hidden-accessible')) {
                $(this).select2('destroy');
            }
        });

        document.getElementById('modalAgregarIngredientes').style.display = 'none';
        document.getElementById('tbodyIngredientes').innerHTML = '';
    }

    /**
     * Eliminar un ingrediente específico
     * @param {number} preparacionId - ID de la preparación
     * @param {string} ingredienteId - ID del ingrediente
     */
    async eliminarIngrediente(preparacionId, ingredienteId) {
        if (!confirm('¿Está seguro de eliminar este ingrediente?')) {
            return;
        }
        
        try {
            const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/${ingredienteId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('✓ Ingrediente eliminado exitosamente');

                // Recargar ingredientes en el acordeón
                this.cargarIngredientesPreparacion(preparacionId);

                // Actualizar el contador de ingredientes en el badge del acordeón
                this.actualizarContadorIngredientes(preparacionId);
            } else {
                alert('Error: ' + (data.error || 'No se pudo eliminar'));
            }
        } catch (error) {
            console.error('Error al eliminar ingrediente:', error);
            alert('Error al eliminar el ingrediente');
        }
    }

    /**
     * Actualizar el contador de ingredientes en el badge del acordeón
     * @param {number} preparacionId - ID de la preparación
     */
    async actualizarContadorIngredientes(preparacionId) {
        try {
            const response = await fetch(`/nutricion/api/preparaciones/${preparacionId}/ingredientes/`);
            const data = await response.json();

            // Calcular cantidad de ingredientes
            const cantidad = data.ingredientes ? data.ingredientes.length : 0;

            // Buscar el contenedor del acordeón de esta preparación
            const contenidoPrep = document.getElementById(`prep-content-${preparacionId}`);
            if (contenidoPrep) {
                // El header es el elemento anterior al contenido
                const header = contenidoPrep.previousElementSibling;
                if (header) {
                    // Buscar el badge de ingredientes
                    const badge = header.querySelector('.ingredientes-badge');
                    if (badge) {
                        badge.innerHTML = `<i class="fas fa-cubes"></i> ${cantidad} ingredientes`;
                    }
                }
            }
        } catch (error) {
            console.error('Error al actualizar contador de ingredientes:', error);
        }
    }

    /**
     * Cargar ingredientes de una preparación específica
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
}

// Exportar para uso global
window.IngredientesManager = IngredientesManager;
