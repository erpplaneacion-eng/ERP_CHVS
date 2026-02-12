/**
 * Módulo de Cálculos Nutricionales
 * Responsable de calcular totales, porcentajes de adecuación y ajustes de peso
 */

const CalculosNutricionales = {
    /**
     * Recalcula los totales nutricionales de un nivel escolar
     * @param {number} nivelIndex - Índice del nivel escolar
     * @param {boolean} skipAutoSave - Si true, no ejecuta guardado automático
     */
    recalcularTotalesNivel(nivelIndex, skipAutoSave = false) {
        let totalCalorias = 0;
        let totalProteina = 0;
        let totalGrasa = 0;
        let totalCho = 0;
        let totalCalcio = 0;
        let totalHierro = 0;
        let totalSodio = 0;
        let totalPesoNeto = 0;
        let totalPesoBruto = 0;

        // Sumar todos los ingredientes del nivel
        $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each(function() {
            const fila = $(this);
            const prepIndex = fila.data('prep');
            const ingIndex = fila.data('ing');

            const calorias = parseFloat($(`#cal-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const proteina = parseFloat($(`#prot-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const grasa = parseFloat($(`#grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const cho = parseFloat($(`#cho-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const calcio = parseFloat($(`#calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const hierro = parseFloat($(`#hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const sodio = parseFloat($(`#sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;
            const pesoNeto = parseFloat(fila.find('.peso-input').val()) || 0;
            const pesoBruto = parseFloat($(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;

            totalCalorias += calorias;
            totalProteina += proteina;
            totalGrasa += grasa;
            totalCho += cho;
            totalCalcio += calcio;
            totalHierro += hierro;
            totalSodio += sodio;
            totalPesoNeto += pesoNeto;
            totalPesoBruto += pesoBruto;
        });

        // Actualizar totales en la interfaz (dentro del card-body)
        $(`#nivel-${nivelIndex}-calorias`).text(`${totalCalorias.toFixed(1)} Kcal`);
        $(`#nivel-${nivelIndex}-proteina`).text(`${totalProteina.toFixed(1)} g`);
        $(`#nivel-${nivelIndex}-grasa`).text(`${totalGrasa.toFixed(1)} g`);
        $(`#nivel-${nivelIndex}-cho`).text(`${totalCho.toFixed(1)} g`);
        $(`#nivel-${nivelIndex}-calcio`).text(`${totalCalcio.toFixed(1)} mg`);
        $(`#nivel-${nivelIndex}-hierro`).text(`${totalHierro.toFixed(1)} mg`);
        $(`#nivel-${nivelIndex}-sodio`).text(`${totalSodio.toFixed(1)} mg`);

        // Actualizar badges en el header del acordeón
        const headerButton = $(`#heading-${nivelIndex}`).find('.nivel-header-btn');
        const badges = headerButton.find('.nivel-summary');
        badges.html(`
            <span class="badge badge-primary">${totalCalorias.toFixed(0)} Kcal</span>
            <span class="badge badge-success">${totalPesoNeto.toFixed(0)}g neto</span>
            <span class="badge badge-warning">${totalPesoBruto.toFixed(0)}g bruto</span>
        `);

        // Recalcular porcentajes de adecuación
        this.recalcularPorcentajesAdecuacion(nivelIndex, {
            calorias: totalCalorias,
            proteina: totalProteina,
            grasa: totalGrasa,
            cho: totalCho,
            calcio: totalCalcio,
            hierro: totalHierro,
            sodio: totalSodio
        });

        // Guardado automático después de los cálculos (solo si no se omite)
        if (!skipAutoSave && window.menuActual && window.menuActual.id) {
            setTimeout(() => {
                GuardadoAutomatico.guardarAnalisis(nivelIndex, window.menuActual.id);
            }, 500); // Pequeño delay para asegurar que todos los cálculos terminen
        }
    },

    /**
     * Calcula y ajusta los pesos de los ingredientes desde el porcentaje de adecuación deseado.
     * Distribuye proporcionalmente el ajuste entre TODOS los ingredientes que aportan el nutriente.
     *
     * @param {number} nivelIndex - Índice del nivel escolar
     * @param {string} nutriente - Nutriente a ajustar (ej: 'calorias', 'proteina')
     * @param {number} porcentajeDeseado - Porcentaje de adecuación deseado (0-100)
     */
    calcularPesosDesdeAdecuacion(nivelIndex, nutriente, porcentajeDeseado) {
        // Obtener el requerimiento nutricional para este nivel y nutriente
        if (!window.requerimientosNiveles || !window.requerimientosNiveles[nivelIndex]) {
            console.warn('No hay datos nutricionales disponibles para nivel:', nivelIndex);
            return;
        }

        const requerimientos = window.requerimientosNiveles[nivelIndex];

        // Mapeo de nombres de nutrientes a claves de requerimientos
        const nutrienteMap = {
            'calorias': 'calorias',
            'calorias': 'calorias',
            'proteina': 'proteina',
            'proteina': 'proteina',
            'grasa': 'grasa',
            'grasa': 'grasa',
            'cho': 'cho',
            'cho': 'cho',
            'calcio': 'calcio',
            'calcio': 'calcio',
            'hierro': 'hierro',
            'hierro': 'hierro',
            'sodio': 'sodio',
            'sodio': 'sodio'
        };

        const nutrienteKey = nutrienteMap[nutriente];
        const requerimientoNecesario = requerimientos[nutrienteKey] || 0;

        if (requerimientoNecesario === 0) {
            console.warn('Requerimiento no encontrado para:', nutriente);
            return;
        }

        // Calcular el valor objetivo del nutriente (limitado entre 0-100%)
        const porcentajeValido = Math.max(0, Math.min(100, porcentajeDeseado));
        const valorObjetivo = (porcentajeValido * requerimientoNecesario) / 100;

        console.log(`[${nutriente}] Objetivo: ${valorObjetivo.toFixed(2)} (${porcentajeValido}% de ${requerimientoNecesario})`);

        // Recolectar información de todos los ingredientes con sus aportes actuales
        const ingredientesData = [];
        let valorActualTotal = 0;

        $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each(function() {
            const row = $(this);
            const pesoInput = row.find('.peso-input');
            const prepIndex = row.data('prep');
            const ingIndex = row.data('ing');
            const pesoActual = parseFloat(pesoInput.val()) || 0;

            // Obtener nutriente por 100g del data attribute
            let nutrientePor100g = 0;
            switch (nutrienteKey) {
                case 'calorias':
                    nutrientePor100g = parseFloat(pesoInput.data('calorias')) || 0;
                    break;
                case 'proteina':
                    nutrientePor100g = parseFloat(pesoInput.data('proteina')) || 0;
                    break;
                case 'grasa':
                    nutrientePor100g = parseFloat(pesoInput.data('grasa')) || 0;
                    break;
                case 'cho':
                    nutrientePor100g = parseFloat(pesoInput.data('cho')) || 0;
                    break;
                case 'calcio':
                    nutrientePor100g = parseFloat(pesoInput.data('calcio')) || 0;
                    break;
                case 'hierro':
                    nutrientePor100g = parseFloat(pesoInput.data('hierro')) || 0;
                    break;
                case 'sodio':
                    nutrientePor100g = parseFloat(pesoInput.data('sodio')) || 0;
                    break;
            }

            const valorActual = (nutrientePor100g * pesoActual) / 100;
            valorActualTotal += valorActual;

            // Solo guardar ingredientes que aportan este nutriente
            if (nutrientePor100g > 0.1) {
                ingredientesData.push({
                    pesoInput: pesoInput,
                    nutrientePor100g: nutrientePor100g,
                    pesoActual: pesoActual,
                    valorActual: valorActual,
                    prepIndex: prepIndex,
                    ingIndex: ingIndex,
                    row: row
                });
            }
        });

        if (ingredientesData.length === 0) {
            console.warn('No hay ingredientes que aporten el nutriente:', nutriente);
            return;
        }

        // Calcular cuánto necesitamos ajustar
        const diferencia = valorObjetivo - valorActualTotal;

        if (Math.abs(diferencia) < 0.01) {
            console.log('El valor actual ya está muy cerca del objetivo');
            return;
        }

        console.log(`Diferencia a ajustar: ${diferencia.toFixed(2)}`);

        // ESTRATEGIA DE AJUSTE PROPORCIONAL:
        // Calcular el factor de escala proporcional para mantener las proporciones de la receta
        const factorEscala = valorActualTotal > 0 ? (valorObjetivo / valorActualTotal) : 1;

        // Aplicar el factor de escala a todos los ingredientes que aportan el nutriente
        ingredientesData.forEach(ing => {
            const nuevoPeso = ing.pesoActual * factorEscala;
            const pesoFinal = Math.max(0, nuevoPeso);

            ing.pesoInput.val(pesoFinal.toFixed(1));
            console.log(`  - Ingrediente [${ing.prepIndex}-${ing.ingIndex}]: ${ing.pesoActual.toFixed(1)}g → ${pesoFinal.toFixed(1)}g`);
        });

        // Recalcular manualmente todos los valores nutricionales sin disparar eventos
        ingredientesData.forEach(ing => {
            const pesoNeto = parseFloat(ing.pesoInput.val()) || 0;
            const parteComestible = parseFloat(ing.pesoInput.data('parte-comestible')) || 100;
            const factor = pesoNeto / 100;

            // Calcular peso bruto
            const pesoBruto = parteComestible > 0 ? (pesoNeto * 100) / parteComestible : pesoNeto;

            // Calcular nutrientes
            const calorias = (parseFloat(ing.pesoInput.data('calorias')) || 0) * factor;
            const proteina = (parseFloat(ing.pesoInput.data('proteina')) || 0) * factor;
            const grasa = (parseFloat(ing.pesoInput.data('grasa')) || 0) * factor;
            const cho = (parseFloat(ing.pesoInput.data('cho')) || 0) * factor;
            const calcio = (parseFloat(ing.pesoInput.data('calcio')) || 0) * factor;
            const hierro = (parseFloat(ing.pesoInput.data('hierro')) || 0) * factor;
            const sodio = (parseFloat(ing.pesoInput.data('sodio')) || 0) * factor;

            // Actualizar UI directamente
            $(`#bruto-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(pesoBruto.toFixed(0));
            $(`#cal-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(calorias.toFixed(1));
            $(`#prot-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(proteina.toFixed(1));
            $(`#grasa-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(grasa.toFixed(1));
            $(`#cho-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(cho.toFixed(1));
            $(`#calcio-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(calcio.toFixed(1));
            $(`#hierro-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(hierro.toFixed(1));
            $(`#sodio-${nivelIndex}-${ing.prepIndex}-${ing.ingIndex}`).text(sodio.toFixed(1));
        });

        // Recalcular totales una sola vez al final (CON guardado automático)
        this.recalcularTotalesNivel(nivelIndex, false);
        console.log(`✓ Ajuste proporcional completado para ${nutriente} (factor: ${factorEscala.toFixed(3)})`);
    },

    /**
     * Recalcula los porcentajes de adecuación nutricional
     * @param {number} nivelIndex - Índice del nivel escolar
     * @param {object} totales - Totales nutricionales calculados
     */
    recalcularPorcentajesAdecuacion(nivelIndex, totales) {
        console.log('Recalculando porcentajes para nivel:', nivelIndex, 'totales:', totales);

        // Obtener requerimientos desde los datos almacenados globalmente
        const requerimientos = window.requerimientosNiveles && window.requerimientosNiveles[nivelIndex];

        if (!requerimientos) {
            console.warn(`No se encontraron requerimientos para nivel ${nivelIndex}`);
            return;
        }

        const nutrientes = [
            { key: 'calorias', id: 'calorias' },
            { key: 'proteina', id: 'proteina' },
            { key: 'grasa', id: 'grasa' },
            { key: 'cho', id: 'cho' },
            { key: 'calcio', id: 'calcio' },
            { key: 'hierro', id: 'hierro' },
            { key: 'sodio', id: 'sodio' }
        ];

        nutrientes.forEach(nutriente => {
            const total = totales[nutriente.key] || 0;
            const requerido = requerimientos[nutriente.key] || 1;

            // Calcular porcentaje limitado entre 0-100%
            let porcentaje = (total / requerido) * 100;
            porcentaje = Math.min(Math.max(porcentaje, 0), 100); // Limitar entre 0-100

            const estado = this.getEstadoAdecuacion(porcentaje, nutriente.key);

            // Actualizar input de porcentaje editable
            const inputPorcentaje = $(`#nivel-${nivelIndex}-${nutriente.id}-pct`);
            if (inputPorcentaje.length) {
                inputPorcentaje.val(porcentaje.toFixed(1));
                inputPorcentaje.closest('.adecuacion-mini').attr('data-estado', estado);
            }

            // Actualizar estado de la tarjeta de total
            const elementoTotal = $(`#nivel-${nivelIndex}-${nutriente.id}`);
            if (elementoTotal.length) {
                elementoTotal.closest('.total-mini').attr('data-estado', estado);
            }
        });
    },

    /**
     * Determina el estado de adecuación nutricional según el porcentaje alcanzado.
     *
     * RANGOS DE EVALUACIÓN (consistentes con el backend Python):
     * - 0-35%: ÓPTIMO (verde) - Aporte bajo pero seguro
     * - 35.1-70%: ACEPTABLE (amarillo) - Aporte moderado
     * - >70%: ALTO (rojo) - Aporte elevado, cerca del límite máximo
     *
     * @param {number} porcentaje - Porcentaje de adecuación (0-100)
     * @param {string} nutriente - Nombre del nutriente (opcional)
     * @returns {string} Estado: 'optimo', 'aceptable', o 'alto'
     */
    getEstadoAdecuacion(porcentaje, nutriente) {
        // Validar y limitar porcentaje entre 0-100
        porcentaje = Math.max(0, Math.min(100, porcentaje));

        // Rangos uniformes para todos los nutrientes
        if (porcentaje <= 35) {
            return 'optimo';      // 0-35%: Verde
        } else if (porcentaje <= 70) {
            return 'aceptable';   // 35.1-70%: Amarillo
        } else {
            return 'alto';        // >70%: Rojo
        }
    }
};

// Exponer globalmente para compatibilidad con código legacy
window.CalculosNutricionales = CalculosNutricionales;
window.recalcularTotalesNivel = CalculosNutricionales.recalcularTotalesNivel.bind(CalculosNutricionales);
window.calcularPesosDesdeAdecuacion = CalculosNutricionales.calcularPesosDesdeAdecuacion.bind(CalculosNutricionales);
window.recalcularPorcentajesAdecuacion = CalculosNutricionales.recalcularPorcentajesAdecuacion.bind(CalculosNutricionales);
window.getEstadoAdecuacion = CalculosNutricionales.getEstadoAdecuacion.bind(CalculosNutricionales);
