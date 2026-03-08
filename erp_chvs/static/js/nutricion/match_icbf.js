/**
 * Match ICBF → Compras
 * Gestiona el modal de asignación, el semáforo y el catálogo simulacro.
 */

// =================== ESTADO ===================
let codigoICBFActual = null;
let editandoCodigo = null; // Para el form del catálogo

// =================== FILTROS ===================
document.addEventListener('DOMContentLoaded', () => {
    const selectMunicipio = document.getElementById('filtroMunicipio');
    const selectPrograma  = document.getElementById('filtroPrograma');
    const btnCargar       = document.getElementById('btnCargarIngredientes');

    selectMunicipio.addEventListener('change', () => {
        const munId = selectMunicipio.value;
        selectPrograma.innerHTML = '<option value="">Cargando...</option>';
        selectPrograma.disabled = true;
        btnCargar.disabled = true;

        if (!munId) {
            selectPrograma.innerHTML = '<option value="">Primero seleccione un municipio...</option>';
            return;
        }

        fetch(`/nutricion/api/programas-por-municipio/?municipio_id=${munId}`)
            .then(r => r.json())
            .then(data => {
                const programas = data.programas || [];

                if (programas.length === 0) {
                    selectPrograma.innerHTML = '<option value="">No hay programas activos</option>';
                    selectPrograma.disabled = true;
                    btnCargar.disabled = true;
                    return;
                }

                // Poblar opciones
                selectPrograma.innerHTML = '';
                programas.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.programa;
                    selectPrograma.appendChild(opt);
                });

                // Siempre auto-seleccionar el primer programa y habilitar el botón
                selectPrograma.disabled = false;
                btnCargar.disabled = false;
            })
            .catch(() => {
                selectPrograma.innerHTML = '<option value="">Error al cargar programas</option>';
                selectPrograma.disabled = true;
                btnCargar.disabled = true;
            });
    });

    selectPrograma.addEventListener('change', () => {
        btnCargar.disabled = !selectPrograma.value;
    });

    // Select2 para el selector de producto Siesa en el modal
    inicializarSelect2();
});

// =================== MODAL MATCH ===================

function abrirModalMatch(codigoICBF, nombreICBF, codigoSiesaActual, nombreSiesaActual) {
    codigoICBFActual = codigoICBF;

    document.getElementById('matchNombreICBF').textContent = nombreICBF;
    document.getElementById('detalleProd').style.display = 'none';

    // Resetear select2
    const select = $('#selectProductoSiesa');
    select.val(null).trigger('change');

    // Si ya tiene match, precargar la opción
    if (codigoSiesaActual) {
        const opcion = new Option(nombreSiesaActual, codigoSiesaActual, true, true);
        select.append(opcion).trigger('change');
        // Cargar detalle del producto actual
        cargarDetalleProd(codigoSiesaActual);
    }

    document.getElementById('modalMatch').style.display = 'flex';
}

function cerrarModalMatch() {
    document.getElementById('modalMatch').style.display = 'none';
    codigoICBFActual = null;
}

function inicializarSelect2() {
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
                    id: p.id,
                    text: p.texto,
                    presentacion: p.presentacion,
                    unidad_medida: p.unidad_medida,
                    contenido_gramos: p.contenido_gramos,
                }))
            }),
            cache: true
        }
    }).on('select2:select', e => {
        const d = e.params.data;
        mostrarDetalleProd(d.presentacion, d.unidad_medida, d.contenido_gramos);
    });
}

function cargarDetalleProd(codigo) {
    fetch(`/nutricion/api/match/productos/?q=${encodeURIComponent(codigo)}`)
        .then(r => r.json())
        .then(data => {
            const prod = (data.productos || []).find(p => p.id === codigo);
            if (prod) mostrarDetalleProd(prod.presentacion, prod.unidad_medida, prod.contenido_gramos);
        });
}

function mostrarDetalleProd(presentacion, unidad, gramos) {
    const div = document.getElementById('detalleProd');
    if (!presentacion && !unidad && !gramos) {
        div.style.display = 'none';
        return;
    }
    document.getElementById('detPresentacion').textContent = presentacion || '—';
    document.getElementById('detUnidad').textContent = unidad || '—';
    document.getElementById('detContenido').textContent = gramos ? `${gramos} g` : '—';
    div.style.display = 'block';
}

async function guardarMatch() {
    const codigoSiesa = $('#selectProductoSiesa').val();
    if (!codigoSiesa) {
        Swal.fire({ icon: 'warning', title: 'Seleccione un producto', text: 'Debe elegir un producto del catálogo.' });
        return;
    }

    const btn = document.getElementById('btnGuardarMatch');
    btn.disabled = true;

    try {
        const resp = await fetch('/nutricion/api/match/guardar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({
                programa_id: PROGRAMA_ID,
                codigo_icbf: codigoICBFActual,
                codigo_siesa: codigoSiesa,
            })
        });
        const data = await resp.json();

        if (data.success) {
            cerrarModalMatch();
            actualizarFilaUI(codigoICBFActual, data.match);
            mostrarToast('Match guardado correctamente', 'success');
        } else {
            Swal.fire({ icon: 'error', title: 'Error', text: data.error || 'No se pudo guardar.' });
        }
    } finally {
        btn.disabled = false;
    }
}

