/**
 * CopiarMenuManager.js
 * Wizard modal de 3 pasos para copiar preparaciones e ingredientes
 * de un menu origen (otro programa) al menu destino (tarjeta actual).
 *
 * Pasos:
 *   1 — Seleccionar programa origen
 *   2 — Seleccionar menu dentro del programa
 *   3 — Revisar / ajustar preparaciones e ingredientes
 */
class CopiarMenuManager {
    constructor() {
        this._menuDestinoId = null;
        this._menuDestinoNombre = null;
        this._programaActualId = null;
        this._programaOrigenId = null;
        this._menuOrigenId = null;
        this._detalle = null;
        this._pasoActual = 1;
        this._buscarTimeout = null;

        window._copiarMenuMgr = this;
        this._bindClose();
    }

    // ================================================================
    // API PUBLICA
    // ================================================================

    /**
     * Abre el wizard para copiar un menu al menu destino indicado.
     * @param {number} menuDestinoId
     * @param {string} menuDestinoNombre  nombre o numero del menu destino
     * @param {number} programaActualId   para excluirlo de la lista de origenes
     */
    abrir(menuDestinoId, menuDestinoNombre, programaActualId) {
        this._menuDestinoId = menuDestinoId;
        this._menuDestinoNombre = menuDestinoNombre;
        this._programaActualId = programaActualId;
        this._programaOrigenId = null;
        this._menuOrigenId = null;
        this._detalle = null;

        this._irPaso(1);
        this._actualizarTituloDestino();
        document.getElementById('modalCopiarMenu').style.display = 'flex';
        this._cargarProgramas();
    }

    cerrar() {
        document.getElementById('modalCopiarMenu').style.display = 'none';
    }

    // ================================================================
    // NAVEGACION ENTRE PASOS
    // ================================================================

    _irPaso(paso) {
        this._pasoActual = paso;

        [1, 2, 3].forEach(n => {
            const panel = document.getElementById(`cmPaso${n}`);
            if (panel) panel.style.display = n === paso ? 'block' : 'none';

            const dot = document.getElementById(`cmDot${n}`);
            if (dot) {
                dot.classList.toggle('activo', n === paso);
                dot.classList.toggle('completado', n < paso);
                dot.classList.toggle('pendiente', n > paso);
            }
        });

        const btnAtras = document.getElementById('cmBtnAtras');
        const btnSig = document.getElementById('cmBtnSiguiente');
        const btnConf = document.getElementById('cmBtnConfirmar');

        if (btnAtras) btnAtras.style.display = paso > 1 ? 'inline-flex' : 'none';
        if (btnSig) btnSig.style.display = paso < 3 ? 'inline-flex' : 'none';
        if (btnConf) btnConf.style.display = paso === 3 ? 'inline-flex' : 'none';
    }

    _actualizarTituloDestino() {
        const el = document.getElementById('cmMenuDestinoNombre');
        if (el) el.textContent = `Menu ${this._menuDestinoNombre}`;
    }

    atras() {
        if (this._pasoActual > 1) this._irPaso(this._pasoActual - 1);
    }

    async siguiente() {
        if (this._pasoActual === 1) {
            if (!this._programaOrigenId) {
                Swal.fire('Atencion', 'Selecciona un programa origen.', 'warning');
                return;
            }
            this._irPaso(2);
            return;
        }

        if (this._pasoActual === 2) {
            if (!this._menuOrigenId) {
                Swal.fire('Atencion', 'Selecciona un menu origen.', 'warning');
                return;
            }
            this._irPaso(3);
            await this._renderizarPaso3();
            return;
        }
    }

    // ================================================================
    // PASO 1 — PROGRAMAS
    // ================================================================

