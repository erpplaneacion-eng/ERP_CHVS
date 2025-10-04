// Gestión Avanzada de Menús por Modalidad - Módulo de Nutrición
console.log('[DEBUG] ✓ Script menus_avanzado.js cargado correctamente');

let programaActual = null;
let municipioActual = null;
let modalidadesData = [];
let menusData = {};

document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] ✓ DOMContentLoaded event disparado');
    console.log('[DEBUG] MUNICIPIO_ACTUAL:', typeof MUNICIPIO_ACTUAL !== 'undefined' ? MUNICIPIO_ACTUAL : 'undefined');
    console.log('[DEBUG] PROGRAMA_ACTUAL:', typeof PROGRAMA_ACTUAL !== 'undefined' ? PROGRAMA_ACTUAL : 'undefined');

    inicializarEventos();

    // Si hay municipio preseleccionado, cargar programas
    if (typeof MUNICIPIO_ACTUAL !== 'undefined' && MUNICIPIO_ACTUAL) {
        console.log('[DEBUG] Cargando programas para municipio preseleccionado:', MUNICIPIO_ACTUAL);
        cargarProgramasPorMunicipio(MUNICIPIO_ACTUAL);
    }
});

function inicializarEventos() {
    console.log('[DEBUG] ✓ Inicializando eventos...');

    // Cambio de municipio
    const filtroMunicipio = document.getElementById('filtroMunicipio');
    console.log('[DEBUG] Elemento filtroMunicipio encontrado:', filtroMunicipio ? 'SÍ' : 'NO');

    if (!filtroMunicipio) {
        console.error('[DEBUG] ❌ ERROR: No se encontró el elemento con id="filtroMunicipio"');
        return;
    }

    // Log de opciones disponibles
    console.log('[DEBUG] Opciones disponibles en select de municipios:');
    for (let i = 0; i < filtroMunicipio.options.length; i++) {
        const option = filtroMunicipio.options[i];
        console.log(`[DEBUG]   ${i}: value="${option.value}", text="${option.text}"`);
    }

    filtroMunicipio.addEventListener('change', function() {
        console.log('[DEBUG] ✓✓✓ EVENT CHANGE DISPARADO EN MUNICIPIO ✓✓✓');
        console.log('[DEBUG] Selected index:', this.selectedIndex);
        console.log('[DEBUG] Selected option:', this.options[this.selectedIndex]);
        const municipioId = this.value;
        console.log('[DEBUG] Municipio seleccionado (this.value):', municipioId);
        console.log('[DEBUG] Tipo de dato:', typeof municipioId);
        console.log('[DEBUG] Longitud:', municipioId.length);
        municipioActual = municipioId;

        if (municipioId) {
            console.log('[DEBUG] Llamando a cargarProgramasPorMunicipio...');
            cargarProgramasPorMunicipio(municipioId);
        } else {
            console.log('[DEBUG] Reseteando filtros (valor vacío)...');
            resetearFiltros();
        }
    });

    console.log('[DEBUG] ✓ Event listener para municipio registrado correctamente');

    // Cambio de programa
    const filtroPrograma = document.getElementById('filtroPrograma');
    console.log('[DEBUG] Elemento filtroPrograma encontrado:', filtroPrograma ? 'SÍ' : 'NO');

    if (filtroPrograma) {
        filtroPrograma.addEventListener('change', function() {
            console.log('[DEBUG] ✓ Event change en programa disparado');
            const programaId = this.value;
            console.log('[DEBUG] Programa seleccionado:', programaId);
            document.getElementById('btnAplicarFiltros').disabled = !programaId;
        });
    }

    // Aplicar filtros y cargar modalidades
    const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
    console.log('[DEBUG] Elemento btnAplicarFiltros encontrado:', btnAplicarFiltros ? 'SÍ' : 'NO');

    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', function() {
            console.log('[DEBUG] ✓ Click en btnAplicarFiltros');
            const programaId = document.getElementById('filtroPrograma').value;
            if (programaId) {
                cargarModalidadesPorPrograma(programaId);
            }
        });
    }

    console.log('[DEBUG] ✓ Todos los eventos inicializados correctamente');
}

