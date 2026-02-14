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
        // Usar SweetAlert2 si está disponible, sino alert simple
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

    function mostrarOverlayGuardando(mensaje = 'Guardando cambios...') {
        const overlay = document.createElement('div');
        overlay.className = 'guardando-overlay';
        overlay.id = 'guardandoOverlay';
        overlay.innerHTML = `
            <div class="guardando-card">
                <div class="guardando-spinner"></div>
                <h4 style="margin: 0; color: #374151; font-size: 16px;">${mensaje}</h4>
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
        const slider = row.querySelector('.slider-peso');
        const badge = row.querySelector('.badge-estado');

        if (!input || !badge) return;

        const peso = parseFloat(input.value) || 0;
        const minimo = input.dataset.minimo;
        const maximo = input.dataset.maximo;

        const resultado = validarRango(peso, minimo, maximo);

        // Actualizar clases del input
        input.classList.remove('fuera-rango', 'en-rango');
        if (minimo || maximo) {
            if (resultado.valido) {
                input.classList.add('en-rango');
            } else {
                input.classList.add('fuera-rango');
            }
        }

        // Actualizar slider si existe
        if (slider) {
            slider.value = Math.round(peso);
            // Cambiar color del thumb según estado
            if (resultado.valido) {
                slider.style.setProperty('--thumb-color', '#10b981');
            } else {
                slider.style.setProperty('--thumb-color', '#ef4444');
            }
        }

        // Actualizar badge con tooltip
        badge.className = 'badge-estado ' + resultado.clase;
        badge.textContent = resultado.valido ? 'OK' : 'FUERA';

        // Actualizar tooltip del badge
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

        // Reinicializar tooltip de Bootstrap si está disponible
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipInstance = bootstrap.Tooltip.getInstance(badge);
            if (tooltipInstance) {
                tooltipInstance.dispose();
            }
            new bootstrap.Tooltip(badge);
        }
    }

    function sincronizarSliderConInput(row) {
        const input = row.querySelector('.input-peso');
        const slider = row.querySelector('.slider-peso');

        if (!input || !slider) return;

        const peso = parseFloat(input.value) || 0;
        slider.value = Math.round(peso);
    }

    function sincronizarInputConSlider(row) {
        const input = row.querySelector('.input-peso');
        const slider = row.querySelector('.slider-peso');

        if (!input || !slider) return;

        const pesoRedondeado = parseFloat(slider.value);
        input.value = pesoRedondeado.toFixed(1);
    }

    // ========================================
    // CÁLCULO DE TOTALES
    // ========================================

    function calcularTotalesNivel(nivelId) {
        const panel = document.querySelector(`[data-nivel-id="${nivelId}"]`);
        if (!panel) return null;

        const tbody = panel.querySelector('.tbody-ingredientes');
        if (!tbody) return null;

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

        // Sumar todos los ingredientes
        tbody.querySelectorAll('tr').forEach(row => {
            const pesoInput = row.querySelector('.input-peso');
            if (!pesoInput) return;

            const peso = parseFloat(pesoInput.value) || 0;
            const idIngrediente = pesoInput.dataset.idIngrediente;

            // Buscar datos nutricionales del ingrediente
            const nivelData = nivelesData.find(n => n.nivel.id === nivelId);
            if (!nivelData) return;

            const fila = nivelData.filas.find(f =>
                String(f.id_ingrediente) === String(idIngrediente) &&
                String(f.id_preparacion) === String(row.dataset.idPreparacion)
            );

            if (!fila) return;

            // Calcular proporción (peso actual / peso original)
            const pesoOriginal = parseFloat(fila.peso_neto) || 100;
            const factor = peso / pesoOriginal;

            // Sumar nutrientes proporcionalmente
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

        const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];

        nutrientes.forEach(nutriente => {
            const card = panel.querySelector(`[data-nutriente="${nutriente}"]`);
            if (!card) return;

            const valorActualSpan = card.querySelector('.valor-actual');
            const porcentajeActualSpan = card.querySelector('.porcentaje-actual');

            if (valorActualSpan) {
                valorActualSpan.textContent = totales[nutriente].toFixed(1);
            }

            // Calcular porcentaje
            const requerimiento = requerimientos[nutriente] || 1;
            const porcentaje = (totales[nutriente] / requerimiento) * 100;

            if (porcentajeActualSpan) {
                porcentajeActualSpan.textContent = porcentaje.toFixed(1);
            }

            // Actualizar estado del semáforo
            let estado = 'optimo';
            if (porcentaje > 70) {
                estado = 'alto';
            } else if (porcentaje > 35) {
                estado = 'aceptable';
            }

            // Actualizar clases de la card
            card.className = `nutriente-card ${estado}`;

            // Actualizar clases del porcentaje
            const porcentajeDiv = card.querySelector('.nutriente-porcentaje');
            if (porcentajeDiv) {
                porcentajeDiv.className = `nutriente-porcentaje ${estado}`;
            }
        });
    }

    function recalcularNivel(nivelId) {
        const nivelData = nivelesData.find(n => n.nivel.id === nivelId);
        if (!nivelData) return;

        const totales = calcularTotalesNivel(nivelId);
        if (!totales) return;

        actualizarPanelTotales(nivelId, totales, nivelData.requerimientos);
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================

    // Listener global para cambios en inputs de peso
    document.addEventListener('input', (e) => {
        if (e.target.classList.contains('input-peso')) {
            const row = e.target.closest('tr');
            if (row) {
                // Sincronizar con slider
                sincronizarSliderConInput(row);

                // Validar rango
                actualizarEstadoFila(row);

                // Recalcular totales del nivel actual
                const panel = e.target.closest('[data-nivel-id]');
                if (panel) {
                    const nivelId = panel.dataset.nivelId;
                    recalcularNivel(nivelId);
                }
            }
        }

        // Listener para sliders
        if (e.target.classList.contains('slider-peso')) {
            const row = e.target.closest('tr');
            if (row) {
                // Sincronizar con input
                sincronizarInputConSlider(row);

                // Validar rango
                actualizarEstadoFila(row);

                // Recalcular totales del nivel actual
                const panel = e.target.closest('[data-nivel-id]');
                if (panel) {
                    const nivelId = panel.dataset.nivelId;
                    recalcularNivel(nivelId);
                }
            }
        }
    });

    // Botón de recalcular manual
    const btnRecalcular = document.getElementById('btnRecalcular');
    if (btnRecalcular) {
        btnRecalcular.addEventListener('click', () => {
            // Recalcular todos los niveles
            nivelesData.forEach(nivelData => {
                recalcularNivel(nivelData.nivel.id);
            });
            showNotification('Totales recalculados', 'success');
        });
    }

    const btnAgregarFila = document.getElementById('btnAgregarFila');
    if (btnAgregarFila) {
        btnAgregarFila.addEventListener('click', agregarIngredienteATodosLosNiveles);
    }

    // ========================================
    // GUARDAR CAMBIOS
    // ========================================

    const btnGuardarCambios = document.getElementById('btnGuardarCambios');
    if (btnGuardarCambios) {
        btnGuardarCambios.addEventListener('click', async () => {
            // Recolectar datos de todos los niveles
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

            // Enviar al backend
            const overlay = mostrarOverlayGuardando('Guardando cambios...');

            try {
                btnGuardarCambios.disabled = true;
                btnGuardarCambios.innerHTML = '<i class="bi bi-hourglass-split"></i> Guardando...';

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

                ocultarOverlayGuardando();
                showNotification(`✅ Cambios guardados exitosamente. ${data.registros_actualizados || 0} ingredientes actualizados.`, 'success');

                // Recargar página para obtener datos actualizados
                setTimeout(() => {
                    window.location.reload();
                }, 1500);

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
    // FUNCIONES AUXILIARES DE OPTIMIZACIÓN (PASO 5)
    // ========================================

    function escaparHtml(texto) {
        const div = document.createElement('div');
        div.textContent = texto == null ? '' : String(texto);
        return div.innerHTML;
    }

    async function agregarIngredienteATodosLosNiveles() {
        let resultadoFormulario = null;

        if (typeof Swal !== 'undefined') {
            const opcionesPreparaciones = preparacionesCatalogo.map((prep) => (
                `<option value="${prep.id_preparacion}">${escaparHtml(prep.preparacion)}</option>`
            )).join('');

            const opcionesIngredientes = ingredientesCatalogo.map((ing) => (
                `<option value="${escaparHtml(ing.codigo)}">${escaparHtml(ing.codigo)} - ${escaparHtml(ing.nombre_del_alimento)}</option>`
            )).join('');

            const result = await Swal.fire({
                title: 'Agregar ingrediente',
                width: 680,
                showCancelButton: true,
                confirmButtonText: 'Agregar',
                cancelButtonText: 'Cancelar',
                html: `
                    <div style="text-align:left;display:grid;gap:10px;">
                        <label style="font-size:13px;font-weight:600;">Preparacion</label>
                        <select id="agregarModoPrep" class="swal2-input" style="margin:0;">
                            <option value="existente">Usar preparacion existente</option>
                            <option value="nueva">Crear nueva preparacion</option>
                        </select>

                        <div id="bloquePrepExistente">
                            <select id="agregarPreparacionExistente" class="swal2-input" style="margin:0;">
                                <option value="">Seleccione una preparacion...</option>
                                ${opcionesPreparaciones}
                            </select>
                        </div>

                        <div id="bloquePrepNueva" style="display:none;">
                            <input id="agregarPreparacionNueva" class="swal2-input" style="margin:0;" placeholder="Nombre de nueva preparacion" />
                            <small style="color:#6b7280;">Se crea con componente vacio.</small>
                        </div>

                        <label style="font-size:13px;font-weight:600;">Ingrediente</label>
                        <select id="agregarIngredienteId" class="swal2-input" style="margin:0;">
                            <option value="">Seleccione un ingrediente...</option>
                            ${opcionesIngredientes}
                        </select>

                        <label style="font-size:13px;font-weight:600;">Gramaje base (opcional)</label>
                        <input id="agregarGramaje" class="swal2-input" type="number" min="0" step="0.1" style="margin:0;" placeholder="Ej: 150" />
                    </div>
                `,
                didOpen: () => {
                    const modo = document.getElementById('agregarModoPrep');
                    const bloqueExistente = document.getElementById('bloquePrepExistente');
                    const bloqueNueva = document.getElementById('bloquePrepNueva');
                    if (!modo || !bloqueExistente || !bloqueNueva) return;
                    modo.addEventListener('change', () => {
                        const usarNueva = modo.value === 'nueva';
                        bloqueExistente.style.display = usarNueva ? 'none' : 'block';
                        bloqueNueva.style.display = usarNueva ? 'block' : 'none';
                    });
                },
                preConfirm: () => {
                    const modo = document.getElementById('agregarModoPrep')?.value || 'existente';
                    const idPreparacion = document.getElementById('agregarPreparacionExistente')?.value || '';
                    const preparacionNueva = (document.getElementById('agregarPreparacionNueva')?.value || '').trim();
                    const idIngrediente = document.getElementById('agregarIngredienteId')?.value || '';
                    const gramajeRaw = (document.getElementById('agregarGramaje')?.value || '').trim();

                    if (!idIngrediente) {
                        Swal.showValidationMessage('Debes seleccionar un ingrediente.');
                        return false;
                    }

                    if (modo === 'existente' && !idPreparacion) {
                        Swal.showValidationMessage('Debes seleccionar una preparacion existente.');
                        return false;
                    }

                    if (modo === 'nueva' && !preparacionNueva) {
                        Swal.showValidationMessage('Debes escribir el nombre de la nueva preparacion.');
                        return false;
                    }

                    let gramaje = null;
                    if (gramajeRaw !== '') {
                        gramaje = parseFloat(gramajeRaw);
                        if (Number.isNaN(gramaje) || gramaje < 0) {
                            Swal.showValidationMessage('El gramaje debe ser un numero mayor o igual a 0.');
                            return false;
                        }
                    }

                    return {
                        id_preparacion: modo === 'existente' ? parseInt(idPreparacion, 10) : null,
                        preparacion_nombre: modo === 'nueva' ? preparacionNueva : '',
                        id_ingrediente: idIngrediente,
                        gramaje: gramaje
                    };
                }
            });

            if (!result.isConfirmed || !result.value) {
                return;
            }
            resultadoFormulario = result.value;
        } else {
            showNotification('Esta funcion requiere SweetAlert2 para seleccionar preparacion e ingrediente.', 'info');
            return;
        }

        const overlay = mostrarOverlayGuardando('Agregando ingrediente en todos los niveles...');
        const btnAgregar = document.getElementById('btnAgregarFila');

        try {
            if (btnAgregar) {
                btnAgregar.disabled = true;
            }

            const payloadFila = {
                id_ingrediente: resultadoFormulario.id_ingrediente,
                gramaje: resultadoFormulario.gramaje
            };

            if (resultadoFormulario.id_preparacion) {
                payloadFila.id_preparacion = resultadoFormulario.id_preparacion;
            } else {
                payloadFila.preparacion_nombre = resultadoFormulario.preparacion_nombre;
            }

            const response = await fetch(`/nutricion/api/menus/${menuId}/guardar-preparaciones-editor/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ filas: [payloadFila] })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                const mensaje = Array.isArray(data.errores) && data.errores.length > 0
                    ? data.errores.join(' | ')
                    : (data.error || 'No se pudo agregar el ingrediente');
                throw new Error(mensaje);
            }

            ocultarOverlayGuardando();
            showNotification('Ingrediente agregado. Se aplicara para todos los niveles al recargar.', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (error) {
            console.error('Error al agregar ingrediente:', error);
            ocultarOverlayGuardando();
            showNotification(error.message || 'Error al agregar ingrediente', 'error');
        } finally {
            if (btnAgregar) {
                btnAgregar.disabled = false;
            }
        }
    }

    // Copiar pesos a otros niveles
    async function copiarPesosAOtrosNiveles(nivelOrigenId) {
        const nivelOrigen = nivelesData.find(n => n.nivel.id === nivelOrigenId);
        if (!nivelOrigen) return;

        // Obtener lista de otros niveles
        const otrosNiveles = nivelesData.filter(n => n.nivel.id !== nivelOrigenId);

        if (otrosNiveles.length === 0) {
            showNotification('No hay otros niveles disponibles', 'info');
            return;
        }

        // Crear opciones para el modal
        const opcionesHtml = otrosNiveles.map(nivel => `
            <div class="form-check">
                <input class="form-check-input nivel-destino-check" type="checkbox"
                       value="${nivel.nivel.id}" id="nivel-${nivel.nivel.id}">
                <label class="form-check-label" for="nivel-${nivel.nivel.id}">
                    ${nivel.nivel.nombre}
                </label>
            </div>
        `).join('');

        // Mostrar modal con SweetAlert2
        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title: `Copiar pesos de ${nivelOrigen.nivel.nombre}`,
                html: `
                    <p>Selecciona los niveles destino:</p>
                    <div style="text-align: left; padding: 10px;">
                        ${opcionesHtml}
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Copiar',
                cancelButtonText: 'Cancelar',
                preConfirm: () => {
                    const checkboxes = document.querySelectorAll('.nivel-destino-check:checked');
                    const seleccionados = Array.from(checkboxes).map(cb => cb.value);
                    if (seleccionados.length === 0) {
                        Swal.showValidationMessage('Debes seleccionar al menos un nivel');
                        return false;
                    }
                    return seleccionados;
                }
            });

            if (result.isConfirmed && result.value) {
                const nivelesDestino = result.value;

                // Copiar pesos
                const overlay = mostrarOverlayGuardando('Copiando pesos...');

                try {
                    // Obtener pesos actuales del nivel origen
                    const panelOrigen = document.querySelector(`#panel-${nivelOrigenId}`);
                    const tbodyOrigen = panelOrigen.querySelector('.tbody-ingredientes');
                    const pesosOrigen = [];

                    tbodyOrigen.querySelectorAll('tr').forEach(row => {
                        const pesoInput = row.querySelector('.input-peso');
                        if (pesoInput) {
                            pesosOrigen.push({
                                id_preparacion: row.dataset.idPreparacion,
                                id_ingrediente: pesoInput.dataset.idIngrediente,
                                peso_neto: parseFloat(pesoInput.value) || 0
                            });
                        }
                    });

                    // Aplicar a cada nivel destino
                    for (const nivelDestinoId of nivelesDestino) {
                        const panelDestino = document.querySelector(`#panel-${nivelDestinoId}`);
                        const tbodyDestino = panelDestino.querySelector('.tbody-ingredientes');

                        tbodyDestino.querySelectorAll('tr').forEach(row => {
                            const pesoInput = row.querySelector('.input-peso');
                            const slider = row.querySelector('.slider-peso');

                            if (pesoInput) {
                                const peso = pesosOrigen.find(p =>
                                    String(p.id_preparacion) === String(row.dataset.idPreparacion) &&
                                    String(p.id_ingrediente) === String(pesoInput.dataset.idIngrediente)
                                );

                                if (peso) {
                                    pesoInput.value = peso.peso_neto.toFixed(1);
                                    if (slider) {
                                        slider.value = Math.round(peso.peso_neto);
                                    }
                                    actualizarEstadoFila(row);
                                }
                            }
                        });

                        // Recalcular totales del nivel destino
                        recalcularNivel(nivelDestinoId);
                    }

                    ocultarOverlayGuardando();
                    showNotification(`✅ Pesos copiados a ${nivelesDestino.length} nivel(es)`, 'success');

                } catch (error) {
                    ocultarOverlayGuardando();
                    console.error('Error al copiar pesos:', error);
                    showNotification('Error al copiar pesos', 'error');
                }
            }
        } else {
            // Fallback sin SweetAlert
            alert('Esta función requiere SweetAlert2');
        }
    }

    // Generar sugerencias de optimización
    function generarSugerencias(nivelId) {
        const nivelData = nivelesData.find(n => n.nivel.id === nivelId);
        if (!nivelData) return;

        const sugerencias = [];

        // Analizar cada nutriente
        const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];

        nutrientes.forEach(nutriente => {
            const porcentaje = nivelData.porcentajes[nutriente] || 0;
            const total = nivelData.totales[nutriente] || 0;
            const requerimiento = nivelData.requerimientos[nutriente] || 0;
            const estado = nivelData.estados[nutriente];

            if (estado === 'alto' && porcentaje > 100) {
                // Muy alto - reducir
                const exceso = total - requerimiento;
                sugerencias.push({
                    tipo: 'reducir',
                    nutriente: nutriente,
                    exceso: exceso,
                    porcentaje: porcentaje,
                    mensaje: `<strong>${nutriente.toUpperCase()}:</strong> Reducir ${exceso.toFixed(1)} unidades (${porcentaje.toFixed(1)}% - excede meta)`
                });
            } else if (estado === 'optimo' && porcentaje < 25) {
                // Muy bajo - aumentar
                const deficit = requerimiento - total;
                sugerencias.push({
                    tipo: 'aumentar',
                    nutriente: nutriente,
                    deficit: deficit,
                    porcentaje: porcentaje,
                    mensaje: `<strong>${nutriente.toUpperCase()}:</strong> Aumentar ${deficit.toFixed(1)} unidades (${porcentaje.toFixed(1)}% - por debajo de meta)`
                });
            }
        });

        return sugerencias;
    }

    function mostrarSugerencias(nivelId) {
        const panel = document.getElementById(`sugerencias-${nivelId}`);
        if (!panel) return;

        const sugerencias = generarSugerencias(nivelId);

        if (sugerencias.length === 0) {
            panel.querySelector('.sugerencias-content').innerHTML = `
                <div class="sugerencia-item">
                    <span class="sugerencia-icon">✅</span>
                    <div class="sugerencia-text">
                        <strong>¡Excelente!</strong>
                        Los valores nutricionales están equilibrados. No hay sugerencias de ajuste.
                    </div>
                </div>
            `;
        } else {
            const sugerenciasHtml = sugerencias.map(sug => `
                <div class="sugerencia-item">
                    <span class="sugerencia-icon">${sug.tipo === 'reducir' ? '⬇️' : '⬆️'}</span>
                    <div class="sugerencia-text">
                        ${sug.mensaje}
                    </div>
                </div>
            `).join('');

            panel.querySelector('.sugerencias-content').innerHTML = sugerenciasHtml;
        }

        // Mostrar panel
        panel.style.display = 'block';
    }

    function ocultarSugerencias(nivelId) {
        const panel = document.getElementById(`sugerencias-${nivelId}`);
        if (panel) {
            panel.style.display = 'none';
        }
    }

    // Comparar con Minuta Patrón
    async function compararConMinutaPatron(nivelId) {
        const nivelData = nivelesData.find(n => n.nivel.id === nivelId);
        if (!nivelData) return;

        const overlay = mostrarOverlayGuardando('Comparando con Minuta Patrón...');

        try {
            // Crear tabla comparativa
            const nutrientes = ['calorias', 'proteina', 'grasa', 'cho', 'calcio', 'hierro', 'sodio'];

            const filasHtml = nutrientes.map(nutriente => {
                const actual = nivelData.totales[nutriente] || 0;
                const requerimiento = nivelData.requerimientos[nutriente] || 0;
                const diferencia = actual - requerimiento;
                const porcentaje = nivelData.porcentajes[nutriente] || 0;

                const colorClass = porcentaje > 100 ? 'text-danger' : (porcentaje < 80 ? 'text-warning' : 'text-success');

                return `
                    <tr>
                        <td><strong>${nutriente.toUpperCase()}</strong></td>
                        <td class="text-end">${actual.toFixed(1)}</td>
                        <td class="text-end">${requerimiento.toFixed(1)}</td>
                        <td class="text-end ${colorClass}">
                            ${diferencia > 0 ? '+' : ''}${diferencia.toFixed(1)}
                        </td>
                        <td class="text-end ${colorClass}">
                            ${porcentaje.toFixed(1)}%
                        </td>
                    </tr>
                `;
            }).join('');

            ocultarOverlayGuardando();

            if (typeof Swal !== 'undefined') {
                await Swal.fire({
                    title: `Comparación con Minuta Patrón - ${nivelData.nivel.nombre}`,
                    html: `
                        <div style="max-height: 400px; overflow-y: auto;">
                            <table class="table table-sm table-bordered">
                                <thead class="table-light">
                                    <tr>
                                        <th>Nutriente</th>
                                        <th class="text-end">Actual</th>
                                        <th class="text-end">Meta</th>
                                        <th class="text-end">Diferencia</th>
                                        <th class="text-end">%</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${filasHtml}
                                </tbody>
                            </table>
                        </div>
                    `,
                    width: '600px',
                    confirmButtonText: 'Cerrar'
                });
            } else {
                alert('Comparación completada. Ver consola para detalles.');
                console.table(nutrientes.map(n => ({
                    Nutriente: n,
                    Actual: nivelData.totales[n],
                    Meta: nivelData.requerimientos[n],
                    Porcentaje: nivelData.porcentajes[n]
                })));
            }

        } catch (error) {
            ocultarOverlayGuardando();
            console.error('Error al comparar:', error);
            showNotification('Error al comparar con Minuta Patrón', 'error');
        }
    }

    // Event listeners para botones de optimización
    document.addEventListener('click', (e) => {
        // Copiar pesos
        if (e.target.closest('.btn-copiar-pesos')) {
            const btn = e.target.closest('.btn-copiar-pesos');
            const nivelId = btn.dataset.nivelId;
            copiarPesosAOtrosNiveles(nivelId);
        }

        // Sugerencias
        if (e.target.closest('.btn-sugerencias')) {
            const btn = e.target.closest('.btn-sugerencias');
            const nivelId = btn.dataset.nivelId;
            mostrarSugerencias(nivelId);
        }

        // Comparar con Minuta Patrón
        if (e.target.closest('.btn-comparar-minuta')) {
            const btn = e.target.closest('.btn-comparar-minuta');
            const nivelId = btn.dataset.nivelId;
            compararConMinutaPatron(nivelId);
        }

        // Cerrar sugerencias
        if (e.target.closest('.btn-close-sugerencias')) {
            const btn = e.target.closest('.btn-close-sugerencias');
            const panel = btn.closest('.panel-sugerencias');
            if (panel) {
                panel.style.display = 'none';
            }
        }

        // Optimizar (placeholder - requiere backend)
        if (e.target.closest('.btn-optimizar-pesos')) {
            const btn = e.target.closest('.btn-optimizar-pesos');
            const nivelId = btn.dataset.nivelId;

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'info',
                    title: 'Optimización Automática',
                    text: 'Esta función ajustará automáticamente los pesos para acercarse lo más posible a las metas nutricionales.',
                    showCancelButton: true,
                    confirmButtonText: 'Optimizar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        // TODO: Implementar optimización automática
                        // Requiere algoritmo de optimización en backend
                        Swal.fire({
                            icon: 'info',
                            title: 'Función en desarrollo',
                            text: 'La optimización automática estará disponible próximamente.'
                        });
                    }
                });
            } else {
                alert('Función de optimización automática en desarrollo');
            }
        }
    });

    // ========================================
    // SINCRONIZAR PESOS BASE
    // ========================================

    const btnSincronizarPesos = document.getElementById('btnSincronizarPesos');
    if (btnSincronizarPesos) {
        btnSincronizarPesos.addEventListener('click', async () => {
            // Confirmar acción
            if (typeof Swal !== 'undefined') {
                const result = await Swal.fire({
                    title: '¿Sincronizar pesos base?',
                    text: 'Esto copiará los gramajes de las preparaciones a todos los niveles escolares',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: 'Sí, sincronizar',
                    cancelButtonText: 'Cancelar'
                });

                if (!result.isConfirmed) return;
            } else {
                if (!confirm('¿Sincronizar pesos base desde preparaciones?')) return;
            }

            const overlay = mostrarOverlayGuardando('Sincronizando pesos en todos los niveles...');

            try {
                btnSincronizarPesos.disabled = true;
                btnSincronizarPesos.innerHTML = '<i class="bi bi-hourglass-split"></i> Sincronizando...';

                // Sincronizar para cada nivel
                const promesas = nivelesData.map(async (nivelData) => {
                    const response = await fetch('/nutricion/api/sincronizar-pesos-preparaciones/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            id_menu: parseInt(menuId),
                            id_nivel_escolar: nivelData.nivel.id,
                            sobrescribir_existentes: true
                        })
                    });

                    const data = await response.json();
                    if (!response.ok || !data.success) {
                        throw new Error(`Error en ${nivelData.nivel.nombre}: ${data.error}`);
                    }

                    return data;
                });

                await Promise.all(promesas);

                ocultarOverlayGuardando();
                showNotification('✅ Pesos sincronizados exitosamente en todos los niveles', 'success');

                // Recargar página
                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } catch (error) {
                console.error('Error al sincronizar:', error);
                ocultarOverlayGuardando();
                showNotification(error.message || 'Error al sincronizar pesos', 'error');
            } finally {
                btnSincronizarPesos.disabled = false;
                btnSincronizarPesos.innerHTML = '<i class="bi bi-arrow-repeat"></i> Sincronizar pesos base';
            }
        });
    }

    // ========================================
    // TOOLTIPS Y MEJORAS VISUALES
    // ========================================

    function inicializarTooltips() {
        // Inicializar tooltips de Bootstrap si está disponible
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            [...tooltipTriggerList].forEach(tooltipTriggerEl => {
                new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }

        // Tooltips nativos para inputs sin Bootstrap
        document.querySelectorAll('.input-peso[title]').forEach(input => {
            input.addEventListener('mouseenter', function() {
                const calorias = this.dataset.calorias || 0;
                const proteina = this.dataset.proteina || 0;
                const grasa = this.dataset.grasa || 0;
                const cho = this.dataset.cho || 0;

                this.title = `📊 Info nutricional:\n` +
                            `🔥 ${parseFloat(calorias).toFixed(1)} kcal\n` +
                            `🥩 ${parseFloat(proteina).toFixed(1)}g proteína\n` +
                            `🧈 ${parseFloat(grasa).toFixed(1)}g grasa\n` +
                            `🍞 ${parseFloat(cho).toFixed(1)}g carbohidratos`;
            });
        });
    }

    function agregarFeedbackVisual() {
        // Agregar animación sutil al cambiar tabs
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabButtons.forEach(btn => {
            btn.addEventListener('shown.bs.tab', function(e) {
                const targetPanel = document.querySelector(this.dataset.bsTarget);
                if (targetPanel) {
                    targetPanel.style.animation = 'fadeIn 0.3s ease-in';
                }
            });
        });

        // Highlight temporal al recalcular
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    const element = mutation.target;
                    if (element.classList && element.classList.contains('valor-actual')) {
                        element.style.transition = 'color 0.3s ease';
                        element.style.color = '#2563eb';
                        setTimeout(() => {
                            element.style.color = '';
                        }, 300);
                    }
                }
            });
        });

        // Observar cambios en valores actuales
        document.querySelectorAll('.valor-actual').forEach(el => {
            observer.observe(el, {
                childList: true,
                characterData: true,
                subtree: true
            });
        });
    }

    // ========================================
    // INICIALIZACIÓN
    // ========================================

    function inicializar() {
        // Validar rangos iniciales y sincronizar sliders
        document.querySelectorAll('.input-peso').forEach(input => {
            const row = input.closest('tr');
            if (row) {
                sincronizarSliderConInput(row);
                actualizarEstadoFila(row);
            }
        });

        // Inicializar tooltips
        inicializarTooltips();

        // Agregar feedback visual
        agregarFeedbackVisual();

        console.log('✅ Editor de preparaciones inicializado');
        console.log('📊 Niveles escolares:', nivelesData.length);
        console.log('🎯 Sliders activos:', document.querySelectorAll('.slider-peso').length);
    }

    // Ejecutar inicialización cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

})();
