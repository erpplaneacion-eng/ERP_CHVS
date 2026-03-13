(function () {
    const cfg = window.BORRADOR_CONFIG;
    if (!cfg) return;

    const { generacionId, modalidadId, csrf, urlMenus, urlEliminarIng, urlDescartar, urlIndex } = cfg;

    // Eliminar ingrediente
    const listaPrep = document.getElementById('lista-preparaciones');
    if (listaPrep) {
        listaPrep.addEventListener('click', function (e) {
            const btn = e.target.closest('.btn-eliminar-ing');
            if (!btn) return;
            const ingId = btn.dataset.ingId;
            if (!confirm('¿Eliminar este ingrediente del borrador?')) return;
            btn.disabled = true;

            fetch(urlEliminarIng, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify({ ingrediente_id: parseInt(ingId) }),
            })
                .then(r => r.json())
                .then(data => {
                    if (data.ok) {
                        document.getElementById('ing-row-' + ingId).remove();
                    } else {
                        alert('Error: ' + data.error);
                        btn.disabled = false;
                    }
                });
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
            const menuId = selMenu ? selMenu.value : null;
            if (!menuId) return;

            const menuTexto = selMenu.options[selMenu.selectedIndex].text;
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