    async _cargarProgramas() {
        const container = document.getElementById('cmListaProgramas');
        container.innerHTML = '<div class="cm-loading"><div class="cm-spinner"></div><p>Cargando programas...</p></div>';

        try {
            const url = `/nutricion/api/copiar-menu/programas/?excluir_programa_id=${this._programaActualId || ''}`;
            const resp = await fetch(url);
            const data = await resp.json();

            if (!data.programas || data.programas.length === 0) {
                container.innerHTML = '<div class="cm-empty">No hay otros programas con menus configurados.</div>';
                return;
            }

            const frag = document.createDocumentFragment();
            data.programas.forEach(prog => {
                const card = document.createElement('div');
                card.className = 'cm-card';
                card.dataset.id = prog.id;
                card.innerHTML = `
                    <div class="cm-card-body">
                        <div class="cm-card-title">${prog.programa}</div>
                        <div class="cm-card-meta">
                            ${prog.municipio ? `<span>${prog.municipio}</span>` : ''}
                            ${prog.contrato ? `<span>Contrato: ${prog.contrato}</span>` : ''}
                        </div>
                    </div>
                    <span class="cm-badge">${prog.cantidad_menus} menus</span>
                `;
                card.addEventListener('click', () => this._seleccionarPrograma(prog.id, card));
                frag.appendChild(card);
            });

            container.innerHTML = '';
            container.appendChild(frag);
        } catch (e) {
            container.innerHTML = '<div class="cm-empty cm-error">Error al cargar programas.</div>';
        }
    }

    _seleccionarPrograma(programaId, cardEl) {
        document.querySelectorAll('#cmListaProgramas .cm-card').forEach(c => c.classList.remove('seleccionada'));
        cardEl.classList.add('seleccionada');
        this._programaOrigenId = programaId;
        this._menuOrigenId = null;
        this._detalle = null;
        // Pre-cargar menus para paso 2
        this._cargarMenusDePrograma(programaId);
    }

    // ================================================================
    // PASO 2 — MENUS
    // ================================================================

    async _cargarMenusDePrograma(programaId) {
        const container = document.getElementById('cmListaMenus');
        container.innerHTML = '<div class="cm-loading"><div class="cm-spinner"></div><p>Cargando menus...</p></div>';

        try {
            const resp = await fetch(`/nutricion/api/copiar-menu/menus/?programa_id=${programaId}`);
            const data = await resp.json();

            if (!data.menus || data.menus.length === 0) {
                container.innerHTML = '<div class="cm-empty">Este programa no tiene menus configurados.</div>';
                return;
            }

            const frag = document.createDocumentFragment();
            data.menus.forEach(menu => {
                const card = document.createElement('div');
                card.className = 'cm-card cm-card-menu';
                card.dataset.id = menu.id_menu;
                card.innerHTML = `
                    ${menu.semana ? `<span class="cm-badge cm-badge-semana">S${menu.semana}</span>` : ''}
                    <div class="cm-card-body">
                        <div class="cm-card-title">Menu ${menu.menu}</div>
                        <div class="cm-card-meta">
                            <span>${menu.num_preparaciones} preparaciones</span>
                            <span>${menu.num_ingredientes} ingredientes</span>
                        </div>
                    </div>
                `;
                card.addEventListener('click', () => this._seleccionarMenu(menu.id_menu, card));
                frag.appendChild(card);
            });

            container.innerHTML = '';
            container.appendChild(frag);
        } catch (e) {
            container.innerHTML = '<div class="cm-empty cm-error">Error al cargar los menus.</div>';
        }
    }

    async _seleccionarMenu(menuId, cardEl) {
        document.querySelectorAll('#cmListaMenus .cm-card').forEach(c => c.classList.remove('seleccionada'));
        cardEl.classList.add('seleccionada');
        this._menuOrigenId = menuId;
        this._detalle = null;

        // Pre-cargar detalle en background
        try {
            const resp = await fetch(`/nutricion/api/copiar-menu/detalle/?menu_id=${menuId}`);
            this._detalle = await resp.json();
        } catch (e) {
            this._detalle = null;
        }
    }

    // ================================================================
    // PASO 3 — DETALLE + AJUSTE
    // ================================================================

