(function () {
    const root = document.getElementById('prepEditorRoot');
    if (!root) return;

    const menuId = root.getAttribute('data-menu-id');
    const tbody = document.getElementById('tablaPreparacionesBody');
    const btnAgregar = document.getElementById('btnAgregarFila');
    const btnGuardar = document.getElementById('btnGuardarEditor');

    const filasIniciales = JSON.parse(document.getElementById('filas-data').textContent || '[]');
    const ingredientes = JSON.parse(document.getElementById('ingredientes-data').textContent || '[]');
    const preparaciones = JSON.parse(document.getElementById('preparaciones-data').textContent || '[]');

    let rows = filasIniciales.map((f, i) => ({
        key: `row-${i}-${Date.now()}`,
        existing: true,
        id_preparacion: String(f.id_preparacion || ''),
        id_ingrediente: String(f.id_ingrediente || ''),
        grupo: f.grupo || '',
        minimo: f.minimo,
        maximo: f.maximo,
        gramaje: f.gramaje ?? '',
    }));

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function optionHtml(items, valueKey, labelKey, selected) {
        const opts = ['<option value="">Seleccione...</option>'];
        items.forEach(item => {
            const val = String(item[valueKey]);
            const label = item[labelKey];
            const sel = val === String(selected) ? 'selected' : '';
            opts.push(`<option value="${val}" ${sel}>${label}</option>`);
        });
        return opts.join('');
    }

    function rangoText(row) {
        if (row.minimo == null && row.maximo == null) return 'Sin rango';
        const min = row.minimo == null ? '-' : row.minimo;
        const max = row.maximo == null ? '-' : row.maximo;
        return `${min} - ${max}`;
    }

    function estado(row) {
        const g = row.gramaje === '' || row.gramaje == null ? null : Number(row.gramaje);
        if (g == null || Number.isNaN(g)) return { text: 'Sin dato', ok: false };
        if (row.minimo != null && g < Number(row.minimo)) return { text: 'Bajo', ok: false };
        if (row.maximo != null && g > Number(row.maximo)) return { text: 'Alto', ok: false };
        return { text: 'OK', ok: true };
    }

    async function refrescarRango(row) {
        if (!row.id_preparacion || !row.id_ingrediente) {
            row.grupo = '';
            row.minimo = null;
            row.maximo = null;
            return;
        }
        const qs = new URLSearchParams({
            id_preparacion: row.id_preparacion,
            id_ingrediente: row.id_ingrediente,
        });
        const resp = await fetch(`/nutricion/api/menus/${menuId}/rango-ingrediente/?${qs.toString()}`);
        const data = await resp.json();
        if (data.success) {
            row.grupo = data.grupo_nombre || 'SIN GRUPO';
            row.minimo = data.minimo;
            row.maximo = data.maximo;
        }
    }

    function render() {
        tbody.innerHTML = rows.map((row, index) => {
            const est = estado(row);
            return `
                <tr data-key="${row.key}">
                    <td>
                        <select class="form-control form-control-sm js-preparacion">
                            ${optionHtml(preparaciones, 'id_preparacion', 'preparacion', row.id_preparacion)}
                        </select>
                    </td>
                    <td>
                        <select class="form-control form-control-sm js-ingrediente">
                            ${optionHtml(ingredientes, 'codigo', 'nombre_del_alimento', row.id_ingrediente)}
                        </select>
                    </td>
                    <td class="grupo-cell">${row.grupo || '—'}</td>
                    <td class="rango-cell">${rangoText(row)}</td>
                    <td>
                        <input type="number" step="0.01" min="0" class="form-control form-control-sm input-gramaje js-gramaje" value="${row.gramaje}">
                    </td>
                    <td class="estado-cell ${est.ok ? 'estado-ok' : 'estado-error'}">${est.text}</td>
                    <td>
                        <button type="button" class="btn btn-danger btn-sm js-eliminar" data-index="${index}">Eliminar</button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    tbody.addEventListener('change', async (e) => {
        const tr = e.target.closest('tr');
        if (!tr) return;
        const key = tr.getAttribute('data-key');
        const row = rows.find(r => r.key === key);
        if (!row) return;

        if (e.target.classList.contains('js-preparacion')) {
            row.id_preparacion = e.target.value;
            await refrescarRango(row);
        }
        if (e.target.classList.contains('js-ingrediente')) {
            row.id_ingrediente = e.target.value;
            await refrescarRango(row);
        }
        if (e.target.classList.contains('js-gramaje')) {
            row.gramaje = e.target.value;
        }
        render();
    });

    tbody.addEventListener('click', async (e) => {
        if (!e.target.classList.contains('js-eliminar')) return;
        const idx = Number(e.target.getAttribute('data-index'));
        const row = rows[idx];
        if (!row) return;

        if (row.existing && row.id_preparacion && row.id_ingrediente) {
            const resp = await fetch(`/nutricion/api/preparaciones/${row.id_preparacion}/ingredientes/${row.id_ingrediente}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            const data = await resp.json();
            if (!data.success) {
                alert(data.error || 'No se pudo eliminar');
                return;
            }
        }
        rows.splice(idx, 1);
        render();
    });

    btnAgregar.addEventListener('click', () => {
        rows.push({
            key: `row-new-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
            existing: false,
            id_preparacion: preparaciones[0] ? String(preparaciones[0].id_preparacion) : '',
            id_ingrediente: '',
            grupo: '',
            minimo: null,
            maximo: null,
            gramaje: '',
        });
        render();
    });

    btnGuardar.addEventListener('click', async () => {
        const payload = rows
            .filter(r => r.id_preparacion && r.id_ingrediente)
            .map(r => ({
                id_preparacion: Number(r.id_preparacion),
                id_ingrediente: r.id_ingrediente,
                gramaje: r.gramaje === '' ? null : r.gramaje,
            }));

        const resp = await fetch(`/nutricion/api/menus/${menuId}/guardar-preparaciones-editor/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ filas: payload }),
        });
        const data = await resp.json();
        if (!resp.ok || !data.success) {
            const msg = data.errores ? data.errores.join('\n') : (data.error || 'Error al guardar');
            alert(msg);
            return;
        }
        rows = rows.map(r => ({ ...r, existing: true }));
        render();
        alert(`Guardado exitoso (${data.guardadas} filas).`);
    });

    render();
})();

