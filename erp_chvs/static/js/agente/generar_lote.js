/**
 * generar_lote.js
 * Orquestador de generación de borradores en lote para la app agente.
 *
 * Flujo:
 *  1. Usuario selecciona Programa + Modalidad + Cantidad → POST api_crear_menus_lote
 *  2. Sistema retorna lista de IDs de menús vacíos recién creados
 *  3. JS llama api_generar N veces en secuencia (una por menú)
 *     pasando menu_id_destino en cada llamada
 *  4. Progreso se muestra en tiempo real con barra + log
 *  5. Tabla de borradores pendientes se actualiza al finalizar
 */

(function () {
    'use strict';

    const CFG = window.LOTE_CONFIG;

    // Elementos del DOM
    const selPrograma = document.getElementById('sel-programa');
    const selModalidad = document.getElementById('sel-modalidad');
    const inpCantidad = document.getElementById('inp-cantidad');
    const inpOcasion = document.getElementById('inp-ocasion');
    const btnIniciar = document.getElementById('btn-iniciar-lote');
    const btnCancelar = document.getElementById('btn-cancelar');
    const panelProgreso = document.getElementById('panel-progreso');
    const barraProgreso = document.getElementById('barra-progreso');
    const tituloProgreso = document.getElementById('titulo-progreso');
    const logLote = document.getElementById('log-lote');
    const infoDisponibilidad = document.getElementById('info-disponibilidad');
    const tbodyBorradores = document.getElementById('tbody-borradores');
    const sinBorradores = document.getElementById('sin-borradores');
    const badgePendientes = document.getElementById('badge-pendientes');
    const cardFormulario = document.getElementById('card-formulario');

    // Estado del lote
    let loteActivo = false;
    let loteCancelado = false;

    // ── Habilitación del botón ────────────────────────────────────────────

    function actualizarBoton() {
        const valido = selPrograma.value && selModalidad.value &&
                       parseInt(inpCantidad.value) >= 1;
        btnIniciar.disabled = !valido || loteActivo;
    }

    selPrograma.addEventListener('change', actualizarBoton);
    selModalidad.addEventListener('change', actualizarBoton);
    inpCantidad.addEventListener('input', actualizarBoton);

    // ── Barra de progreso ─────────────────────────────────────────────────

    function actualizarBarra(actual, total) {
        const pct = Math.round((actual / total) * 100);
        barraProgreso.style.width = pct + '%';
        barraProgreso.setAttribute('aria-valuenow', pct);
        barraProgreso.textContent = actual + '/' + total;
        tituloProgreso.textContent = 'Generando borradores... ' + actual + ' de ' + total;
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

    function agregarLogEspera(num, total) {
        return agregarLogItem(
            '<span class="spinner-border spinner-border-sm me-1"></span> ' +
            'Generando menú ' + num + ' de ' + total + '...',
            'secondary'
        );
    }

    function reemplazarLogItem(item, html, tipo) {
        item.className = 'alert alert-' + tipo + ' py-1 px-2 mb-1 small log-item';
        item.innerHTML = html;
    }

    // ── Llamadas API ──────────────────────────────────────────────────────

    async function crearMenus(programaId, modalidadId, cantidad) {
        const resp = await fetch(CFG.urlCrearMenus, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CFG.csrf,
            },
            body: JSON.stringify({
                programa_id: programaId,
                modalidad_id: modalidadId,
                cantidad: cantidad,
            }),
        });
        return resp.json();
    }

    async function generarBorrador(modalidadId, menuId, ocasion) {
        const resp = await fetch(CFG.urlGenerar, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CFG.csrf,
            },
            body: JSON.stringify({
                modalidad_id: modalidadId,
                ocasion_especial: ocasion,
                menu_id_destino: menuId,
            }),
        });
        return resp.json();
    }

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

    // ── Flujo principal del lote ──────────────────────────────────────────

    btnIniciar.addEventListener('click', async function () {
        if (loteActivo) return;

        const programaId = parseInt(selPrograma.value);
        const modalidadId = selModalidad.value;
        const cantidad = Math.min(20, Math.max(1, parseInt(inpCantidad.value) || 5));
        const ocasion = inpOcasion.value.trim();

        // ── Paso 1: crear los menús vacíos ───────────────────────────────
        loteActivo = true;
        loteCancelado = false;
        btnIniciar.disabled = true;
        panelProgreso.classList.remove('d-none');
        logLote.innerHTML = '';
        tituloProgreso.textContent = 'Creando ' + cantidad + ' menús vacíos...';
        barraProgreso.style.width = '0%';
        barraProgreso.textContent = '0/' + cantidad;

        let menuIds;
        const itemCrear = agregarLogItem(
            '<span class="spinner-border spinner-border-sm me-1"></span> ' +
            'Creando ' + cantidad + ' menús vacíos en el programa seleccionado...',
            'secondary'
        );

        try {
            const resultCrear = await crearMenus(programaId, modalidadId, cantidad);
            if (!resultCrear.ok) {
                reemplazarLogItem(itemCrear,
                    '✗ No se pudieron crear los menús: ' + (resultCrear.error || 'Error desconocido'),
                    'danger'
                );
                _finalizarLote(0, 0);
                return;
            }
            menuIds = resultCrear.menu_ids;
            reemplazarLogItem(itemCrear,
                '✓ ' + menuIds.length + ' menús vacíos creados correctamente.',
                'success'
            );
        } catch (err) {
            reemplazarLogItem(itemCrear,
                '✗ Error de red al crear menús: ' + err.message,
                'danger'
            );
            _finalizarLote(0, 0);
            return;
        }

        // ── Paso 2: generar borradores para cada menú ────────────────────
        let exitosos = 0;
        let fallidos = 0;
        const total = menuIds.length;

        for (let i = 0; i < total; i++) {
            if (loteCancelado) {
                agregarLogItem(
                    '⛔ Lote cancelado en el menú ' + (i + 1) +
                    '. Generados: ' + exitosos + ', Fallidos: ' + fallidos + '.',
                    'warning'
                );
                break;
            }

            actualizarBarra(i + 1, total);
            const itemEspera = agregarLogEspera(i + 1, total);

            try {
                const data = await generarBorrador(modalidadId, menuIds[i], ocasion);

                if (data.ok) {
                    exitosos++;
                    reemplazarLogItem(itemEspera,
                        '✓ Menú ' + (i + 1) + ' — Borrador listo. ' +
                        '<a href="/agente/borrador/' + data.generacion_id + '/" ' +
                        'target="_blank" class="alert-link">Ver borrador →</a>',
                        'success'
                    );
                } else {
                    fallidos++;
                    reemplazarLogItem(itemEspera,
                        '✗ Menú ' + (i + 1) + ': ' + (data.error || 'Error al generar'),
                        'danger'
                    );
                }
            } catch (err) {
                fallidos++;
                reemplazarLogItem(itemEspera,
                    '✗ Menú ' + (i + 1) + ': Error de red — ' + err.message,
                    'danger'
                );
            }

            // Pausa entre llamadas para respetar rate limits de la API de Gemini
            if (i < total - 1 && !loteCancelado) {
                await _sleep(1500);
            }
        }

        _finalizarLote(exitosos, fallidos);
    });

    // ── Cancelar ─────────────────────────────────────────────────────────

    btnCancelar.addEventListener('click', function () {
        loteCancelado = true;
        btnCancelar.disabled = true;
        btnCancelar.textContent = 'Cancelando...';
    });

    // ── Finalizar lote ────────────────────────────────────────────────────

    function _finalizarLote(exitosos, fallidos) {
        loteActivo = false;
        btnIniciar.disabled = false;
        btnCancelar.disabled = false;
        btnCancelar.textContent = '⛔ Cancelar';
        tituloProgreso.textContent = 'Lote completado';
        barraProgreso.classList.remove('progress-bar-animated');

        if (exitosos > 0 || fallidos > 0) {
            const tipo = fallidos === 0 ? 'success' : (exitosos > 0 ? 'warning' : 'danger');
            agregarLogItem(
                '<strong>Resumen:</strong> ' + exitosos + ' borradores generados, ' +
                fallidos + ' fallidos.',
                tipo
            );
        }

        // Actualizar tabla de borradores pendientes
        setTimeout(cargarBorradores, 1000);
    }

    // ── Utilidades ────────────────────────────────────────────────────────

    function _sleep(ms) {
        return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

})();
