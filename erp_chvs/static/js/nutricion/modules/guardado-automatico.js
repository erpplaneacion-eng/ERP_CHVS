/**
 * Módulo de Guardado Automático
 * Responsable de persistir los cambios del análisis nutricional al servidor
 */

const GuardadoAutomatico = {
    /**
     * Guarda automáticamente el análisis nutricional editado
     * Se ejecuta después de cada cambio en pesos o porcentajes
     *
     * @param {number} nivelIndex - Índice del nivel escolar
     * @param {number} menuId - ID del menú
     */
    async guardarAnalisis(nivelIndex, menuId) {
        try {
            // Recopilar totales actuales del nivel
            const totales = {
                calorias: parseFloat($(`#nivel-${nivelIndex}-calorias`).text().replace(' Kcal', '')) || 0,
                proteina: parseFloat($(`#nivel-${nivelIndex}-proteina`).text().replace(' g', '')) || 0,
                grasa: parseFloat($(`#nivel-${nivelIndex}-grasa`).text().replace(' g', '')) || 0,
                cho: parseFloat($(`#nivel-${nivelIndex}-cho`).text().replace(' g', '')) || 0,
                calcio: parseFloat($(`#nivel-${nivelIndex}-calcio`).text().replace(' mg', '')) || 0,
                hierro: parseFloat($(`#nivel-${nivelIndex}-hierro`).text().replace(' mg', '')) || 0,
                sodio: parseFloat($(`#nivel-${nivelIndex}-sodio`).text().replace(' mg', '')) || 0,
                peso_neto: 0,  // Se calculará sumando ingredientes
                peso_bruto: 0  // Se calculará sumando ingredientes
            };

            // Recopilar porcentajes de adecuación
            const porcentajes = {
                calorias: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="calorias"]`).val()) || 0,
                proteina: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="proteina"]`).val()) || 0,
                grasa: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="grasa"]`).val()) || 0,
                cho: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="cho"]`).val()) || 0,
                calcio: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="calcio"]`).val()) || 0,
                hierro: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="hierro"]`).val()) || 0,
                sodio: parseFloat($(`.porcentaje-input[data-nivel="${nivelIndex}"][data-nutriente="sodio"]`).val()) || 0
            };

            // Recopilar datos de ingredientes configurados
            const ingredientes = [];
            $(`.ingrediente-row[data-nivel="${nivelIndex}"]`).each(function() {
                const row = $(this);
                const prepIndex = row.data('prep');
                const ingIndex = row.data('ing');
                const pesoInput = row.find('.peso-input');

                // Obtener IDs reales desde data attributes
                const prepIdReal = row.data('prep-id') || pesoInput.data('prep-id');
                const ingIdReal = row.data('ing-id') || pesoInput.data('ing-id');

                console.log(`[DEBUG] Guardando ingrediente - Índices: prep=${prepIndex}, ing=${ingIndex}, IDs reales: prepId=${prepIdReal}, ingId=${ingIdReal}`);

                const pesoNeto = parseFloat(pesoInput.val()) || 0;
                const pesoBruto = parseFloat($(`#bruto-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0;

                const ingrediente = {
                    id_preparacion: prepIdReal,
                    id_ingrediente_siesa: ingIdReal,
                    peso_neto: pesoNeto,
                    peso_bruto: pesoBruto,
                    calorias: parseFloat($(`#cal-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                    proteina: parseFloat($(`#prot-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                    grasa: parseFloat($(`#grasa-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                    cho: parseFloat($(`#cho-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                    calcio: parseFloat($(`#calcio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                    hierro: parseFloat($(`#hierro-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0,
                    sodio: parseFloat($(`#sodio-${nivelIndex}-${prepIndex}-${ingIndex}`).text()) || 0
                };

                // Acumular pesos totales
                totales.peso_neto += pesoNeto;
                totales.peso_bruto += pesoBruto;

                ingredientes.push(ingrediente);
            });

            // Obtener ID del nivel escolar desde los datos almacenados
            const idNivelEscolar = datosNutricionales &&
                                  datosNutricionales.analisis_por_nivel &&
                                  datosNutricionales.analisis_por_nivel[nivelIndex] &&
                                  datosNutricionales.analisis_por_nivel[nivelIndex].nivel_escolar &&
                                  datosNutricionales.analisis_por_nivel[nivelIndex].nivel_escolar.id;

            console.log('[DEBUG] ID Nivel Escolar obtenido:', {
                nivelIndex,
                idNivelEscolar,
                nivel_escolar_completo: datosNutricionales?.analisis_por_nivel?.[nivelIndex]?.nivel_escolar,
                existe_datos: !!datosNutricionales
            });

            if (!idNivelEscolar || idNivelEscolar === '-1' || idNivelEscolar === -1) {
                console.error('ID de nivel escolar inválido:', idNivelEscolar);
                console.error('Datos completos:', datosNutricionales?.analisis_por_nivel?.[nivelIndex]);
                NutricionUtils.mostrarNotificacion('error', 'No se puede guardar: nivel escolar inválido');
                return;
            }

            // Preparar datos para el guardado
            const datosGuardado = {
                id_menu: menuId,
                id_nivel_escolar: idNivelEscolar,
                totales: totales,
                porcentajes: porcentajes,
                ingredientes: ingredientes
            };

            console.log('[GUARDADO AUTOMÁTICO] Datos a enviar:', {
                menuId,
                idNivelEscolar,
                totalIngredientes: ingredientes.length,
                datosCompletos: datosGuardado
            });

            // Enviar datos al servidor
            const response = await fetch('/nutricion/api/guardar-analisis-nutricional/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': NutricionUtils.getCsrfToken()
                },
                body: JSON.stringify(datosGuardado)
            });

            console.log('[GUARDADO AUTOMÁTICO] Response status:', response.status);

            const result = await response.json();
            console.log('[GUARDADO AUTOMÁTICO] Response data:', result);

            if (result.success) {
                console.log('✓ Análisis nutricional guardado automáticamente:', {
                    analisisId: result.analisis_id,
                    ingredientesGuardados: result.ingredientes_guardados,
                    created: result.created
                });

                // Mostrar indicador visual de guardado exitoso
                NutricionUtils.mostrarNotificacion('success', `Guardado: ${result.ingredientes_guardados} ingredientes`);
            } else {
                console.error('✗ Error al guardar análisis nutricional:', result.error);
                NutricionUtils.mostrarNotificacion('error', `Error: ${result.error || 'Desconocido'}`);
            }

        } catch (error) {
            console.error('✗ Error en guardado automático:', error);
            NutricionUtils.mostrarNotificacion('error', `Error: ${error.message || 'Conexión fallida'}`);
        }
    }
};

// Exponer globalmente para compatibilidad con código legacy
window.GuardadoAutomatico = GuardadoAutomatico;
window.guardarAnalisisAutomatico = GuardadoAutomatico.guardarAnalisis.bind(GuardadoAutomatico);
