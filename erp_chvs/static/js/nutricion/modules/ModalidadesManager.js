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
        grid.className = 'menus-grid';
        grid.id = `grid-${modalidadId}`;

        if (tieneMenus) {
            grid.innerHTML = this.generarTarjetasMenus(menusModalidad);
        } else {
            grid.innerHTML = `<p style="padding: 20px;" id="placeholder-${modalidadId}">Genere los menús para esta modalidad</p>`;
        }

        content.appendChild(grid);
        accordionDiv.appendChild(header);
        accordionDiv.appendChild(content);
        
        return accordionDiv;
    }

    /**
     * Generar tarjetas de menús
     * @param {Array} menus - Array de menús
     * @param {boolean} animate - Si se deben animar las tarjetas
     * @returns {string} HTML de las tarjetas
     */
    generarTarjetasMenus(menus, animate = false) {
        const tarjetasMenus = menus.map((menu, index) => {
            const esNumerico = !isNaN(menu.menu) && parseInt(menu.menu) >= 1 && parseInt(menu.menu) <= 20;
            const esEspecial = !esNumerico;
            const menuEscaped = String(menu.menu).replace(/'/g, "\\'");
            const downloadUrl = `/nutricion/exportar-excel/${menu.id_menu}/`;
            
            // Estilo de animación escalonada
            const animStyle = animate ? `style="animation-delay: ${index * 0.05}s"` : '';
            const animClass = animate ? 'menu-card-anim' : '';

            if (esEspecial) {
                return `
                    <div class="menu-card menu-card-especial ${animClass} ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                         ${animStyle}
                         onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                        <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                            <i class="fas fa-file-excel"></i>
                        </a>
                        <div class="menu-numero-especial">
                            ${menu.menu}
                        </div>
                        <div class="menu-actions" style="flex-direction: column;">
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                                <i class="fas fa-utensils"></i> Preparaciones
                            </button>
                            <button class="btn btn-sm btn-warning" onclick="event.stopPropagation(); abrirEditarMenuEspecial(${menu.id_menu}, '${menuEscaped}')">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div class="menu-card ${animClass} ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                         ${animStyle}
                         onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                        <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                            <i class="fas fa-file-excel"></i>
                        </a>
                        <div class="menu-numero">${menu.menu}</div>
                        <div class="menu-actions">
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                                <i class="fas fa-utensils"></i> Preparaciones
                            </button>
                        </div>
                    </div>
                `;
            }
        }).join('');

        const modalidadId = menus.length > 0 ? menus[0].id_modalidad__id_modalidades : '';
        const delayBase = animate ? menus.length * 0.05 : 0;
        
        const tarjetaEspecial = `
            <div class="menu-card menu-card-especial ${animate ? 'menu-card-anim' : ''}" 
                 ${animate ? `style="animation-delay: ${delayBase + 0.1}s"` : ''}
                 onclick="abrirModalMenuEspecial('${modalidadId}')">
                <div class="menu-numero-especial">
                    <i class="fas fa-plus-circle"></i>
                </div>
                <div class="menu-label-especial">Crear Especial</div>
            </div>
            <div class="menu-card menu-card-ia ${animate ? 'menu-card-anim' : ''}" 
                 ${animate ? `style="animation-delay: ${delayBase + 0.2}s"` : ''}
                 onclick="abrirModalMenuIA('${modalidadId}')">
                <div class="menu-numero-ia">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="menu-label-ia">Generar con IA</div>
            </div>
        `;

        return tarjetasMenus + tarjetaEspecial;
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
                
                // 5. Cerrar modal de carga y mostrar éxito
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
