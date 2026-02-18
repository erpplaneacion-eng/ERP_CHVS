/**
 * ModalidadesManager.js
 * Maneja toda la lógica relacionada con modalidades y menús
 * - Gestión de modalidades
 * - Creación y gestión de acordeones
 * - Generación de menús automáticos
 * - Tarjetas de menús
 */

class ModalidadesManager {
    constructor() {
        this.programaActual = null;
        this.modalidadesData = [];
        this.menusData = {};
        
        this.init();
    }

    init() {
        // Inicialización del manager
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
     * Cargar menús existentes por programa
     * @param {string} programaId - ID del programa
     */
    async cargarMenusExistentes(programaId) {
        try {
            const response = await fetch(`/nutricion/api/menus/?programa_id=${programaId}`);
            const data = await response.json();
            
            // Agrupar menús por modalidad
            this.menusData = {};
            if (data.menus) {
                data.menus.forEach(menu => {
                    const modalidadId = menu.id_modalidad__id_modalidades;
                    if (!this.menusData[modalidadId]) {
                        this.menusData[modalidadId] = [];
                    }
                    this.menusData[modalidadId].push(menu);
                });
                
                // Ordenar menús numéricamente dentro de cada modalidad
                Object.keys(this.menusData).forEach(modalidadId => {
                    this.menusData[modalidadId].sort((a, b) => {
                        const numA = parseInt(a.menu) || 0;
                        const numB = parseInt(b.menu) || 0;
                        return numA - numB;
                    });
                });
            }
        } catch (error) {
            console.error('Error al cargar menús:', error);
        }
    }

    /**
     * Mostrar información del programa
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
     * Crear acordeón para una modalidad
     * @param {Object} modalidad - Datos de la modalidad
     * @returns {HTMLElement} Elemento del acordeón
     */
    crearAcordeon(modalidad) {
        const modalidadId = modalidad.id_modalidades;
        const menusModalidad = this.menusData[modalidadId] || [];
        const tieneMenus = menusModalidad.length > 0;
        
        const accordionDiv = document.createElement('div');
        accordionDiv.className = 'accordion';
        accordionDiv.id = `accordion-${modalidadId}`;

        // Crear header
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.onclick = () => this.toggleAccordion(header);

        const downloadUrl = `/nutricion/exportar-modalidad-excel/${this.programaActual.id}/${modalidadId}/`;

        header.innerHTML = `
            <div>
                <strong>${modalidad.modalidad}</strong>
                <span class="preparacion-badge" id="badge-${modalidadId}">${menusModalidad.length} / 20 menús</span>
            </div>
            <div class="accordion-header-actions" id="actions-${modalidadId}">
                <a href="${downloadUrl}" class="btn btn-success btn-sm" onclick="event.stopPropagation();" title="Descargar Reporte Maestro para ${modalidad.modalidad}">
                    <i class="fas fa-file-excel"></i> Descargar Modalidad
                </a>
                ${!tieneMenus ? `<button class="btn-generar-auto" data-modalidad-id="${modalidadId}" data-modalidad-nombre="${modalidad.modalidad}">
                    <i class="fas fa-magic"></i> Generar 20 Menús
                </button>` : ''}
                <i class="fas fa-chevron-down"></i>
            </div>
        `;

        // Agregar event listener al botón de generar menús si existe
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
            }, 0);
        }

        // Crear content
        const content = document.createElement('div');
        content.className = 'accordion-content';
        content.id = `content-${modalidadId}`;
        
        const grid = document.createElement('div');
        // Contenedor vertical para semanas (evita distribución horizontal por grid global)
        grid.className = 'semanas-stack';
        grid.id = `grid-${modalidadId}`;

        if (tieneMenus) {
            grid.innerHTML = this.generarTarjetasMenus(menusModalidad);

            // Cargar validadores semanales de forma asíncrona
            setTimeout(() => {
                this.cargarValidadoresSemana(modalidadId);
            }, 100);
        } else {
            grid.innerHTML = `<p style="padding: 20px;" id="placeholder-${modalidadId}">Genere los menús para esta modalidad</p>`;
        }

        content.appendChild(grid);
        accordionDiv.appendChild(header);
        accordionDiv.appendChild(content);

        return accordionDiv;
    }

    /**
     * Generar tarjetas de menús con agrupación semanal
     * @param {Array} menus - Array de menús
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de las tarjetas
     */
    generarTarjetasMenus(menus, animate = false) {
        // Separar menús regulares (1-20) de menús especiales
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

        // Generar 4 semanas de 5 menús cada una
        for (let semana = 1; semana <= 4; semana++) {
            const inicio = (semana - 1) * 5;
            const fin = inicio + 5;
            const menusSemana = menusRegulares.slice(inicio, fin);

            html += this.generarSeccionSemana(semana, menusSemana, modalidadId, animate);
        }

        // Sección de menús especiales al final
        html += this.generarSeccionEspeciales(menusEspeciales, modalidadId, animate);

        return html;
    }

    /**
     * Generar sección de una semana con validador
     * @param {number} numSemana - Número de semana (1-4)
     * @param {Array} menus - Menús de la semana
     * @param {string} modalidadId - ID de la modalidad
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de la sección de semana
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

        // Si no hay 5 menús, rellenar con placeholders
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
     * Generar sección de menús especiales
     * @param {Array} menusEspeciales - Menús especiales existentes
     * @param {string} modalidadId - ID de la modalidad
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de la sección de menús especiales
     */
    generarSeccionEspeciales(menusEspeciales, modalidadId, animate) {
        const delayBase = animate ? 20 * 0.05 : 0; // Delay después de los 20 menús regulares

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
                    <span>Menús Especiales</span>
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
                validador.innerHTML = '<div class="validador-vacio">No hay menús para validar</div>';
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
                    const cumple = comp.actual >= comp.requerido;
                    const icono = cumple ? '✅' : '❌';
                    const claseEstado = cumple ? 'cumple' : 'no-cumple';

                    let mensaje = '';
                    if (comp.actual > comp.requerido) {
                        mensaje = `(Excede por ${comp.actual - comp.requerido})`;
                    } else if (comp.actual < comp.requerido) {
                        mensaje = `(Falta ${comp.requerido - comp.actual})`;
                    }

                    return `
                        <div class="validador-item ${claseEstado}">
                            <span class="validador-icono">${icono}</span>
                            <span class="validador-componente">${comp.componente}</span>
                            <div class="validador-frecuencias">
                                <span class="frecuencia-badge ${claseEstado}">
                                    ${comp.actual} / ${comp.requerido}
                                </span>
                                ${mensaje ? `<span class="frecuencia-mensaje">${mensaje}</span>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');

                const cumpleGeneral = data.cumple;
                const estadoGeneral = cumpleGeneral
                    ? '<span class="validador-estado-ok"><i class="fas fa-check-circle"></i> Semana completa</span>'
                    : '<span class="validador-estado-error"><i class="fas fa-exclamation-circle"></i> Semana incompleta</span>';

                validador.innerHTML = `
                    <div class="validador-componentes">
                        ${componentesHtml}
                    </div>
                    <div class="validador-resumen ${cumpleGeneral ? 'valido' : 'invalido'}">
                        ${estadoGeneral}
                    </div>
                `;

            } catch (error) {
                console.error('Error al validar semana:', error);
                validador.innerHTML = '<div class="validador-error">Error al cargar validación</div>';
            }
        }
    }

    /**
     * Alternar acordeón
     * @param {HTMLElement} header - Header del acordeón
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
     * Generar menús automáticos para una modalidad
     * @param {string} modalidadId - ID de la modalidad
     * @param {string} modalidadNombre - Nombre de la modalidad
     */
    async generarMenusAutomaticos(modalidadId, modalidadNombre) {
        const result = await Swal.fire({
            title: '¿Generar 20 menús?',
            text: `Se crearán automáticamente los menús regulares para ${modalidadNombre}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#10b981',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Sí, generar',
            cancelButtonText: 'Cancelar'
        });

        if (!result.isConfirmed) return;
        
        const grid = document.getElementById(`grid-${modalidadId}`);
        const originalContent = grid.innerHTML;
        
        // 1. Mostrar Modal de Carga Global (Solo con nuestro spinner esmeralda)
        Swal.fire({
            title: 'Generando ciclo de 20 menús...',
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
                    badge.textContent = `${menusNuevos.length} / 20 menús`;
                }

                // 3. Ocultar botón de generación
                const btnGenerar = document.querySelector(`#actions-${modalidadId} .btn-generar-auto`);
                if (btnGenerar) {
                    btnGenerar.style.display = 'none';
                }
                
                // 4. Renderizar con animación escalonada
                grid.innerHTML = this.generarTarjetasMenus(menusNuevos, true);

                // 5. Cargar validadores semanales
                setTimeout(() => {
                    this.cargarValidadoresSemana(modalidadId);
                }, 500);

                // 6. Cerrar modal de carga y mostrar éxito
                Swal.fire({
                    title: '¡Éxito!',
                    text: `Se han generado ${data.menus_creados} menús correctamente.`,
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false
                });
            } else {
                Swal.fire('Error', data.error || 'No se pudieron generar los menús', 'error');
            }
        } catch (error) {
            console.error('Error al generar menús automáticos:', error);
            Swal.fire('Error', 'Hubo un problema en la conexión con el servidor', 'error');
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
     * Obtener datos de menús
     * @returns {Object} Objeto con menús agrupados por modalidad
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
     * @param {Function} callback - Función a ejecutar
     */
    setOnModalidadesRecargadas(callback) {
        this.onModalidadesRecargadas = callback;
    }

    /**
     * Actualizar datos de menús para una modalidad específica
     * @param {string} modalidadId - ID de la modalidad
     * @param {Array} menus - Array de menús
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
     * Obtener menús de una modalidad específica
     * @param {string} modalidadId - ID de la modalidad
     * @returns {Array} Array de menús
     */
    getMenusModalidad(modalidadId) {
        return this.menusData[modalidadId] || [];
    }

    /**
     * Verificar si una modalidad tiene menús
     * @param {string} modalidadId - ID de la modalidad
     * @returns {boolean} True si tiene menús
     */
    tieneMenusModalidad(modalidadId) {
        return this.menusData[modalidadId] && this.menusData[modalidadId].length > 0;
    }

    /**
     * Obtener estadísticas de modalidades
     * @returns {Object} Estadísticas
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
}

// Exportar para uso global
window.ModalidadesManager = ModalidadesManager;
