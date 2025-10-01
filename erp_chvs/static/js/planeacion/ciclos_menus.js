/**
 * ciclos_menus.js
 * Lógica para la página de Planificación de Ciclos de Menús.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Obtener elementos del DOM
    const btnBuscar = document.getElementById('btn-buscar');
    const btnInicializar = document.getElementById('btn-inicializar');
    const etcSelect = document.getElementById('filter-etc');
    const focalizacionSelect = document.getElementById('filter-focalizacion');
    const anoInput = document.getElementById('filter-ano');
    const resultsContainer = document.getElementById('results-container');

    // Configuración desde el template de Django
    const config = window.CICLOS_MENUS_CONFIG || {};

    // =================================================================
    // EVENT LISTENERS
    // =================================================================

    // Evento para el botón de Buscar
    if (btnBuscar) {
        btnBuscar.addEventListener('click', function() {
            const etc = etcSelect.value;
            const focalizacion = focalizacionSelect.value;
            const ano = anoInput.value;

            if (!etc || !focalizacion) {
                ERPUtils.showAlert('Por favor, seleccione un ETC y una Focalización.', 'warning');
                return;
            }

            buscarDatos(etc, focalizacion, ano);
        });
    }

    // Evento para el botón de Inicializar
    if (btnInicializar) {
        btnInicializar.addEventListener('click', function() {
            const etc = etcSelect.value;
            const focalizacion = focalizacionSelect.value;
            const ano = anoInput.value;

            if (!etc || !focalizacion) {
                ERPUtils.showAlert('Por favor, seleccione un ETC y una Focalización.', 'warning');
                return;
            }

            // Inicia el proceso. El primer llamado nunca se fuerza.
            inicializarCiclos(etc, focalizacion, ano, false);
        });
    }

    // =================================================================
    // FUNCIÓN: BUSCAR DATOS EXISTENTES
    // =================================================================

    /**
     * Busca datos de planificación existentes sin modificarlos.
     */
    async function buscarDatos(etc, focalizacion, ano) {
        mostrarCargando();

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
                if (data.datos && data.datos.length > 0) {
                    renderizarTabla(data.datos);
                } else {
                    resultsContainer.innerHTML = `
                        <div class="no-data">
                            <i class="fas fa-info-circle"></i>
                            <p>No se encontraron datos de planificación. Use "Inicializar desde Listados" para crear los registros.</p>
                        </div>
                    `;
                }
            } else {
                ERPUtils.showAlert(data.error || 'Error al obtener datos', 'error');
                resultsContainer.innerHTML = `
                    <div class="no-data">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Error al cargar datos</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error al buscar datos:', error);
            ERPUtils.showAlert('Error de conexión al servidor', 'error');
            resultsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error de conexión</p>
                </div>
            `;
        }
    }

    // =================================================================
    // FUNCIÓN: INICIALIZAR CICLOS DE MENÚS
    // =================================================================

    /**
     * Función asíncrona para inicializar o actualizar los ciclos de menús.
     * @param {string} etc - El ETC seleccionado.
     * @param {string} focalizacion - La focalización seleccionada.
     * @param {string} ano - El año seleccionado.
     * @param {boolean} forzar - Si se debe forzar la actualización sobre datos existentes.
     */
    async function inicializarCiclos(etc, focalizacion, ano, forzar) {
        // Mostrar indicador de carga
        btnInicializar.disabled = true;
        btnInicializar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';

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
                    ano: parseInt(ano),
                    forzar_actualizacion: forzar
                })
            });

            const data = await response.json();

            if (response.ok) {
                if (data.success) {
                    ERPUtils.showNotification(data.message, 'success');
                    // Renderizar la tabla con los datos recibidos
                    renderizarTabla(data.datos);

                } else if (data.requiere_confirmacion) {
                    // Pedir confirmación al usuario antes de sobrescribir
                    const userConfirmed = await ERPUtils.showConfirm(
                        'Confirmación Requerida',
                        `${data.warning}. Existen ${data.total_registros_existentes} registros que serán sobreescritos. ¿Desea continuar?`,
                        'warning'
                    );

                    if (userConfirmed) {
                        // Si el usuario confirma, llamamos de nuevo forzando la actualización.
                        inicializarCiclos(etc, focalizacion, ano, true);
                    } else {
                        // Si el usuario cancela, cargar los datos existentes sin modificar
                        ERPUtils.showNotification('Operación cancelada. Los registros existentes se mantienen intactos.', 'info');
                        buscarDatos(etc, focalizacion, ano);
                    }
                } else {
                    // Otros errores controlados por el backend
                    ERPUtils.showAlert(data.error || 'Ocurrió un error inesperado.', 'error');
                }
            } else {
                // Errores de servidor (500, etc.)
                const errorMsg = data.error || 'Error desconocido del servidor';
                ERPUtils.showAlert(`Error del servidor: ${errorMsg}`, 'error');
            }

        } catch (error) {
            console.error('Error de red o al procesar la petición:', error);
            ERPUtils.showAlert('Error de red. Por favor, intente de nuevo.', 'error');
        } finally {
            // Reactivar botón
            btnInicializar.disabled = false;
            btnInicializar.innerHTML = '<i class="fas fa-sync-alt"></i> Inicializar desde Listados';
        }
    }

    // =================================================================
    // FUNCIÓN: RENDERIZAR TABLA
    // =================================================================

    /**
     * Renderiza los resultados en tablas por sede con acordeón.
     */
    function renderizarTabla(sedes) {
        if (!sedes || sedes.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-info-circle"></i>
                    <p>No hay datos disponibles</p>
                </div>
            `;
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

            // Fila de totales
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

        // Agregar event listeners
        agregarListenersAcordeon();
        agregarListenersEdicion();
    }

    // =================================================================
    // FUNCIÓN: ACORDEÓN
    // =================================================================

    /**
     * Agrega event listeners para el acordeón de sedes.
     */
    function agregarListenersAcordeon() {
        const headers = document.querySelectorAll('.sede-header');

        headers.forEach(header => {
            header.addEventListener('click', function() {
                const body = this.nextElementSibling;

                // Toggle classes
                this.classList.toggle('collapsed');
                body.classList.toggle('collapsed');
            });
        });
    }

    // =================================================================
    // FUNCIÓN: EDICIÓN INLINE
    // =================================================================

    /**
     * Agrega event listeners a las celdas editables.
     */
    function agregarListenersEdicion() {
        const editableCells = document.querySelectorAll('.editable-cell');

        editableCells.forEach(cell => {
            cell.addEventListener('click', function(e) {
                // Evitar que el click se propague al header del acordeón
                e.stopPropagation();
                hacerEditable(this);
            });
        });
    }

    /**
     * Convierte una celda en editable.
     */
    function hacerEditable(cell) {
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
                ERPUtils.showAlert('Valor inválido', 'error');
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
                    ERPUtils.showNotification('Valor actualizado exitosamente', 'success');

                    // Actualizar totales
                    actualizarTotales(cell.closest('table'));
                } else {
                    ERPUtils.showAlert(data.error || 'Error al actualizar', 'error');
                    cell.innerHTML = `<span class="value">${currentValue}</span><i class="fas fa-edit edit-icon"></i>`;
                }
            } catch (error) {
                console.error('Error:', error);
                ERPUtils.showAlert('Error de conexión al servidor', 'error');
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
     * Actualiza los totales de una tabla después de editar.
     */
    function actualizarTotales(table) {
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
                const rowTotal =
                    parseInt(cells[2].querySelector('.value')?.textContent || 0) +
                    parseInt(cells[3].querySelector('.value')?.textContent || 0) +
                    parseInt(cells[4].querySelector('.value')?.textContent || 0) +
                    parseInt(cells[5].querySelector('.value')?.textContent || 0);
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

        // Actualizar resumen en el header
        const sedeCard = table.closest('.sede-card');
        if (sedeCard) {
            const summary = sedeCard.querySelector('.sede-summary span');
            if (summary) {
                summary.textContent = `${totalGeneral} raciones`;
            }
        }
    }

    // =================================================================
    // FUNCIÓN: MOSTRAR CARGANDO
    // =================================================================

    /**
     * Muestra un indicador de carga.
     */
    function mostrarCargando() {
        resultsContainer.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Cargando datos...</p>
            </div>
        `;
    }
});
