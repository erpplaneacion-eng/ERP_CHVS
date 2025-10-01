/**
 * ciclos_menus.js
 * Gestión de planificación de ciclos de menús
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const btnBuscar = document.getElementById('btn-buscar');
    const btnInicializar = document.getElementById('btn-inicializar');
    const filterEtc = document.getElementById('filter-etc');
    const filterFocalizacion = document.getElementById('filter-focalizacion');
    const filterAno = document.getElementById('filter-ano');
    const resultsContainer = document.getElementById('results-container');
    const messageContainer = document.getElementById('message-container');

    // Configuración de URLs desde el template
    const config = window.CICLOS_MENUS_CONFIG;

    // Event Listeners
    btnBuscar.addEventListener('click', handleBuscar);
    btnInicializar.addEventListener('click', handleInicializar);

    /**
     * Maneja la búsqueda de datos existentes
     */
    async function handleBuscar() {
        const etc = filterEtc.value.trim();
        const focalizacion = filterFocalizacion.value.trim();
        const ano = filterAno.value.trim();

        if (!etc || !focalizacion) {
            showMessage('Por favor seleccione ETC y Focalización', 'error');
            return;
        }

        showLoading();
        clearMessage();

        try {
            const url = `${config.urlObtener}?etc=${encodeURIComponent(etc)}&focalizacion=${encodeURIComponent(focalizacion)}&ano=${ano}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                if (data.datos.length === 0) {
                    showMessage('No se encontraron datos de planificación. Use "Inicializar desde Listados" para crear los registros.', 'info');
                    resultsContainer.innerHTML = '<div class="no-data"><i class="fas fa-info-circle"></i><p>No hay datos disponibles. Inicialice desde los listados de focalización.</p></div>';
                } else {
                    renderResults(data.datos);
                }
            } else {
                showMessage(data.error || 'Error al obtener datos', 'error');
                resultsContainer.innerHTML = '<div class="no-data"><i class="fas fa-exclamation-circle"></i><p>Error al cargar datos</p></div>';
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión al servidor', 'error');
            resultsContainer.innerHTML = '<div class="no-data"><i class="fas fa-exclamation-circle"></i><p>Error de conexión</p></div>';
        }
    }

    /**
     * Maneja la inicialización desde listados
     */
    async function handleInicializar() {
        const etc = filterEtc.value.trim();
        const focalizacion = filterFocalizacion.value.trim();
        const ano = filterAno.value.trim();

        if (!etc || !focalizacion) {
            showMessage('Por favor seleccione ETC y Focalización', 'error');
            return;
        }

        if (!confirm(`¿Está seguro de inicializar/actualizar la planificación para ${etc} - ${focalizacion}?\n\nEsto calculará las cantidades automáticamente desde los listados de focalización.`)) {
            return;
        }

        showLoading();
        clearMessage();

        try {
            const response = await fetch(config.urlInicializar, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': config.csrfToken
                },
                body: JSON.stringify({
                    etc: etc,
                    focalizacion: focalizacion,
                    ano: parseInt(ano)
                })
            });

            const data = await response.json();

            if (data.success) {
                showMessage(`${data.message}`, 'success');
                renderResults(data.datos);
            } else {
                showMessage(data.error || 'Error al inicializar', 'error');
                resultsContainer.innerHTML = '<div class="no-data"><i class="fas fa-exclamation-circle"></i><p>Error al inicializar</p></div>';
            }
        } catch (error) {
            console.error('Error:', error);
            showMessage('Error de conexión al servidor', 'error');
            resultsContainer.innerHTML = '<div class="no-data"><i class="fas fa-exclamation-circle"></i><p>Error de conexión</p></div>';
        }
    }

    /**
     * Renderiza los resultados en tablas por sede
     */
    function renderResults(sedes) {
        if (!sedes || sedes.length === 0) {
            resultsContainer.innerHTML = '<div class="no-data"><i class="fas fa-info-circle"></i><p>No hay datos disponibles</p></div>';
            return;
        }

        let html = '';

        sedes.forEach((sedeData, index) => {
            // Calcular totales para el resumen
            let totalCapAm = 0;
            let totalCapPm = 0;
            let totalAlmuerzo = 0;
            let totalRefuerzo = 0;
            let totalGeneral = 0;

            sedeData.niveles.forEach(nivel => {
                totalCapAm += nivel.cap_am;
                totalCapPm += nivel.cap_pm;
                totalAlmuerzo += nivel.almuerzo_ju;
                totalRefuerzo += nivel.refuerzo;
                totalGeneral += nivel.total;
            });

            html += `
                <div class="sede-card">
                    <div class="sede-header collapsed" data-sede-index="${index}">
                        <div class="sede-info">
                            <div>
                                <i class="fas fa-school"></i> ${sedeData.sede}
                            </div>
                            <div class="sede-summary">
                                <span title="Total de raciones">${totalGeneral} raciones</span>
                            </div>
                        </div>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    </div>
                    <div class="sede-body collapsed">
                        <table class="sede-table">
                        <thead>
                            <tr>
                                <th>Nivel Escolar</th>
                                <th>Grados</th>
                                <th>CAP AM</th>
                                <th>CAP PM</th>
                                <th>Almuerzo JU</th>
                                <th>Refuerzo</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            sedeData.niveles.forEach(nivel => {
                html += `
                    <tr>
                        <td><strong>${nivel.nivel_escolar}</strong></td>
                        <td class="grados-cell">${nivel.grados || 'N/A'}</td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="cap_am">
                            <span class="value">${nivel.cap_am}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="cap_pm">
                            <span class="value">${nivel.cap_pm}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="almuerzo_ju">
                            <span class="value">${nivel.almuerzo_ju}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td class="editable-cell" data-id="${nivel.id}" data-campo="refuerzo">
                            <span class="value">${nivel.refuerzo}</span>
                            <i class="fas fa-edit edit-icon"></i>
                        </td>
                        <td><strong>${nivel.total}</strong></td>
                    </tr>
                `;
            });

            // Fila de totales (usar los valores ya calculados)
            html += `
                    <tr class="total-row">
                        <td colspan="2"><strong>TOTAL SEDE</strong></td>
                        <td><strong>${totalCapAm}</strong></td>
                        <td><strong>${totalCapPm}</strong></td>
                        <td><strong>${totalAlmuerzo}</strong></td>
                        <td><strong>${totalRefuerzo}</strong></td>
                        <td><strong>${totalGeneral}</strong></td>
                    </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            `;
        });

        resultsContainer.innerHTML = html;

        // Agregar event listeners a las celdas editables
        attachEditListeners();

        // Agregar event listeners para acordeón
        attachAccordionListeners();
    }

    /**
     * Agrega event listeners para el acordeón
     */
    function attachAccordionListeners() {
        const headers = document.querySelectorAll('.sede-header');

        headers.forEach(header => {
            header.addEventListener('click', function() {
                toggleAccordion(this);
            });
        });
    }

    /**
     * Alterna el estado de expansión/contracción del acordeón
     */
    function toggleAccordion(header) {
        const body = header.nextElementSibling;

        // Toggle classes
        header.classList.toggle('collapsed');
        body.classList.toggle('collapsed');
    }

    /**
     * Agrega event listeners a las celdas editables
     */
    function attachEditListeners() {
        const editableCells = document.querySelectorAll('.editable-cell');

        editableCells.forEach(cell => {
            cell.addEventListener('click', function(e) {
                // Evitar que el click se propague al header del acordeón
                e.stopPropagation();
                makeEditable(this);
            });
        });
    }

    /**
     * Convierte una celda en editable
     */
    function makeEditable(cell) {
        if (cell.querySelector('input')) {
            return; // Ya está en modo edición
        }

        const valueSpan = cell.querySelector('.value');
        const currentValue = valueSpan.textContent.trim();
        const id = cell.dataset.id;
        const campo = cell.dataset.campo;

        // Crear input
        const input = document.createElement('input');
        input.type = 'number';
        input.min = '0';
        input.value = currentValue;
        input.style.width = '60px';

        // Reemplazar el contenido
        cell.innerHTML = '';
        cell.appendChild(input);
        input.focus();
        input.select();

        // Guardar al presionar Enter o perder foco
        const saveValue = async () => {
            const newValue = input.value.trim();

            if (newValue === currentValue) {
                // No hubo cambios
                cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                return;
            }

            if (!newValue || newValue < 0) {
                showMessage('Valor inválido', 'error');
                cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                return;
            }

            // Guardar en servidor
            try {
                const response = await fetch(config.urlActualizar, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': config.csrfToken
                    },
                    body: JSON.stringify({
                        id: id,
                        campo: campo,
                        valor: parseInt(newValue)
                    })
                });

                const data = await response.json();

                if (data.success) {
                    cell.innerHTML = `<span class="value">${newValue}</span><i class="fas fa-edit edit-icon"></i>`;
                    showMessage('Valor actualizado exitosamente', 'success');

                    // Actualizar totales
                    updateTotals(cell.closest('table'));
                } else {
                    showMessage(data.error || 'Error al actualizar', 'error');
                    cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('Error de conexión al servidor', 'error');
                cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
            }
        };

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveValue();
            }
        });

        input.addEventListener('blur', saveValue);
    }

    /**
     * Actualiza los totales de una tabla
     */
    function updateTotals(table) {
        const rows = table.querySelectorAll('tbody tr:not(.total-row)');
        let totalCapAm = 0;
        let totalCapPm = 0;
        let totalAlmuerzo = 0;
        let totalRefuerzo = 0;

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 7) {
                totalCapAm += parseInt(cells[2].querySelector('.value')?.textContent || 0);
                totalCapPm += parseInt(cells[3].querySelector('.value')?.textContent || 0);
                totalAlmuerzo += parseInt(cells[4].querySelector('.value')?.textContent || 0);
                totalRefuerzo += parseInt(cells[5].querySelector('.value')?.textContent || 0);

                // Actualizar total de la fila
                const rowTotal = totalCapAm + totalCapPm + totalAlmuerzo + totalRefuerzo;
                cells[6].innerHTML = `<strong>${rowTotal}</strong>`;
            }
        });

        const totalGeneral = totalCapAm + totalCapPm + totalAlmuerzo + totalRefuerzo;

        // Actualizar fila de totales
        const totalRow = table.querySelector('.total-row');
        if (totalRow) {
            const totalCells = totalRow.querySelectorAll('td');
            totalCells[1].innerHTML = `<strong>${totalCapAm}</strong>`;
            totalCells[2].innerHTML = `<strong>${totalCapPm}</strong>`;
            totalCells[3].innerHTML = `<strong>${totalAlmuerzo}</strong>`;
            totalCells[4].innerHTML = `<strong>${totalRefuerzo}</strong>`;
            totalCells[5].innerHTML = `<strong>${totalGeneral}</strong>`;
        }
    }

    /**
     * Muestra un spinner de carga
     */
    function showLoading() {
        resultsContainer.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner"></i>
                <p>Cargando datos...</p>
            </div>
        `;
    }

    /**
     * Muestra un mensaje al usuario
     */
    function showMessage(message, type = 'info') {
        const alertClass = type === 'error' ? 'alert-error' : type === 'success' ? 'alert-success' : 'alert-info';
        const icon = type === 'error' ? 'fa-exclamation-circle' : type === 'success' ? 'fa-check-circle' : 'fa-info-circle';

        messageContainer.innerHTML = `
            <div class="alert ${alertClass}">
                <i class="fas ${icon}"></i> ${message}
            </div>
        `;

        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            messageContainer.innerHTML = '';
        }, 5000);
    }

    /**
     * Limpia el mensaje actual
     */
    function clearMessage() {
        messageContainer.innerHTML = '';
    }
});
