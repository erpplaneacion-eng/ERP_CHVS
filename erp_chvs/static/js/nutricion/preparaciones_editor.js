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
    let copiaPreparacionEnCurso = false;

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
        // ✨ AJUSTE: Ahora devolvemos todos los componentes sin filtrar por grupo
        // para que sean independientes en la UI.
        return componentesCatalogo
            .map(c => ({
                id: c?.id_componente ?? '',
                nombre: c?.componente ?? ''
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

                if (ingredientes.length > 0 && nivelData.id_analisis) {
                    cambiosPorNivel.push({
                        id_nivel_escolar: nivelData.nivel.id,
                        id_analisis: nivelData.id_analisis,
                        ingredientes: ingredientes
                    });
                }
            });

            // Recopilar selecciones de grupo/componente
            const filasGrupoCompMap = new Map();
            
            // 1. Recopilar ingredientes y sus componentes/grupos individuales
            document.querySelectorAll('.tbody-ingredientes tr[data-id-ingrediente]').forEach(row => {
                const idPrep = row.dataset.idPreparacion;
                const idIng = row.dataset.idIngrediente;
                const key = `${idPrep}_${idIng}`;
                if (!filasGrupoCompMap.has(key)) {
                    const selectGrupo = row.querySelector('.select-grupo');
                    const selectComp = row.querySelector('.select-componente');
                    
                    // Buscar si la preparación tiene un select principal
                    const prepHeaderRow = document.querySelector(`.prep-header-row[data-id-preparacion="${idPrep}"]`);
                    const selectCompPrincipal = prepHeaderRow ? prepHeaderRow.querySelector('.select-componente-principal') : null;
                    const compPrincipalId = selectCompPrincipal ? selectCompPrincipal.value : null;

                    filasGrupoCompMap.set(key, {
                        id_preparacion: parseInt(idPrep),
                        id_ingrediente: idIng,
                        id_grupo: selectGrupo ? selectGrupo.value || null : null,
                        id_componente_ingrediente: selectComp ? selectComp.value || null : null,
                        id_componente: compPrincipalId, // El endpoint backend espera que 'id_componente' sea el de la preparacion principal
                        gramaje: null
                    });
                }
            });
            
            // 2. Manejar el caso especial donde una preparación puede estar vacía pero su componente principal fue cambiado
            document.querySelectorAll('.prep-header-row').forEach(row => {
                const idPrep = row.dataset.idPreparacion;
                const selectCompPrincipal = row.querySelector('.select-componente-principal');
                if (idPrep && selectCompPrincipal) {
                    // Si no hay ingredientes para esta preparación, enviamos una fila "dummy" solo para actualizar el componente de la preparación
                    let tieneIngredientes = false;
                    for (const key of filasGrupoCompMap.keys()) {
                        if (key.startsWith(`${idPrep}_`)) {
                            tieneIngredientes = true;
                            // Asegurarnos que todas las filas de esta preparación lleven el componente principal actualizado
                            const fila = filasGrupoCompMap.get(key);
                            fila.id_componente = selectCompPrincipal.value || null;
                        }
                    }
                    
                    if (!tieneIngredientes) {
                         filasGrupoCompMap.set(`${idPrep}_dummy`, {
                            id_preparacion: parseInt(idPrep),
                            id_componente: selectCompPrincipal.value || null,
                            gramaje: null,
                            id_ingrediente: null // Para que el backend sepa que es solo una actualización de preparación
                        });
                    }
                }
            });

            const filasGrupoComp = Array.from(filasGrupoCompMap.values());

            const overlay = mostrarOverlayGuardando('Guardando cambios...');

            try {
                btnGuardarCambios.disabled = true;
                btnGuardarCambios.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando...';

                // Si cambiaron un componente principal, permitimos guardar aunque no haya ingredientes
                if (cambiosPorNivel.length === 0 && filasGrupoComp.length === 0) {
                    ocultarOverlayGuardando();
                    showNotification('No hay ingredientes configurados para guardar en este menu.', 'info');
                    return;
                }

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
            showNotification('El nombre de la preparacion no puede estar vacío.', 'warning');
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
        const mensajeConfirmacion = '¿Eliminar este ingrediente de la preparacion en todos los niveles?';
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
                title: 'Eliminar preparacion',
                text: `¿Eliminar "${nombrePrep}" con todos sus ingredientes? Esta acción no se puede deshacer.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#dc3545'
            })).isConfirmed
            : confirm(`¿Eliminar la preparacion "${nombrePrep}"?`);

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

            showNotification(`Preparación "${nombrePrep}" eliminada correctamente.`, 'success');
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
        if (copiaPreparacionEnCurso) {
            showNotification('Ya hay una copia en proceso. Espera un momento.', 'info');
            return;
        }
        if (typeof Swal === 'undefined') {
            showNotification('Se requiere SweetAlert2', 'info');
            return;
        }

        let debounceTimer = null;

        await Swal.fire({
            title: '<div class="swal-title-inner"><i class="bi bi-files swal-title-icon"></i><span class="swal-title-text">Copiar preparación</span></div>',
            width: 760,
            showCancelButton: true,
            confirmButtonText: '<i class="bi bi-check-circle-fill"></i> Copiar seleccionadas',
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
                            <i class="bi bi-search modal-label-icon-purple"></i>
                            Buscar preparación
                            <span class="required-star">*</span>
                        </label>
                        <div class="input-search-wrapper">
                            <i class="bi bi-search input-search-icon"></i>
                            <input id="copiarBuscadorPrep" class="modal-input modal-input-search"
                                   placeholder="Escribe el nombre de la preparación..."
                                   autocomplete="off" />
                        </div>
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Busca en todos los menús de la misma modalidad. Escribe al menos 2 caracteres.
                        </small>
                    </div>
                    <div id="copiarResultados" class="copiar-resultados-container modal-field-group">
                        <small class="text-muted">Escribe para buscar preparaciones...</small>
                    </div>
                    <div class="modal-info-box">
                        <div class="modal-info-box-content">
                            <i class="bi bi-lightbulb-fill modal-info-icon"></i>
                            <div class="modal-info-text">
                                <div class="modal-info-title">Regla de copia</div>
                                <div class="modal-info-desc">
                                    Se copia la estructura base (ingredientes, grupo/componente y gramaje).
                                    Los <strong>pesos por nivel</strong> se ajustan manualmente en este menú.
                                    Puedes seleccionar <strong>varias preparaciones</strong> a la vez.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            didOpen: () => {
                const buscador  = document.getElementById('copiarBuscadorPrep');
                const contenedor = document.getElementById('copiarResultados');

                const renderResultados = (preparaciones) => {
                    if (preparaciones.length === 0) {
                        contenedor.innerHTML = '<small class="text-muted">No se encontraron preparaciones con ese nombre.</small>';
                        return;
                    }

                    const frag = document.createDocumentFragment();
                    preparaciones.forEach(prep => {
                        const card = document.createElement('div');
                        card.className = 'copiar-prep-card';
                        card.innerHTML = `
                            <label class="copiar-prep-titulo">
                                <input type="checkbox" class="chk-prep-completa"
                                       data-id="${prep.id_preparacion}" checked />
                                <strong>${escaparHtml(prep.preparacion)}</strong>
                                <small class="text-muted"> — Menú ${escaparHtml(prep.menu)} | ${escaparHtml(prep.programa)}</small>
                            </label>
                            <div class="copiar-ing-lista">
                                ${prep.ingredientes.map(ing => `
                                    <label class="copiar-ing-item">
                                        <input type="checkbox" class="chk-ingrediente-copia"
                                               data-prep="${prep.id_preparacion}"
                                               value="${escaparHtml(String(ing.codigo))}" checked />
                                        <span>${escaparHtml(String(ing.codigo))} — ${escaparHtml(ing.nombre)}</span>
                                    </label>
                                `).join('')}
                            </div>
                        `;
                        frag.appendChild(card);
                    });

                    contenedor.innerHTML = '';
                    contenedor.appendChild(frag);

                    // Checkbox preparación completa → marca/desmarca sus ingredientes
                    contenedor.querySelectorAll('.chk-prep-completa').forEach(chk => {
                        chk.addEventListener('change', () => {
                            contenedor.querySelectorAll(`.chk-ingrediente-copia[data-prep="${chk.dataset.id}"]`)
                                .forEach(c => { c.checked = chk.checked; });
                        });
                    });

                    // Si se desmarca un ingrediente individual, desmarcar el checkbox de la preparación
                    contenedor.querySelectorAll('.chk-ingrediente-copia').forEach(chk => {
                        chk.addEventListener('change', () => {
                            const todos = contenedor.querySelectorAll(`.chk-ingrediente-copia[data-prep="${chk.dataset.prep}"]`);
                            const alguno = Array.from(todos).some(c => c.checked);
                            const prepChk = contenedor.querySelector(`.chk-prep-completa[data-id="${chk.dataset.prep}"]`);
                            if (prepChk) prepChk.checked = alguno;
                        });
                    });
                };

                const buscar = async (termino) => {
                    if (termino.length < 2) {
                        contenedor.innerHTML = '<small class="text-muted">Escribe al menos 2 caracteres para buscar.</small>';
                        return;
                    }
                    contenedor.innerHTML = '<small class="text-muted"><i class="bi bi-hourglass-split"></i> Buscando...</small>';
                    try {
                        const resp = await fetch(
                            `/nutricion/api/menus/${menuId}/buscar-preparaciones-modalidad/?q=${encodeURIComponent(termino)}`,
                            { headers: { 'X-Requested-With': 'XMLHttpRequest' } }
                        );
                        const data = await resp.json();
                        renderResultados(data.preparaciones || []);
                    } catch {
                        contenedor.innerHTML = '<small class="text-danger">Error al buscar. Intenta de nuevo.</small>';
                    }
                };

                buscador.addEventListener('input', () => {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => buscar(buscador.value.trim()), 300);
                });

                setTimeout(() => buscador.focus(), 100);
            },
            preConfirm: () => {
                const contenedor = document.getElementById('copiarResultados');
                const copias = [];

                // Agrupar ingredientes marcados por preparación
                const prepIds = new Set(
                    Array.from(contenedor.querySelectorAll('.chk-ingrediente-copia'))
                        .map(c => c.dataset.prep)
                );
                prepIds.forEach(idPrep => {
                    const ids = Array.from(
                        contenedor.querySelectorAll(`.chk-ingrediente-copia[data-prep="${idPrep}"]:checked`)
                    ).map(c => c.value);
                    if (ids.length > 0) {
                        copias.push({ source_preparacion_id: parseInt(idPrep), ingredient_ids: ids });
                    }
                });

                if (copias.length === 0) {
                    return Swal.showValidationMessage('Debes seleccionar al menos un ingrediente para copiar.');
                }
                return copias;
            }
        }).then(async (result) => {
            if (!result.isConfirmed || !result.value) return;
            if (copiaPreparacionEnCurso) return;

            copiaPreparacionEnCurso = true;
            if (btnCopiarPreparacion) btnCopiarPreparacion.disabled = true;
            const overlay = mostrarOverlayGuardando('Copiando preparaciones...');
            try {
                const response = await fetch('/nutricion/api/preparaciones/copiar/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({
                        target_menu_id: parseInt(menuId, 10),
                        copias: result.value
                    })
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'No fue posible copiar las preparaciones');
                }
                ocultarOverlayGuardando();
                showNotification(data.message || 'Preparaciones copiadas exitosamente.', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } catch (error) {
                console.error('Error al copiar preparaciones:', error);
                ocultarOverlayGuardando();
                showNotification(error.message || 'Error al copiar preparaciones', 'error');
            } finally {
                copiaPreparacionEnCurso = false;
                if (btnCopiarPreparacion) btnCopiarPreparacion.disabled = false;
            }
        });
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

        // Estado local: ingredientes añadidos a la lista
        let ingSeleccionados = [];

        const result = await Swal.fire({
            title: '<div class="swal-title-inner"><i class="bi bi-plus-circle-fill swal-title-icon"></i><span class="swal-title-text">Agregar Preparación</span></div>',
            width: 750,
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

                    <!-- ── Modo ── -->
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

                    <!-- ── Prep existente ── -->
                    <div id="bloquePrepExistente" class="modal-field-group">
                        <select id="agregarPreparacionExistente" class="modal-select">
                            <option value="">Seleccione una preparación...</option>
                            ${opcionesPreparaciones}
                        </select>
                        <small class="modal-help-text">
                            <i class="bi bi-info-circle"></i>
                            Seleccione la preparación a la que desea agregar ingredientes
                        </small>
                    </div>

                    <!-- ── Prep nueva ── -->
                    <div id="bloquePrepNueva" class="modal-field-group" style="display:none;">
                        <input id="agregarPreparacionNueva" class="modal-input"
                               placeholder="Nombre de la nueva preparación" />
                        <!-- Componente Principal (solo para prep nueva) -->
                        <div class="modal-comp-principal-box" style="margin-top:10px;">
                            <div class="modal-comp-principal-label">
                                <i class="bi bi-tag-fill"></i> Componente Principal de la Preparación
                            </div>
                            <select id="agregarGrupoCompPrincipal" class="modal-select" style="margin-bottom:6px;">
                                <option value="">— seleccione grupo —</option>
                                ${opcionesGrupos}
                            </select>
                            <select id="agregarComponentePrincipal" class="modal-select">
                                <option value="">— seleccione componente —</option>
                            </select>
                            <small class="modal-help-text" style="margin-top:4px;">
                                <i class="bi bi-info-circle"></i>
                                Define el componente nutricional que representa esta preparación en el menú
                            </small>
                        </div>
                    </div>

                    <!-- ── Ingredientes ── -->
                    <div class="modal-field-group">
                        <label class="modal-label">
                            <i class="bi bi-basket3 modal-label-icon-green"></i>
                            Ingredientes ICBF
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
                        <button type="button" id="btnAnadirALista" class="btn-agregar-a-lista">
                            <i class="bi bi-plus-circle"></i> Añadir a la lista
                        </button>
                        <!-- Lista de ingredientes seleccionados -->
                        <div id="listaIngredientesSeleccionados" class="modal-ing-lista vacia"></div>
                    </div>

                    <div class="modal-info-box">
                        <div class="modal-info-box-content">
                            <i class="bi bi-lightbulb-fill modal-info-icon"></i>
                            <div class="modal-info-text">
                                <div class="modal-info-title">Nota importante</div>
                                <div class="modal-info-desc">
                                    Los ingredientes se agregarán a <strong>todos los niveles escolares</strong>.
                                    Puedes ajustar el grupo y componente de cada ingrediente desde la tabla,
                                    columna <strong>Grupo / Componente</strong>.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `,
            didOpen: () => {
                const modo           = document.getElementById('agregarModoPrep');
                const bExistente     = document.getElementById('bloquePrepExistente');
                const bNueva         = document.getElementById('bloquePrepNueva');
                const selectGrupoPrinc = document.getElementById('agregarGrupoCompPrincipal');
                const selectCompPrinc  = document.getElementById('agregarComponentePrincipal');

                // Cascade grupo → componente para prep nueva
                selectGrupoPrinc.addEventListener('change', () => {
                    selectCompPrinc.innerHTML = '<option value="">— seleccione componente —</option>';
                    const comps = obtenerComponentesPorGrupo(selectGrupoPrinc.value);
                    comps.forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.textContent = c.nombre;
                        selectCompPrinc.appendChild(opt);
                    });
                });

                // Alternar bloques según modo
                const actualizarVistaModo = () => {
                    const esNueva = modo.value === 'nueva';
                    bExistente.style.display = esNueva ? 'none' : 'block';
                    bNueva.style.display     = esNueva ? 'block' : 'none';
                };
                modo.addEventListener('change', actualizarVistaModo);
                actualizarVistaModo();

                // Filtro de ingredientes en tiempo real
                const filtroIng = document.getElementById('filtroIngrediente');
                const selectIng = document.getElementById('agregarIngredienteId');
                const contador  = document.getElementById('contadorIngredientes');

                filtroIng.addEventListener('input', () => {
                    const termino = filtroIng.value.toLowerCase().trim();
                    const filtrados = termino
                        ? ingredientesCatalogo.filter(ing =>
                            ing.nombre_del_alimento.toLowerCase().includes(termino) ||
                            String(ing.codigo).toLowerCase().includes(termino)
                          )
                        : ingredientesCatalogo;

                    const valorActual = selectIng.value;
                    selectIng.innerHTML = '<option value="">— seleccione —</option>';
                    filtrados.forEach(ing => {
                        const opt = document.createElement('option');
                        opt.value = ing.codigo;
                        opt.textContent = `${ing.codigo} - ${ing.nombre_del_alimento}`;
                        selectIng.appendChild(opt);
                    });
                    if (valorActual && filtrados.some(ing => String(ing.codigo) === String(valorActual))) {
                        selectIng.value = valorActual;
                    }
                    if (contador) {
                        contador.innerHTML = termino
                            ? `<i class="bi bi-funnel-fill"></i> ${filtrados.length} de ${ingredientesCatalogo.length} ingredientes`
                            : `<i class="bi bi-list-ul"></i> ${ingredientesCatalogo.length} ingredientes disponibles`;
                    }
                    if (filtrados.length === 1) selectIng.value = filtrados[0].codigo;
                });

                // Renderizar la lista de tags seleccionados
                const renderLista = () => {
                    const contenedor = document.getElementById('listaIngredientesSeleccionados');
                    if (!contenedor) return;
                    contenedor.innerHTML = '';
                    if (ingSeleccionados.length === 0) {
                        contenedor.classList.add('vacia');
                        return;
                    }
                    contenedor.classList.remove('vacia');
                    const frag = document.createDocumentFragment();
                    ingSeleccionados.forEach((ing, idx) => {
                        const tag = document.createElement('span');
                        tag.className = 'ing-tag';
                        tag.innerHTML = `<span title="${escaparHtml(ing.nombre)}">${escaparHtml(ing.codigo)} — ${escaparHtml(ing.nombre)}</span>
                            <button type="button" class="ing-tag-remove" data-idx="${idx}" title="Quitar">&times;</button>`;
                        frag.appendChild(tag);
                    });
                    contenedor.appendChild(frag);

                    // Listeners para quitar tags
                    contenedor.querySelectorAll('.ing-tag-remove').forEach(btn => {
                        btn.addEventListener('click', () => {
                            ingSeleccionados.splice(parseInt(btn.dataset.idx), 1);
                            renderLista();
                        });
                    });
                };

                // Botón "Añadir a la lista"
                document.getElementById('btnAnadirALista').addEventListener('click', () => {
                    const codigo = selectIng.value;
                    if (!codigo) {
                        showNotification('Selecciona un ingrediente primero', 'info');
                        return;
                    }
                    if (ingSeleccionados.some(i => String(i.codigo) === String(codigo))) {
                        showNotification('Ese ingrediente ya está en la lista', 'info');
                        return;
                    }
                    const ing = ingredientesCatalogo.find(i => String(i.codigo) === String(codigo));
                    if (ing) {
                        ingSeleccionados.push({ codigo: ing.codigo, nombre: ing.nombre_del_alimento });
                        renderLista();
                        // Limpiar selección y filtro para facilitar agregar el siguiente
                        selectIng.value = '';
                        filtroIng.value = '';
                        filtroIng.dispatchEvent(new Event('input'));
                        filtroIng.focus();
                    }
                });

                // También agregar con Enter en el filtro
                filtroIng.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        document.getElementById('btnAnadirALista').click();
                    }
                });

                setTimeout(() => filtroIng.focus(), 100);
            },
            preConfirm: () => {
                const modo    = document.getElementById('agregarModoPrep').value;
                const idPrep  = document.getElementById('agregarPreparacionExistente').value;
                const nomPrep = document.getElementById('agregarPreparacionNueva').value.trim();
                const idComp  = document.getElementById('agregarComponentePrincipal').value;

                if (modo === 'existente' && !idPrep) {
                    return Swal.showValidationMessage('Debes seleccionar una preparación existente');
                }
                if (modo === 'nueva' && !nomPrep) {
                    return Swal.showValidationMessage('Debes escribir el nombre de la nueva preparación');
                }
                if (modo === 'nueva' && !idComp) {
                    return Swal.showValidationMessage('Debes seleccionar el Componente Principal de la preparación');
                }
                if (ingSeleccionados.length === 0) {
                    return Swal.showValidationMessage('Debes añadir al menos un ingrediente a la lista');
                }

                return { modo, id_preparacion: idPrep ? parseInt(idPrep) : null, preparacion_nombre: nomPrep, id_componente: idComp || null };
            }
        });

        if (!result.isConfirmed) return;

        // Construir array de filas: una por cada ingrediente seleccionado
        const { modo, id_preparacion, preparacion_nombre, id_componente } = result.value;
        const filas = ingSeleccionados.map(ing => ({
            id_preparacion:    modo === 'existente' ? id_preparacion : null,
            preparacion_nombre: modo === 'nueva' ? preparacion_nombre : '',
            id_componente:     modo === 'nueva' ? id_componente : null,
            id_ingrediente:    ing.codigo,
            gramaje:           null
        }));

        const overlay = mostrarOverlayGuardando('Guardando ingredientes...');
        try {
            const response = await fetch(`/nutricion/api/menus/${menuId}/guardar-preparaciones-editor/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ filas })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                let errorMsg = data.error || 'Error al guardar';
                if (data.errores && data.errores.length > 0) {
                    errorMsg += ':\n' + data.errores.join('\n');
                }
                throw new Error(errorMsg);
            }

            ocultarOverlayGuardando();
            const plural = filas.length > 1 ? `${filas.length} ingredientes agregados` : '1 ingrediente agregado';
            showNotification(`✅ ${plural} exitosamente`, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } catch (error) {
            console.error('Error al guardar ingredientes:', error);
            ocultarOverlayGuardando();
            showNotification(error.message || 'Error desconocido al guardar', 'error');
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

        // Inicializar select-componente-principal (si existe)
        const principalSelects = document.querySelectorAll('.select-componente-principal');
        const componentesFlat = componentesCatalogo.map(c => ({
            id: c?.id_componente ?? '',
            nombre: c?.componente ?? ''
        })).filter(c => c.id && c.nombre);

        principalSelects.forEach(selectComp => {
            const compActual = selectComp.dataset.componenteActual || '';
            // vaciar primero
            selectComp.innerHTML = '<option value="">— Sin Componente (No sale en PDF) —</option>';
            componentesFlat.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.nombre;
                if (String(c.id) === String(compActual)) opt.selected = true;
                selectComp.appendChild(opt);
            });
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
        if (e.target.classList.contains('select-componente-principal')) {
            const selectCompPrincipal = e.target;
            const compId = selectCompPrincipal.value;
            const idPreparacion = selectCompPrincipal.dataset.idPreparacion;
            
            // Sincronizar en otros niveles
            document.querySelectorAll('.select-componente-principal').forEach(sc => {
                if (String(sc.dataset.idPreparacion) === String(idPreparacion) && sc !== selectCompPrincipal) {
                    sc.value = compId;
                    sc.dataset.componenteActual = compId;
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