    async _renderizarPaso3() {
        const container = document.getElementById('cmDetallePreps');
        container.innerHTML = '<div class="cm-loading"><div class="cm-spinner"></div><p>Cargando detalle...</p></div>';

        if (!this._detalle) {
            try {
                const resp = await fetch(`/nutricion/api/copiar-menu/detalle/?menu_id=${this._menuOrigenId}`);
                this._detalle = await resp.json();
            } catch (e) {
                container.innerHTML = '<div class="cm-empty cm-error">Error al cargar el detalle del menu.</div>';
                return;
            }
        }

        if (this._detalle.error) {
            container.innerHTML = `<div class="cm-empty cm-error">${this._detalle.error}</div>`;
            return;
        }

        const { preparaciones } = this._detalle;
        if (!preparaciones || preparaciones.length === 0) {
            container.innerHTML = '<div class="cm-empty">Este menu no tiene preparaciones configuradas.</div>';
            return;
        }

        container.innerHTML = '';
        const frag = document.createDocumentFragment();

        preparaciones.forEach((prep, pIdx) => {
            const section = document.createElement('div');
            section.className = 'cm-prep-section';
            section.dataset.prepIdx = pIdx;

            const ingredientesHtml = prep.ingredientes.map((ing, iIdx) => `
                <div class="cm-ing-row" data-prep-idx="${pIdx}" data-ing-idx="${iIdx}">
                    <input type="checkbox" class="cm-ing-check" id="cmIng-${pIdx}-${iIdx}" checked>
                    <label for="cmIng-${pIdx}-${iIdx}" class="cm-ing-label">
                        <span class="cm-ing-nombre">${ing.nombre}</span>
                        ${ing.gramaje != null ? `<span class="cm-ing-gramaje">${ing.gramaje} g</span>` : ''}
                    </label>
                    <button type="button" class="cm-btn-remove-ing"
                            onclick="window._copiarMenuMgr._quitarFila(this)"
                            title="Quitar ingrediente">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `).join('');

            section.innerHTML = `
                <div class="cm-prep-header">
                    <input type="checkbox" class="cm-prep-check" id="cmPrep-${pIdx}" checked
                           onchange="window._copiarMenuMgr._togglePrep(${pIdx}, this.checked)">
                    <label for="cmPrep-${pIdx}" class="cm-prep-nombre">${prep.nombre}</label>
                </div>
                <div class="cm-prep-ingredientes" id="cmIngs-${pIdx}">
                    ${ingredientesHtml}
                    <div class="cm-add-ing-section">
                        <div class="cm-add-ing-search" id="cmSearch-${pIdx}" style="display:none">
                            <input type="text" class="cm-search-input"
                                   placeholder="Buscar alimento ICBF..."
                                   oninput="window._copiarMenuMgr._buscarAlimento(${pIdx}, this.value)"
                                   autocomplete="off">
                            <div class="cm-search-results" id="cmSearchResults-${pIdx}"></div>
                        </div>
                        <button type="button" class="cm-btn-add-ing"
                                onclick="window._copiarMenuMgr._toggleBuscador(${pIdx})">
                            <i class="fas fa-plus"></i> Agregar ingrediente
                        </button>
                    </div>
                </div>
            `;

            frag.appendChild(section);
        });

        container.appendChild(frag);
    }

    _togglePrep(prepIdx, checked) {
        const panel = document.getElementById(`cmIngs-${prepIdx}`);
        if (panel) panel.style.opacity = checked ? '1' : '0.4';
        document.querySelectorAll(`#cmIngs-${prepIdx} .cm-ing-check`).forEach(chk => {
            chk.checked = checked;
        });
    }

    _quitarFila(btnEl) {
        const row = btnEl.closest('.cm-ing-row');
        if (row) row.remove();
    }

    _toggleBuscador(prepIdx) {
        const search = document.getElementById(`cmSearch-${prepIdx}`);
        if (!search) return;
        const visible = search.style.display !== 'none';
        search.style.display = visible ? 'none' : 'block';
        if (!visible) {
            const input = search.querySelector('input');
            if (input) { input.value = ''; input.focus(); }
            const results = document.getElementById(`cmSearchResults-${prepIdx}`);
            if (results) results.innerHTML = '';
        }
    }

