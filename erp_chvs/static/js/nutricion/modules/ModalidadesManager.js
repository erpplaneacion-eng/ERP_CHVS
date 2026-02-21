/**
 * ModalidadesManager.js
 * Maneja toda la lÃ³gica relacionada con modalidades y Menus
 * - GestiÃ³n de modalidades
 * - CreaciÃ³n y gestiÃ³n de acordeones
 * - GeneraciÃ³n de Menus automÃ¡ticos
 * - Tarjetas de Menus
 */

class ModalidadesManager {
    constructor() {
        this.programaActual = null;
        this.modalidadesData = [];
        this.menusData = {};

        // Exponer instancia globalmente para las funciones inline del modal
        window._modalidadesMgr = this;

        this.init();
    }

    init() {
        // InicializaciÃ³n del manager
    }

    /**
     * Cargar modalidades por programa
     * @param {string} programaId - ID del programa
     * @returns {Promise<Object>} Datos del programa y modalidades
     */
    async cargarModalidadesPorPrograma(programaId) {
        try {
            const url = `/nutricion/api/modalidades-por-programa/?programa_id=${programaId}`;
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.programaActual = data.programa;
            this.modalidadesData = data.modalidades;
            
            await this.cargarMenusExistentes(programaId);
            
            return {
                programa: data.programa,
                modalidades: data.modalidades,
                menus: this.menusData
            };
        } catch (error) {
            console.error('Error al cargar modalidades:', error);
            throw error;
        }
    }

    /**
     * Cargar Menus existentes por programa
     * @param {string} programaId - ID del programa
     */
    async cargarMenusExistentes(programaId) {
        try {
            const response = await fetch(`/nutricion/api/menus/?programa_id=${programaId}`);
            const data = await response.json();
            
            // Agrupar Menus por modalidad
            this.menusData = {};
            if (data.menus) {
                data.menus.forEach(menu => {
                    const modalidadId = menu.id_modalidad__id_modalidades;
                    if (!this.menusData[modalidadId]) {
                        this.menusData[modalidadId] = [];
                    }
                    this.menusData[modalidadId].push(menu);
                });
                
                // Ordenar Menus numÃ©ricamente dentro de cada modalidad
                Object.keys(this.menusData).forEach(modalidadId => {
                    this.menusData[modalidadId].sort((a, b) => {
                        const numA = parseInt(a.menu) || 0;
                        const numB = parseInt(b.menu) || 0;
                        return numA - numB;
                    });
                });
            }
        } catch (error) {
            console.error('Error al cargar Menus:', error);
        }
    }

    /**
     * Mostrar informaciÃ³n del programa
     * @param {Object} programa - Datos del programa
     */
    mostrarInfoPrograma(programa) {
        const container = document.getElementById('infoProgramaContainer');
        document.getElementById('infoProgramaNombre').querySelector('span').textContent = programa.nombre;
        document.getElementById('infoProgramaContrato').querySelector('span').textContent = programa.contrato;
        
        const municipioSelect = document.getElementById('filtroMunicipio');
        const municipioNombre = municipioSelect.options[municipioSelect.selectedIndex].text;
        document.getElementById('infoProgramaMunicipio').querySelector('span').textContent = municipioNombre;
        
        container.style.display = 'block';
    }

    /**
     * Generar acordeones de modalidades
     * @param {Array} modalidades - Array de modalidades
     */
    generarAcordeones(modalidades) {
        const container = document.getElementById('modalidadesContainer');
        container.innerHTML = '';
        
        modalidades.forEach(modalidad => {
            const accordion = this.crearAcordeon(modalidad);
            container.appendChild(accordion);
        });
    }

