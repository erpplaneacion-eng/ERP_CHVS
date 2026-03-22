/**
 * generar_lote.js
 * Simula generación en tiempo real tomando borradores del pool.
 * Cada tarjeta muestra animación de "thinking" antes de revelar el contenido.
 */

(function () {
    'use strict';

    const CFG = window.LOTE_CONFIG;

    const selModalidad = document.getElementById('sel-modalidad');
    const inpCantidad  = document.getElementById('inp-cantidad');
    const btnGenerar   = document.getElementById('btn-generar');
    const alertaForm   = document.getElementById('alerta-form');
    const gridMenus    = document.getElementById('grid-menus');
    const resumenFinal = document.getElementById('resumen-final');

    // ── Habilitar botón ───────────────────────────────────────────────────────

    selModalidad.addEventListener('change', _actualizarBoton);
    inpCantidad.addEventListener('input', _actualizarBoton);

    function _actualizarBoton() {
        btnGenerar.disabled = !selModalidad.value || parseInt(inpCantidad.value) < 1;
        alertaForm.classList.add('d-none');
    }

    // ── Flujo principal ───────────────────────────────────────────────────────

    btnGenerar.addEventListener('click', async function () {
        const modalidadId = selModalidad.value;
        const cantidad    = Math.min(20, Math.max(1, parseInt(inpCantidad.value) || 5));
        if (!modalidadId) return;

        // Resetear estado visual
        btnGenerar.disabled = true;
        btnGenerar.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Generando...';
        alertaForm.classList.add('d-none');
        gridMenus.innerHTML = '';
        gridMenus.classList.remove('d-none');
        resumenFinal.classList.add('d-none');

        // 1. Tomar del pool
        let ids;
        try {
            const resp = await fetch(CFG.urlTomarPool, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf },
                body: JSON.stringify({ modalidad_id: modalidadId, cantidad }),
            });
            const data = await resp.json();
            if (!data.ok) {
                _mostrarAlerta(data.error, 'warning');
                _resetBoton();
                return;
            }
            ids = data.ids;
        } catch (e) {
            _mostrarAlerta('Error de red: ' + e.message, 'danger');
            _resetBoton();
            return;
        }

        // 2. Mostrar tarjetas con animación secuencial
        let aprobados = 0;
        let rechazados = 0;

        for (let i = 0; i < ids.length; i++) {
            const id = ids[i];

            // Crear tarjeta en estado "thinking"
            const card = _crearCartaPensando(id, i + 1);
            gridMenus.appendChild(card);
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            // Simular tiempo de generación (1.2s – 2.8s aleatorio)
            const thinkTime = 1200 + Math.random() * 1600;
            await _sleep(thinkTime);

            // Obtener datos reales y revelar
            try {
                const preview = await _fetchPreview(id);
                _revelarCarta(card, id, preview);
            } catch (e) {
                _revelarCartaError(card, i + 1);
            }

            // Pausa breve entre tarjetas
            if (i < ids.length - 1) await _sleep(300);
        }

        // 3. Resumen final
        _mostrarResumen(ids.length);
        _resetBoton();
    });

    // ── Crear tarjeta en estado thinking ─────────────────────────────────────

    function _crearCartaPensando(id, num) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-xl-4';
        col.id = 'col-card-' + id;
        col.innerHTML = `
            <div class="menu-card card h-100 shadow-sm border-0 card-thinking">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex align-items-center gap-2 mb-3">
                        <span class="text-muted small">Generando...</span>
                    </div>
                    <div class="thinking-area flex-grow-1 d-flex flex-column align-items-start justify-content-center gap-2">
                        <div class="thinking-line w-75"></div>
                        <div class="thinking-line w-50"></div>
                        <div class="thinking-line w-85"></div>
                        <div class="thinking-line w-60"></div>
                        <div class="thinking-line w-70"></div>
                    </div>
                    <div class="thinking-dots mt-3">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>`;
        return col;
    }

    // ── Revelar tarjeta con contenido real ────────────────────────────────────

    function _revelarCarta(col, id, preview) {
        const prepsHtml = preview.preparaciones.map(p => {
            const badge = p.invalidos > 0
                ? `<span class="badge bg-warning text-dark ms-1" title="${p.invalidos} ingrediente(s) sin código">${p.invalidos} ⚠</span>`
                : '<span class="badge bg-success ms-1">✓</span>';
            return `<li class="prep-item">
                        <span class="prep-nombre">${p.nombre}</span>${badge}
                        <span class="text-muted small ms-1">(${p.componente})</span>
                    </li>`;
        }).join('');

        const card = col.querySelector('.menu-card');
        card.classList.remove('card-thinking');
        card.classList.add('card-revealed');
        card.innerHTML = `
            <div class="card-body d-flex flex-column">
                <div class="d-flex align-items-center gap-2 mb-2">
                    <span class="text-muted small">${preview.modalidad}</span>
                </div>
                <ul class="prep-list flex-grow-1 mb-3">${prepsHtml}</ul>
                <div class="d-flex gap-2 mt-auto">
                    <a href="${CFG.urlBorrador}${id}/"
                       target="_blank"
                       class="btn btn-success btn-sm flex-grow-1">
                        ✅ Revisar y aprobar
                    </a>
                    <button class="btn btn-outline-secondary btn-sm btn-rechazar"
                            data-id="${id}" title="Devolver al pool">
                        ✕
                    </button>
                </div>
            </div>`;

        // Listener del botón rechazar
        card.querySelector('.btn-rechazar').addEventListener('click', function () {
            _rechazarBorrador(id, col);
        });
    }

    function _revelarCartaError(col, num) {
        const card = col.querySelector('.menu-card');
        card.classList.remove('card-thinking');
        card.classList.add('border-warning');
        card.innerHTML = `
            <div class="card-body text-center text-muted py-4">
                <p class="mb-0">⚠️ No se pudo cargar el menú ${num}</p>
                <small>Intenta recargar la página</small>
            </div>`;
    }

    // ── Rechazar borrador → vuelve al pool ────────────────────────────────────

    async function _rechazarBorrador(id, col) {
        const btn = col.querySelector('.btn-rechazar');
        if (btn) btn.disabled = true;

        try {
            const resp = await fetch(CFG.urlRechazar + id + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': CFG.csrf },
            });
            const data = await resp.json();
            if (data.ok) {
                col.classList.add('card-rechazada');
                setTimeout(function () { col.remove(); }, 400);
            }
        } catch (e) {
            if (btn) btn.disabled = false;
        }
    }

    // ── Fetch preview ─────────────────────────────────────────────────────────

    function _fetchPreview(id) {
        return fetch(CFG.urlPreview + id + '/preview/')
            .then(function (r) { return r.json(); });
    }

    // ── Resumen final ─────────────────────────────────────────────────────────

    function _mostrarResumen(total) {
        resumenFinal.className = 'lote-summary mt-4';
        resumenFinal.innerHTML =
            `<strong>✅ ${total} menú${total !== 1 ? 's' : ''} generado${total !== 1 ? 's' : ''}.</strong> ` +
            'Revisa cada tarjeta y aprueba los que quieras importar a producción. ' +
            'Los que rechaces vuelven al pool automáticamente.';
        resumenFinal.classList.remove('d-none');
    }

    // ── Utilidades ────────────────────────────────────────────────────────────

    function _mostrarAlerta(msg, tipo) {
        alertaForm.className = 'lote-alert mt-3' + (tipo === 'danger' ? ' alert-danger' : '');
        alertaForm.textContent = msg;
        alertaForm.classList.remove('d-none');
    }

    function _resetBoton() {
        btnGenerar.disabled = false;
        btnGenerar.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generar menús';
    }

    function _sleep(ms) {
        return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

})();
