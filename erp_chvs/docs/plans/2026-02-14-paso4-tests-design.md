# Diseno de Tests Integracion Paso 4

## Objetivo
Validar lo descrito en `erp_chvs/PASO4_README.md` para mejoras de UI del editor de preparaciones.

## Alcance
- Backend: mantener contrato funcional de vista y guardado por nivel.
- Frontend: validar contrato de template y JavaScript para sliders, tooltips, sincronizacion y overlay.

## Enfoque
- Tests de integracion con `Client` para render de template y endpoint.
- Tests de contrato sobre `static/js/nutricion/preparaciones_editor.js` leyendo el archivo y verificando funciones/flujo clave.

## Casos implementados
1. `test_paso4_template_incluye_slider_y_labels_de_rango`
2. `test_paso4_template_incluye_tooltips_y_data_nutricional`
3. `test_paso4_js_contiene_funciones_clave_de_sync_y_validacion`
4. `test_paso4_js_contiene_overlay_y_uso_en_guardar_y_sincronizar`

## Resultado
La suite `nutricion.tests_paso2_preparaciones_editor` ejecuta 9 tests (PASO 2 + PASO 4) en verde.
