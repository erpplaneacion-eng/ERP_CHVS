/**
 * Match ICBF → Compras
 * Granularidad: (ingrediente_icbf, programa, menú) → 1 producto de compras.
 *
 * Flujos:
 *  - Asignación masiva: mismo producto a todos los menús del ingrediente.
 *  - Override individual: cambia el producto de un menú específico.
 */

// =================== ESTADO ===================
let _matchCodigoICBF = null;
let _matchMenuId     = null;
let _matchMenuNum    = null;
let _bulkCodigoICBF  = null;
let _editandoCodigo  = null; // catálogo

// =================== INIT ===================
document.addEventListener('DOMContentLoaded', () => {
    _initFiltros();
    _initProgresoBarra();
    _initEventDelegation();
    _initModalMatch();
    _initModalBulk();
    _initModalCatalogo();
    _initSelect2Match();
    _initSelect2Bulk();
});

// =================== BARRA DE PROGRESO INICIAL ===================
function _initProgresoBarra() {
    const fill = document.querySelector('.progreso-fill');
    if (fill) fill.style.width = (fill.dataset.pct || 0) + '%';
}

// =================== FILTROS ===================
function _initFiltros() {
    const selMun    = document.getElementById('filtroMunicipio');
    const selProg   = document.getElementById('filtroPrograma');
    const btnCargar = document.getElementById('btnCargarIngredientes');
    if (!selMun) return;

    selMun.addEventListener('change', () => {
        const munId = selMun.value;
        selProg.innerHTML = '<option value="">Cargando...</option>';
        selProg.disabled = true;
        btnCargar.disabled = true;
        if (!munId) {
            selProg.innerHTML = '<option value="">Primero seleccione un municipio...</option>';
            return;
        }
        fetch(`/nutricion/api/programas-por-municipio/?municipio_id=${munId}`)
            .then(r => r.json())
            .then(data => {
                const programas = data.programas || [];
                if (!programas.length) {
                    selProg.innerHTML = '<option value="">No hay programas activos</option>';
                    return;
                }
                selProg.innerHTML = '';
                programas.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.programa;
                    selProg.appendChild(opt);
                });
                selProg.disabled = false;
                btnCargar.disabled = false;
            })
            .catch(() => {
                selProg.innerHTML = '<option value="">Error al cargar programas</option>';
            });
    });

    selProg.addEventListener('change', () => { btnCargar.disabled = !selProg.value; });
}

// =================== EVENT DELEGATION ===================
function _initEventDelegation() {
    document.addEventListener('click', e => {
        // Toggle acordeón (ignorar si el clic fue en un botón interno)
        const toggleTarget = e.target.closest('[data-toggle-card]');
        if (toggleTarget && !e.target.closest('button')) {
            _toggleCard(toggleTarget.dataset.toggleCard);
            return;
        }

        // Asignar a todos (bulk)
        const btnTodos = e.target.closest('[data-asignar-todos]');
        if (btnTodos) {
            e.stopPropagation();
            _abrirModalBulk(btnTodos.dataset.asignarTodos, btnTodos.dataset.nombreIcbf);
            return;
        }

        // Asignar/cambiar en un menú individual
        const btnMenu = e.target.closest('[data-asignar-menu]');
        if (btnMenu) {
            e.stopPropagation();
            _abrirModalMatch(
                btnMenu.dataset.codigoIcbf,
                btnMenu.dataset.nombreIcbf,
                parseInt(btnMenu.dataset.asignarMenu, 10),
                btnMenu.dataset.menuNum,
            );
            return;
        }

        // Quitar match de un menú
        const btnQuitar = e.target.closest('[data-match-id]');
        if (btnQuitar && btnQuitar.classList.contains('btn-quitar-menu')) {
            _quitarMatch(
                parseInt(btnQuitar.dataset.matchId, 10),
                btnQuitar.dataset.codigoIcbf,
                parseInt(btnQuitar.dataset.menuId, 10),
                btnQuitar.dataset.nombreIcbf,
                btnQuitar.dataset.nombreSiesa,
            );
            return;
        }

        // Catálogo: editar / eliminar (delegación sobre #catalogoLista)
        const btnEdit = e.target.closest('.btn-cat-edit');
        if (btnEdit) {
            const item = btnEdit.closest('.catalogo-item');
            _abrirFormProducto(item.dataset.codigo, item.dataset.nombre,
                item.dataset.presentacion, item.dataset.unidad, item.dataset.gramos);
            return;
        }
        const btnDel = e.target.closest('.btn-cat-del');
        if (btnDel) {
            const item = btnDel.closest('.catalogo-item');
            _eliminarProducto(item.dataset.codigo, item.dataset.nombre);
        }
    });
}