async function cargarProgramasPorMunicipio(municipioId) {
    console.log('[DEBUG] Iniciando carga de programas...');
    console.log('[DEBUG] municipioId:', municipioId);

    try {
        const url = `/nutricion/api/programas-por-municipio/?municipio_id=${municipioId}`;
        console.log('[DEBUG] URL:', url);

        const response = await fetch(url);
        console.log('[DEBUG] Response status:', response.status);

        const data = await response.json();
        console.log('[DEBUG] Data recibida:', data);

        const selectPrograma = document.getElementById('filtroPrograma');

        if (!selectPrograma) {
            console.error('[DEBUG] No se encontró el elemento filtroPrograma');
            return;
        }

        selectPrograma.innerHTML = '<option value="">Seleccione un programa...</option>';

        if (data.programas && data.programas.length > 0) {
            console.log('[DEBUG] Se encontraron', data.programas.length, 'programas');

            data.programas.forEach(programa => {
                console.log('[DEBUG] Agregando programa:', programa);
                const option = document.createElement('option');
                option.value = programa.id;
                option.textContent = `${programa.programa} (${programa.contrato})`;
                selectPrograma.appendChild(option);
            });

            selectPrograma.disabled = false;
            console.log('[DEBUG] Select de programas habilitado');

            // Si solo hay un programa, seleccionarlo automáticamente
            if (data.programas.length === 1) {
                selectPrograma.value = data.programas[0].id;
                document.getElementById('btnAplicarFiltros').disabled = false;
                console.log('[DEBUG] Programa seleccionado automáticamente');
            }
        } else {
            console.log('[DEBUG] No se encontraron programas');
            console.log('[DEBUG] data.debug:', data.debug);
            selectPrograma.innerHTML = '<option value="">No hay programas activos en este municipio</option>';
            selectPrograma.disabled = true;
        }
    } catch (error) {
        console.error('[DEBUG] Error al cargar programas:', error);
        console.error('[DEBUG] Stack:', error.stack);
        alert('Error al cargar programas del municipio: ' + error.message);
    }
}

async function cargarModalidadesPorPrograma(programaId) {
    console.log('[DEBUG] Cargando modalidades para programa:', programaId);
    try {
        const url = `/nutricion/api/modalidades-por-programa/?programa_id=${programaId}`;
        console.log('[DEBUG] URL modalidades:', url);

        const response = await fetch(url);
        console.log('[DEBUG] Response status modalidades:', response.status);

        const data = await response.json();
        console.log('[DEBUG] Data modalidades recibida:', data);

        if (data.error) {
            console.error('[DEBUG] Error en respuesta:', data.error);
            alert(data.error);
            return;
        }

        programaActual = data.programa;
        modalidadesData = data.modalidades;

        console.log('[DEBUG] Programa actual:', programaActual);
        console.log('[DEBUG] Modalidades encontradas:', modalidadesData.length);

        // Mostrar información del programa
        mostrarInfoPrograma(data.programa);

        // Ocultar mensaje inicial
        document.getElementById('mensajeInicial').style.display = 'none';

        // Cargar menús existentes y generar acordeones
        await cargarMenusExistentes(programaId);

        generarAcordeones(data.modalidades);

    } catch (error) {
        console.error('[DEBUG] Error al cargar modalidades:', error);
        console.error('[DEBUG] Stack:', error.stack);
        alert('Error al cargar modalidades del programa: ' + error.message);
    }
}

async function cargarMenusExistentes(programaId) {
    try {
        const response = await fetch(`/nutricion/api/menus/?programa_id=${programaId}`);
        const data = await response.json();

        // Agrupar menús por modalidad
        menusData = {};
        if (data.menus) {
            data.menus.forEach(menu => {
                const modalidadId = menu.id_modalidad__id_modalidades;
                if (!menusData[modalidadId]) {
                    menusData[modalidadId] = [];
                }
                menusData[modalidadId].push(menu);
            });

            // Ordenar menús numéricamente dentro de cada modalidad
            Object.keys(menusData).forEach(modalidadId => {
                menusData[modalidadId].sort((a, b) => {
                    const numA = parseInt(a.menu) || 0;
                    const numB = parseInt(b.menu) || 0;
                    return numA - numB;
                });
            });
        }
    } catch (error) {
        console.error('Error al cargar menús:', error);
    }
}

function mostrarInfoPrograma(programa) {
    const container = document.getElementById('infoProgramaContainer');
    document.getElementById('infoProgramaNombre').querySelector('span').textContent = programa.nombre;
    document.getElementById('infoProgramaContrato').querySelector('span').textContent = programa.contrato;

    const municipioSelect = document.getElementById('filtroMunicipio');
    const municipioNombre = municipioSelect.options[municipioSelect.selectedIndex].text;
    document.getElementById('infoProgramaMunicipio').querySelector('span').textContent = municipioNombre;

    container.style.display = 'block';
}

function generarAcordeones(modalidades) {
    const container = document.getElementById('modalidadesContainer');
    container.innerHTML = '';

    modalidades.forEach(modalidad => {
        const accordion = crearAcordeon(modalidad);
        container.appendChild(accordion);
    });
}

