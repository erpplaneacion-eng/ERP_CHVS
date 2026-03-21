/**
 * generar_lote.js
 * Orquestador de generación de borradores en lote para la app agente.
 *
 * Flujo:
 *  1. Usuario selecciona Modalidad + Cantidad → inicia lote
 *  2. POST a api_iniciar_lote → servidor lanza hilo background → retorna lote_id
 *  3. Frontend hace polling cada 3s a api_estado_lote/<lote_id>/
 *  4. Progreso en tiempo real con barra + log
 *  5. El usuario puede navegar a otro módulo y volver: el lote_id se guarda en localStorage
 *     y el polling se reanuda automáticamente al cargar la página
 */

(function () {
    'use strict';

    const CFG = window.LOTE_CONFIG;

    // Elementos del DOM
    const selModalidad = document.getElementById('sel-modalidad');
    const inpCantidad = document.getElementById('inp-cantidad');
    const inpOcasion = document.getElementById('inp-ocasion');
    const btnIniciar = document.getElementById('btn-iniciar-lote');
    const btnCancelar = document.getElementById('btn-cancelar');
    const panelProgreso = document.getElementById('panel-progreso');
    const barraProgreso = document.getElementById('barra-progreso');
    const tituloProgreso = document.getElementById('titulo-progreso');
    const logLote = document.getElementById('log-lote');
    const tbodyBorradores = document.getElementById('tbody-borradores');
    const sinBorradores = document.getElementById('sin-borradores');
    const badgePendientes = document.getElementById('badge-pendientes');

    const LOTE_KEY = 'agente_lote_activo_id';
    const POLL_INTERVAL_MS = 3000;

    let _pollingTimer = null;
    let _ultimoProcesado = 0;
    let _totalActual = 0;

    // ── Habilitación del botón ────────────────────────────────────────────

    function actualizarBoton() {
        const valido = selModalidad.value && parseInt(inpCantidad.value) >= 1;
        btnIniciar.disabled = !valido || !!_pollingTimer;
    }

    selModalidad.addEventListener('change', actualizarBoton);
    inpCantidad.addEventListener('input', actualizarBoton);

    // ── Barra de progreso ─────────────────────────────────────────────────

    function actualizarBarra(actual, total) {
        const pct = total > 0 ? Math.round((actual / total) * 100) : 0;
        barraProgreso.style.width = pct + '%';
        barraProgreso.setAttribute('aria-valuenow', pct);
        barraProgreso.textContent = actual + '/' + total;
        tituloProgreso.textContent = 'Generando borradores en servidor... ' + actual + ' de ' + total;
    }

    // ── Log de resultados ─────────────────────────────────────────────────

    function agregarLogItem(html, tipo) {
        const item = document.createElement('div');
        item.className = 'alert alert-' + tipo + ' py-1 px-2 mb-1 small log-item';
        item.innerHTML = html;
        logLote.appendChild(item);
        logLote.scrollTop = logLote.scrollHeight;
        return item;
    }

    // ── Polling ───────────────────────────────────────────────────────────

    function iniciarPolling(loteId, total) {
        _ultimoProcesado = 0;
        _totalActual = total;
        panelProgreso.classList.remove('d-none');
        logLote.innerHTML = '';
        actualizarBarra(0, total);
        tituloProgreso.textContent = 'El servidor está generando ' + total + ' borradores en background...';
        btnIniciar.disabled = true;

        _pollingTimer = setInterval(function () {
            _consultarEstado(loteId);
        }, POLL_INTERVAL_MS);
    }

    function _consultarEstado(loteId) {
        fetch(CFG.urlEstadoLote + loteId + '/estado/')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) return;

                actualizarBarra(data.cantidad_procesada, data.cantidad_total);

                // Mostrar solo los nuevos resultados
                var nuevos = data.resultados.slice(_ultimoProcesado);
                nuevos.forEach(function (r) {
                    if (r.ok) {
                        agregarLogItem(
                            '✓ Borrador ' + r.num + ' listo. ' +
                            '<a href="/agente/borrador/' + r.generacion_id + '/" ' +
                            'target="_blank" class="alert-link">Revisar y aprobar →</a>',
                            'success'
                        );
                    } else {
                        agregarLogItem(
                            '✗ Borrador ' + r.num + ': ' + (r.error || 'Error al generar'),
                            'danger'
                        );
                    }
                });
                _ultimoProcesado = data.resultados.length;

                if (data.estado !== 'procesando') {
                    _detenerPolling();
                    localStorage.removeItem(LOTE_KEY);
                    _finalizarLote(data.cantidad_exitosa, data.cantidad_fallida);
                }
            })
            .catch(function (err) {
                console.warn('Error al consultar estado del lote:', err);
            });
    }

    function _detenerPolling() {
        if (_pollingTimer) {
            clearInterval(_pollingTimer);
            _pollingTimer = null;
        }
    }

    // ── Flujo principal ───────────────────────────────────────────────────

    btnIniciar.addEventListener('click', async function () {
        if (_pollingTimer) return;

        const modalidadId = selModalidad.value;
        const cantidad = Math.min(20, Math.max(1, parseInt(inpCantidad.value) || 5));
        const ocasion = inpOcasion.value.trim();

        btnIniciar.disabled = true;

        try {
            const resp = await fetch(CFG.urlIniciarLote, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CFG.csrf,
                },
                body: JSON.stringify({
                    modalidad_id: modalidadId,
                    cantidad: cantidad,
                    ocasion_especial: ocasion,
                }),
            });
            const data = await resp.json();

            if (!data.ok) {
                alert('Error al iniciar lote: ' + (data.error || 'Error desconocido'));
                btnIniciar.disabled = false;
                return;
            }

            localStorage.setItem(LOTE_KEY, JSON.stringify({ loteId: data.lote_id, total: cantidad }));
            iniciarPolling(data.lote_id, cantidad);

        } catch (err) {
            alert('Error de red: ' + err.message);
            btnIniciar.disabled = false;
        }
    });

    // ── Cancelar (detiene polling, el hilo en servidor continúa) ─────────

    btnCancelar.addEventListener('click', function () {
        _detenerPolling();
        localStorage.removeItem(LOTE_KEY);
        tituloProgreso.textContent = 'Seguimiento cancelado (el servidor puede seguir generando)';
        btnCancelar.disabled = false;
        btnIniciar.disabled = false;
        agregarLogItem('ℹ️ Dejaste de ver el progreso. Los borradores que se generen aparecerán en la tabla al recargar.', 'info');
    });

    // ── Finalizar lote ────────────────────────────────────────────────────

    function _finalizarLote(exitosos, fallidos) {
        btnIniciar.disabled = false;
        tituloProgreso.textContent = 'Lote completado';
        barraProgreso.classList.remove('progress-bar-animated');

        const tipo = fallidos === 0 ? 'success' : (exitosos > 0 ? 'warning' : 'danger');
        agregarLogItem(
            '<strong>Resumen:</strong> ' + exitosos + ' borradores generados, ' + fallidos + ' fallidos.',
            tipo
        );

        setTimeout(cargarBorradores, 1000);
    }

    // ── Tabla de borradores ───────────────────────────────────────────────

    async function cargarBorradores() {
        try {
            const resp = await fetch(CFG.urlBorradores);
            const data = await resp.json();
            if (!data.ok || !data.borradores.length) {
                if (tbodyBorradores) tbodyBorradores.innerHTML = '';
                if (sinBorradores) sinBorradores.classList.remove('d-none');
                if (badgePendientes) badgePendientes.textContent = '0';
                return;
            }
            if (sinBorradores) sinBorradores.classList.add('d-none');
            if (badgePendientes) badgePendientes.textContent = data.borradores.length;

            if (!tbodyBorradores) return;
            const frag = document.createDocumentFragment();
            data.borradores.forEach(function (b, idx) {
                const tr = document.createElement('tr');
                tr.id = 'fila-borrador-' + b.id;
                tr.innerHTML =
                    '<td class="text-muted">' + (idx + 1) + '</td>' +
                    '<td>' + b.modalidad + '</td>' +
                    '<td>' + (b.menu || '<span class="text-muted fst-italic">Sin asignar</span>') + '</td>' +
                    '<td>' + (b.programa || '<span class="text-muted">—</span>') + '</td>' +
                    '<td class="text-muted small">' + b.fecha + '</td>' +
                    '<td><a href="' + b.url_borrador + '" class="btn btn-sm btn-outline-primary" target="_blank">Ver / Aprobar</a></td>';
                frag.appendChild(tr);
            });
            tbodyBorradores.innerHTML = '';
            tbodyBorradores.appendChild(frag);
        } catch (e) {
            console.warn('No se pudo actualizar la tabla de borradores:', e);
        }
    }

    // ── Reanudar polling si el usuario volvió con un lote activo ─────────

    (function reanudarSiHayLoteActivo() {
        const guardado = localStorage.getItem(LOTE_KEY);
        if (!guardado) return;

        var info;
        try { info = JSON.parse(guardado); } catch (e) { localStorage.removeItem(LOTE_KEY); return; }

        // Verificar estado actual antes de reanudar
        fetch(CFG.urlEstadoLote + info.loteId + '/estado/')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) { localStorage.removeItem(LOTE_KEY); return; }

                if (data.estado === 'procesando') {
                    // Reanudar polling
                    _ultimoProcesado = data.resultados.length;
                    _totalActual = data.cantidad_total;
                    panelProgreso.classList.remove('d-none');
                    actualizarBarra(data.cantidad_procesada, data.cantidad_total);
                    tituloProgreso.textContent = '↩️ Reanudando seguimiento del lote en curso...';
                    btnIniciar.disabled = true;

                    // Mostrar resultados ya obtenidos
                    logLote.innerHTML = '';
                    data.resultados.forEach(function (r) {
                        if (r.ok) {
                            agregarLogItem(
                                '✓ Borrador ' + r.num + ' (ya generado) — ' +
                                '<a href="/agente/borrador/' + r.generacion_id + '/" target="_blank" class="alert-link">Ver →</a>',
                                'success'
                            );
                        } else {
                            agregarLogItem('✗ Borrador ' + r.num + ': ' + (r.error || 'Error'), 'danger');
                        }
                    });

                    _pollingTimer = setInterval(function () {
                        _consultarEstado(info.loteId);
                    }, POLL_INTERVAL_MS);
                } else {
                    // Lote ya terminó mientras el usuario estaba fuera
                    localStorage.removeItem(LOTE_KEY);
                    cargarBorradores();
                }
            })
            .catch(function () { localStorage.removeItem(LOTE_KEY); });
    })();

})();
