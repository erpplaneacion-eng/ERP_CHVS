(function () {
    'use strict';

    // ========================================
    // INICIALIZACIÃ“N Y DATOS
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

    // DiagnÃ³stico: verificar que los catÃ¡logos se cargaron correctamente
    console.log('[PrepEditor] CatÃ¡logos cargados:', {
        grupos: gruposCatalogo.length,
        componentesPorGrupo: Object.keys(componentesPorGrupo).length,
        ingredientes: ingredientesCatalogo.length,
        preparaciones: preparacionesCatalogo.length
    });

    // Crear mapa de ingredientes para cÃ¡lculos nutricionales
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
    // VALIDACIÃ“N DE RANGOS
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
    // CÃLCULO DE TOTALES DINÃMICO
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
            
            // Factor de proporciÃ³n: si cambio el peso, los nutrientes cambian proporcionalmente
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

        // Obtener referencias de adecuaciÃ³n para este nivel (semaforizaciÃ³n por proximidad)
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

            // SemaforizaciÃ³n por proximidad al valor de referencia ICBF
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

    const btnCopiarPreparacion = document.getElementById('btnCopiarPreparacion');
    if (btnCopiarPreparacion) {
        btnCopiarPreparacion.addEventListener('click', copiarPreparacionDesdeOtroMenu);
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
                        `âš ï¸ Guardado parcial: ${data.registros_actualizados} ingrediente(s) guardado(s). Errores: ${data.errores.join(', ')}`,
                        'warning'
                    );
                } else {
                    showNotification(`âœ… Cambios guardados exitosamente (${data.registros_actualizados} ingrediente(s)).`, 'success');
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
        // Quitar del modelo en memoria para que guardados y cÃ¡lculos futuros no lo incluyan.
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

    function actualizarNombrePreparacionEnUI(idPreparacion, nuevoNombre) {
        document.querySelectorAll(`.prep-header-nombre[data-id-preparacion="${idPreparacion}"]`).forEach(el => {
            el.textContent = nuevoNombre;
        });

        document.querySelectorAll(`.prep-nombre-celda[data-id-preparacion="${idPreparacion}"]`).forEach(el => {
            el.textContent = nuevoNombre;
        });

        document.querySelectorAll(`.btn-eliminar-preparacion-editor[data-id-preparacion="${idPreparacion}"]`).forEach(btn => {
            btn.dataset.nombrePreparacion = nuevoNombre;
        });

        document.querySelectorAll(`.btn-editar-preparacion-inline[data-id-preparacion="${idPreparacion}"]`).forEach(btn => {
            btn.dataset.nombrePreparacion = nuevoNombre;
        });

        preparacionesCatalogo.forEach(prep => {
            if (String(prep.id_preparacion) === String(idPreparacion)) {
                prep.preparacion = nuevoNombre;
            }
        });

        nivelesData.forEach(nivel => {
            (nivel.filas || []).forEach(fila => {
                if (String(fila.id_preparacion) === String(idPreparacion)) {
                    fila.preparacion = nuevoNombre;
                }
            });
        });
    }

    function cancelarEdicionInlinePreparacion(headerRow) {
        if (!headerRow) return;
        const nombreEl = headerRow.querySelector('.prep-header-nombre');
        const btnEditar = headerRow.querySelector('.btn-editar-preparacion-inline');
        const editor = headerRow.querySelector('.prep-inline-editor');

        if (editor) editor.remove();
        if (nombreEl) nombreEl.classList.remove('d-none');
        if (btnEditar) btnEditar.classList.remove('d-none');
    }

    function abrirEdicionInlinePreparacion(btnEditar) {
        const headerRow = btnEditar.closest('.prep-header-row');
        if (!headerRow) return;

        const nombreEl = headerRow.querySelector('.prep-header-nombre');
        if (!nombreEl) return;

        if (headerRow.querySelector('.prep-inline-editor')) return;

        const nombreActual = (btnEditar.dataset.nombrePreparacion || nombreEl.textContent || '').trim();
        const editor = document.createElement('div');
        editor.className = 'prep-inline-editor d-flex align-items-center gap-2';
        editor.innerHTML = `
            <input type="text" class="form-control form-control-sm input-preparacion-inline" value="${escaparHtml(nombreActual)}" />
            <button type="button" class="btn btn-success btn-sm btn-guardar-preparacion-inline">
                <i class="bi bi-check-lg"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm btn-cancelar-preparacion-inline">
                <i class="bi bi-x-lg"></i>
            </button>
        `;

        nombreEl.classList.add('d-none');
        btnEditar.classList.add('d-none');
        nombreEl.insertAdjacentElement('afterend', editor);

        const input = editor.querySelector('.input-preparacion-inline');
        if (input) {
            input.focus();
            input.select();
        }
    }

    async function guardarNombrePreparacionInline(btnGuardar) {
        const headerRow = btnGuardar.closest('.prep-header-row');
        if (!headerRow) return;

        const idPreparacion = headerRow.dataset.idPreparacion;
        const input = headerRow.querySelector('.input-preparacion-inline');
        if (!idPreparacion || !input) return;

        const nuevoNombre = input.value.trim();
        if (!nuevoNombre) {
            showNotification('El nombre de la preparacion no puede estar vacÃ­o.', 'warning');
            input.focus();
            return;
        }

        btnGuardar.disabled = true;
        try {
            const response = await fetch(`/nutricion/api/preparaciones/${idPreparacion}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    preparacion: nuevoNombre,
                    id_menu: parseInt(menuId, 10)
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'No fue posible actualizar la preparacion');
            }

            actualizarNombrePreparacionEnUI(idPreparacion, nuevoNombre);
            cancelarEdicionInlinePreparacion(headerRow);
            showNotification('Nombre de preparacion actualizado.', 'success');
        } catch (error) {
            console.error('Error al actualizar preparacion:', error);
            showNotification(error.message || 'Error al actualizar preparacion', 'error');
        } finally {
            btnGuardar.disabled = false;
        }
    }

    async function eliminarIngredienteDePreparacion(idPreparacion, idIngrediente) {
        const mensajeConfirmacion = 'Â¿Eliminar este ingrediente de la preparacion en todos los niveles?';
        const confirmado = typeof Swal !== 'undefined'
            ? (await Swal.fire({
                text: mensajeConfirmacion,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'SÃ­, eliminar',
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
                title: 'Eliminar preparacion',
                text: `Â¿Eliminar "${nombrePrep}" con todos sus ingredientes? Esta acciÃ³n no se puede deshacer.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'SÃ­, eliminar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#dc3545'
            })).isConfirmed
            : confirm(`Â¿Eliminar la preparacion "${nombrePrep}"?`);

        if (!confirmado) return;

        const overlay = mostrarOverlayGuardando('Eliminando preparacion...');
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
                throw new Error(data.error || 'No fue posible eliminar la preparacion');
            }

            showNotification(`PreparaciÃ³n "${nombrePrep}" eliminada correctamente.`, 'success');
            setTimeout(() => window.location.reload(), 1200);
        } catch (error) {
            console.error('Error al eliminar preparacion:', error);
            ocultarOverlayGuardando();
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Error al eliminar',
                    text: error.message || 'No fue posible eliminar la preparacion. Intente de nuevo.',
                    icon: 'error',
                    confirmButtonText: 'Aceptar'
                });
            } else {
                alert(error.message || 'Error al eliminar preparacion');
            }
            return;
        } finally {
            ocultarOverlayGuardando();
        }
    }

    async function copiarPreparacionDesdeOtroMenu() {
        if (typeof Swal === 'undefined') {
            showNotification('Se requiere SweetAlert2', 'info');
            return;
        }

        const cargarJson = async (url) => {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await response.json();
            if (!response.ok || data.success === false) {
                throw new Error(data.error || 'No fue posible cargar datos');
            }
            return data;
        };

        const setPreviewPlaceholder = (contenedor, mensaje) => {
            if (!contenedor) return;
            contenedor.innerHTML = `<small class="text-muted">${escaparHtml(mensaje)}</small>`;
        };

        try {
            const origenesData = await cargarJson(`/nutricion/api/menus/${menuId}/origenes-copia-preparaciones/`);
            const menusOrigen = origenesData.menus || [];
            if (menusOrigen.length === 0) {
                showNotification('No hay menus disponibles para copiar en esta modalidad.', 'info');
                return;
            }

            const opcionesMenus = menusOrigen.map(m => (
                `<option value="${m.id_menu}">
                    Menu ${escaparHtml(m.menu)} - ${escaparHtml(m.programa)}${m.es_actual ? ' (actual)' : ''}
                </option>`
            )).join('');

            await Swal.fire({
                title: '<div class="swal-title-inner"><i class="bi bi-files swal-title-icon"></i><span class="swal-title-text">Copiar preparacion</span></div>',
                width: 760,
                showCancelButton: true,
                confirmButtonText: '<i class="bi bi-check-circle-fill"></i> Copiar',
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
                                <i class="bi bi-collection modal-label-icon-purple"></i>
                                Menu origen
                                <span class="required-star">*</span>
                            </label>
                            <div class="input-search-wrapper">
                                <i class="bi bi-search input-search-icon"></i>
                                <input id="copiarFiltroMenu" class="modal-input modal-input-search"
                                       placeholder="Buscar menu por nombre o contrato..."
                                       autocomplete="off" />
                            </div>
                            <select id="copiarMenuOrigen" class="modal-select">
                                ${opcionesMenus}
                            </select>
                        </div>
                        <div class="modal-field-group">
                            <label class="modal-label">
                                <i class="bi bi-journal-text modal-label-icon-yellow"></i>
                                Preparacion a copiar
                                <span class="required-star">*</span>
                            </label>
                            <div class="input-search-wrapper">
                                <i class="bi bi-search input-search-icon"></i>
                                <input id="copiarFiltroPreparacion" class="modal-input modal-input-search"
                                       placeholder="Buscar preparacion por nombre..."
                                       autocomplete="off" />
                            </div>
                            <select id="copiarPreparacionOrigen" class="modal-select">
                                <option value="">Cargando preparaciones...</option>
                            </select>
                            <small id="copiarPrepHint" class="modal-help-text">
                                <i class="bi bi-info-circle"></i>
                                Seleccione una preparacion con ingredientes.
                            </small>
                        </div>
                        <div class="modal-field-group">
                            <label class="modal-label">
                                <i class="bi bi-eye-fill modal-label-icon-green"></i>
                                Vista previa de ingredientes
                            </label>
                            <div id="copiarPreviewIngredientes" class="border rounded p-2" style="max-height: 220px; overflow:auto; text-align:left;"></div>
                        </div>
                        <div class="modal-info-box">
                            <div class="modal-info-box-content">
                                <i class="bi bi-lightbulb-fill modal-info-icon"></i>
                                <div class="modal-info-text">
                                    <div class="modal-info-title">Regla de copia</div>
                                    <div class="modal-info-desc">
                                        Se copia la estructura base (ingredientes, grupo/componente y gramaje base). Los pesos por nivel se ajustan manualmente en este menu.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `,
                                didOpen: async () => {
                    const selectMenu = document.getElementById('copiarMenuOrigen');
                    const selectPrep = document.getElementById('copiarPreparacionOrigen');
                    const filtroMenu = document.getElementById('copiarFiltroMenu');
                    const filtroPrep = document.getElementById('copiarFiltroPreparacion');
                    const hint = document.getElementById('copiarPrepHint');
                    const preview = document.getElementById('copiarPreviewIngredientes');
                    let preparacionesMenuActual = [];

                    const normalizar = (v) => String(v || '').toLowerCase().trim();
                    const etiquetaMenu = (m) => `Menu ${m.menu} - ${m.programa}${m.es_actual ? ' (actual)' : ''}`;

                    const renderMenus = () => {
                        const termino = normalizar(filtroMenu?.value);
                        const valorPrevio = selectMenu.value;
                        const filtrados = termino
                            ? menusOrigen.filter(m => normalizar(etiquetaMenu(m)).includes(termino))
                            : menusOrigen;

                        if (filtrados.length === 0) {
                            selectMenu.innerHTML = '<option value="">Sin resultados</option>';
                            return '';
                        }

                        selectMenu.innerHTML = '';
                        filtrados.forEach(m => {
                            const opt = document.createElement('option');
                            opt.value = String(m.id_menu);
                            opt.textContent = etiquetaMenu(m);
                            selectMenu.appendChild(opt);
                        });

                        const conservar = filtrados.some(m => String(m.id_menu) === String(valorPrevio));
                        selectMenu.value = conservar ? valorPrevio : String(filtrados[0].id_menu);
                        return selectMenu.value;
                    };

                    const renderPreparaciones = () => {
                        const termino = normalizar(filtroPrep?.value);
                        const filtradas = termino
                            ? preparacionesMenuActual.filter(p => normalizar(p.preparacion).includes(termino))
                            : preparacionesMenuActual;

                        if (filtradas.length === 0) {
                            const msg = preparacionesMenuActual.length === 0
                                ? 'No hay preparaciones en este menu'
                                : 'No hay preparaciones que coincidan con el filtro';
                            selectPrep.innerHTML = `<option value="">${msg}</option>`;
                            return;
                        }

                        selectPrep.innerHTML = '<option value="">Seleccione una preparacion...</option>';
                        filtradas.forEach(p => {
                            const opt = document.createElement('option');
                            opt.value = String(p.id_preparacion);
                            opt.dataset.totalIngredientes = String(p.total_ingredientes || 0);
                            opt.textContent = `${p.preparacion} (${p.total_ingredientes || 0} ingrediente(s))`;
                            selectPrep.appendChild(opt);
                        });
                    };

                    const cargarPreparacionesMenu = async (idMenuOrigen) => {
                        selectPrep.innerHTML = '<option value="">Cargando...</option>';
                        setPreviewPlaceholder(preview, 'Seleccione una preparacion para ver sus ingredientes.');
                        const data = await cargarJson(`/nutricion/api/menus/${idMenuOrigen}/preparaciones-para-copia/`);
                        preparacionesMenuActual = data.preparaciones || [];
                        if (preparacionesMenuActual.length === 0) {
                            selectPrep.innerHTML = '<option value="">No hay preparaciones en este menu</option>';
                            if (hint) hint.innerHTML = '<i class="bi bi-exclamation-circle"></i> Este menu no tiene preparaciones.';
                            return;
                        }
                        renderPreparaciones();
                        if (hint) hint.innerHTML = '<i class="bi bi-info-circle"></i> Seleccione una preparacion con ingredientes.';
                    };

                    const cargarPreviewPreparacion = async (idPreparacion) => {
                        setPreviewPlaceholder(preview, 'Cargando ingredientes...');
                        const data = await cargarJson(`/nutricion/api/preparaciones/${idPreparacion}/ingredientes/`);
                        const ingredientes = data.ingredientes || [];
                        if (ingredientes.length === 0) {
                            setPreviewPlaceholder(preview, 'Esta preparacion no tiene ingredientes.');
                            return;
                        }
                        preview.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <small class="text-muted">Marca los ingredientes que deseas copiar.</small>
                                <div class="d-flex gap-2">
                                    <button type="button" id="btnSelTodosIngredientesCopia" class="btn btn-outline-secondary btn-sm">Seleccionar todos</button>
                                    <button type="button" id="btnQuitarTodosIngredientesCopia" class="btn btn-outline-secondary btn-sm">Quitar todos</button>
                                </div>
                            </div>
                            <div id="listaIngredientesPreview">
                                ${ingredientes.map(ing => (
                                    `<label class="d-flex align-items-center gap-2" style="padding:4px 0; border-bottom:1px solid #f3f4f6; cursor:pointer;">
                                        <input type="checkbox"
                                               class="chk-ingrediente-copia"
                                               value="${escaparHtml(String(ing.codigo || ''))}"
                                               checked />
                                        <span><strong>${escaparHtml(String(ing.codigo || ''))}</strong> - ${escaparHtml(ing.nombre_del_alimento || '')}</span>
                                    </label>`
                                )).join('')}
                            </div>
                        `;

                        const btnSelTodos = document.getElementById('btnSelTodosIngredientesCopia');
                        const btnQuitarTodos = document.getElementById('btnQuitarTodosIngredientesCopia');
                        if (btnSelTodos) {
                            btnSelTodos.addEventListener('click', () => {
                                preview.querySelectorAll('.chk-ingrediente-copia').forEach(chk => {
                                    chk.checked = true;
                                });
                            });
                        }
                        if (btnQuitarTodos) {
                            btnQuitarTodos.addEventListener('click', () => {
                                preview.querySelectorAll('.chk-ingrediente-copia').forEach(chk => {
                                    chk.checked = false;
                                });
                            });
                        }
                    };

                    selectMenu.addEventListener('change', async () => {
                        try {
                            await cargarPreparacionesMenu(selectMenu.value);
                        } catch (error) {
                            showNotification(error.message || 'Error cargando preparaciones', 'error');
                            selectPrep.innerHTML = '<option value="">Error al cargar</option>';
                        }
                    });

                    selectPrep.addEventListener('change', async () => {
                        const idPrep = selectPrep.value;
                        if (!idPrep) {
                            setPreviewPlaceholder(preview, 'Seleccione una preparacion para ver sus ingredientes.');
                            return;
                        }
                        try {
                            await cargarPreviewPreparacion(idPrep);
                        } catch (error) {
                            showNotification(error.message || 'Error cargando vista previa', 'error');
                            setPreviewPlaceholder(preview, 'No fue posible cargar la vista previa.');
                        }
                    });

                    if (filtroMenu) {
                        filtroMenu.addEventListener('input', () => {
                            const idMenu = renderMenus();
                            if (!idMenu) {
                                selectPrep.innerHTML = '<option value="">Seleccione un menu origen</option>';
                                setPreviewPlaceholder(preview, 'Seleccione una preparacion para ver sus ingredientes.');
                                return;
                            }
                            cargarPreparacionesMenu(idMenu).catch((error) => {
                                showNotification(error.message || 'Error cargando preparaciones', 'error');
                                selectPrep.innerHTML = '<option value="">Error al cargar</option>';
                            });
                        });
                    }

                    if (filtroPrep) {
                        filtroPrep.addEventListener('input', () => {
                            renderPreparaciones();
                            setPreviewPlaceholder(preview, 'Seleccione una preparacion para ver sus ingredientes.');
                        });
                    }

                    const menuInicial = renderMenus();
                    if (menuInicial) {
                        await cargarPreparacionesMenu(menuInicial);
                    }
                },
                preConfirm: () => {
                    const selectPrep = document.getElementById('copiarPreparacionOrigen');
                    const idPreparacion = selectPrep?.value || '';
                    if (!idPreparacion) {
                        return Swal.showValidationMessage('Debes seleccionar una preparacion.');
                    }
                    const totalIngredientes = parseInt(
                        selectPrep.options[selectPrep.selectedIndex]?.dataset.totalIngredientes || '0',
                        10
                    );
                    if (!totalIngredientes) {
                        return Swal.showValidationMessage('La preparacion seleccionada no tiene ingredientes para copiar.');
                    }
                    const ingredientIds = Array.from(
                        document.querySelectorAll('#copiarPreviewIngredientes .chk-ingrediente-copia:checked')
                    ).map(chk => chk.value);

                    if (ingredientIds.length === 0) {
                        return Swal.showValidationMessage('Debes seleccionar al menos un ingrediente para copiar.');
                    }

                    return {
                        source_preparacion_id: parseInt(idPreparacion, 10),
                        ingredient_ids: ingredientIds
                    };
                }
            }).then(async (result) => {
                if (!result.isConfirmed || !result.value) return;

                const overlay = mostrarOverlayGuardando('Copiando preparacion...');
                try {
                    const response = await fetch('/nutricion/api/preparaciones/copiar/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            source_preparacion_id: result.value.source_preparacion_id,
                            target_menu_id: parseInt(menuId, 10),
                            ingredient_ids: result.value.ingredient_ids || []
                        })
                    });

                    const data = await response.json();
                    if (!response.ok || !data.success) {
                        throw new Error(data.error || 'No fue posible copiar la preparacion');
                    }

                    ocultarOverlayGuardando();
                    showNotification(data.message || 'Preparacion copiada exitosamente.', 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } catch (error) {
                    console.error('Error al copiar preparacion:', error);
                    ocultarOverlayGuardando();
                    showNotification(error.message || 'Error al copiar preparacion', 'error');
                }
            });
        } catch (error) {
            console.error('Error al iniciar copia de preparacion:', error);
            showNotification(error.message || 'No fue posible cargar los menus origen.', 'error');
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
            title: '<div class="swal-title-inner"><i class="bi bi-plus-circle-fill swal-title-icon"></i><span class="swal-title-text">Agregar PreparaciÃ³n</span></div>',
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
                            PreparaciÃ³n
                            <span class="required-star">*</span>
                        </label>
                        <select id="agregarModoPrep" class="modal-select">
                            <option value="existente">Usar preparacion existente</option>
                            <option value="nueva">Crear nueva preparacion</option>
                        </select>
                    </div>

                    <div id="bloquePrepExistente" class="modal-field-group">
                        <select id="agregarPreparacionExistente" class="modal-select">
                            <option value="">Seleccione una preparacion...</option>
                            ${opcionesPreparaciones}
                        </select>
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Seleccione la preparacion a la que agregarÃ¡ el ingrediente
                        </small>
                    </div>

                    <div id="bloquePrepNueva" class="modal-field-group" style="display:none;">
                        <input id="agregarPreparacionNueva" class="modal-input" placeholder="Nombre de la nueva preparacion" />
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Ingrese el nombre de la nueva preparacion
                        </small>
                    </div>

                    <div id="bloqueComponente" class="modal-field-group">
                        <label class="modal-label">
                            <i class="bi bi-grid-3x3-gap-fill modal-label-icon-yellow"></i>
                            Grupo de Alimento
                            <span class="required-star">*</span>
                        </label>
                        <select id="agregarGrupoId" class="modal-select">
                            <option value="">â€” seleccione grupo â€”</option>
                            ${opcionesGrupos}
                        </select>
                        <label class="modal-label modal-label-top-spacing">
                            <i class="bi bi-tag-fill modal-label-icon-yellow"></i>
                            Componente
                            <span class="required-star">*</span>
                        </label>
                        <select id="agregarComponenteId" class="modal-select">
                            <option value="">â€” seleccione componente â€”</option>
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
                                   placeholder="Filtrar por nombre o cÃ³digo..."
                                   autocomplete="off" />
                        </div>
                        <select id="agregarIngredienteId" class="modal-select modal-select-multirow" size="5">
                            <option value="">â€” seleccione â€”</option>
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
                                    El ingrediente se agregarÃ¡ a <strong>todos los niveles escolares</strong>.
                                    PodrÃ¡s ajustar los pesos individuales despuÃ©s.
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
                    selectComponente.innerHTML = '<option value="">â€” seleccione componente â€”</option>';
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
                    selectIng.innerHTML = '<option value="">â€” seleccione â€”</option>';
                    filtrados.forEach(ing => {
                        const opt = document.createElement('option');
                        opt.value = ing.codigo;
                        opt.textContent = `${ing.codigo} - ${ing.nombre_del_alimento}`;
                        selectIng.appendChild(opt);
                    });

                    // Restaurar selecciÃ³n si sigue siendo vÃ¡lida
                    if (valorActual && filtrados.some(ing => String(ing.codigo) === String(valorActual))) {
                        selectIng.value = valorActual;
                    }

                    // Actualizar contador
                    if (contador) {
                        contador.innerHTML = termino
                            ? `<i class="bi bi-funnel-fill"></i> ${filtrados.length} de ${ingredientesCatalogo.length} ingredientes`
                            : `<i class="bi bi-list-ul"></i> ${ingredientesCatalogo.length} ingredientes disponibles`;
                    }

                    // Si hay exactamente un resultado, seleccionarlo automÃ¡ticamente
                    if (filtrados.length === 1) {
                        selectIng.value = filtrados[0].codigo;
                    }
                });

                // Focus automÃ¡tico en el filtro al abrir el modal
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
                    return Swal.showValidationMessage('Debes seleccionar una preparacion existente');
                }

                if (modo === 'nueva' && !nomPrep) {
                    return Swal.showValidationMessage('Debes escribir el nombre de la nueva preparacion');
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
                    gramaje: null  // Siempre null, se usarÃ¡n valores predeterminados por nivel
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

                // Si hay errores especÃ­ficos, agregarlos
                if (data.errores && data.errores.length > 0) {
                    errorMsg += ':\n' + data.errores.join('\n');
                }

                throw new Error(errorMsg);
            }

            ocultarOverlayGuardando();
            showNotification('âœ… Ingrediente agregado exitosamente', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } catch (error) {
            console.error('Error al agregar ingrediente:', error);
            ocultarOverlayGuardando();
            showNotification(error.message || 'Error desconocido al agregar ingrediente', 'error');
        }
    }

    // ========================================
    // DROPDOWNS CASCADE GRUPO â†’ COMPONENTE
    // ========================================

    function poblarSelectGrupo(selectGrupo) {
        const grupoActual = selectGrupo.dataset.grupoActual || '';
        selectGrupo.innerHTML = '<option value="">â€” Grupo â€”</option>';
        gruposCatalogo.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.nombre;
            if (g.id === grupoActual) opt.selected = true;
            selectGrupo.appendChild(opt);
        });
    }

    function poblarSelectComponente(selectComp, grupoId, componenteActual) {
        selectComp.innerHTML = '<option value="">â€” Componente â€”</option>';
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
    // INICIALIZACIÃ“N
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

        console.log('âœ… Editor inicializado. Niveles:', nivelesData.length);
    }

    document.addEventListener('click', (e) => {
        const btnEditarPrep = e.target.closest('.btn-editar-preparacion-inline');
        if (btnEditarPrep) {
            abrirEdicionInlinePreparacion(btnEditarPrep);
            return;
        }

        const btnGuardarPrep = e.target.closest('.btn-guardar-preparacion-inline');
        if (btnGuardarPrep) {
            guardarNombrePreparacionInline(btnGuardarPrep);
            return;
        }

        const btnCancelarPrep = e.target.closest('.btn-cancelar-preparacion-inline');
        if (btnCancelarPrep) {
            cancelarEdicionInlinePreparacion(btnCancelarPrep.closest('.prep-header-row'));
            return;
        }

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
            const nombrePrep = btnEliminarPrep.dataset.nombrePreparacion || 'esta preparacion';
            if (!idPreparacion) return;
            eliminarPreparacion(idPreparacion, nombrePrep);
        }
    });

    document.addEventListener('keydown', (e) => {
        if (!e.target.classList.contains('input-preparacion-inline')) return;

        if (e.key === 'Enter') {
            e.preventDefault();
            const btnGuardar = e.target.closest('.prep-inline-editor')?.querySelector('.btn-guardar-preparacion-inline');
            if (btnGuardar) guardarNombrePreparacionInline(btnGuardar);
            return;
        }

        if (e.key === 'Escape') {
            e.preventDefault();
            cancelarEdicionInlinePreparacion(e.target.closest('.prep-header-row'));
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

})();



