(function () {
    'use strict';

    // ========================================
    // INICIALIZACIÓN Y DATOS
    // ========================================

    const root = document.getElementById('prepEditorRoot');
    if (!root) return;

    const menuId = root.getAttribute('data-menu-id');

    // Cargar datos desde el template
    let nivelesData = JSON.parse(document.getElementById('niveles-data')?.textContent || '[]');
    const ingredientesCatalogo = JSON.parse(document.getElementById('ingredientes-catalogo')?.textContent || '[]');
    const preparacionesCatalogo = JSON.parse(document.getElementById('preparaciones-catalogo')?.textContent || '[]');
    const componentesCatalogo = JSON.parse(document.getElementById('componentes-catalogo')?.textContent || '[]');
    const gruposCatalogo = JSON.parse(document.getElementById('grupos-catalogo')?.textContent || '[]');
    const componentesPorGrupo = JSON.parse(document.getElementById('componentes-por-grupo')?.textContent || '{}');

    // Diagnóstico: verificar que los catálogos se cargaron correctamente
    console.log('[PrepEditor] Catálogos cargados:', {
        grupos: gruposCatalogo.length,
        componentesPorGrupo: Object.keys(componentesPorGrupo).length,
        ingredientes: ingredientesCatalogo.length,
        preparaciones: preparacionesCatalogo.length
    });

    // Crear mapa de ingredientes para cálculos nutricionales
    const ingredientesMap = new Map();
    ingredientesCatalogo.forEach(ing => {
        ingredientesMap.set(String(ing.codigo), ing);
    });

    // ========================================
    // UTILIDADES
    // ========================================

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function showNotification(message, type = 'success') {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                text: message,
                icon: type,
                timer: 3000,
                showConfirmButton: false
            });
        } else {
            alert(message);
        }
    }

    function obtenerComponentesPorGrupo(grupoId) {
        if (!grupoId) return [];
        const esGrupoEspecias = String(grupoId).trim().toLowerCase() === 'g8';
        const base = esGrupoEspecias
            ? componentesCatalogo
            : (componentesPorGrupo[grupoId] || []);

        // Unificar estructura de datos:
        // - componentesCatalogo: {id_componente, componente}
        // - componentesPorGrupo: {id, nombre}
        return base
            .map(c => ({
                id: c?.id ?? c?.id_componente ?? '',
                nombre: c?.nombre ?? c?.componente ?? ''
            }))
            .filter(c => c.id && c.nombre);
    }

    function mostrarOverlayGuardando(mensaje = 'Guardando cambios...') {
        const overlay = document.createElement('div');
        overlay.className = 'guardando-overlay';
        overlay.id = 'guardandoOverlay';
        overlay.innerHTML = `
            <div class="guardando-card">
                <div class="guardando-spinner"></div>
                <h4 class="guardando-mensaje">${mensaje}</h4>
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    }

    function ocultarOverlayGuardando() {
        const overlay = document.getElementById('guardandoOverlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => {
                overlay.remove();
            }, 200);
        }
    }

    // ========================================
    // VALIDACIÓN DE RANGOS
    // ========================================

    function validarRango(peso, minimo, maximo) {
        if (minimo == null && maximo == null) {
            return { valido: true, clase: 'ok' };
        }

        const pesoNum = parseFloat(peso);
        if (isNaN(pesoNum)) {
            return { valido: false, clase: 'fuera' };
        }

        if (minimo != null && pesoNum < parseFloat(minimo)) {
            return { valido: false, clase: 'fuera' };
        }

        if (maximo != null && pesoNum > parseFloat(maximo)) {
            return { valido: false, clase: 'fuera' };
        }

        return { valido: true, clase: 'ok' };
    }

    function actualizarEstadoFila(row) {
        const input = row.querySelector('.input-peso');
        const badge = row.querySelector('.badge-estado');

        if (!input || !badge) return;

        const peso = parseFloat(input.value) || 0;
        const minimo = input.dataset.minimo;
        const maximo = input.dataset.maximo;

        const resultado = validarRango(peso, minimo, maximo);

        input.classList.remove('fuera-rango', 'en-rango');
        if (minimo || maximo) {
            if (resultado.valido) {
                input.classList.add('en-rango');
            } else {
                input.classList.add('fuera-rango');
            }
        }

        badge.className = 'badge-estado ' + resultado.clase;
        badge.textContent = resultado.valido ? 'OK' : 'FUERA';

        if (resultado.valido) {
            badge.setAttribute('title', 'Dentro del rango permitido');
        } else {
            if (minimo && maximo) {
                badge.setAttribute('title', `Fuera de rango (${minimo}-${maximo}g)`);
            } else if (minimo) {
                badge.setAttribute('title', `Fuera de rango (>= ${minimo}g)`);
            } else if (maximo) {
                badge.setAttribute('title', `Fuera de rango (<= ${maximo}g)`);
            } else {
                badge.setAttribute('title', 'Sin rango definido');
            }
        }

        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipInstance = bootstrap.Tooltip.getInstance(badge);
            if (tooltipInstance) tooltipInstance.dispose();
            new bootstrap.Tooltip(badge);
        }
    }

    function sincronizarSliderConInput(row) {
        const input = row.querySelector('.input-peso');
        const slider = row.querySelector('.slider-peso');
        if (!input || !slider) return;
        slider.value = Math.round(parseFloat(input.value) || 0);
    }

    function sincronizarInputConSlider(row) {
        const input = row.querySelector('.input-peso');
        const slider = row.querySelector('.slider-peso');
        if (!input || !slider) return;
        input.value = parseFloat(slider.value).toFixed(1);
    }

    // ========================================
    // CÁLCULO DE TOTALES DINÁMICO
    // ========================================

    function recalcularNivel(nivelId) {
        const nivelIdNormalizado = String(nivelId);
        const nivelData = nivelesData.find(n => String(n.nivel.id) === nivelIdNormalizado);
        if (!nivelData) return;

        // 1. Actualizar los pesos en el objeto nivelesData leyendo del DOM
        const panel = document.querySelector(`#panel-${nivelIdNormalizado}`);
        if (panel) {
            panel.querySelectorAll('.input-peso').forEach(input => {
                const row = input.closest('tr');
                const idIngrediente = input.dataset.idIngrediente;
                const idPreparacion = row.dataset.idPreparacion;
                const nuevoPeso = parseFloat(input.value) || 0;

                const fila = nivelData.filas.find(f => 
                    String(f.id_ingrediente) === String(idIngrediente) && 
                    String(f.id_preparacion) === String(idPreparacion)
                );
                if (fila) {
                    fila.peso_actualizado = nuevoPeso;
                }
            });
        }

        // 2. Calcular totales usando los pesos actualizados
        const totales = calcularTotalesNivelObjeto(nivelData);
        if (!totales) return;

        nivelData.totales = totales; // Actualizar totales en memoria
        
        // 3. Reflejar en la UI
        actualizarPanelTotales(nivelIdNormalizado, totales, nivelData.requerimientos);
    }

    function calcularTotalesNivelObjeto(nivelData) {
        const totales = {
            calorias: 0,
            proteina: 0,
            grasa: 0,
            cho: 0,
            calcio: 0,
            hierro: 0,
            sodio: 0,
            peso_neto: 0
        };

        nivelData.filas.forEach(fila => {
            const peso = fila.peso_actualizado !== undefined ? fila.peso_actualizado : parseFloat(fila.peso_neto);
            const pesoOriginal = parseFloat(fila.peso_neto) || 100;
            
            // Factor de proporción: si cambio el peso, los nutrientes cambian proporcionalmente
            const factor = pesoOriginal > 0 ? (peso / pesoOriginal) : 0;

            totales.calorias += (fila.calorias || 0) * factor;
            totales.proteina += (fila.proteina || 0) * factor;
            totales.grasa += (fila.grasa || 0) * factor;
            totales.cho += (fila.cho || 0) * factor;
            totales.calcio += (fila.calcio || 0) * factor;
            totales.hierro += (fila.hierro || 0) * factor;
            totales.sodio += (fila.sodio || 0) * factor;
            totales.peso_neto += peso;
        });

        return totales;
    }

    function actualizarPanelTotales(nivelId, totales, requerimientos) {
        const panel = document.querySelector(`#panel-${nivelId}`);
        if (!panel) return;

        // Obtener referencias de adecuación para este nivel (semaforización por proximidad)
        const nivelDataRef = nivelesData.find(n => String(n.nivel.id) === String(nivelId));
        const referencias = nivelDataRef?.referencias || {};

        const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];

        nutrientes.forEach(nutriente => {
            const card = panel.querySelector(`[data-nutriente="${nutriente}"]`);
            if (!card) return;

            const valorActualSpan = card.querySelector('.valor-actual');
            const porcentajeActualSpan = card.querySelector('.porcentaje-actual');

            if (valorActualSpan) {
                valorActualSpan.textContent = totales[nutriente].toFixed(1);
            }

            const requerimiento = requerimientos[nutriente] || 1;
            const porcentaje = (totales[nutriente] / requerimiento) * 100;

            if (porcentajeActualSpan) {
                porcentajeActualSpan.textContent = porcentaje.toFixed(1);
            }

            // Semaforización por proximidad al valor de referencia ICBF
            let estado;
            const ref = referencias[nutriente];
            if (ref !== undefined && ref !== null) {
                const diff = Math.abs(porcentaje - parseFloat(ref));
                if (diff <= 3)       estado = 'optimo';
                else if (diff <= 5)  estado = 'azul';
                else if (diff <= 7)  estado = 'aceptable';
                else                 estado = 'alto';
            } else {
                // Fallback: rangos absolutos
                if (porcentaje <= 35)      estado = 'optimo';
                else if (porcentaje <= 70) estado = 'aceptable';
                else                       estado = 'alto';
            }

            card.className = `nutriente-card ${estado}`;
            const porcentajeDiv = card.querySelector('.nutriente-porcentaje');
            if (porcentajeDiv) {
                porcentajeDiv.className = `nutriente-porcentaje ${estado}`;
            }
        });
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================

    function actualizarPesoBruto(row) {
        const input = row.querySelector('.input-peso');
        const cell  = row.querySelector('.peso-bruto-cell');
        if (!input || !cell) return;
        const pesoNeto        = parseFloat(input.value) || 0;
        const parteComestible = parseFloat(input.dataset.parteComestible) || 100;
        const pesoBruto = parteComestible > 0
            ? (pesoNeto * 100) / parteComestible
            : pesoNeto;
        cell.textContent = pesoBruto.toFixed(1);
    }

    document.addEventListener('input', (e) => {
        if (e.target.classList.contains('input-peso')) {
            const row = e.target.closest('tr');
            const tbody = e.target.closest('.tbody-ingredientes');
            if (row && tbody) {
                const nivelId = tbody.dataset.nivelId;
                actualizarPesoBruto(row);
                actualizarEstadoFila(row);
                sincronizarSliderConInput(row);
                recalcularNivel(nivelId);
            }
        }

        if (e.target.classList.contains('slider-peso')) {
            const row = e.target.closest('tr');
            const tbody = e.target.closest('.tbody-ingredientes');
            if (row && tbody) {
                const nivelId = tbody.dataset.nivelId;
                sincronizarInputConSlider(row);
                actualizarPesoBruto(row);
                actualizarEstadoFila(row);
                recalcularNivel(nivelId);
            }
        }
    });

    const btnAgregarFila = document.getElementById('btnAgregarFila');
    if (btnAgregarFila) {
        btnAgregarFila.addEventListener('click', agregarIngredienteATodosLosNiveles);
    }

    const btnGuardarCambios = document.getElementById('btnGuardarCambios');
    if (btnGuardarCambios) {
        btnGuardarCambios.addEventListener('click', async () => {
            const cambiosPorNivel = [];

            nivelesData.forEach(nivelData => {
                const panel = document.querySelector(`#panel-${nivelData.nivel.id}`);
                if (!panel) return;

                const tbody = panel.querySelector('.tbody-ingredientes');
                if (!tbody) return;

                const ingredientes = [];
                tbody.querySelectorAll('tr').forEach(row => {
                    const pesoInput = row.querySelector('.input-peso');
                    if (!pesoInput) return;

                    ingredientes.push({
                        id_preparacion: parseInt(row.dataset.idPreparacion),
                        id_ingrediente: pesoInput.dataset.idIngrediente,
                        peso_neto: parseFloat(pesoInput.value) || 0
                    });
                });

                cambiosPorNivel.push({
                    id_nivel_escolar: nivelData.nivel.id,
                    id_analisis: nivelData.id_analisis,
                    ingredientes: ingredientes
                });
            });

            // Recoger cambios de grupo/componente desde el primer nivel (son iguales para todos)
            const filasGrupoComp = [];
            const primerPanel = document.querySelector('.tab-pane.show.active .tbody-ingredientes')
                             || document.querySelector('.tbody-ingredientes');
            if (primerPanel) {
                primerPanel.querySelectorAll('tr').forEach(row => {
                    const selectGrupo = row.querySelector('.select-grupo');
                    const selectComp = row.querySelector('.select-componente');
                    if (!selectGrupo) return;
                    filasGrupoComp.push({
                        id_preparacion: parseInt(row.dataset.idPreparacion),
                        id_ingrediente: row.dataset.idIngrediente,
                        id_grupo: selectGrupo.value || null,
                        id_componente: selectComp?.value || null,
                        gramaje: null
                    });
                });
            }

            const overlay = mostrarOverlayGuardando('Guardando cambios...');

            try {
                btnGuardarCambios.disabled = true;
                btnGuardarCambios.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando...';

                // 1. Guardar pesos por nivel
                const response = await fetch(`/nutricion/api/menus/${menuId}/guardar-ingredientes-por-nivel/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ niveles: cambiosPorNivel })
                });

                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'Error al guardar cambios');
                }

                // 2. Guardar grupo/componente por ingrediente (solo si hay cambios)
                if (filasGrupoComp.length > 0) {
                    await fetch(`/nutricion/api/menus/${menuId}/guardar-preparaciones-editor/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({ filas: filasGrupoComp })
                    });
                    // Ignoramos errores de esta segunda llamada para no bloquear el flujo principal
                }

                ocultarOverlayGuardando();

                if (data.errores && data.errores.length > 0) {
                    showNotification(
                        `⚠️ Guardado parcial: ${data.registros_actualizados} ingrediente(s) guardado(s). Errores: ${data.errores.join(', ')}`,
                        'warning'
                    );
                } else {
                    showNotification(`✅ Cambios guardados exitosamente (${data.registros_actualizados} ingrediente(s)).`, 'success');
                }

                setTimeout(() => {
                    window.location.reload();
                }, 1000);

            } catch (error) {
                console.error('Error al guardar:', error);
                ocultarOverlayGuardando();
                showNotification(error.message || 'Error al guardar cambios', 'error');
            } finally {
                btnGuardarCambios.disabled = false;
                btnGuardarCambios.innerHTML = '<i class="bi bi-save"></i> Guardar cambios';
            }
        });
    }