function crearAcordeon(modalidad) {
    const modalidadId = modalidad.id_modalidades;
    const menusModalidad = menusData[modalidadId] || [];
    const tieneMenus = menusModalidad.length > 0;

    const accordionDiv = document.createElement('div');
    accordionDiv.className = 'accordion';

    // Crear header
    const header = document.createElement('div');
    header.className = 'accordion-header';
    header.onclick = function() { toggleAccordion(this); };

    header.innerHTML = `
        <div>
            <strong>${modalidad.modalidad}</strong>
            <span class="preparacion-badge">${menusModalidad.length} / 20 menús</span>
        </div>
        <div>
            ${!tieneMenus ? `<button class="btn-generar-auto" data-modalidad-id="${modalidadId}" data-modalidad-nombre="${modalidad.modalidad}">
                <i class="fas fa-magic"></i> Generar 20 Menús
            </button>` : ''}
            <i class="fas fa-chevron-down"></i>
        </div>
    `;

    // Agregar event listener al botón si existe
    if (!tieneMenus) {
        setTimeout(() => {
            const btn = header.querySelector('.btn-generar-auto');
            if (btn) {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const modalidadId = this.getAttribute('data-modalidad-id');
                    const modalidadNombre = this.getAttribute('data-modalidad-nombre');
                    generarMenusAutomaticos(modalidadId, modalidadNombre);
                });
            }
        }, 0);
    }

    // Crear content
    const content = document.createElement('div');
    content.className = 'accordion-content';
    content.id = `content-${modalidadId}`;

    const grid = document.createElement('div');
    grid.className = 'menus-grid';
    grid.id = `grid-${modalidadId}`;

    if (tieneMenus) {
        grid.innerHTML = generarTarjetasMenus(menusModalidad);
    } else {
        grid.innerHTML = '<p style="padding: 20px;">Genere los menús para esta modalidad</p>';
    }

    content.appendChild(grid);
    accordionDiv.appendChild(header);
    accordionDiv.appendChild(content);

    return accordionDiv;
}

function generarTarjetasMenus(menus) {
    return menus.map(menu => `
        <div class="menu-card ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
             onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
            <div class="menu-numero">${menu.menu}</div>
            <div class="menu-actions">
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                    <i class="fas fa-utensils"></i> Preparaciones
                </button>
            </div>
        </div>
    `).join('');
}

function toggleAccordion(header) {
    const content = header.nextElementSibling;
    const isActive = content.classList.contains('active');

    // Cerrar todos los acordeones
    document.querySelectorAll('.accordion-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.accordion-header').forEach(h => h.classList.remove('active'));

    // Abrir el actual si estaba cerrado
    if (!isActive) {
        content.classList.add('active');
        header.classList.add('active');
    }
}

async function generarMenusAutomaticos(modalidadId, modalidadNombre) {
    if (!confirm(`¿Generar automáticamente 20 menús para ${modalidadNombre}?`)) {
        return;
    }

    try {
        const response = await fetch('/nutricion/api/generar-menus-automaticos/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                programa_id: programaActual.id,
                modalidad_id: modalidadId
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✓ Se generaron ${data.menus_creados} menús exitosamente`);
            // Recargar la vista
            cargarModalidadesPorPrograma(programaActual.id);
        } else {
            alert('Error: ' + (data.error || 'No se pudieron generar los menús'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al generar menús automáticos');
    }
}

function abrirGestionPreparaciones(menuId, menuNumero) {
    // TODO: Implementar modal de gestión de preparaciones
    document.getElementById('menuNumeroModal').textContent = menuNumero;
    document.getElementById('modalPreparaciones').style.display = 'block';

    // Cargar preparaciones del menú
    cargarPreparacionesMenu(menuId);
}

async function cargarPreparacionesMenu(menuId) {
    try {
        const response = await fetch(`/nutricion/api/preparaciones/?menu_id=${menuId}`);
        const data = await response.json();

        const tbody = document.getElementById('tablaPreparacionesMenu');
        tbody.innerHTML = '';

        if (data.preparaciones && data.preparaciones.length > 0) {
            data.preparaciones.forEach(prep => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${prep.preparacion}</td>
                    <td>
                        <a href="/nutricion/preparaciones/${prep.id_preparacion}/" class="btn btn-sm btn-info">
                            <i class="fas fa-list"></i> Ver Ingredientes
                        </a>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-delete" onclick="eliminarPreparacion(${prep.id_preparacion})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center;">No hay preparaciones asociadas</td></tr>';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function resetearFiltros() {
    document.getElementById('filtroPrograma').innerHTML = '<option value="">Primero seleccione un municipio...</option>';
    document.getElementById('filtroPrograma').disabled = true;
    document.getElementById('btnAplicarFiltros').disabled = true;
    document.getElementById('infoProgramaContainer').style.display = 'none';
    document.getElementById('modalidadesContainer').innerHTML = '';
    document.getElementById('mensajeInicial').style.display = 'block';
}

// Cerrar modales
document.querySelectorAll('.modal .close').forEach(closeBtn => {
    closeBtn.addEventListener('click', function() {
        this.closest('.modal').style.display = 'none';
    });
});

window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
