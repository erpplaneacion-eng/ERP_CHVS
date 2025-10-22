/**
 * AnalisisNutricionalManager.js
 * Maneja toda la lógica relacionada con análisis nutricional
 * - Carga de análisis nutricional por menú
 * - Renderizado de datos nutricionales
 * - Cálculos de adecuación
 * - Gestión de inputs editables
 */

class AnalisisNutricionalManager {
    constructor() {
        this.menuActual = null;
        this.datosNutricionales = null;
        this.requerimientosNiveles = {};
        
        this.init();
    }

    init() {
        // Inicialización del manager
    }

    /**
     * Abrir modal de análisis nutricional
     * @param {number} menuId - ID del menú
     */
    abrirModalAnalisisNutricional(menuId) {
        const modal = document.getElementById('modalAnalisisNutricional');
        if (modal) {
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
            modal.style.zIndex = '1200';
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';

            const menuNumero = document.getElementById('menuNumeroModal').textContent;
            document.getElementById('menuNombreAnalisis').textContent = menuNumero;

            this.cargarAnalisisNutricional(menuId);
        }
    }

    /**
     * Cargar análisis nutricional
     * @param {number} menuId - ID del menú
     */
    async cargarAnalisisNutricional(menuId) {
        try {
            const contenidoAnalisis = document.getElementById('contenidoAnalisis');

            contenidoAnalisis.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin fa-3x"></i><p>Calculando análisis nutricional...</p></div>';

            const response = await fetch(`/nutricion/api/menus/${menuId}/analisis-nutricional/`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Error al cargar análisis');
            }

            this.renderizarAnalisisNutricional(data);

        } catch (error) {
            console.error('Error al cargar análisis nutricional:', error);
            document.getElementById('contenidoAnalisis').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> Error al cargar el análisis nutricional: ${error.message}
                </div>
            `;
        }
    }

    /**
     * Renderizar análisis nutricional
     * @param {Object} data - Datos del análisis nutricional
     */
    renderizarAnalisisNutricional(data) {
        this.menuActual = data.menu;
        this.datosNutricionales = data;
        
        const contenidoAnalisis = document.getElementById('contenidoAnalisis');

        if (!data.success) {
            contenidoAnalisis.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error: ${data.error}
                </div>
            `;
            return;
        }

        const { menu, analisis_por_nivel } = data;
        
        this.requerimientosNiveles = {};
        analisis_por_nivel.forEach((nivel, index) => {
            this.requerimientosNiveles[index] = nivel.requerimientos;
        });

        contenidoAnalisis.innerHTML = `
            <div class="menu-info-header">
                <h4><i class="fas fa-utensils"></i> ${menu.nombre}</h4>
                <div class="menu-details">
                    <span class="badge badge-primary">Programa: ${menu.programa}</span>
                    <span class="badge badge-secondary">Modalidad: ${menu.modalidad}</span>
                </div>
            </div>
            
            <div class="analisis-niveles-container">
                <h5><i class="fas fa-graduation-cap"></i> Análisis por Nivel Escolar</h5>
                <div class="niveles-accordion" id="nivelesAccordion">
                    ${analisis_por_nivel.map((nivel, index) => this.crearAccordionNivelEscolar(nivel, index)).join('')}
                </div>
            </div>
            
            <!-- Botones de acción -->
            <div class="analisis-actions mt-4">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="action-buttons-left">
                        <button type="button" class="btn btn-success btn-lg" id="btnGuardarAnalisis">
                            <i class="fas fa-save"></i> Guardar Análisis Nutricional
                        </button>
                    </div>
                    <div class="action-buttons-right">
                        <button type="button" class="btn btn-secondary btn-lg" onclick="cerrarModalAnalisisNutricional()">
                            <i class="fas fa-times"></i> Cerrar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.inicializarEventosInputs();
        this.inicializarEventosBotones();
    }

    /**
     * Crear acordeón para nivel escolar
     * @param {Object} nivel - Datos del nivel
     * @param {number} index - Índice del nivel
     * @returns {string} HTML del acordeón
     */
    crearAccordionNivelEscolar(nivel, index) {
        const cardId = `collapse-${index}`;
        const isOpen = nivel.es_programa_actual;

        return `
            <div class="card nivel-card">
                <div class="card-header" id="heading-${index}">
                    <h6 class="mb-0">
                        <button class="btn btn-link nivel-header-btn ${isOpen ? '' : 'collapsed'}" type="button" 
                                data-target="#${cardId}" 
                                aria-expanded="${isOpen ? 'true' : 'false'}" aria-controls="${cardId}">
                            <i class="fas fa-graduation-cap"></i>
                            ${nivel.nivel_escolar.nombre}
                            <div class="nivel-summary">
                                <span class="badge badge-primary">${nivel.totales.calorias_kcal.toFixed(0)} Kcal</span>
                                <span class="badge badge-success">${nivel.totales.peso_neto_total.toFixed(0)}g neto</span>
                                <span class="badge badge-warning">${nivel.totales.peso_bruto_total.toFixed(0)}g bruto</span>
                            </div>
                            <i class="fas fa-chevron-down toggle-icon" style="transform: ${isOpen ? 'rotate(180deg)' : 'rotate(0deg)'}"></i>
                        </button>
                    </h6>
                </div>
                
                <div id="${cardId}" class="collapse ${isOpen ? 'show' : ''}" 
                     aria-labelledby="heading-${index}" data-parent="#nivelesAccordion">
                    <div class="card-body">
                        ${this.crearContenidoNivel(nivel, index)}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Crear contenido del nivel
     * @param {Object} nivel - Datos del nivel
     * @param {number} index - Índice del nivel
     * @returns {string} HTML del contenido
     */
    crearContenidoNivel(nivel, index) {
        return `
            <div class="nivel-totales mb-3">
                <h6><i class="fas fa-calculator"></i> Totales del Nivel</h6>
                <div class="totales-grid-mini">
                    ${this.crearGridTotales(nivel.totales, nivel.porcentajes_adecuacion, index)}
                </div>
                
                <h6 class="mt-3"><i class="fas fa-target"></i> Requerimientos</h6>
                <div class="requerimientos-grid-mini">
                    ${this.crearGridRequerimientos(nivel.requerimientos)}
                </div>
                
                <h6 class="mt-3"><i class="fas fa-percentage"></i> % de Adecuación (Editable)</h6>
                <div class="adecuacion-grid-mini">
                    ${this.crearGridAdecuacion(nivel.porcentajes_adecuacion, index)}
                </div>
            </div>
            
            <div class="preparaciones-container">
                <h6><i class="fas fa-list-ul"></i> Preparaciones e Ingredientes</h6>
                ${nivel.preparaciones.map((prep, prepIndex) => this.crearPreparacion(prep, index, prepIndex)).join('')}
            </div>
        `;
    }

    /**
     * Crear grid de totales
     * @param {Object} totales - Totales del nivel
     * @param {Object} porcentajes - Porcentajes de adecuación
     * @param {number} index - Índice del nivel
     * @returns {string} HTML del grid
     */
    crearGridTotales(totales, porcentajes, index) {
        const nutrientes = [
            { key: 'calorias_kcal', label: 'Calorías', suffix: 'Kcal', id: `nivel-${index}-calorias` },
            { key: 'proteina_g', label: 'Proteína', suffix: 'g', id: `nivel-${index}-proteina` },
            { key: 'grasa_g', label: 'Grasa', suffix: 'g', id: `nivel-${index}-grasa` },
            { key: 'cho_g', label: 'CHO', suffix: 'g', id: `nivel-${index}-cho` },
            { key: 'calcio_mg', label: 'Calcio', suffix: 'mg', id: `nivel-${index}-calcio` },
            { key: 'hierro_mg', label: 'Hierro', suffix: 'mg', id: `nivel-${index}-hierro` },
            { key: 'sodio_mg', label: 'Sodio', suffix: 'mg', id: `nivel-${index}-sodio` }
        ];

        return nutrientes.map(nutriente => `
            <div class="total-mini" data-estado="${porcentajes[nutriente.key].estado}">
                <span>${nutriente.label}:</span>
                <span class="value" id="${nutriente.id}">${totales[nutriente.key].toFixed(1)} ${nutriente.suffix}</span>
            </div>
        `).join('');
    }

    /**
     * Crear grid de requerimientos
     * @param {Object} requerimientos - Requerimientos del nivel
     * @returns {string} HTML del grid
     */
    crearGridRequerimientos(requerimientos) {
        const nutrientes = [
            { key: 'calorias_kcal', label: 'Calorías', suffix: 'Kcal' },
            { key: 'proteina_g', label: 'Proteína', suffix: 'g' },
            { key: 'grasa_g', label: 'Grasa', suffix: 'g' },
            { key: 'cho_g', label: 'CHO', suffix: 'g' },
            { key: 'calcio_mg', label: 'Calcio', suffix: 'mg' },
            { key: 'hierro_mg', label: 'Hierro', suffix: 'mg' },
            { key: 'sodio_mg', label: 'Sodio', suffix: 'mg' }
        ];

        return nutrientes.map(nutriente => `
            <div class="requerimiento-mini">
                <span>${nutriente.label}:</span>
                <span class="value">${requerimientos[nutriente.key].toFixed(1)} ${nutriente.suffix}</span>
            </div>
        `).join('');
    }

    /**
     * Crear grid de adecuación
     * @param {Object} porcentajes - Porcentajes de adecuación
     * @param {number} index - Índice del nivel
     * @returns {string} HTML del grid
     */
    crearGridAdecuacion(porcentajes, index) {
        const nutrientes = [
            { key: 'calorias_kcal', label: 'Calorías' },
            { key: 'proteina_g', label: 'Proteína' },
            { key: 'grasa_g', label: 'Grasa' },
            { key: 'cho_g', label: 'CHO' },
            { key: 'calcio_mg', label: 'Calcio' },
            { key: 'hierro_mg', label: 'Hierro' },
            { key: 'sodio_mg', label: 'Sodio' }
        ];

        return nutrientes.map(nutriente => `
            <div class="adecuacion-mini" data-estado="${porcentajes[nutriente.key].estado}">
                <span>${nutriente.label}:</span>
                <input type="number" 
                       class="form-control form-control-sm porcentaje-input" 
                       id="nivel-${index}-${nutriente.key}-pct"
                       value="${porcentajes[nutriente.key].porcentaje}" 
                       min="0" 
                       max="100" 
                       step="0.1"
                       data-nutriente="${nutriente.key}"
                       data-nivel="${index}">
                <span class="porcentaje-symbol">%</span>
            </div>
        `).join('');
    }

    /**
     * Crear preparación
     * @param {Object} preparacion - Datos de la preparación
     * @param {number} nivelIndex - Índice del nivel
     * @param {number} prepIndex - Índice de la preparación
     * @returns {string} HTML de la preparación
     */
    crearPreparacion(preparacion, nivelIndex, prepIndex) {
        return `
            <div class="preparacion-item">
                <h6 class="preparacion-titulo">
                    <i class="fas fa-utensils"></i> ${preparacion.nombre}
                </h6>
                <div class="ingredientes-table">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Ingrediente</th>
                                <th>Peso Neto (g)</th>
                                <th>Peso Bruto (g)</th>
                                <th>% Comestible</th>
                                <th>Calorías (kcal)</th>
                                <th>Proteína (g)</th>
                                <th>Grasa (g)</th>
                                <th>CHO (g)</th>
                                <th>Calcio (mg)</th>
                                <th>Hierro (mg)</th>
                                <th>Sodio (mg)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${preparacion.ingredientes.map((ing, ingIndex) => {
                                ing.id_preparacion_real = preparacion.id_preparacion;
                                return this.crearFilaIngrediente(ing, nivelIndex, prepIndex, ingIndex);
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    /**
     * Crear fila de ingrediente
     * @param {Object} ingrediente - Datos del ingrediente
     * @param {number} nivelIndex - Índice del nivel
     * @param {number} prepIndex - Índice de la preparación
     * @param {number} ingIndex - Índice del ingrediente
     * @returns {string} HTML de la fila
     */
    crearFilaIngrediente(ingrediente, nivelIndex, prepIndex, ingIndex) {
        const inputId = `peso-${nivelIndex}-${prepIndex}-${ingIndex}`;
        const pesoNeto = ingrediente.peso_neto_base;
        let nutrientesFinales;
        let baseNutrientesPor100g;

        if (ingrediente.valores_finales_guardados && pesoNeto > 0) {
            nutrientesFinales = ingrediente.valores_finales_guardados;
            
            baseNutrientesPor100g = {
                calorias_kcal: (nutrientesFinales.calorias / pesoNeto) * 100,
                proteina_g: (nutrientesFinales.proteina / pesoNeto) * 100,
                grasa_g: (nutrientesFinales.grasa / pesoNeto) * 100,
                cho_g: (nutrientesFinales.cho / pesoNeto) * 100,
                calcio_mg: (nutrientesFinales.calcio / pesoNeto) * 100,
                hierro_mg: (nutrientesFinales.hierro / pesoNeto) * 100,
                sodio_mg: (nutrientesFinales.sodio / pesoNeto) * 100,
            };
        } else {
            baseNutrientesPor100g = ingrediente.valores_por_100g;
            const factor = pesoNeto / 100;
            nutrientesFinales = {
                calorias: baseNutrientesPor100g.calorias_kcal * factor,
                proteina: baseNutrientesPor100g.proteina_g * factor,
                grasa: baseNutrientesPor100g.grasa_g * factor,
                cho: baseNutrientesPor100g.cho_g * factor,
                calcio: baseNutrientesPor100g.calcio_mg * factor,
                hierro: baseNutrientesPor100g.hierro_mg * factor,
                sodio: baseNutrientesPor100g.sodio_mg * factor,
            };
        }

        return `
            <tr class="ingrediente-row"
                data-nivel="${nivelIndex}"
                data-prep="${prepIndex}"
                data-ing="${ingIndex}"
                data-prep-id="${ingrediente.id_preparacion_real || prepIndex}"
                data-ing-id="${ingrediente.id_ingrediente || ingrediente.id_ingrediente_siesa || ingIndex}">
                <td class="ingrediente-nombre">${ingrediente.nombre}</td>
                <td>
                    <input type="number"
                           class="form-control form-control-sm peso-input"
                           id="${inputId}"
                           value="${ingrediente.peso_neto_base.toFixed(0)}"
                           min="0"
                           step="1"
                           data-base="${ingrediente.peso_neto_base}"
                           data-parte-comestible="${ingrediente.parte_comestible}"
                           data-calorias="${baseNutrientesPor100g.calorias_kcal}"
                           data-proteina="${baseNutrientesPor100g.proteina_g}"
                           data-grasa="${baseNutrientesPor100g.grasa_g}"
                           data-cho="${baseNutrientesPor100g.cho_g}"
                           data-calcio="${baseNutrientesPor100g.calcio_mg}"
                           data-hierro="${baseNutrientesPor100g.hierro_mg}"
                           data-sodio="${baseNutrientesPor100g.sodio_mg}"
                           data-prep-id="${ingrediente.id_preparacion_real || prepIndex}"
                           data-ing-id="${ingrediente.id_ingrediente || ingrediente.id_ingrediente_siesa || ingIndex}">
                </td>
                <td class="peso-bruto-calc" id="bruto-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${ingrediente.peso_bruto_base.toFixed(0)}
                </td>
                <td class="parte-comestible">${ingrediente.parte_comestible}%</td>
                <td class="nutriente-cal" id="cal-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.calorias.toFixed(1)}
                </td>
                <td class="nutriente-prot" id="prot-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.proteina.toFixed(1)}
                </td>
                <td class="nutriente-grasa" id="grasa-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.grasa.toFixed(1)}
                </td>
                <td class="nutriente-cho" id="cho-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.cho.toFixed(1)}
                </td>
                <td class="nutriente-calcio" id="calcio-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.calcio.toFixed(1)}
                </td>
                <td class="nutriente-hierro" id="hierro-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.hierro.toFixed(1)}
                </td>
                <td class="nutriente-sodio" id="sodio-${nivelIndex}-${prepIndex}-${ingIndex}">
                    ${nutrientesFinales.sodio.toFixed(1)}
                </td>
            </tr>
        `;
    }

    /**
     * Inicializar eventos de botones
     */
    inicializarEventosBotones() {
        // Botón de guardar análisis
        const btnGuardar = document.getElementById('btnGuardarAnalisis');
        if (btnGuardar) {
            btnGuardar.addEventListener('click', () => this.guardarAnalisisNutricional());
        }
    }

    /**
     * Inicializar eventos de inputs
     */
    inicializarEventosInputs() {
        let actualizandoPorPeso = false;
        let actualizandoPorPorcentaje = false;
        
        $(document).on('input change', '.peso-input', (e) => {
            if (actualizandoPorPorcentaje) return;

            actualizandoPorPeso = true;

            const input = $(e.target);
            const nivelIndex = input.closest('.ingrediente-row').data('nivel');
            const prepIndex = input.closest('.ingrediente-row').data('prep');
            const ingIndex = input.closest('.ingrediente-row').data('ing');

            const pesoNeto = Math.max(0, parseFloat(input.val()) || 0);
            const parteComestible = parseFloat(input.data('parte-comestible')) || 100;
            
            const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];
            const nutrientesPor100g = {};
            nutrientes.forEach(nutriente => {
                nutrientesPor100g[nutriente] = parseFloat(input.data(nutriente)) || 0;
            });

            const pesoBruto = parteComestible > 0 ? (pesoNeto * 100) / parteComestible : pesoNeto;
            $(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text(pesoBruto.toFixed(0));

            const factor = pesoNeto / 100;
            nutrientes.forEach(nutriente => {
                const valor = nutrientesPor100g[nutriente] * factor;
                const sufijo = nutriente === 'calorias' ? 'cal' : 
                              nutriente === 'proteina' ? 'prot' :
                              nutriente === 'grasa' ? 'grasa' :
                              nutriente === 'cho' ? 'cho' :
                              nutriente === 'calcio' ? 'calcio' :
                              nutriente === 'hierro' ? 'hierro' : 'sodio';
                $(`#${sufijo}-${nivelIndex}-${prepIndex}-${ingIndex}`).text(valor.toFixed(1));
            });