// =================== ACORDEÓN ===================
function _toggleCard(codigoICBF) {
    const body = document.getElementById(`body-${codigoICBF}`);
    const icon = document.getElementById(`toggle-${codigoICBF}`);
    const open = body.classList.toggle('card-body-open');
    icon.style.transform = open ? 'rotate(180deg)' : '';
}

// =================== MODAL MATCH (individual) ===================
function _initModalMatch() {
    document.getElementById('btnCerrarModalMatch')?.addEventListener('click', _cerrarModalMatch);
    document.getElementById('btnCancelarMatch')?.addEventListener('click', _cerrarModalMatch);
    document.getElementById('btnGuardarMatch')?.addEventListener('click', _guardarMatch);
    window.addEventListener('click', e => { if (e.target.id === 'modalMatch') _cerrarModalMatch(); });
}

function _abrirModalMatch(codigoICBF, nombreICBF, menuId, menuNum) {
    _matchCodigoICBF = codigoICBF;
    _matchMenuId     = menuId;
    _matchMenuNum    = menuNum;

    document.getElementById('matchNombreICBF').textContent = nombreICBF;
    document.getElementById('matchNombreMenu').textContent = `Menú ${menuNum}`;
    document.getElementById('detalleProd').classList.add('hidden');
    $('#selectProductoSiesa').val(null).trigger('change');
    document.getElementById('modalMatch').style.display = 'flex';
}

function _cerrarModalMatch() {
    document.getElementById('modalMatch').style.display = 'none';
    _matchCodigoICBF = _matchMenuId = _matchMenuNum = null;
}

function _initSelect2Match() {
    if (!document.getElementById('selectProductoSiesa')) return;
    $('#selectProductoSiesa').select2({
        dropdownParent: document.getElementById('modalMatch'),
        placeholder: 'Buscar producto...',
        minimumInputLength: 0,
        ajax: {
            url: '/nutricion/api/match/productos/',
            dataType: 'json',
            delay: 250,
            data: params => ({ q: params.term || '' }),
            processResults: data => ({
                results: data.productos.map(p => ({
                    id: p.id, text: p.texto,
                    presentacion: p.presentacion, unidad_medida: p.unidad_medida,
                    contenido_gramos: p.contenido_gramos,
                }))
            }),
            cache: true,
        }
    }).on('select2:select', e => {
        const d = e.params.data;
        _mostrarDetalle('detalleProd', 'detPresentacion', 'detUnidad', 'detContenido',
            d.presentacion, d.unidad_medida, d.contenido_gramos);
    });
}

async function _guardarMatch() {
    const codigoSiesa = $('#selectProductoSiesa').val();
    if (!codigoSiesa) {
        Swal.fire({ icon: 'warning', title: 'Seleccione un producto' });
        return;
    }
    const btn = document.getElementById('btnGuardarMatch');
    btn.disabled = true;
    try {
        const resp = await fetch('/nutricion/api/match/guardar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _getCookie('csrftoken') },
            body: JSON.stringify({
                programa_id: PROGRAMA_ID,
                codigo_icbf: _matchCodigoICBF,
                menu_id:     _matchMenuId,
                codigo_siesa: codigoSiesa,
            }),
        });
        const data = await resp.json();
        if (data.success) {
            const codigo = _matchCodigoICBF;
            _cerrarModalMatch();
            _actualizarFilaMenu(codigo, data.match);
            _actualizarEstadoTarjeta(codigo);
            _actualizarContadores();
            _toast('Producto asignado', 'success');
        } else {
            Swal.fire({ icon: 'error', title: 'Error', text: data.error });
        }
    } finally {
        btn.disabled = false;
    }
}