    async _buscarAlimento(prepIdx, query) {
        clearTimeout(this._buscarTimeout);
        const resultsEl = document.getElementById(`cmSearchResults-${prepIdx}`);
        if (!query || query.trim().length < 2) {
            if (resultsEl) resultsEl.innerHTML = '';
            return;
        }
        this._buscarTimeout = setTimeout(async () => {
            try {
                const resp = await fetch(`/nutricion/api/copiar-menu/buscar-alimento/?q=${encodeURIComponent(query.trim())}`);
                const data = await resp.json();

                if (!data.alimentos || data.alimentos.length === 0) {
                    resultsEl.innerHTML = '<div class="cm-search-item cm-empty" style="padding:8px 12px">Sin resultados</div>';
                    return;
                }
                resultsEl.innerHTML = data.alimentos.map(al => {
                    const nombreEsc = al.nombre_del_alimento.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
                    return `<div class="cm-search-item"
                                 onclick="window._copiarMenuMgr._agregarIngrediente(${prepIdx}, '${al.codigo}', '${nombreEsc}')">
                                ${al.nombre_del_alimento}
                            </div>`;
                }).join('');
            } catch (e) {
                if (resultsEl) resultsEl.innerHTML = '<div class="cm-search-item cm-error" style="padding:8px 12px">Error en busqueda</div>';
            }
        }, 300);
    }

    _agregarIngrediente(prepIdx, codigo, nombre) {
        const ingsContainer = document.getElementById(`cmIngs-${prepIdx}`);
        if (!ingsContainer) return;

        // Evitar duplicados
        if (ingsContainer.querySelector(`[data-codigo="${codigo}"]`)) {
            const existente = ingsContainer.querySelector(`[data-codigo="${codigo}"] .cm-ing-check`);
            if (existente) existente.checked = true;
            this._toggleBuscador(prepIdx);
            return;
        }

        const addSection = ingsContainer.querySelector('.cm-add-ing-section');
        const uid = `new-${Date.now()}`;
        const row = document.createElement('div');
        row.className = 'cm-ing-row cm-ing-nuevo';
        row.dataset.prepIdx = prepIdx;
        row.dataset.ingIdx = uid;
        row.dataset.codigo = codigo;
        row.dataset.nuevo = '1';
        row.innerHTML = `
            <input type="checkbox" class="cm-ing-check" id="cmIng-${prepIdx}-${uid}" checked>
            <label for="cmIng-${prepIdx}-${uid}" class="cm-ing-label">
                <span class="cm-ing-nombre">${nombre}</span>
                <span class="cm-ing-gramaje-nuevo">
                    <input type="number" class="cm-gramaje-input"
                           placeholder="gramaje (g)" min="0" step="0.1" style="margin-left:6px">
                </span>
            </label>
            <button type="button" class="cm-btn-remove-ing"
                    onclick="window._copiarMenuMgr._quitarFila(this)"
                    title="Quitar">
                <i class="fas fa-times"></i>
            </button>
        `;
        ingsContainer.insertBefore(row, addSection);
        this._toggleBuscador(prepIdx);
    }

    // ================================================================
    // CONFIRMAR Y ENVIAR
    // ================================================================

