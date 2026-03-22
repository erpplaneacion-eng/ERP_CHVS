/**
 * index.js — NOVA Neural Studio: generación individual de preparaciones IA
 */
(function () {
    'use strict';

    const CFG = window.NOVA_CONFIG;

    const selModal    = document.getElementById('sel-modalidad');
    const inpOcasion  = document.getElementById('inp-ocasion');
    const btnGenerar  = document.getElementById('btn-generar');
    const errorBox    = document.getElementById('error-box');
    const errorText   = document.getElementById('error-text');
    const chipModal   = document.getElementById('chip-modalidad');
    const chipText    = document.getElementById('chip-text');
    const ocasionWrap = document.getElementById('ocasion-wrap');
    const typingRow   = document.getElementById('typing-row');
    const novaMsgs    = document.getElementById('nova-msgs');
    const novaGen     = document.getElementById('nova-generating');
    const genMsg      = document.getElementById('gen-msg');
    const genSub      = document.getElementById('gen-sub');
    const fieldCta    = document.getElementById('field-cta');
    let msg3Added = false;

    // ── Add agent message with typing animation ───────────────────────────

    function _addMsg(id, html) {
        typingRow.classList.add('active');
        setTimeout(function () {
            typingRow.classList.remove('active');
            const div = document.createElement('div');
            div.className = 'nova-msg';
            div.id = id;
            div.style.animation = 'novaMsgIn 0.4s ease forwards';
            div.innerHTML =
                '<div class="nova-mini-av"><i class="fa-solid fa-brain"></i></div>' +
                '<div class="nova-bubble">' + html + '</div>';
            novaMsgs.appendChild(div);
        }, 1100);
    }

    // ── Modalidad change ──────────────────────────────────────────────────

    selModal.addEventListener('change', function () {
        const val = this.value;
        const txt = val ? this.options[this.selectedIndex].text : '';
        btnGenerar.disabled = !val;
        errorBox.classList.remove('active');

        if (val) {
            chipText.textContent = txt + ' seleccionada';
            chipModal.classList.add('visible');

            if (!msg3Added) {
                msg3Added = true;
                _addMsg(
                    'nova-msg-3',
                    'Perfecto, trabajaré con <strong>' + txt + '</strong>. ' +
                    '¿Habrá alguna <em>ocasión especial</em> — Halloween, Día del Niño, Navidad — ' +
                    'para darle nombres temáticos a las preparaciones? ' +
                    'Déjalo vacío si no hay.'
                );
                setTimeout(function () { ocasionWrap.classList.add('open'); }, 1400);
            }
        } else {
            chipModal.classList.remove('visible');
        }
    });

    // ── Status cycles ─────────────────────────────────────────────────────

    const liveSteps = [
        ['Consultando base de conocimientos PAE...', 'Analizando la Resolución 3803 de 2016'],
        ['Identificando ingredientes disponibles...', 'Revisando catálogo ICBF para esta modalidad'],
        ['Generando preparaciones con Gemini 2.5...', 'Creando nombres, componentes e ingredientes'],
        ['Validando códigos ICBF...', 'Verificando cada ingrediente en el catálogo'],
        ['Finalizando borrador...', 'Casi listo para tu revisión'],
    ];
    const poolSteps = [
        ['Consultando banco de preparaciones...', 'Recuperando borrador del pool IA'],
        ['Preparando tu borrador...', 'Personalizando para esta solicitud'],
    ];

    function _startCycle(steps, ms) {
        let idx = 0;
        _applyMsg(steps[0]);
        return setInterval(function () {
            idx = (idx + 1) % steps.length;
            genMsg.style.opacity = '0';
            genSub.style.opacity  = '0';
            setTimeout(function () {
                _applyMsg(steps[idx]);
                genMsg.style.opacity = '1';
                genSub.style.opacity  = '1';
            }, 220);
        }, ms);
    }

    function _applyMsg(pair) {
        genMsg.textContent = pair[0];
        genSub.textContent = pair[1];
    }

    // ── Show/restore generating state ─────────────────────────────────────

    function _showGenerating() {
        document.querySelector('.nova-panel').style.pointerEvents = 'none';
        fieldCta.style.display = 'none';
        novaGen.classList.add('active');
    }

    function _restoreForm(msg) {
        novaGen.classList.remove('active');
        fieldCta.style.display = '';
        document.querySelector('.nova-panel').style.pointerEvents = '';
        btnGenerar.disabled = false;
        if (msg) { errorText.textContent = msg; errorBox.classList.add('active'); }
    }

    // ── Poll live generation ───────────────────────────────────────────────

    function _pollGeneracion(id, cycleTimer) {
        let attempts = 0;
        const poll = setInterval(function () {
            attempts++;
            fetch('/agente/api/generar/' + id + '/estado/')
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d.estado === 'pendiente_revision') {
                        clearInterval(poll); clearInterval(cycleTimer);
                        _applyMsg(['¡Borrador listo!', 'Abriendo editor...']);
                        setTimeout(function () {
                            window.location.href = '/agente/borrador/' + id + '/';
                        }, 600);
                    } else if (d.estado === 'error') {
                        clearInterval(poll); clearInterval(cycleTimer);
                        _restoreForm(d.error || 'El servidor no pudo generar el borrador.');
                    } else if (attempts >= 60) {
                        clearInterval(poll); clearInterval(cycleTimer);
                        _restoreForm('La generación tardó demasiado. Intenta de nuevo.');
                    }
                })
                .catch(function () {
                    if (attempts >= 60) {
                        clearInterval(poll); clearInterval(cycleTimer);
                        _restoreForm('No se pudo contactar al servidor.');
                    }
                });
        }, 3000);
    }

    // ── Main click ────────────────────────────────────────────────────────

    btnGenerar.addEventListener('click', function () {
        const modId = selModal.value;
        if (!modId) return;

        errorBox.classList.remove('active');
        _showGenerating();

        const poolTimer = _startCycle(poolSteps, 1700);

        fetch(CFG.urlGenerar, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CFG.csrf,
            },
            body: JSON.stringify({
                modalidad_id: parseInt(modId),
                ocasion_especial: inpOcasion.value.trim(),
            }),
        })
        .then(function (r) {
            if (!r.ok) return r.text().then(function (t) { throw new Error('HTTP ' + r.status); });
            return r.json();
        })
        .then(function (data) {
            clearInterval(poolTimer);
            if (!data.ok) { _restoreForm(data.error || 'Error desconocido'); return; }

            if (data.fuente === 'pool') {
                _applyMsg(['¡Pensando!', 'Preparando para tu revisión...']);
                setTimeout(function () {
                    window.location.href = '/agente/borrador/' + data.generacion_id + '/';
                }, 1500);
            } else {
                const liveTimer = _startCycle(liveSteps, 3500);
                _pollGeneracion(data.generacion_id, liveTimer);
            }
        })
        .catch(function (err) {
            clearInterval(poolTimer);
            _restoreForm(err.message);
        });
    });

})();