// =================== MODAL BULK ===================
function _initModalBulk() {
    document.getElementById('btnCerrarModalBulk')?.addEventListener('click', _cerrarModalBulk);
    document.getElementById('btnCancelarBulk')?.addEventListener('click', _cerrarModalBulk);
    document.getElementById('btnGuardarBulk')?.addEventListener('click', _guardarBulk);
    window.addEventListener('click', e => { if (e.target.id === 'modalBulk') _cerrarModalBulk(); });
}

function _abrirModalBulk(codigoICBF, nombreICBF) {
    _bulkCodigoICBF = codigoICBF;
    document.getElementById('bulkNombreICBF').textContent = nombreICBF;
    document.getElementById('detalleProdBulk').classList.add('hidden');
    $('#selectProductoBulk').val(null).trigger('change');
    // Restablecer opción por defecto
    document.querySelector('input[name="modoAsignacion"][value="solo_vacios"]').checked = true;
    document.getElementById('modalBulk').style.display = 'flex';
}

function _cerrarModalBulk() {
    document.getElementById('modalBulk').style.display = 'none';
    _bulkCodigoICBF = null;
}

function _initSelect2Bulk() {
    if (!document.getElementById('selectProductoBulk')) return;
    $('#selectProductoBulk').select2({
        dropdownParent: document.getElementById('modalBulk'),
        placeholder: 'Buscar producto...',
        minimumInputLength: 0,
        ajax: {
            url: '/nutricion/api/match/productos/',
            dataType: 'json',
            delay: 250,
            data: params => ({ q: params.term || '' }),
            processResults: data => ({
                results: data.productos.map(p => ({
                    id: p.id, text: p.texto,
                    presentacion: p.presentacion,
                    contenido_gramos: p.contenido_gramos,
                }))
            }),
            cache: true,
        }
    }).on('select2:select', e => {
        const d = e.params.data;
        _mostrarDetalle('detalleProdBulk', 'detPresBulk', null, 'detGrBulk',
            d.presentacion, null, d.contenido_gramos);
    });
}

async function _guardarBulk() {
    const codigoSiesa = $('#selectProductoBulk').val();
    if (!codigoSiesa) {
        Swal.fire({ icon: 'warning', title: 'Seleccione un producto' });
        return;
    }
    const soloVacios = document.querySelector('input[name="modoAsignacion"]:checked').value === 'solo_vacios';
    const btn = document.getElementById('btnGuardarBulk');
    btn.disabled = true;

    try {
        const resp = await fetch('/nutricion/api/match/guardar/bulk/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _getCookie('csrftoken') },
            body: JSON.stringify({
                programa_id:      PROGRAMA_ID,
                codigo_icbf:      _bulkCodigoICBF,
                codigo_siesa:     codigoSiesa,
                solo_sin_asignar: soloVacios,
            }),
        });
        const data = await resp.json();

        if (data.success) {
            const codigo = _bulkCodigoICBF;
            _cerrarModalBulk();
            if (data.matches && data.matches.length > 0) {
                data.matches.forEach(match => _actualizarFilaMenu(codigo, match));
                _actualizarEstadoTarjeta(codigo);
                _actualizarContadores();
            }
            const msg = data.creados + data.actualizados === 0
                ? data.mensaje
                : `${data.creados} asignados, ${data.actualizados} actualizados`;
            _toast(msg, 'success');
        } else {
            Swal.fire({ icon: 'error', title: 'Error', text: data.error });
        }
    } finally {
        btn.disabled = false;
    }
}