    async confirmar() {
        const preparaciones = this._recolectarSeleccion();

        if (preparaciones.length === 0) {
            Swal.fire('Atencion', 'Selecciona al menos una preparacion para copiar.', 'warning');
            return;
        }

        const totalIng = preparaciones.reduce((acc, p) => acc + p.ingredientes.length, 0);

        const confirmResult = await Swal.fire({
            title: 'Copiar menu?',
            html: `Se copiarán <strong>${preparaciones.length}</strong> preparacion(es) y
                   <strong>${totalIng}</strong> ingrediente(s) al
                   <strong>Menu ${this._menuDestinoNombre}</strong>.<br><br>
                   <small style="color:#64748b">El contenido previo del menu destino sera reemplazado.</small>`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#10b981',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Si, copiar',
            cancelButtonText: 'Cancelar',
        });

        if (!confirmResult.isConfirmed) return;

        Swal.fire({
            title: 'Copiando...',
            html: '<div class="cm-spinner" style="margin:16px auto;width:32px;height:32px"></div>',
            allowOutsideClick: false,
            showConfirmButton: false,
        });

        try {
            const resp = await fetch('/nutricion/api/copiar-menu/ejecutar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    menu_destino_id: this._menuDestinoId,
                    preparaciones: preparaciones,
                }),
            });

            const data = await resp.json();

            if (data.success) {
                this.cerrar();
                await Swal.fire({
                    title: 'Copiado!',
                    text: `${data.preparaciones} preparaciones y ${data.ingredientes} ingredientes copiados al Menu ${this._menuDestinoNombre}.`,
                    icon: 'success',
                    timer: 2800,
                    showConfirmButton: false,
                });
                // Recargar la vista completa del programa
                location.reload();
            } else {
                Swal.fire('Error', data.error || 'No se pudo copiar el menu.', 'error');
            }
        } catch (e) {
            Swal.fire('Error', 'Problema de conexion con el servidor.', 'error');
        }
    }

    // ================================================================
    // RECOLECTAR SELECCION DESDE EL DOM
    // ================================================================

    _recolectarSeleccion() {
        const preparaciones = [];

        document.querySelectorAll('#cmDetallePreps .cm-prep-section').forEach(section => {
            const prepCheck = section.querySelector('.cm-prep-check');
            if (!prepCheck || !prepCheck.checked) return;

            const pIdx = parseInt(section.dataset.prepIdx);
            const prepData = this._detalle.preparaciones[pIdx];

            const ingredientes = [];
            section.querySelectorAll('.cm-ing-row').forEach(row => {
                const chk = row.querySelector('.cm-ing-check');
                if (!chk || !chk.checked) return;

                const esNuevo = row.dataset.nuevo === '1';

                if (esNuevo) {
                    const gramajeInput = row.querySelector('.cm-gramaje-input');
                    const gramaje = gramajeInput?.value ? parseFloat(gramajeInput.value) : null;
                    ingredientes.push({
                        codigo: row.dataset.codigo,
                        gramaje: gramaje,
                        id_componente: null,
                    });
                } else {
                    const iIdx = parseInt(row.dataset.ingIdx);
                    const ingData = prepData.ingredientes[iIdx];
                    if (ingData) {
                        ingredientes.push({
                            codigo: ingData.codigo,
                            gramaje: ingData.gramaje,
                            id_componente: ingData.id_componente,
                        });
                    }
                }
            });

            preparaciones.push({
                nombre: prepData.nombre,
                id_componente: prepData.id_componente,
                ingredientes: ingredientes,
            });
        });

        return preparaciones;
    }

    // ================================================================
    // UTIL
    // ================================================================

    _bindClose() {
        document.addEventListener('DOMContentLoaded', () => {
            const modal = document.getElementById('modalCopiarMenu');
            if (!modal) return;
            window.addEventListener('click', e => {
                if (e.target === modal) this.cerrar();
            });
        });
    }
}

// ================================================================
// INSTANCIA GLOBAL + FUNCIONES BRIDGE (llamadas desde HTML onclick)
// ================================================================

window.copiarMenuManager = new CopiarMenuManager();

function abrirCopiarMenu(menuId, menuNombre, programaId) {
    window.copiarMenuManager.abrir(menuId, menuNombre, programaId);
}

function cmCerrar()    { window.copiarMenuManager.cerrar(); }
function cmAtras()     { window.copiarMenuManager.atras(); }
function cmSiguiente() { window.copiarMenuManager.siguiente(); }
function cmConfirmar() { window.copiarMenuManager.confirmar(); }