            this.recalcularTotalesNivel(nivelIndex);
            actualizandoPorPeso = false;
        });
        
        let timeoutPorcentaje = null;
        $(document).on('change', '.porcentaje-input', (e) => {
            if (actualizandoPorPeso) return;

            const input = $(e.target);
            const nivelIndex = input.data('nivel');
            const nutriente = input.data('nutriente');
            const porcentajeDeseado = parseFloat(input.val()) || 0;

            if (porcentajeDeseado < 0) {
                input.val(0);
                return;
            }
            if (porcentajeDeseado > 100) {
                input.val(100);
                return;
            }

            clearTimeout(timeoutPorcentaje);
            timeoutPorcentaje = setTimeout(() => {
                actualizandoPorPorcentaje = true;
                this.calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado);
                actualizandoPorPorcentaje = false;
            }, 300);
        });
        
        $(document).on('click', '.nivel-header-btn', (e) => {
            e.preventDefault();
            const button = $(e.target);
            const targetId = button.data('target');
            const target = $(targetId);
            const icon = button.find('.toggle-icon');

            if (target.hasClass('show')) {
                target.removeClass('show');
                button.attr('aria-expanded', 'false').addClass('collapsed');
                icon.css('transform', 'rotate(0deg)');
            } else {
                $('.nivel-card .collapse.show').each(function() {
                    const otherCollapse = $(this);
                    const otherButton = $(`[data-target="#${otherCollapse.attr('id')}"]`);
                    const otherIcon = otherButton.find('.toggle-icon');

                    otherCollapse.removeClass('show');
                    otherButton.attr('aria-expanded', 'false').addClass('collapsed');
                    otherIcon.css('transform', 'rotate(0deg)');
                });

                target.addClass('show');
                button.attr('aria-expanded', 'true').removeClass('collapsed');
                icon.css('transform', 'rotate(180deg)');
            }
        });
    }

    /**
     * Recalcular totales del nivel
     * @param {number} nivelIndex - Índice del nivel
     */
    recalcularTotalesNivel(nivelIndex) {
        console.log(`[DEBUG] Recalculando totales para nivel ${nivelIndex}`);
        
        // Calcular totales sumando todos los ingredientes del nivel
        const totales = this.calcularTotalesNivel(nivelIndex);
        console.log(`[DEBUG] Totales calculados:`, totales);
        
        // Actualizar campos de totales en la interfaz
        $(`#nivel-${nivelIndex}-calorias`).text(totales.calorias.toFixed(1));
        $(`#nivel-${nivelIndex}-proteina`).text(totales.proteina.toFixed(1));
        $(`#nivel-${nivelIndex}-grasa`).text(totales.grasa.toFixed(1));
        $(`#nivel-${nivelIndex}-cho`).text(totales.cho.toFixed(1));
        $(`#nivel-${nivelIndex}-calcio`).text(totales.calcio.toFixed(1));
        $(`#nivel-${nivelIndex}-hierro`).text(totales.hierro.toFixed(1));
        $(`#nivel-${nivelIndex}-sodio`).text(totales.sodio.toFixed(1));
        
        // Calcular porcentajes de adecuación
        const porcentajes = this.calcularPorcentajesNivel(nivelIndex, totales);
        console.log(`[DEBUG] Porcentajes calculados:`, porcentajes);
        
        // Actualizar campos de porcentajes en la interfaz
        $(`#nivel-${nivelIndex}-calorias_kcal-pct`).val(porcentajes.calorias.toFixed(1));
        $(`#nivel-${nivelIndex}-proteina_g-pct`).val(porcentajes.proteina.toFixed(1));
        $(`#nivel-${nivelIndex}-grasa_g-pct`).val(porcentajes.grasa.toFixed(1));
        $(`#nivel-${nivelIndex}-cho_g-pct`).val(porcentajes.cho.toFixed(1));
        $(`#nivel-${nivelIndex}-calcio_mg-pct`).val(porcentajes.calcio.toFixed(1));
        $(`#nivel-${nivelIndex}-hierro_mg-pct`).val(porcentajes.hierro.toFixed(1));
        $(`#nivel-${nivelIndex}-sodio_mg-pct`).val(porcentajes.sodio.toFixed(1));
        
        // Actualizar badges del header del acordeón
        $(`#heading-${nivelIndex} .badge-primary`).text(`${totales.calorias.toFixed(0)} Kcal`);
        $(`#heading-${nivelIndex} .badge-success`).text(`${totales.peso_neto.toFixed(0)}g neto`);
        $(`#heading-${nivelIndex} .badge-warning`).text(`${totales.peso_bruto.toFixed(0)}g bruto`);
        
        // Actualizar colores de estado
        this.actualizarColoresEstado(nivelIndex, porcentajes);
        
        console.log(`[DEBUG] Actualización completada para nivel ${nivelIndex}`);
    }

    /**
     * Actualizar colores de estado según porcentajes
     * @param {number} nivelIndex - Índice del nivel
     * @param {Object} porcentajes - Porcentajes de adecuación
     */
    actualizarColoresEstado(nivelIndex, porcentajes) {
        const nutrientes = [
            { key: 'calorias_kcal', nombre: 'calorias' },
            { key: 'proteina_g', nombre: 'proteina' },
            { key: 'grasa_g', nombre: 'grasa' },
            { key: 'cho_g', nombre: 'cho' },
            { key: 'calcio_mg', nombre: 'calcio' },
            { key: 'hierro_mg', nombre: 'hierro' },
            { key: 'sodio_mg', nombre: 'sodio' }
        ];
        
        nutrientes.forEach(nutriente => {
            const porcentaje = porcentajes[nutriente.nombre] || 0;
            const inputId = `nivel-${nivelIndex}-${nutriente.key}-pct`;
            const $input = $(`#${inputId}`);
            
            // Remover clases anteriores
            $input.removeClass('optimo aceptable alto');
            
            // Aplicar nueva clase según el porcentaje
            if (porcentaje <= 35) {
                $input.addClass('optimo');
            } else if (porcentaje <= 70) {
                $input.addClass('aceptable');
            } else {
                $input.addClass('alto');
            }
        });
    }

    /**
     * Calcular pesos desde adecuación
     * @param {number} nivelIndex - Índice del nivel
     * @param {string} nutriente - Nombre del nutriente
     * @param {number} porcentajeDeseado - Porcentaje deseado
     */
    calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado) {
        // TODO: Implementar lógica de cálculo desde adecuación
    }

    /**
     * Guardar análisis nutricional
     */
    async guardarAnalisisNutricional() {
        try {
            const btnGuardar = document.getElementById('btnGuardarAnalisis');
            if (btnGuardar) {
                btnGuardar.disabled = true;
                btnGuardar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
            }

            // Guardar cada nivel por separado
            const niveles = this.recopilarDatosParaGuardar();
            let guardadosExitosos = 0;
            let errores = [];

            for (const nivel of niveles) {
                try {
                    console.log('Enviando datos para nivel:', nivel.id_nivel_escolar, nivel);
                    
                    const response = await fetch('/nutricion/api/guardar-analisis-nutricional/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify(nivel)
                    });

                    const resultado = await response.json();

                    if (resultado.success) {
                        guardadosExitosos++;
                    } else {
                        errores.push(`${nivel.id_nivel_escolar}: ${resultado.error}`);
                    }
                } catch (error) {
                    errores.push(`${nivel.id_nivel_escolar}: ${error.message}`);
                }
            }

            // Mostrar resultado
            if (guardadosExitosos === niveles.length) {
                alert(`✅ Análisis nutricional guardado exitosamente (${guardadosExitosos} niveles)`);
            } else if (guardadosExitosos > 0) {
                alert(`⚠️ Guardado parcial: ${guardadosExitosos}/${niveles.length} niveles guardados\nErrores: ${errores.join(', ')}`);
            } else {
                throw new Error('No se pudo guardar ningún nivel: ' + errores.join(', '));
            }

        } catch (error) {
            console.error('Error al guardar análisis:', error);
            alert('❌ Error al guardar el análisis: ' + error.message);
        } finally {
            const btnGuardar = document.getElementById('btnGuardarAnalisis');
            if (btnGuardar) {
                btnGuardar.disabled = false;
                btnGuardar.innerHTML = '<i class="fas fa-save"></i> Guardar Análisis Nutricional';
            }
        }
    }

    /**
     * Recopilar datos para guardar
     */
    recopilarDatosParaGuardar() {
        const niveles = [];

        // Recopilar datos de cada nivel por separado
        this.datosNutricionales.analisis_por_nivel.forEach((nivel, nivelIndex) => {
            const totales = this.calcularTotalesNivel(nivelIndex);
            const porcentajes = this.calcularPorcentajesNivel(nivelIndex, totales);
            const ingredientes = this.recopilarIngredientesNivel(nivelIndex);

            niveles.push({
                id_menu: this.menuActual.id,
                id_nivel_escolar: nivel.nivel_escolar.id,
                totales: totales,
                porcentajes: porcentajes,
                ingredientes: ingredientes
            });
        });

        return niveles;
    }

    /**
     * Calcular totales del nivel
     */
    calcularTotalesNivel(nivelIndex) {
        const totales = {
            calorias: 0,
            proteina: 0,
            grasa: 0,
            cho: 0,
            calcio: 0,
            hierro: 0,
            sodio: 0,
            peso_neto: 0,
            peso_bruto: 0
        };

        // Sumar todos los ingredientes del nivel
        $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each((index, row) => {
            const $row = $(row);
            const pesoNeto = parseFloat($row.find('.peso-input').val()) || 0;
            const pesoBruto = parseFloat($row.find('.peso-bruto-calc').text()) || 0;
            
            totales.peso_neto += pesoNeto;
            totales.peso_bruto += pesoBruto;
            
            // Sumar nutrientes
            totales.calorias += parseFloat($row.find('.nutriente-cal').text()) || 0;
            totales.proteina += parseFloat($row.find('.nutriente-prot').text()) || 0;
            totales.grasa += parseFloat($row.find('.nutriente-grasa').text()) || 0;
            totales.cho += parseFloat($row.find('.nutriente-cho').text()) || 0;
            totales.calcio += parseFloat($row.find('.nutriente-calcio').text()) || 0;
            totales.hierro += parseFloat($row.find('.nutriente-hierro').text()) || 0;
            totales.sodio += parseFloat($row.find('.nutriente-sodio').text()) || 0;
        });

        return totales;
    }

    /**
     * Calcular porcentajes del nivel
     */
    calcularPorcentajesNivel(nivelIndex, totales) {
        const nivel = this.datosNutricionales.analisis_por_nivel[nivelIndex];
        const requerimientos = nivel.requerimientos;
        
        const porcentajes = {};
        const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];
        
        nutrientes.forEach(nutriente => {
            const total = totales[nutriente] || 0;
            const requerimiento = requerimientos[nutriente + '_kcal'] || requerimientos[nutriente + '_g'] || requerimientos[nutriente + '_mg'] || 0;
            
            if (requerimiento > 0) {
                porcentajes[nutriente] = Math.min((total / requerimiento) * 100, 100);
            } else {
                porcentajes[nutriente] = 0;
            }
        });

        return porcentajes;
    }

    /**
     * Recopilar ingredientes del nivel
     */
    recopilarIngredientesNivel(nivelIndex) {
        const ingredientes = [];

        $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each((index, row) => {
            const $row = $(row);
            const pesoNeto = parseFloat($row.find('.peso-input').val()) || 0;
            const pesoBruto = parseFloat($row.find('.peso-bruto-calc').text()) || 0;
            
            ingredientes.push({
                id_preparacion: $row.data('prep-id'),
                id_ingrediente_siesa: $row.data('ing-id'),
                peso_neto: pesoNeto,
                peso_bruto: pesoBruto,
                calorias: parseFloat($row.find('.nutriente-cal').text()) || 0,
                proteina: parseFloat($row.find('.nutriente-prot').text()) || 0,
                grasa: parseFloat($row.find('.nutriente-grasa').text()) || 0,
                cho: parseFloat($row.find('.nutriente-cho').text()) || 0,
                calcio: parseFloat($row.find('.nutriente-calcio').text()) || 0,
                hierro: parseFloat($row.find('.nutriente-hierro').text()) || 0,
                sodio: parseFloat($row.find('.nutriente-sodio').text()) || 0
            });
        });

        return ingredientes;
    }

    /**
     * Cerrar modal de análisis nutricional
     */
    cerrarModalAnalisisNutricional() {
        const modal = document.getElementById('modalAnalisisNutricional');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Obtener datos nutricionales actuales
     * @returns {Object|null} Datos nutricionales
     */
    getDatosNutricionales() {
        return this.datosNutricionales;
    }

    /**
     * Obtener menú actual
     * @returns {Object|null} Menú actual
     */
    getMenuActual() {
        return this.menuActual;
    }

    /**
     * Obtener requerimientos por nivel
     * @returns {Object} Requerimientos por nivel
     */
    getRequerimientosNiveles() {
        return this.requerimientosNiveles;
    }
}

// Exportar para uso global
window.AnalisisNutricionalManager = AnalisisNutricionalManager;