// =================== FILA DE MENÚ ===================
function _actualizarFilaMenu(codigoICBF, match) {
    const tr = document.getElementById(`tr-${codigoICBF}-${match.menu_id}`);
    if (!tr) return;

    // Actualizar clase de fila
    tr.classList.remove('fila-vacia');
    tr.classList.add('fila-asignada');

    // Celda producto
    const tdProd = document.getElementById(`td-prod-${codigoICBF}-${match.menu_id}`);
    if (tdProd) {
        const detalle = [
            match.presentacion,
            match.contenido_gramos ? `${parseFloat(match.contenido_gramos).toFixed(0)}g` : ''
        ].filter(Boolean).join(' · ');

        tdProd.innerHTML = `<span class="prod-nombre">${match.nombre_siesa}</span>` +
            (detalle ? `<span class="prod-detalle">${detalle}</span>` : '');
    }

    // Botones de acción: reemplazar con los correctos (editar + quitar)
    const colAccion = tr.querySelector('.col-accion');
    if (colAccion) {
        colAccion.innerHTML = '';

        const btnEdit = document.createElement('button');
        btnEdit.className = 'btn-asignar-menu';
        btnEdit.title = 'Cambiar producto';
        btnEdit.dataset.asignarMenu  = match.menu_id;
        btnEdit.dataset.codigoIcbf   = codigoICBF;
        btnEdit.dataset.nombreIcbf   = tr.dataset.nombreIcbf || '';
        btnEdit.dataset.menuNum      = match.menu_num;
        btnEdit.innerHTML = '<i class="fas fa-edit"></i>';
        colAccion.appendChild(btnEdit);

        const btnQuitar = document.createElement('button');
        btnQuitar.className = 'btn-quitar-menu';
        btnQuitar.title = 'Quitar este producto';
        btnQuitar.dataset.matchId    = match.id;
        btnQuitar.dataset.codigoIcbf = codigoICBF;
        btnQuitar.dataset.menuId     = match.menu_id;
        btnQuitar.dataset.nombreIcbf  = tr.dataset.nombreIcbf || '';
        btnQuitar.dataset.nombreSiesa = match.nombre_siesa;
        btnQuitar.innerHTML = '<i class="fas fa-times"></i>';
        colAccion.appendChild(btnQuitar);
    }
}

async function _quitarMatch(matchId, codigoICBF, menuId, nombreICBF, nombreSiesa) {
    const conf = await Swal.fire({
        title: '¿Quitar el producto?',
        html: `Se eliminará <strong>${nombreSiesa}</strong> del Menú ${menuId} para <em>${nombreICBF}</em>.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, quitar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#e74c3c',
    });
    if (!conf.isConfirmed) return;

    const resp = await fetch(`/nutricion/api/match/${matchId}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': _getCookie('csrftoken') },
    });
    const data = await resp.json();

    if (data.success) {
        const tr = document.getElementById(`tr-${codigoICBF}-${menuId}`);
        if (tr) {
            tr.classList.remove('fila-asignada');
            tr.classList.add('fila-vacia');

            const tdProd = document.getElementById(`td-prod-${codigoICBF}-${menuId}`);
            if (tdProd) {
                tdProd.innerHTML = '<span class="prod-vacio"><i class="fas fa-minus"></i> Sin asignar</span>';
            }

            const colAccion = tr.querySelector('.col-accion');
            if (colAccion) {
                colAccion.innerHTML = '';
                const btnAsignar = document.createElement('button');
                btnAsignar.className = 'btn-asignar-menu';
                btnAsignar.title = 'Asignar producto';
                btnAsignar.dataset.asignarMenu = menuId;
                btnAsignar.dataset.codigoIcbf  = codigoICBF;
                btnAsignar.dataset.nombreIcbf  = tr.dataset.nombreIcbf || '';
                btnAsignar.dataset.menuNum     = tr.querySelector('.menu-badge')?.textContent || '';
                btnAsignar.innerHTML = '<i class="fas fa-plus"></i>';
                colAccion.appendChild(btnAsignar);
            }
        }
        _actualizarEstadoTarjeta(codigoICBF);
        _actualizarContadores();
        _toast('Producto quitado', 'info');
    } else {
        Swal.fire({ icon: 'error', title: 'Error', text: data.error });
    }
}