    /**
     * Crear acordeÃ³n para una modalidad
     * @param {Object} modalidad - Datos de la modalidad
     * @returns {HTMLElement} Elemento del acordeÃ³n
     */
    crearAcordeon(modalidad) {
        const modalidadId = modalidad.id_modalidades;
        const menusModalidad = this.menusData[modalidadId] || [];
        const tieneMenus = menusModalidad.length > 0;
        const menusCompletos = menusModalidad.length >= 20;
        
        const accordionDiv = document.createElement('div');
        accordionDiv.className = 'accordion';
        accordionDiv.id = `accordion-${modalidadId}`;

        // Crear header
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.onclick = () => this.toggleAccordion(header);

        const downloadUrl = `/nutricion/exportar-modalidad-excel/${this.programaActual.id}/${modalidadId}/`;
        const guiasDownloadUrl = `/nutricion/exportar-guias-preparacion/${this.programaActual.id}/${modalidadId}/`;

        header.innerHTML = `
            <div>
                <strong>${modalidad.modalidad}</strong>
                <span class="preparacion-badge" id="badge-${modalidadId}">${menusModalidad.length} / 20 Menus</span>
            </div>
            <div class="accordion-header-actions" id="actions-${modalidadId}">
                <a href="${downloadUrl}" class="btn btn-success btn-sm" style="${menusCompletos ? "" : "display:none;"}" onclick="event.stopPropagation();" title="Descargar Reporte Maestro para ${modalidad.modalidad}">
                    <i class="fas fa-file-excel"></i> Descargar Analisis
                </a>
                <a href="${guiasDownloadUrl}" class="btn btn-success btn-sm" style="${menusCompletos ? "" : "display:none;"}" onclick="event.stopPropagation();" title="Descargar Guias de Preparacion para ${modalidad.modalidad}">
                    <i class="fas fa-file-excel"></i> Descargar Guias
                </a>
                ${!tieneMenus ? `
                <button class="btn-generar-auto" data-modalidad-id="${modalidadId}" data-modalidad-nombre="${modalidad.modalidad}">
                    <i class="fas fa-magic"></i> Generar 20 Menus
                </button>
                <button class="btn-copiar-modalidad" data-modalidad-id="${modalidadId}" data-modalidad-nombre="${modalidad.modalidad}">
                    <i class="fas fa-copy"></i> Copiar desde otro programa
                </button>` : ''}
                <i class="fas fa-chevron-down"></i>
            </div>
        `;

        // Agregar event listeners a los botones cuando no hay Menus
        if (!tieneMenus) {
            setTimeout(() => {
                const btn = header.querySelector('.btn-generar-auto');
                if (btn) {
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const modalidadId = btn.getAttribute('data-modalidad-id');
                        const modalidadNombre = btn.getAttribute('data-modalidad-nombre');
                        this.generarMenusAutomaticos(modalidadId, modalidadNombre);
                    });
                }

                const btnCopiar = header.querySelector('.btn-copiar-modalidad');
                if (btnCopiar) {
                    btnCopiar.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const modalidadId = btnCopiar.getAttribute('data-modalidad-id');
                        const modalidadNombre = btnCopiar.getAttribute('data-modalidad-nombre');
                        this.abrirModalCopiar(modalidadId, modalidadNombre);
                    });
                }
            }, 0);
        }

        // Crear content
        const content = document.createElement('div');
        content.className = 'accordion-content';
        content.id = `content-${modalidadId}`;
        
        const grid = document.createElement('div');
        // Contenedor vertical para semanas (evita distribuciÃ³n horizontal por grid global)
        grid.className = 'semanas-stack';
        grid.id = `grid-${modalidadId}`;

        if (tieneMenus) {
            grid.innerHTML = this.generarTarjetasMenus(menusModalidad);

            // Cargar validadores semanales de forma asÃ­ncrona
            setTimeout(() => {
                this.cargarValidadoresSemana(modalidadId);
            }, 100);
        } else {
            grid.innerHTML = `<p style="padding: 20px;" id="placeholder-${modalidadId}">Genere los Menus para esta modalidad</p>`;
        }

        content.appendChild(grid);
        accordionDiv.appendChild(header);
        accordionDiv.appendChild(content);

        return accordionDiv;
    }

    /**
     * Generar tarjetas de Menus con agrupaciÃ³n semanal
     * @param {Array} menus - Array de Menus
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de las tarjetas
     */
    generarTarjetasMenus(menus, animate = false) {
        // Separar Menus regulares (1-20) de Menus especiales
        const menusRegulares = menus.filter(menu => {
            const num = parseInt(menu.menu);
            return !isNaN(num) && num >= 1 && num <= 20;
        });

        const menusEspeciales = menus.filter(menu => {
            const num = parseInt(menu.menu);
            return isNaN(num) || num < 1 || num > 20;
        });

        const modalidadId = menus.length > 0 ? menus[0].id_modalidad__id_modalidades : '';

        let html = '';

        // Generar 4 semanas de 5 Menus cada una
        for (let semana = 1; semana <= 4; semana++) {
            const inicio = (semana - 1) * 5;
            const fin = inicio + 5;
            const menusSemana = menusRegulares.slice(inicio, fin);

            html += this.generarSeccionSemana(semana, menusSemana, modalidadId, animate);
        }

        // SecciÃ³n de Menus especiales al final
        html += this.generarSeccionEspeciales(menusEspeciales, modalidadId, animate);

        return html;
    }

    /**
     * Generar secciÃ³n de una semana con validador
     * @param {number} numSemana - NÃºmero de semana (1-4)
     * @param {Array} menus - Menus de la semana
     * @param {string} modalidadId - ID de la modalidad
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de la secciÃ³n de semana
     */
    generarSeccionSemana(numSemana, menus, modalidadId, animate) {
        const menuIds = menus.map(m => m.id_menu).join(',');
        const containerId = `validador-semana-${modalidadId}-${numSemana}`;

        let tarjetasMenus = menus.map((menu, index) => {
            const menuEscaped = String(menu.menu).replace(/'/g, "\\'");
            const downloadUrl = `/nutricion/exportar-excel/${menu.id_menu}/`;
            const animStyle = animate ? `style="animation-delay: ${index * 0.05}s"` : '';
            const animClass = animate ? 'menu-card-anim' : '';

            return `
                <div class="menu-card ${animClass} ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                     ${animStyle}
                     onclick="abrirPaginaPreparaciones(${menu.id_menu})">
                    <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                        <i class="fas fa-file-excel"></i>
                    </a>
                    <div class="menu-numero">${menu.menu}</div>
                    <div class="menu-actions">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirPaginaPreparaciones(${menu.id_menu})">
                            <i class="fas fa-utensils"></i> Preparaciones
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Si no hay 5 Menus, rellenar con placeholders
        const faltantes = 5 - menus.length;
        for (let i = 0; i < faltantes; i++) {
            const numeroMenu = (numSemana - 1) * 5 + menus.length + i + 1;
            tarjetasMenus += `
                <div class="menu-card menu-card-placeholder">
                    <div class="menu-numero">${numeroMenu}</div>
                    <div class="menu-placeholder-text">Pendiente</div>
                </div>
            `;
        }

        return `
            <div class="semana-container" data-semana="${numSemana}">
                <div class="semana-titulo">
                    <span>Semana ${numSemana}</span>
                </div>

                <div class="semana-menus-grid">
                    ${tarjetasMenus}
                </div>

                <div class="validador-semanal" id="${containerId}" data-modalidad-id="${modalidadId}" data-menu-ids="${menuIds}">
                    <div class="validador-loading">
                        <div class="spinner-border spinner-border-sm text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <span>Validando semana...</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Generar secciÃ³n de Menus especiales
     * @param {Array} menusEspeciales - Menus especiales existentes
     * @param {string} modalidadId - ID de la modalidad
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de la secciÃ³n de Menus especiales
     */
    generarSeccionEspeciales(menusEspeciales, modalidadId, animate) {
        const delayBase = animate ? 20 * 0.05 : 0; // Delay despuÃ©s de los 20 Menus regulares

        const tarjetasEspeciales = menusEspeciales.map((menu, index) => {
            const menuEscaped = String(menu.menu).replace(/'/g, "\\'");
            const downloadUrl = `/nutricion/exportar-excel/${menu.id_menu}/`;
            const animStyle = animate ? `style="animation-delay: ${delayBase + index * 0.05}s"` : '';
            const animClass = animate ? 'menu-card-anim' : '';

            return `
                <div class="menu-card menu-card-especial ${animClass} ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                     ${animStyle}
                     onclick="abrirPaginaPreparaciones(${menu.id_menu})">
                    <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                        <i class="fas fa-file-excel"></i>
                    </a>
                    <div class="menu-numero-especial">
                        ${menu.menu}
                    </div>
                    <div class="menu-actions" style="flex-direction: column;">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirPaginaPreparaciones(${menu.id_menu})">
                            <i class="fas fa-utensils"></i> Preparaciones
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="event.stopPropagation(); abrirEditarMenuEspecial(${menu.id_menu}, '${menuEscaped}')">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        const tarjetaCrear = `
            <div class="menu-card menu-card-especial ${animate ? 'menu-card-anim' : ''}"
                 ${animate ? `style="animation-delay: ${delayBase + menusEspeciales.length * 0.05 + 0.1}s"` : ''}
                 onclick="abrirModalMenuEspecial('${modalidadId}')">
                <div class="menu-numero-especial">
                    <i class="fas fa-plus-circle"></i>
                </div>
                <div class="menu-label-especial">Crear Especial</div>
            </div>
        `;

        const tarjetaIA = `
            <div class="menu-card menu-card-ia ${animate ? 'menu-card-anim' : ''}"
                 ${animate ? `style="animation-delay: ${delayBase + menusEspeciales.length * 0.05 + 0.2}s"` : ''}
                 onclick="abrirModalMenuIA('${modalidadId}')">
                <div class="menu-numero-ia">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="menu-label-ia">Generar con IA</div>
            </div>
        `;

        return `
            <div class="menus-especiales-section">
                <div class="menus-especiales-titulo">
                    <i class="fas fa-star"></i>
                    <span>Menus Especiales</span>
                </div>
                <div class="menus-especiales-grid">
                    ${tarjetasEspeciales}
                    ${tarjetaCrear}
                    ${tarjetaIA}
                </div>
            </div>
        `;
    }

    /**
     * Cargar validadores semanales para una modalidad
     * @param {string} modalidadId - ID de la modalidad
     */
    async cargarValidadoresSemana(modalidadId) {
        // Buscar todos los contenedores de validadores para esta modalidad
        const validadores = document.querySelectorAll(`[id^="validador-semana-${modalidadId}-"]`);

        for (const validador of validadores) {
            const menuIds = validador.getAttribute('data-menu-ids');

            if (!menuIds || menuIds === '') {
                validador.innerHTML = '<div class="validador-vacio">No hay Menus para validar</div>';
                continue;
            }

            try {
                const response = await fetch(`/nutricion/api/validar-semana/?menu_ids=${menuIds}&modalidad_id=${modalidadId}`);
                const data = await response.json();

                if (data.error) {
                    validador.innerHTML = `<div class="validador-error">${data.error}</div>`;
                    continue;
                }

                // Generar HTML del validador
                const componentesHtml = data.componentes.map(comp => {
                    const requeridoDisplay = comp.requerido_efectivo !== undefined
                        ? comp.requerido_efectivo
                        : comp.requerido;
                    const cumple = comp.cumple;
                    const icono = cumple ? 'âœ…' : 'âŒ';
                    const claseEstado = cumple ? 'cumple' : 'no-cumple';

                    let mensaje = '';
                    const falta = requeridoDisplay - comp.actual;
                    if (comp.actual > requeridoDisplay) {
                        mensaje = `(Excede por ${comp.actual - requeridoDisplay})`;
                    } else if (falta > 0) {
                        mensaje = `(Falta ${falta})`;
                    }

                    // Tooltip para grupos excluyentes
                    const tooltipHtml = this._generarTooltipExcluyente(comp);
                    const badgeExcluyente = comp.exclusion
                        ? `<span class="badge-excluyente" title="Grupos excluyentes">â‡„</span>`
                        : '';

                    return `
                        <div class="validador-item ${claseEstado}${comp.exclusion ? ' excluyente' : ''}">
                            <span class="validador-icono">${icono}</span>
                            <span class="validador-componente">
                                ${comp.grupo}${badgeExcluyente}
                            </span>
                            <div class="validador-frecuencias">
                                <span class="frecuencia-badge ${claseEstado}">
                                    ${comp.actual} / ${requeridoDisplay}
                                </span>
                                ${mensaje ? `<span class="frecuencia-mensaje">${mensaje}</span>` : ''}
                                ${tooltipHtml}
                            </div>
                        </div>
                    `;
                }).join('');

                // Sub-restricciones de alimentos
                let subRestriccionesHtml = '';
                if (data.restricciones_subgrupo && data.restricciones_subgrupo.length > 0) {
                    subRestriccionesHtml = data.restricciones_subgrupo.map(r => {
                        const cumple = r.cumple;
                        const icono = cumple ? 'âœ…' : 'âŒ';
                        const claseEstado = cumple ? 'cumple' : 'no-cumple';
                        const falta = r.frecuencia - r.actual;
                        let mensaje = '';
                        if (r.actual > r.frecuencia) {
                            mensaje = `(Excede por ${r.actual - r.frecuencia})`;
                        } else if (falta > 0) {
                            mensaje = `(Falta ${falta})`;
                        }
                        const tooltipHtml = this._generarTooltipSubRestriccion(r);
                        return `
                            <div class="validador-item ${claseEstado} sub-restriccion">
                                <span class="validador-icono">${icono}</span>
                                <span class="validador-componente">
                                    ${r.grupo_id} â€º ${r.nombre}
                                </span>
                                <div class="validador-frecuencias">
                                    <span class="frecuencia-badge ${claseEstado}">
                                        ${r.actual} / ${r.frecuencia}
                                    </span>
                                    ${mensaje ? `<span class="frecuencia-mensaje">${mensaje}</span>` : ''}
                                    ${tooltipHtml}
                                </div>
                            </div>
                        `;
                    }).join('');
                }

                const cumpleGeneral = data.cumple;
                const estadoGeneral = cumpleGeneral
                    ? '<span class="validador-estado-ok"><i class="fas fa-check-circle"></i> Semana completa</span>'
                    : '<span class="validador-estado-error"><i class="fas fa-exclamation-circle"></i> Semana incompleta</span>';

                validador.innerHTML = `
                    <div class="validador-componentes">
                        ${componentesHtml}
                        ${subRestriccionesHtml}
                    </div>
                    <div class="validador-resumen ${cumpleGeneral ? 'valido' : 'invalido'}">
                        ${estadoGeneral}
                    </div>
                `;

                // Inicializar tooltips custom (sin Bootstrap Tooltip / Popper.js).
                // Bootstrap Tooltip falla silenciosamente en contenedores con animaciÃ³n CSS.
                validador.querySelectorAll('[data-tooltip-json]').forEach(el => {
                    const encoded = el.getAttribute('data-tooltip-json');
                    if (!encoded) return;
                    let htmlContent = '';
                    try {
                        const parsed = JSON.parse(decodeURIComponent(encoded));
                        if (el.classList.contains('sub-restriccion-tooltip-icon')) {
                            htmlContent = this._buildTooltipSubRestriccionHtml(parsed);
                        } else {
                            htmlContent = this._buildTooltipHtml(parsed);
                        }
                    } catch (err) {
                        console.warn('[ModalidadesManager] Error al parsear tooltip JSON:', err);
                        return;
                    }
                    this._attachTooltipCustom(el, htmlContent);
                });

            } catch (error) {
                console.error('Error al validar semana:', error);
                validador.innerHTML = '<div class="validador-error">Error al cargar validaciÃ³n</div>';
            }
        }
    }

    /**
     * Alternar acordeÃ³n
     * @param {HTMLElement} header - Header del acordeÃ³n
     */
    toggleAccordion(header) {
        const content = header.nextElementSibling;
        const isActive = content.classList.contains('active');
        
        document.querySelectorAll('.accordion-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.accordion-header').forEach(h => h.classList.remove('active'));
        
        if (!isActive) {
            content.classList.add('active');
            header.classList.add('active');
        }
    }

    /**
     * Generar Menus automÃ¡ticos para una modalidad
     * @param {string} modalidadId - ID de la modalidad
     * @param {string} modalidadNombre - Nombre de la modalidad
     */
    async generarMenusAutomaticos(modalidadId, modalidadNombre) {
        const result = await Swal.fire({
            title: 'Â¿Generar 20 Menus?',
            text: `Se crearÃ¡n automÃ¡ticamente los Menus regulares para ${modalidadNombre}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#10b981',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'SÃ­, generar',
            cancelButtonText: 'Cancelar'
        });

        if (!result.isConfirmed) return;
        
        const grid = document.getElementById(`grid-${modalidadId}`);
        const originalContent = grid.innerHTML;
        
        // 1. Mostrar Modal de Carga Global (Solo con nuestro spinner esmeralda)
        Swal.fire({
            title: 'Generando ciclo de 20 Menus...',
            html: `
                <div class="generating-spinner" style="margin: 20px auto;"></div>
                <p style="font-weight: 500; color: #334155;">Por favor, espere un momento.</p>
                <p style="font-size: 0.85rem; color: #64748b;">Estamos preparando el plan nutricional...</p>
            `,
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false
        });
        
        try {
            const response = await fetch('/nutricion/api/generar-menus-automaticos/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    programa_id: this.programaActual.id,
                    modalidad_id: modalidadId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Actualizar datos localmente
                await this.cargarMenusExistentes(this.programaActual.id);
                const menusNuevos = this.menusData[modalidadId] || [];
                
                // 2. Actualizar Badge reactivamente
                const badge = document.getElementById(`badge-${modalidadId}`);
                if (badge) {
                    badge.textContent = `${menusNuevos.length} / 20 Menus`;
                }

                // 3. Ocultar botÃ³n de generaciÃ³n
                const btnGenerar = document.querySelector(`#actions-${modalidadId} .btn-generar-auto`);
                if (btnGenerar) {
                    btnGenerar.style.display = 'none';
                }
                
                // 4. Renderizar con animaciÃ³n escalonada
                grid.innerHTML = this.generarTarjetasMenus(menusNuevos, true);

                // 5. Cargar validadores semanales
                setTimeout(() => {
                    this.cargarValidadoresSemana(modalidadId);
                }, 500);

                // 6. Cerrar modal de carga y mostrar Ã©xito
                Swal.fire({
                    title: 'Â¡Ã‰xito!',
                    text: `Se han generado ${data.menus_creados} Menus correctamente.`,
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false
                });
            } else {
                Swal.fire('Error', data.error || 'No se pudieron generar los Menus', 'error');
            }
        } catch (error) {
            console.error('Error al generar Menus automÃ¡ticos:', error);
            Swal.fire('Error', 'Hubo un problema en la conexiÃ³n con el servidor', 'error');
        }
    }

    /**
     * Obtener datos de modalidades
     * @returns {Array} Array de modalidades
     */
    getModalidadesData() {
        return this.modalidadesData;
    }

    /**
     * Obtener datos de Menus
     * @returns {Object} Objeto con Menus agrupados por modalidad
     */
    getMenusData() {
        return this.menusData;
    }

    /**
     * Obtener programa actual
     * @returns {Object|null} Datos del programa actual
     */
    getProgramaActual() {
        return this.programaActual;
    }

    /**
     * Establecer callback para cuando se recargan modalidades
     * @param {Function} callback - FunciÃ³n a ejecutar
     */
    setOnModalidadesRecargadas(callback) {
        this.onModalidadesRecargadas = callback;
    }

    /**
     * Actualizar datos de Menus para una modalidad especÃ­fica
     * @param {string} modalidadId - ID de la modalidad
     * @param {Array} menus - Array de Menus
     */
    actualizarMenusModalidad(modalidadId, menus) {
        this.menusData[modalidadId] = menus;

        // Actualizar el grid si existe
        const grid = document.getElementById(`grid-${modalidadId}`);
        if (grid) {
            grid.innerHTML = this.generarTarjetasMenus(menus);

            // Recargar validadores semanales
            setTimeout(() => {
                this.cargarValidadoresSemana(modalidadId);
            }, 100);
        }
    }

    /**
     * Obtener Menus de una modalidad especÃ­fica
     * @param {string} modalidadId - ID de la modalidad
     * @returns {Array} Array de Menus
     */
    getMenusModalidad(modalidadId) {
        return this.menusData[modalidadId] || [];
    }

    /**
     * Verificar si una modalidad tiene Menus
     * @param {string} modalidadId - ID de la modalidad
     * @returns {boolean} True si tiene Menus
     */
    tieneMenusModalidad(modalidadId) {
        return this.menusData[modalidadId] && this.menusData[modalidadId].length > 0;
    }

    /**
     * Obtener estadÃ­sticas de modalidades
     * @returns {Object} EstadÃ­sticas
     */
    getEstadisticas() {
        const estadisticas = {
            totalModalidades: this.modalidadesData.length,
            modalidadesConMenus: 0,
            totalMenus: 0,
            menusConPreparaciones: 0
        };

        Object.keys(this.menusData).forEach(modalidadId => {
            const menus = this.menusData[modalidadId];
            if (menus.length > 0) {
                estadisticas.modalidadesConMenus++;
                estadisticas.totalMenus += menus.length;
                estadisticas.menusConPreparaciones += menus.filter(menu => menu.tiene_preparaciones).length;
            }
        });

        return estadisticas;
    }

    /**
     * Genera el icono de tooltip para un componente excluyente.
     * Usa encodeURIComponent para serializar el JSON de forma segura en el atributo HTML,
     * evitando problemas con caracteres especiales (&, <, >, comillas) en nombres de grupos
     * o preparaciones.
     * @param {Object} comp - Componente del validador semanal
     * @returns {string} HTML del icono con el atributo data-tooltip-json
     */
    _generarTooltipExcluyente(comp) {
        if (!comp.exclusion) return '';

        // encodeURIComponent garantiza que cualquier caracter especial quede seguro
        // para ser usado como valor de atributo HTML.
        const jsonEncoded = encodeURIComponent(JSON.stringify(comp.exclusion));

        return `<span class="excluyente-tooltip-icon" data-tooltip-json="${jsonEncoded}">
                    <i class="fas fa-link"></i>
                </span>`;
    }

    /**
     * Construye el HTML interno del tooltip de exclusiÃ³n a partir del objeto exclusion.
     * Se llama en tiempo de inicializaciÃ³n del tooltip (no en innerHTML).
     * @param {Object} excl - Datos de exclusiÃ³n del componente
     * @returns {string} HTML para mostrar en el tooltip
     */
    _buildTooltipHtml(excl) {
        const DIAS = ['Lunes', 'Martes', 'MiÃ©rcoles', 'Jueves', 'Viernes'];
        const nombresHermanos = excl.grupos_hermanos.map(g => g.nombre).join(', ');

        let partes = [];

        const cuotaRestante = excl.cuota_compartida - excl.cuota_total_usada;
        if (cuotaRestante <= 0) {
            partes.push(`<strong>&#10003; Cuota cubierta (${excl.cuota_total_usada}/${excl.cuota_compartida})</strong>`);
        } else {
            partes.push(`<strong>&#8644; Compartida con ${nombresHermanos}: ${excl.cuota_total_usada}/${excl.cuota_compartida}</strong>`);
        }

        if (excl.aporte_hermanos.length === 0) {
            partes.push(`<em>NingÃºn grupo hermano ha aportado aÃºn</em>`);
        } else {
            excl.aporte_hermanos.forEach(item => {
                const dia = DIAS[item.menu_index] || `DÃ­a ${item.menu_index + 1}`;
                partes.push(`&bull; ${dia}: ${item.preparacion} <span style="opacity:.7">(${item.grupo_nombre})</span>`);
            });
        }

        return partes.join('<br>');
    }

    /**
     * Genera el icono de tooltip para una sub-restricciÃ³n de alimentos.
     * @param {Object} r - Sub-restricciÃ³n del validador semanal
     * @returns {string} HTML del icono con el atributo data-tooltip-json
     */
    _generarTooltipSubRestriccion(r) {
        const payload = {
            nombre: r.nombre,
            nombres_validos: r.nombres_validos,
            detalle: r.detalle,
        };
        const jsonEncoded = encodeURIComponent(JSON.stringify(payload));
        return `<span class="sub-restriccion-tooltip-icon" data-tooltip-json="${jsonEncoded}">
                    <i class="fas fa-list-check"></i>
                </span>`;
    }

    /**
     * Construye el HTML interno del tooltip de una sub-restricciÃ³n.
     * @param {Object} data - {nombre, nombres_validos, detalle}
     * @returns {string} HTML para mostrar en el tooltip
     */
    _buildTooltipSubRestriccionHtml(data) {
        const DIAS = ['Lunes', 'Martes', 'MiÃ©rcoles', 'Jueves', 'Viernes'];
        const partes = [];

        partes.push(`<strong>${data.nombre}</strong>`);

        if (data.nombres_validos && data.nombres_validos.length > 0) {
            partes.push(`<em>VÃ¡lidos: ${data.nombres_validos.join(', ')}</em>`);
        }

        if (data.detalle && data.detalle.length > 0) {
            partes.push('');
            data.detalle.forEach(item => {
                const dia = DIAS[item.menu_index] || `DÃ­a ${item.menu_index + 1}`;
                partes.push(`&bull; ${dia}: ${item.preparacion} <span style="opacity:.7">(${item.alimento_usado})</span>`);
            });
        } else {
            partes.push('<em>NingÃºn alimento vÃ¡lido usado aÃºn</em>');
        }

        return partes.join('<br>');
    }

    // =================== COPIAR MODALIDAD ===================

    /**
     * Abre el modal para copiar una modalidad desde otro programa.
     * Carga la lista de programas disponibles vÃ­a API y renderiza opciones.
     * @param {string} modalidadId - ID de la modalidad a copiar
     * @param {string} modalidadNombre - Nombre legible de la modalidad
     */
    async abrirModalCopiar(modalidadId, modalidadNombre) {
        // Setear valor oculto y nombre visible
        document.getElementById('copiarModalidadId').value = modalidadId;
        document.getElementById('copiarNombreModalidad').textContent = modalidadNombre;

        // Resetear estado del modal
        document.getElementById('listaProgramasOrigen').style.display = 'none';
        document.getElementById('sinProgramasOrigen').style.display = 'none';
        document.getElementById('accionesCopiar').style.display = 'none';
        document.getElementById('cargandoProgramas').style.display = 'block';

        // Mostrar modal
        document.getElementById('modalCopiarModalidad').style.display = 'flex';

        try {
            const programaActualId = this.programaActual?.id;
            const resp = await fetch(
                `/nutricion/api/programas-con-modalidad/?modalidad_id=${encodeURIComponent(modalidadId)}&programa_excluir=${programaActualId || ''}`
            );
            const data = await resp.json();

            document.getElementById('cargandoProgramas').style.display = 'none';

            if (data.programas && data.programas.length > 0) {
                this.renderizarProgramasOrigen(data.programas);
            } else {
                document.getElementById('sinProgramasOrigen').style.display = 'block';
            }
        } catch (error) {
            console.error('[ModalidadesManager] Error al cargar programas con modalidad:', error);
            document.getElementById('cargandoProgramas').style.display = 'none';
            document.getElementById('sinProgramasOrigen').style.display = 'block';
        }
    }

    /**
     * Renderiza las tarjetas de programas origen disponibles para seleccionar.
     * @param {Array} programas - Lista de programas con Menus para la modalidad
     */
    renderizarProgramasOrigen(programas) {
        const container = document.getElementById('programasOrigenContainer');
        const fragment = document.createDocumentFragment();

        programas.forEach(prog => {
            const card = document.createElement('label');
            card.className = 'programa-origen-card';
            card.innerHTML = `
                <input type="radio" name="programaOrigen" value="${prog.id}">
                <div class="programa-origen-info">
                    <div class="programa-origen-nombre">${prog.programa}</div>
                    <div class="programa-origen-meta">
                        Contrato: ${prog.contrato || 'N/A'} &nbsp;|&nbsp; Municipio: ${prog.municipio_nombre || 'N/A'}
                    </div>
                </div>
                <span class="programa-origen-badge">${prog.cantidad_menus} Menus</span>
            `;

            // Seleccionar visualmente la tarjeta al hacer clic en el radio
            const radio = card.querySelector('input[type="radio"]');
            radio.addEventListener('change', () => {
                document.querySelectorAll('.programa-origen-card').forEach(c => c.classList.remove('seleccionado'));
                card.classList.add('seleccionado');
                document.getElementById('accionesCopiar').style.display = 'block';
            });

            fragment.appendChild(card);
        });

        container.innerHTML = '';
        container.appendChild(fragment);
        document.getElementById('listaProgramasOrigen').style.display = 'block';
    }

    /**
     * Ejecuta la copia de la modalidad tras confirmar con SweetAlert2.
     * Llamado desde la funciÃ³n global ejecutarCopiaModalidad().
     */
    async _ejecutarCopiaModalidad() {
        const modalidadId = document.getElementById('copiarModalidadId').value;
        const radioSeleccionado = document.querySelector('input[name="programaOrigen"]:checked');
        const programaDestinoId = this.programaActual?.id;

        if (!radioSeleccionado) {
            Swal.fire('AtenciÃ³n', 'Selecciona un programa origen antes de continuar.', 'warning');
            return;
        }

        const programaOrigenId = radioSeleccionado.value;

        const confirmacion = await Swal.fire({
            title: 'Â¿Copiar modalidad?',
            text: 'Se copiarÃ¡n todos los Menus con preparaciones, ingredientes y gramajes por nivel educativo. Esta acciÃ³n no se puede deshacer.',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#6366f1',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'SÃ­, copiar',
            cancelButtonText: 'Cancelar'
        });

        if (!confirmacion.isConfirmed) return;

        // Mostrar spinner mientras se copia
        Swal.fire({
            title: 'Copiando modalidad...',
            html: `
                <div class="generating-spinner" style="margin: 20px auto;"></div>
                <p style="font-weight: 500; color: #334155;">Por favor, espere un momento.</p>
            `,
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false
        });

        try {
            const resp = await fetch('/nutricion/api/copiar-modalidad/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    programa_origen_id: parseInt(programaOrigenId),
                    programa_destino_id: parseInt(programaDestinoId),
                    modalidad_id: modalidadId
                })
            });

            const data = await resp.json();

            if (data.success) {
                // Cerrar modal de copia
                document.getElementById('modalCopiarModalidad').style.display = 'none';

                // Recargar Menus y actualizar UI
                await this.cargarMenusExistentes(this.programaActual.id);
                const menusNuevos = this.menusData[modalidadId] || [];

                // Actualizar badge
                const badge = document.getElementById(`badge-${modalidadId}`);
                if (badge) {
                    badge.textContent = `${menusNuevos.length} / 20 Menus`;
                }

                // Ocultar botones de acciÃ³n inicial
                const actionsDiv = document.getElementById(`actions-${modalidadId}`);
                if (actionsDiv) {
                    actionsDiv.querySelectorAll('.btn-generar-auto, .btn-copiar-modalidad').forEach(b => {
                        b.style.display = 'none';
                    });
                }

                // Renderizar tarjetas con animaciÃ³n
                const grid = document.getElementById(`grid-${modalidadId}`);
                if (grid) {
                    grid.innerHTML = this.generarTarjetasMenus(menusNuevos, true);
                    setTimeout(() => {
                        this.cargarValidadoresSemana(modalidadId);
                    }, 500);
                }

                Swal.fire({
                    title: 'Â¡Copia exitosa!',
                    text: `Se copiaron ${data.menus_copiados} Menus correctamente.`,
                    icon: 'success',
                    timer: 2500,
                    showConfirmButton: false
                });
            } else {
                Swal.fire('Error', data.error || 'No se pudo copiar la modalidad.', 'error');
            }
        } catch (error) {
            console.error('[ModalidadesManager] Error al copiar modalidad:', error);
            Swal.fire('Error', 'Hubo un problema en la conexiÃ³n con el servidor.', 'error');
        }
    }

    /**
     * Adjunta un tooltip custom (sin Bootstrap/Popper) a un elemento.
     * Crea una burbuja flotante en el body al hacer hover.
     * @param {HTMLElement} el - Elemento disparador
     * @param {string} htmlContent - HTML del contenido del tooltip
     */
    _attachTooltipCustom(el, htmlContent) {
        let burbuja = null;

        el.addEventListener('mouseenter', () => {
            burbuja = document.createElement('div');
            burbuja.className = 'tooltip-excluyente-burbuja';
            burbuja.innerHTML = htmlContent;
            document.body.appendChild(burbuja);

            // position:fixed usa coordenadas del viewport (getBoundingClientRect),
            // NO se suma window.scrollY.
            const rect = el.getBoundingClientRect();
            const bH = burbuja.offsetHeight;
            const bW = burbuja.offsetWidth;

            let top = rect.top - bH - 10;
            let left = rect.left + rect.width / 2 - bW / 2;

            // Si no cabe arriba, mostrar debajo
            if (top < 8) {
                top = rect.bottom + 10;
                // Quitar la flecha superior y agregar flecha inferior
                burbuja.classList.add('tooltip-abajo');
            }

            // Evitar desborde horizontal
            const maxLeft = window.innerWidth - bW - 8;
            burbuja.style.left = Math.max(8, Math.min(left, maxLeft)) + 'px';
            burbuja.style.top = top + 'px';
        });

        el.addEventListener('mouseleave', () => {
            if (burbuja) {
                burbuja.remove();
                burbuja = null;
            }
        });
    }
}

// Exportar para uso global
window.ModalidadesManager = ModalidadesManager;

// =================== FUNCIONES GLOBALES: MODAL COPIAR MODALIDAD ===================

/**
 * Cierra el modal de copia de modalidad.
 * Llamado desde onclick en el HTML del modal.
 */
function cerrarModalCopiar() {
    document.getElementById('modalCopiarModalidad').style.display = 'none';
}

/**
 * Delega la ejecuciÃ³n de la copia al ModalidadesManager activo.
 * Llamado desde onclick en el botÃ³n "Copiar Modalidad" del modal.
 */
async function ejecutarCopiaModalidad() {
    if (window._modalidadesMgr) {
        await window._modalidadesMgr._ejecutarCopiaModalidad();
    }
}


