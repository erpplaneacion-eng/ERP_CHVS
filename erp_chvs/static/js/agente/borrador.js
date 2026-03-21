(function () {
    const cfg = window.BORRADOR_CONFIG;
    if (!cfg) return;

    const { generacionId, modalidadId, csrf, urlMenus, urlEliminarIng, urlCorregirIng,
            urlBuscarAlimento, urlDescartar, urlIndex, menuIdPreasignado } = cfg;

    // ── Eliminar / Corregir ingrediente ──────────────────────────────────────
    const listaPrep = document.getElementById('lista-preparaciones');
    if (listaPrep) {

        listaPrep.addEventListener('click', function (e) {
            // Eliminar
            const btnElim = e.target.closest('.btn-eliminar-ing');
            if (btnElim) {
                const ingId = btnElim.dataset.ingId;
                if (!confirm('¿Eliminar este ingrediente del borrador?')) return;
                btnElim.disabled = true;
                fetch(urlEliminarIng, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: JSON.stringify({ ingrediente_id: parseInt(ingId) }),
                })
                    .then(r => r.json())
                    .then(data => {
                        if (data.ok) {
                            document.getElementById('ing-row-' + ingId).remove();
                            document.getElementById('ing-busqueda-' + ingId)?.remove();
                        } else {
                            alert('Error: ' + data.error);
                            btnElim.disabled = false;
                        }
                    });
                return;
            }

            // Abrir buscador de corrección
            const btnCorr = e.target.closest('.btn-corregir-ing');
            if (btnCorr) {
                const ingId = btnCorr.dataset.ingId;
                const filaBusqueda = document.getElementById('ing-busqueda-' + ingId);
                if (filaBusqueda) {
                    filaBusqueda.classList.toggle('d-none');
                    if (!filaBusqueda.classList.contains('d-none')) {
                        filaBusqueda.querySelector('.inp-buscar-alimento').focus();
                    }
                }
                return;
            }

            // Cancelar corrección
            const btnCancel = e.target.closest('.btn-cancelar-correccion');
            if (btnCancel) {
                const ingId = btnCancel.dataset.ingId;
                document.getElementById('ing-busqueda-' + ingId)?.classList.add('d-none');
            }
        });

        // Autocomplete de búsqueda de alimentos (delegado)
        let _debounceTimer = null;
        listaPrep.addEventListener('input', function (e) {
            const inp = e.target.closest('.inp-buscar-alimento');
            if (!inp) return;

            clearTimeout(_debounceTimer);
            const ingId = inp.dataset.ingId;
            const q = inp.value.trim();
            const lista = document.getElementById('ing-sugerencias-' + ingId);

            if (q.length < 2) {
                lista.innerHTML = '';
                return;
            }

            _debounceTimer = setTimeout(function () {
                fetch(urlBuscarAlimento + '?q=' + encodeURIComponent(q))
                    .then(r => r.json())
                    .then(data => {
                        lista.innerHTML = '';
                        if (!data.resultados.length) {
                            lista.innerHTML = '<div class="list-group-item text-muted small">Sin resultados</div>';
                            return;
                        }
                        const frag = document.createDocumentFragment();
                        data.resultados.forEach(function (al) {
                            const item = document.createElement('button');
                            item.type = 'button';
                            item.className = 'list-group-item list-group-item-action small py-1';
                            item.innerHTML = '<code class="me-2">' + al.codigo + '</code>' + al.nombre_del_alimento;
                            item.addEventListener('click', function () {
                                _aplicarCorreccion(ingId, al.codigo, inp, lista);
                            });
                            frag.appendChild(item);
                        });
                        lista.appendChild(frag);
                    });
            }, 300);
        });
    }

    function _aplicarCorreccion(ingId, codigoIcbf, inp, lista) {
        inp.disabled = true;
        fetch(urlCorregirIng, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({ ingrediente_id: parseInt(ingId), codigo_icbf: codigoIcbf }),
        })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    const fila = document.getElementById('ing-row-' + ingId);
                    // Quitar rojo y badge "No encontrado"
                    fila.classList.remove('table-danger');
                    fila.querySelector('.badge.bg-danger')?.remove();
                    fila.querySelector('.btn-corregir-ing')?.remove();
                    // Actualizar nombre del ingrediente
                    const tdNombre = fila.cells[1];
                    tdNombre.textContent = data.nombre;
                    // Actualizar código mostrado
                    fila.cells[0].querySelector('code').textContent = codigoIcbf;
                    // Ocultar fila de búsqueda
                    document.getElementById('ing-busqueda-' + ingId)?.classList.add('d-none');
                    lista.innerHTML = '';
                } else {
                    alert('Error: ' + data.error);
                    inp.disabled = false;
                }
            });
    }

    // Cascading selector programa → menú destino
    const selPrograma = document.getElementById('sel-programa-destino');
    const selMenu = document.getElementById('sel-menu-destino');
    const btnAprobar = document.getElementById('btn-aprobar');

    if (selPrograma) {
        selPrograma.addEventListener('change', function () {
            const programaId = this.value;
            selMenu.innerHTML = '<option value="">Cargando...</option>';
            selMenu.disabled = true;
            btnAprobar.disabled = true;

            if (!programaId) {
                selMenu.innerHTML = '<option value="">Primero seleccione un programa...</option>';
                return;
            }

            fetch(`${urlMenus}?programa_id=${programaId}&modalidad_id=${modalidadId}`)
                .then(r => r.json())
                .then(data => {
                    selMenu.innerHTML = '<option value="">Seleccione menú...</option>';
                    if (!data.menus.length) {
                        selMenu.innerHTML = '<option value="">Sin menús disponibles para esta modalidad</option>';
                        return;
                    }
                    const fragment = document.createDocumentFragment();
                    data.menus.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m.id_menu;
                        opt.textContent = `Menú ${m.menu}`;
                        fragment.appendChild(opt);
                    });
                    selMenu.appendChild(fragment);
                    selMenu.disabled = false;
                });
        });

        selMenu.addEventListener('change', function () {
            btnAprobar.disabled = !this.value;
        });
    }

    // Aprobar
    if (btnAprobar) {
        btnAprobar.addEventListener('click', function () {
            // Usa menú pre-asignado (lote) o el seleccionado manualmente (flujo unitario)
            const menuId = menuIdPreasignado || (selMenu ? selMenu.value : null);
            if (!menuId) return;

            const menuTexto = menuIdPreasignado
                ? 'menú pre-asignado'
                : (selMenu ? selMenu.options[selMenu.selectedIndex].text : '');
            if (!confirm(`¿Confirmas que revisaste el borrador y deseas importar las preparaciones al "${menuTexto}"?`)) return;

            this.disabled = true;
            this.textContent = 'Importando...';

            fetch(`/agente/api/aprobar/${generacionId}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify({ menu_id: parseInt(menuId) }),
            })
                .then(r => r.json())
                .then(data => {
                    const box = document.getElementById('alert-resultado');
                    if (data.ok) {
                        box.className = 'alert alert-success mt-3';
                        box.innerHTML = `<strong>✅ Importado correctamente.</strong> Se crearon <strong>${data.preparaciones_creadas}</strong> preparaciones en el menú.` +
                            (data.advertencias && data.advertencias.length
                                ? '<ul class="mt-2 mb-0">' + data.advertencias.map(a => `<li>${a}</li>`).join('') + '</ul>'
                                : '');
                        box.classList.remove('d-none');
                        document.getElementById('btn-aprobar').classList.add('d-none');
                        document.getElementById('btn-descartar').classList.add('d-none');
                        document.querySelector('.card.border-success').classList.add('d-none');
                    } else {
                        box.className = 'alert alert-danger mt-3';
                        box.textContent = 'Error: ' + data.error;
                        box.classList.remove('d-none');
                        btnAprobar.disabled = false;
                        btnAprobar.textContent = '✅ Aprobar e importar al menú seleccionado';
                    }
                });
        });
    }

    // Descartar
    const btnDescartar = document.getElementById('btn-descartar');
    if (btnDescartar) {
        btnDescartar.addEventListener('click', function () {
            if (!confirm('¿Descartar este borrador? Esta acción no se puede deshacer.')) return;
            fetch(urlDescartar, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
            })
                .then(r => r.json())
                .then(data => {
                    if (data.ok) window.location.href = urlIndex;
                });
        });
    }
})();