// =================== ESTADO TARJETA ===================
function _actualizarEstadoTarjeta(codigoICBF) {
    const tbody = document.getElementById(`tbody-${codigoICBF}`);
    if (!tbody) return;

    const total     = tbody.querySelectorAll('tr').length;
    const asignados = tbody.querySelectorAll('tr.fila-asignada').length;
    const completo  = asignados === total;
    const parcial   = asignados > 0 && !completo;

    const card = document.getElementById(`card-${codigoICBF}`);
    card.classList.toggle('card-completo', completo);
    card.classList.toggle('card-parcial', parcial);
    card.classList.toggle('card-pendiente', asignados === 0);

    const sem = document.getElementById(`sem-${codigoICBF}`);
    sem.className = `semaforo ${completo ? 'semaforo-verde' : parcial ? 'semaforo-amarillo' : 'semaforo-rojo'}`;

    const badge = document.getElementById(`badge-${codigoICBF}`);
    badge.textContent = `${asignados}/${total}`;
    badge.className = `badge-progreso ${completo ? 'badge-completo' : parcial ? 'badge-parcial' : 'badge-sin-match'}`;
}

function _actualizarContadores() {
    const total    = document.querySelectorAll('.ingrediente-card').length;
    const completos = document.querySelectorAll('.ingrediente-card.card-completo').length;
    const incompletos = total - completos;

    document.querySelector('.stat-total .stat-num').textContent = total;
    document.querySelector('.stat-ok .stat-num').textContent = completos;
    document.querySelector('.stat-pendiente .stat-num').textContent = incompletos;

    if (total > 0) {
        const pct = Math.round((completos / total) * 100);
        document.querySelector('.progreso-fill').style.width = pct + '%';
        document.querySelector('.progreso-pct').textContent = pct + '%';
    }
}

// =================== MODAL CATÁLOGO ===================
function _initModalCatalogo() {
    document.getElementById('linkCatalogo')?.addEventListener('click', e => { e.preventDefault(); _abrirCatalogo(); });
    document.getElementById('btnCerrarCatalogo')?.addEventListener('click', _cerrarCatalogo);
    document.getElementById('btnNuevoProducto')?.addEventListener('click', () => _abrirFormProducto(null));
    document.getElementById('btnGuardarProducto')?.addEventListener('click', _guardarProducto);
    document.getElementById('btnCancelarProducto')?.addEventListener('click', _cancelarFormProducto);

    const buscar = document.getElementById('buscarCatalogo');
    if (buscar) {
        let t;
        buscar.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => _cargarCatalogo(buscar.value), 300); });
    }
    window.addEventListener('click', e => { if (e.target.id === 'modalCatalogo') _cerrarCatalogo(); });
}

function _abrirCatalogo() {
    document.getElementById('modalCatalogo').style.display = 'flex';
    document.getElementById('formProductoContainer').classList.add('hidden');
    _cargarCatalogo();
}

function _cerrarCatalogo() { document.getElementById('modalCatalogo').style.display = 'none'; }

async function _cargarCatalogo(q = '') {
    const resp = await fetch(`/nutricion/api/match/catalogo/?q=${encodeURIComponent(q)}`);
    const data = await resp.json();
    const lista = document.getElementById('catalogoLista');
    if (!data.productos.length) {
        lista.innerHTML = '<p class="catalogo-vacio"><i class="fas fa-box-open"></i> No hay productos registrados.</p>';
        return;
    }
    const frag = document.createDocumentFragment();
    data.productos.forEach(p => {
        const div = document.createElement('div');
        div.className = 'catalogo-item';
        div.dataset.codigo = p.codigo; div.dataset.nombre = p.nombre;
        div.dataset.presentacion = p.presentacion || '';
        div.dataset.unidad = p.unidad_medida || ''; div.dataset.gramos = p.contenido_gramos || '';

        const info = document.createElement('div');
        info.className = 'cat-info';
        info.innerHTML = `<span class="cat-nombre">${p.nombre}</span>
            <span class="cat-codigo">${p.codigo}</span>
            ${p.presentacion ? `<span class="cat-pres">${p.presentacion}${p.contenido_gramos ? ' — ' + p.contenido_gramos + 'g' : ''}</span>` : ''}`;

        const acc = document.createElement('div');
        acc.className = 'cat-acciones';
        const be = document.createElement('button'); be.className = 'btn-cat-edit'; be.innerHTML = '<i class="fas fa-edit"></i>';
        const bd = document.createElement('button'); bd.className = 'btn-cat-del';  bd.innerHTML = '<i class="fas fa-trash"></i>';
        acc.appendChild(be); acc.appendChild(bd);
        div.appendChild(info); div.appendChild(acc);
        frag.appendChild(div);
    });
    lista.innerHTML = '';
    lista.appendChild(frag);
}

