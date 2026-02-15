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

            let estado = 'optimo';
            if (porcentaje > 100) {
                estado = 'alto'; // Rojo
            } else if (porcentaje >= 80) {
                estado = 'optimo'; // Verde
            } else if (porcentaje >= 50) {
                estado = 'aceptable'; // Amarillo
            } else {
                estado = 'info'; // Azul
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

    document.addEventListener('input', (e) => {
        if (e.target.classList.contains('input-peso')) {
            const row = e.target.closest('tr');
            const tbody = e.target.closest('.tbody-ingredientes');
            if (row && tbody) {
                const nivelId = tbody.dataset.nivelId;
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
                actualizarEstadoFila(row);
                recalcularNivel(nivelId);
            }
        }
    });

    // ========================================
    // LÓGICA DE SUGERENCIAS - ELIMINADA
    // ========================================

    // Event Delegation para botones de sugerencias por nivel (ELIMINADO)
    
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
                showNotification(`✅ Cambios guardados exitosamente.`, 'success');

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

    const btnSincronizarPesos = document.getElementById('btnSincronizarPesos');
    if (btnSincronizarPesos) {
        btnSincronizarPesos.addEventListener('click', async () => {
            if (typeof Swal === 'undefined') {
                if (!confirm('¿Estás seguro de restablecer los pesos a los valores originales de la receta? Se perderán las personalizaciones manuales.')) return;
            } else {
                const result = await Swal.fire({
                    title: '¿Sincronizar con receta base?',
                    text: "Esto restablecerá los pesos de TODOS los niveles a los valores originales de la preparación. Se perderán las personalizaciones manuales que hayas hecho aquí.",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: 'Sí, sincronizar',
                    cancelButtonText: 'Cancelar'
                });
                if (!result.isConfirmed) return;
            }

            const overlay = mostrarOverlayGuardando('Sincronizando pesos...');

            try {
                // Iteramos sobre todos los niveles para sincronizarlos uno por uno (o podríamos ajustar el endpoint para masivo)
                // Según el test, el endpoint recibe 'id_nivel_escolar'. Vamos a intentar enviar null o hacerlo por loop.
                // Como el test muestra 'id_nivel_escolar', lo haremos por loop para asegurar compatibilidad.
                
                const promesas = nivelesData.map(nivelData => {
                    return fetch('/nutricion/api/sincronizar-pesos-preparaciones/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            id_menu: menuId,
                            id_nivel_escolar: nivelData.nivel.id,
                            sobrescribir_existentes: true
                        })
                    });
                });

                await Promise.all(promesas);

                ocultarOverlayGuardando();
                
                if (typeof Swal !== 'undefined') {
                    await Swal.fire('¡Sincronizado!', 'Los pesos se han restablecido a la receta original.', 'success');
                } else {
                    alert('Pesos sincronizados correctamente.');
                }
                
                window.location.reload();

            } catch (error) {
                console.error('Error al sincronizar:', error);
                ocultarOverlayGuardando();
                showNotification('Error al sincronizar pesos', 'error');
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

        const result = await Swal.fire({
            title: 'Agregar ingrediente',
            width: 680,
            showCancelButton: true,
            confirmButtonText: 'Agregar',
            cancelButtonText: 'Cancelar',
            html: `
                <div style="text-align:left;display:grid;gap:10px;">
                    <label style="font-size:13px;font-weight:600;">Preparación</label>
                    <select id="agregarModoPrep" class="swal2-input" style="margin:0;">
                        <option value="existente">Usar preparación existente</option>
                        <option value="nueva">Crear nueva preparación</option>
                    </select>
                    <div id="bloquePrepExistente">
                        <select id="agregarPreparacionExistente" class="swal2-input" style="margin:0;">
                            <option value="">Seleccione una preparación...</option>
                            ${opcionesPreparaciones}
                        </select>
                    </div>
                    <div id="bloquePrepNueva" style="display:none;">
                        <input id="agregarPreparacionNueva" class="swal2-input" style="margin:0;" placeholder="Nombre de nueva preparación" />
                    </div>
                    <label style="font-size:13px;font-weight:600;">Ingrediente</label>
                    <select id="agregarIngredienteId" class="swal2-input" style="margin:0;">
                        <option value="">Seleccione un ingrediente...</option>
                        ${opcionesIngredientes}
                    </select>
                    <label style="font-size:13px;font-weight:600;">Gramaje base (opcional)</label>
                    <input id="agregarGramaje" class="swal2-input" type="number" min="0" step="0.1" style="margin:0;" placeholder="Ej: 100 (dejar vacío para valor por defecto)" />
                    <small style="color:#6b7280;font-size:11px;">Si no especificas gramaje, se aplicarán los valores predeterminados por nivel.</small>
                </div>
            `,
            didOpen: () => {
                const modo = document.getElementById('agregarModoPrep');
                const bExistente = document.getElementById('bloquePrepExistente');
                const bNueva = document.getElementById('bloquePrepNueva');
                modo.addEventListener('change', () => {
                    const esNueva = modo.value === 'nueva';
                    bExistente.style.display = esNueva ? 'none' : 'block';
                    bNueva.style.display = esNueva ? 'block' : 'none';
                });
            },
            preConfirm: () => {
                const modo = document.getElementById('agregarModoPrep').value;
                const idPrep = document.getElementById('agregarPreparacionExistente').value;
                const nomPrep = document.getElementById('agregarPreparacionNueva').value.trim();
                const idIng = document.getElementById('agregarIngredienteId').value;
                const gramajeInput = document.getElementById('agregarGramaje').value;

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

                // Validar gramaje (permitir vacío para usar valores por defecto)
                let gramaje = null;
                if (gramajeInput && gramajeInput.trim() !== '') {
                    const gramajeNum = parseFloat(gramajeInput);
                    if (isNaN(gramajeNum)) {
                        return Swal.showValidationMessage('El gramaje debe ser un número válido');
                    }
                    if (gramajeNum < 0) {
                        return Swal.showValidationMessage('El gramaje debe ser mayor o igual a cero');
                    }
                    gramaje = gramajeNum;
                }

                return {
                    id_preparacion: modo === 'existente' ? parseInt(idPrep) : null,
                    preparacion_nombre: modo === 'nueva' ? nomPrep : '',
                    id_ingrediente: idIng,
                    gramaje: gramaje
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

        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }

        console.log('✅ Editor inicializado. Niveles:', nivelesData.length);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

})();