function actualizarFilaUI(codigoICBF, match) {
    const fila = document.querySelector(`tr[data-codigo-icbf="${codigoICBF}"]`);
    if (!fila) return;

    // Semáforo
    fila.querySelector('.semaforo').className = 'semaforo semaforo-verde';
    fila.querySelector('.semaforo i').className = 'fas fa-circle';
    fila.querySelector('.semaforo').title = 'Match configurado';

    // Clase fila
    fila.classList.remove('fila-pendiente');
    fila.classList.add('fila-ok');

    // Nombre Siesa
    const celdaSiesa = document.getElementById(`nombre-siesa-${codigoICBF}`);
    celdaSiesa.className = 'siesa-nombre';
    celdaSiesa.innerHTML = `${match.nombre_siesa} <span class="siesa-codigo">${match.codigo_siesa}</span>`;

    // Presentación
    const celdaPres = document.getElementById(`pres-${codigoICBF}`);
    celdaPres.textContent = match.presentacion || '—';

    // Botones
    const celdaAcciones = fila.querySelector('.col-acciones');
    const nombreEscapado = match.nombre_siesa.replace(/'/g, "\\'");
    celdaAcciones.innerHTML = `
        <button class="btn-match"
            onclick="abrirModalMatch('${codigoICBF}', '${fila.querySelector('.icbf-nombre').textContent}', '${match.codigo_siesa}', '${nombreEscapado}')">
            <i class="fas fa-edit"></i> Cambiar
        </button>
        <button class="btn-quitar"
            onclick="quitarMatch('${codigoICBF}', '${fila.querySelector('.icbf-nombre').textContent}')">
            <i class="fas fa-unlink"></i>
        </button>
    `;

    actualizarContadores();
}

async function quitarMatch(codigoICBF, nombreICBF) {
    const conf = await Swal.fire({
        title: '¿Quitar el match?',
        html: `Se eliminará la asociación de <strong>${nombreICBF}</strong> con su producto de compras.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, quitar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#e74c3c',
    });
    if (!conf.isConfirmed) return;

    const resp = await fetch(
        `/nutricion/api/match/${encodeURIComponent(codigoICBF)}/?programa_id=${PROGRAMA_ID}`,
        { method: 'DELETE', headers: { 'X-CSRFToken': getCookie('csrftoken') } }
    );
    const data = await resp.json();

    if (data.success) {
        const fila = document.querySelector(`tr[data-codigo-icbf="${codigoICBF}"]`);
        if (fila) {
            fila.classList.remove('fila-ok');
            fila.classList.add('fila-pendiente');
            fila.querySelector('.semaforo').className = 'semaforo semaforo-rojo';
            fila.querySelector('.semaforo').title = 'Sin match';
            document.getElementById(`nombre-siesa-${codigoICBF}`).className = 'siesa-vacio';
            document.getElementById(`nombre-siesa-${codigoICBF}`).innerHTML = '<i class="fas fa-minus"></i> Sin asignar';
            document.getElementById(`pres-${codigoICBF}`).textContent = '—';
            fila.querySelector('.col-acciones').innerHTML = `
                <button class="btn-match"
                    onclick="abrirModalMatch('${codigoICBF}', '${fila.querySelector('.icbf-nombre').textContent}', '', '')">
                    <i class="fas fa-link"></i> Asignar
                </button>
            `;
        }
        actualizarContadores();
        mostrarToast('Match eliminado', 'info');
    } else {
        Swal.fire({ icon: 'error', title: 'Error', text: data.error });
    }
}

function actualizarContadores() {
    const filas = document.querySelectorAll('tr.fila-match');
    const conMatch = document.querySelectorAll('tr.fila-ok').length;
    const sinMatch = document.querySelectorAll('tr.fila-pendiente').length;
    const total = filas.length;

    document.querySelector('.stat-total .stat-num').textContent = total;
    document.querySelector('.stat-ok .stat-num').textContent = conMatch;
    document.querySelector('.stat-pendiente .stat-num').textContent = sinMatch;

    if (total > 0) {
        const pct = Math.round((conMatch / total) * 100);
        document.querySelector('.progreso-fill').style.width = pct + '%';
        document.querySelector('.progreso-pct').textContent = pct + '%';
    }
}

// =================== CATÁLOGO SIMULACRO ===================

function abrirCatalogo() {
    document.getElementById('modalCatalogo').style.display = 'flex';
    document.getElementById('formProductoContainer').style.display = 'none';
    cargarCatalogo();
}

function cerrarCatalogo() {
    document.getElementById('modalCatalogo').style.display = 'none';
}

async function cargarCatalogo(q = '') {
    const resp = await fetch(`/nutricion/api/match/catalogo/?q=${encodeURIComponent(q)}`);
    const data = await resp.json();
    const lista = document.getElementById('catalogoLista');

    if (!data.productos.length) {
        lista.innerHTML = '<p class="catalogo-vacio"><i class="fas fa-box-open"></i> No hay productos registrados.</p>';
        return;
    }

    lista.innerHTML = data.productos.map(p => `
        <div class="catalogo-item" id="cat-${p.codigo}">
            <div class="cat-info">
                <span class="cat-nombre">${p.nombre}</span>
                <span class="cat-codigo">${p.codigo}</span>
                ${p.presentacion ? `<span class="cat-pres">${p.presentacion}${p.contenido_gramos ? ' — ' + p.contenido_gramos + 'g' : ''}</span>` : ''}
            </div>
            <div class="cat-acciones">
                <button class="btn-cat-edit" onclick="abrirFormProducto('${p.codigo}', '${p.nombre.replace(/'/g,"\\'")}', '${p.presentacion}', '${p.unidad_medida}', '${p.contenido_gramos}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-cat-del" onclick="eliminarProducto('${p.codigo}', '${p.nombre.replace(/'/g,"\\'")}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    const buscarInput = document.getElementById('buscarCatalogo');
    if (buscarInput) {
        let timeout;
        buscarInput.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => cargarCatalogo(buscarInput.value), 300);
        });
    }
});

function abrirFormProducto(codigo, nombre = '', presentacion = '', unidad = '', gramos = '') {
    editandoCodigo = codigo;
    document.getElementById('formProductoTitulo').textContent = codigo ? 'Editar Producto' : 'Nuevo Producto';
    document.getElementById('fpCodigo').value = codigo || '';
    document.getElementById('fpCodigo').disabled = !!codigo;
    document.getElementById('fpNombre').value = nombre;
    document.getElementById('fpPresentacion').value = presentacion;
    document.getElementById('fpUnidad').value = unidad;
    document.getElementById('fpGramos').value = gramos;
    document.getElementById('formProductoContainer').style.display = 'block';
    document.getElementById('fpNombre').focus();
}

function cancelarFormProducto() {
    document.getElementById('formProductoContainer').style.display = 'none';
    editandoCodigo = null;
}

async function guardarProducto() {
    const codigo = document.getElementById('fpCodigo').value.trim();
    const nombre = document.getElementById('fpNombre').value.trim();
    if (!nombre) { mostrarToast('El nombre es obligatorio', 'error'); return; }

    const body = {
        codigo,
        nombre,
        presentacion: document.getElementById('fpPresentacion').value.trim(),
        unidad_medida: document.getElementById('fpUnidad').value.trim(),
        contenido_gramos: document.getElementById('fpGramos').value || null,
    };

    let url, method;
    if (editandoCodigo) {
        url = `/nutricion/api/match/catalogo/${encodeURIComponent(editandoCodigo)}/`;
        method = 'PUT';
    } else {
        if (!codigo) { mostrarToast('El código es obligatorio', 'error'); return; }
        url = '/nutricion/api/match/catalogo/';
        method = 'POST';
    }

    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(body),
    });
    const data = await resp.json();

    if (data.success || data.producto) {
        cancelarFormProducto();
        cargarCatalogo(document.getElementById('buscarCatalogo').value);
        mostrarToast(editandoCodigo ? 'Producto actualizado' : 'Producto creado', 'success');
    } else {
        Swal.fire({ icon: 'error', title: 'Error', text: data.error || 'No se pudo guardar.' });
    }
}

async function eliminarProducto(codigo, nombre) {
    const conf = await Swal.fire({
        title: '¿Eliminar producto?',
        html: `<strong>${nombre}</strong><br><small>Si tiene matches activos no se puede eliminar.</small>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Eliminar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#e74c3c',
    });
    if (!conf.isConfirmed) return;

    const resp = await fetch(`/nutricion/api/match/catalogo/${encodeURIComponent(codigo)}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
    });
    const data = await resp.json();

    if (data.success) {
        cargarCatalogo(document.getElementById('buscarCatalogo').value);
        mostrarToast('Producto eliminado', 'info');
    } else {
        Swal.fire({ icon: 'error', title: 'No se puede eliminar', text: data.error });
    }
}

// =================== UTILIDADES ===================

function mostrarToast(mensaje, tipo = 'success') {
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: tipo,
        title: mensaje,
        showConfirmButton: false,
        timer: 2500,
        timerProgressBar: true,
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        for (const cookie of document.cookie.split(';')) {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Cerrar modales al hacer clic fuera
window.addEventListener('click', e => {
    if (e.target.id === 'modalMatch') cerrarModalMatch();
    if (e.target.id === 'modalCatalogo') cerrarCatalogo();
});