function _abrirFormProducto(codigo, nombre = '', presentacion = '', unidad = '', gramos = '') {
    _editandoCodigo = codigo;
    document.getElementById('formProductoTitulo').textContent = codigo ? 'Editar Producto' : 'Nuevo Producto';
    document.getElementById('fpCodigo').value = codigo || '';
    document.getElementById('fpCodigo').disabled = !!codigo;
    document.getElementById('fpNombre').value = nombre;
    document.getElementById('fpPresentacion').value = presentacion;
    document.getElementById('fpUnidad').value = unidad;
    document.getElementById('fpGramos').value = gramos;
    document.getElementById('formProductoContainer').classList.remove('hidden');
    document.getElementById('fpNombre').focus();
}

function _cancelarFormProducto() {
    document.getElementById('formProductoContainer').classList.add('hidden');
    _editandoCodigo = null;
}

async function _guardarProducto() {
    const codigo = document.getElementById('fpCodigo').value.trim();
    const nombre = document.getElementById('fpNombre').value.trim();
    if (!nombre) { _toast('El nombre es obligatorio', 'error'); return; }
    const body = { codigo, nombre,
        presentacion:    document.getElementById('fpPresentacion').value.trim(),
        unidad_medida:   document.getElementById('fpUnidad').value.trim(),
        contenido_gramos: document.getElementById('fpGramos').value || null,
    };
    const url    = _editandoCodigo ? `/nutricion/api/match/catalogo/${encodeURIComponent(_editandoCodigo)}/` : '/nutricion/api/match/catalogo/';
    const method = _editandoCodigo ? 'PUT' : 'POST';
    if (!_editandoCodigo && !codigo) { _toast('El código es obligatorio', 'error'); return; }

    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _getCookie('csrftoken') },
        body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (data.success || data.producto) {
        const fueEdicion = !!_editandoCodigo;
        _cancelarFormProducto();
        _cargarCatalogo(document.getElementById('buscarCatalogo').value);
        _toast(fueEdicion ? 'Producto actualizado' : 'Producto creado', 'success');
    } else {
        Swal.fire({ icon: 'error', title: 'Error', text: data.error });
    }
}

async function _eliminarProducto(codigo, nombre) {
    const conf = await Swal.fire({
        title: '¿Eliminar producto?',
        html: `<strong>${nombre}</strong><br><small>Si tiene matches activos no se puede eliminar.</small>`,
        icon: 'warning', showCancelButton: true,
        confirmButtonText: 'Eliminar', cancelButtonText: 'Cancelar', confirmButtonColor: '#e74c3c',
    });
    if (!conf.isConfirmed) return;
    const resp = await fetch(`/nutricion/api/match/catalogo/${encodeURIComponent(codigo)}/`, {
        method: 'DELETE', headers: { 'X-CSRFToken': _getCookie('csrftoken') },
    });
    const data = await resp.json();
    if (data.success) {
        _cargarCatalogo(document.getElementById('buscarCatalogo').value);
        _toast('Producto eliminado', 'info');
    } else {
        Swal.fire({ icon: 'error', title: 'No se puede eliminar', text: data.error });
    }
}

// =================== UTILIDADES ===================
function _mostrarDetalle(divId, presId, unidId, grId, pres, unid, gramos) {
    const div = document.getElementById(divId);
    if (!pres && !unid && !gramos) { div.classList.add('hidden'); return; }
    if (presId) document.getElementById(presId).textContent = pres || '—';
    if (unidId) document.getElementById(unidId).textContent = unid || '—';
    if (grId)   document.getElementById(grId).textContent   = gramos ? `${gramos} g` : '—';
    div.classList.remove('hidden');
}

function _toast(mensaje, tipo = 'success') {
    Swal.fire({ toast: true, position: 'top-end', icon: tipo, title: mensaje,
        showConfirmButton: false, timer: 2500, timerProgressBar: true });
}

function _getCookie(name) {
    for (const cookie of document.cookie.split(';')) {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
    }
    return null;
}