// ========================================
    // FUNCIONES DE SOPORTE
    // ========================================

    function escaparHtml(texto) {
        const div = document.createElement('div');
        div.textContent = texto == null ? '' : String(texto);
        return div.innerHTML;
    }

    function quitarFilasDeIngredienteEnTodosLosNiveles(idPreparacion, idIngrediente) {
        // Quitar del modelo en memoria para que guardados y cálculos futuros no lo incluyan.
        nivelesData.forEach((nivelData) => {
            nivelData.filas = (nivelData.filas || []).filter((fila) => !(
                String(fila.id_preparacion) === String(idPreparacion) &&
                String(fila.id_ingrediente) === String(idIngrediente)
            ));
        });

        // Quitar del DOM en todos los tabs/niveles.
        document.querySelectorAll('.tbody-ingredientes tr').forEach((row) => {
            if (
                String(row.dataset.idPreparacion) === String(idPreparacion) &&
                String(row.dataset.idIngrediente) === String(idIngrediente)
            ) {
                row.remove();
            }
        });

        // Recalcular tarjetas nutricionales de todos los niveles.
        nivelesData.forEach((nivelData) => {
            recalcularNivel(nivelData.nivel.id);
        });
    }

    async function eliminarIngredienteDePreparacion(idPreparacion, idIngrediente) {
        const mensajeConfirmacion = '¿Eliminar este ingrediente de la preparación en todos los niveles?';
        const confirmado = typeof Swal !== 'undefined'
            ? (await Swal.fire({
                text: mensajeConfirmacion,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            })).isConfirmed
            : confirm(mensajeConfirmacion);

        if (!confirmado) return;

        const overlay = mostrarOverlayGuardando('Eliminando ingrediente...');
        try {
            const response = await fetch(
                `/nutricion/api/preparaciones/${idPreparacion}/ingredientes/${encodeURIComponent(idIngrediente)}/`,
                {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') }
                }
            );
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'No fue posible eliminar el ingrediente');
            }

            quitarFilasDeIngredienteEnTodosLosNiveles(idPreparacion, idIngrediente);
            showNotification('Ingrediente eliminado correctamente.', 'success');
            setTimeout(() => window.location.reload(), 1200);
        } catch (error) {
            console.error('Error al eliminar ingrediente:', error);
            ocultarOverlayGuardando();
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Error al eliminar',
                    text: error.message || 'No fue posible eliminar el ingrediente. Intente de nuevo.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            } else {
                alert(error.message || 'Error al eliminar ingrediente');
            }
            return;
        } finally {
            ocultarOverlayGuardando();
        }
    }

    async function eliminarPreparacion(idPreparacion, nombrePrep) {
        const confirmado = typeof Swal !== 'undefined'
            ? (await Swal.fire({
                title: 'Eliminar preparación',
                text: `¿Eliminar "${nombrePrep}" con todos sus ingredientes? Esta acción no se puede deshacer.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#dc3545'
            })).isConfirmed
            : confirm(`¿Eliminar la preparación "${nombrePrep}"?`);

        if (!confirmado) return;

        const overlay = mostrarOverlayGuardando('Eliminando preparación...');
        try {
            const response = await fetch(
                `/nutricion/api/preparaciones/${idPreparacion}/`,
                {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') }
                }
            );
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'No fue posible eliminar la preparación');
            }

            showNotification(`Preparación "${nombrePrep}" eliminada correctamente.`, 'success');
            setTimeout(() => window.location.reload(), 1200);
        } catch (error) {
            console.error('Error al eliminar preparación:', error);
            ocultarOverlayGuardando();
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Error al eliminar',
                    text: error.message || 'No fue posible eliminar la preparación. Intente de nuevo.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            } else {
                alert(error.message || 'Error al eliminar preparación');
            }
            return;
        } finally {
            ocultarOverlayGuardando();
        }
    }

    async function agregarIngredienteATodosLosNiveles() {
        if (typeof Swal === 'undefined') {
            showNotification('Se requiere SweetAlert2', 'info');
            return;
        }

        const opcionesPreparaciones = preparacionesCatalogo.map((prep) => (
            `<option value="${prep.id_preparacion}">${escaparHtml(prep.preparacion)}</option>`
        )).join('');

        const opcionesIngredientes = ingredientesCatalogo.map((ing) => (
            `<option value="${escaparHtml(ing.codigo)}">${escaparHtml(ing.codigo)} - ${escaparHtml(ing.nombre_del_alimento)}</option>`
        )).join('');

        const opcionesGrupos = gruposCatalogo.map((g) => (
            `<option value="${g.id}">${escaparHtml(g.nombre)}</option>`
        )).join('');

        const result = await Swal.fire({
            title: '<div class="swal-title-inner"><i class="bi bi-plus-circle-fill swal-title-icon"></i><span class="swal-title-text">Agregar Preparación</span></div>',
            width: 700,
            showCancelButton: true,
            confirmButtonText: '<i class="bi bi-check-circle-fill"></i> Agregar',
            cancelButtonText: '<i class="bi bi-x-circle"></i> Cancelar',
            customClass: {
                popup: 'swal-popup-modern',
                title: 'swal-title-modern',
                confirmButton: 'swal-confirm-modern',
                cancelButton: 'swal-cancel-modern'
            },
            html: `
                <div class="swal-body-padding">
                    <div class="modal-field-group">
                        <label class="modal-label">
                            <i class="bi bi-egg-fried modal-label-icon-purple"></i>
                            Preparación
                            <span class="required-star">*</span>
                        </label>
                        <select id="agregarModoPrep" class="modal-select">
                            <option value="existente">Usar preparación existente</option>
                            <option value="nueva">Crear nueva preparación</option>
                        </select>
                    </div>

                    <div id="bloquePrepExistente" class="modal-field-group">
                        <select id="agregarPreparacionExistente" class="modal-select">
                            <option value="">Seleccione una preparación...</option>
                            ${opcionesPreparaciones}
                        </select>
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Seleccione la preparación a la que agregará el ingrediente
                        </small>
                    </div>

                    <div id="bloquePrepNueva" class="modal-field-group" style="display:none;">
                        <input id="agregarPreparacionNueva" class="modal-input" placeholder="Nombre de la nueva preparación" />
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Ingrese el nombre de la nueva preparación
                        </small>
                    </div>

                    <div id="bloqueComponente" class="modal-field-group">
                        <label class="modal-label">
                            <i class="bi bi-grid-3x3-gap-fill modal-label-icon-yellow"></i>
                            Grupo de Alimento
                            <span class="required-star">*</span>
                        </label>
                        <select id="agregarGrupoId" class="modal-select">
                            <option value="">— seleccione grupo —</option>
                            ${opcionesGrupos}
                        </select>
                        <label class="modal-label modal-label-top-spacing">
                            <i class="bi bi-tag-fill modal-label-icon-yellow"></i>
                            Componente
                            <span class="required-star">*</span>
                        </label>
                        <select id="agregarComponenteId" class="modal-select">
                            <option value="">— seleccione componente —</option>
                        </select>
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Seleccione primero el grupo para filtrar los componentes disponibles
                        </small>
                    </div>

                    <div class="modal-field-group">
                        <label class="modal-label">
                            <i class="bi bi-basket3 modal-label-icon-green"></i>
                            Ingrediente ICBF
                            <span class="required-star">*</span>
                        </label>
                        <div class="input-search-wrapper">
                            <i class="bi bi-search input-search-icon"></i>
                            <input id="filtroIngrediente" class="modal-input modal-input-search"
                                   placeholder="Filtrar por nombre o código..."
                                   autocomplete="off" />
                        </div>
                        <select id="agregarIngredienteId" class="modal-select modal-select-multirow" size="5">
                            <option value="">— seleccione —</option>
                            ${opcionesIngredientes}
                        </select>
                        <small class="modal-help-text" id="contadorIngredientes">
                            <i class="bi bi-list-ul"></i>
                            ${ingredientesCatalogo.length} ingredientes disponibles
                        </small>
                    </div>

                    <div class="modal-info-box">
                        <div class="modal-info-box-content">
                            <i class="bi bi-lightbulb-fill modal-info-icon"></i>
                            <div class="modal-info-text">
                                <div class="modal-info-title">Nota importante</div>
                                <div class="modal-info-desc">
                                    El ingrediente se agregará a <strong>todos los niveles escolares</strong>.
                                    Podrás ajustar los pesos individuales después.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            didOpen: () => {
                const modo = document.getElementById('agregarModoPrep');
                const bExistente = document.getElementById('bloquePrepExistente');
                const bNueva = document.getElementById('bloquePrepNueva');
                const bComponente = document.getElementById('bloqueComponente');
                const selectGrupo = document.getElementById('agregarGrupoId');
                const selectComponente = document.getElementById('agregarComponenteId');

                // Cascade: al cambiar grupo, filtrar componentes
                const actualizarComponentesModal = (grupoId, compActual) => {
                    selectComponente.innerHTML = '<option value="">— seleccione componente —</option>';
                    if (!grupoId) return;
                    const comps = obtenerComponentesPorGrupo(grupoId);
                    comps.forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.textContent = c.nombre;
                        if (c.id === compActual) opt.selected = true;
                        selectComponente.appendChild(opt);
                    });
                };

                selectGrupo.addEventListener('change', () => {
                    actualizarComponentesModal(selectGrupo.value, '');
                });

                const actualizarVistaModo = () => {
                    const esNueva = modo.value === 'nueva';
                    bExistente.style.display = esNueva ? 'none' : 'block';
                    bNueva.style.display = esNueva ? 'block' : 'none';
                    bComponente.style.display = 'block';
                };

                modo.addEventListener('change', () => {
                    actualizarVistaModo();
                });
                document.getElementById('agregarPreparacionExistente').addEventListener('change', () => {
                    if (modo.value === 'existente') {
                        actualizarVistaModo();
                    }
                });
                actualizarVistaModo();

                // Filtro de ingredientes en tiempo real
                const filtroIng = document.getElementById('filtroIngrediente');
                const selectIng = document.getElementById('agregarIngredienteId');
                const contador = document.getElementById('contadorIngredientes');

                filtroIng.addEventListener('input', () => {
                    const termino = filtroIng.value.toLowerCase().trim();

                    const filtrados = termino
                        ? ingredientesCatalogo.filter(ing =>
                            ing.nombre_del_alimento.toLowerCase().includes(termino) ||
                            String(ing.codigo).toLowerCase().includes(termino)
                          )
                        : ingredientesCatalogo;

                    const valorActual = selectIng.value;

                    // Reconstruir opciones del select
                    selectIng.innerHTML = '<option value="">— seleccione —</option>';
                    filtrados.forEach(ing => {
                        const opt = document.createElement('option');
                        opt.value = ing.codigo;
                        opt.textContent = `${ing.codigo} - ${ing.nombre_del_alimento}`;
                        selectIng.appendChild(opt);
                    });

                    // Restaurar selección si sigue siendo válida
                    if (valorActual && filtrados.some(ing => String(ing.codigo) === String(valorActual))) {
                        selectIng.value = valorActual;
                    }

                    // Actualizar contador
                    if (contador) {
                        contador.innerHTML = termino
                            ? `<i class="bi bi-funnel-fill"></i> ${filtrados.length} de ${ingredientesCatalogo.length} ingredientes`
                            : `<i class="bi bi-list-ul"></i> ${ingredientesCatalogo.length} ingredientes disponibles`;
                    }

                    // Si hay exactamente un resultado, seleccionarlo automáticamente
                    if (filtrados.length === 1) {
                        selectIng.value = filtrados[0].codigo;
                    }
                });

                // Focus automático en el filtro al abrir el modal
                setTimeout(() => filtroIng.focus(), 100);
            },
            preConfirm: () => {
                const modo = document.getElementById('agregarModoPrep').value;
                const idPrep = document.getElementById('agregarPreparacionExistente').value;
                const nomPrep = document.getElementById('agregarPreparacionNueva').value.trim();
                const idGrupo = document.getElementById('agregarGrupoId').value;
                const idComp = document.getElementById('agregarComponenteId').value;
                const idIng = document.getElementById('agregarIngredienteId').value;

                // Validaciones
                if (!idIng) {
                    return Swal.showValidationMessage('Debes seleccionar un ingrediente');
                }

                if (modo === 'existente' && !idPrep) {
                    return Swal.showValidationMessage('Debes seleccionar una preparación existente');
                }

                if (modo === 'nueva' && !nomPrep) {
                    return Swal.showValidationMessage('Debes escribir el nombre de la nueva preparación');
                }

                if (!idGrupo) {
                    return Swal.showValidationMessage('Debes seleccionar un grupo de alimento');
                }

                if (!idComp) {
                    return Swal.showValidationMessage('Debes seleccionar un componente');
                }

                return {
                    id_preparacion: modo === 'existente' ? parseInt(idPrep) : null,
                    preparacion_nombre: modo === 'nueva' ? nomPrep : '',
                    id_grupo: idGrupo || null,
                    id_componente: idComp || null,
                    id_ingrediente: idIng,
                    gramaje: null  // Siempre null, se usarán valores predeterminados por nivel
                };
            }
        });

        if (!result.isConfirmed) return;

        const overlay = mostrarOverlayGuardando('Agregando ingrediente...');
        try {
            const response = await fetch(`/nutricion/api/menus/${menuId}/guardar-preparaciones-editor/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ filas: [result.value] })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                // Construir mensaje de error detallado
                let errorMsg = data.error || 'Error al agregar ingrediente';

                // Si hay errores específicos, agregarlos
                if (data.errores && data.errores.length > 0) {
                    errorMsg += ':\n' + data.errores.join('\n');
                }

                throw new Error(errorMsg);
            }

            ocultarOverlayGuardando();
            showNotification('✅ Ingrediente agregado exitosamente', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } catch (error) {
            console.error('Error al agregar ingrediente:', error);
            ocultarOverlayGuardando();
            showNotification(error.message || 'Error desconocido al agregar ingrediente', 'error');
        }
    }

    // ========================================
    // DROPDOWNS CASCADE GRUPO → COMPONENTE
    // ========================================

    function poblarSelectGrupo(selectGrupo) {
        const grupoActual = selectGrupo.dataset.grupoActual || '';
        selectGrupo.innerHTML = '<option value="">— Grupo —</option>';
        gruposCatalogo.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.nombre;
            if (g.id === grupoActual) opt.selected = true;
            selectGrupo.appendChild(opt);
        });
    }

    function poblarSelectComponente(selectComp, grupoId, componenteActual) {
        selectComp.innerHTML = '<option value="">— Componente —</option>';
        if (!grupoId) return;
        const comps = obtenerComponentesPorGrupo(grupoId);
        comps.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.nombre;
            if (c.id === componenteActual) opt.selected = true;
            selectComp.appendChild(opt);
        });
    }

    function inicializarSelectsGrupoComponente() {
        const selects = document.querySelectorAll('.select-grupo');
        console.log(`[PrepEditor] inicializarSelectsGrupoComponente: ${selects.length} selects encontrados, ${gruposCatalogo.length} grupos disponibles`);
        selects.forEach(selectGrupo => {
            const row = selectGrupo.closest('tr');
            if (!row) return;
            poblarSelectGrupo(selectGrupo);

            // Poblar componente con el valor actual
            const selectComp = row.querySelector('.select-componente');
            if (selectComp) {
                const grupoId = selectGrupo.value;
                const compActual = selectComp.dataset.componenteActual || '';
                poblarSelectComponente(selectComp, grupoId, compActual);
            }
        });
    }

    // Sincronizar selects del mismo ingrediente en todos los niveles
    function sincronizarSelectsEnNiveles(idPreparacion, idIngrediente, grupoId, compId) {
        document.querySelectorAll('.select-grupo').forEach(sg => {
            if (
                String(sg.dataset.idPreparacion) === String(idPreparacion) &&
                String(sg.dataset.idIngrediente) === String(idIngrediente) &&
                sg.value !== grupoId
            ) {
                sg.value = grupoId;
                const row = sg.closest('tr');
                const sc = row?.querySelector('.select-componente');
                if (sc) {
                    poblarSelectComponente(sc, grupoId, compId);
                }
            }
        });
    }

    // Listener delegado para cambio en select-grupo
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('select-grupo')) {
            const selectGrupo = e.target;
            const row = selectGrupo.closest('tr');
            if (!row) return;
            const selectComp = row.querySelector('.select-componente');
            if (selectComp) {
                poblarSelectComponente(selectComp, selectGrupo.value, '');
            }
            // Sincronizar en otros niveles
            sincronizarSelectsEnNiveles(
                selectGrupo.dataset.idPreparacion,
                selectGrupo.dataset.idIngrediente,
                selectGrupo.value,
                ''
            );
        }
        if (e.target.classList.contains('select-componente')) {
            const selectComp = e.target;
            const row = selectComp.closest('tr');
            if (!row) return;
            const selectGrupo = row.querySelector('.select-grupo');
            const grupoId = selectGrupo?.value || '';
            const compId = selectComp.value;
            // Sincronizar componente en otros niveles
            document.querySelectorAll('.select-componente').forEach(sc => {
                if (
                    String(sc.dataset.idPreparacion) === String(selectComp.dataset.idPreparacion) &&
                    String(sc.dataset.idIngrediente) === String(selectComp.dataset.idIngrediente) &&
                    sc !== selectComp
                ) {
                    if (sc.value !== compId) {
                        poblarSelectComponente(sc, grupoId, compId);
                    }
                }
            });
        }
    });

    // ========================================
    // INICIALIZACIÓN
    // ========================================

    function inicializar() {
        document.querySelectorAll('.input-peso').forEach(input => {
            const row = input.closest('tr');
            if (row) {
                sincronizarSliderConInput(row);
                actualizarEstadoFila(row);
            }
        });

        inicializarSelectsGrupoComponente();

        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }

        console.log('✅ Editor inicializado. Niveles:', nivelesData.length);
    }

    document.addEventListener('click', (e) => {
        const btnEliminarIngrediente = e.target.closest('.btn-eliminar-ingrediente-editor');
        if (btnEliminarIngrediente) {
            const idPreparacion = btnEliminarIngrediente.dataset.idPreparacion;
            const idIngrediente = btnEliminarIngrediente.dataset.idIngrediente;
            if (!idPreparacion || !idIngrediente) return;
            eliminarIngredienteDePreparacion(idPreparacion, idIngrediente);
            return;
        }

        const btnEliminarPrep = e.target.closest('.btn-eliminar-preparacion-editor');
        if (btnEliminarPrep) {
            const idPreparacion = btnEliminarPrep.dataset.idPreparacion;
            const nombrePrep = btnEliminarPrep.dataset.nombrePreparacion || 'esta preparación';
            if (!idPreparacion) return;
            eliminarPreparacion(idPreparacion, nombrePrep);
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

})();
