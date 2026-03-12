# Documento 1: Análisis Funcional del Módulo de Despachos (Referencia: Supply Controller)

Este documento detalla el comportamiento, la estructura y las funcionalidades observadas en el módulo de "Despachos" de la plataforma Supply Controller, para servir como línea base en la adaptación hacia la aplicación `planeacion` del proyecto ERP_CHVS.

## 1. Estructura General del Menú
El módulo se divide en tres sub-opciones principales, lo que indica un flujo de trabajo en tres etapas:
1.  **Generar Proyección:** (Posiblemente) La planificación a largo plazo de los despachos basada en variables iniciales.
2.  **Generar Despacho:** La creación u orden de salida específica para una fecha o paquete de sedes.
3.  **Consultar Despacho:** Un panel gerencial e interactivo para visualizar el estado operativo de los despachos en una vista consolidada.

## 2. Pantalla de "Consultar Despacho" (El Core Visual)

La pantalla principal de consulta está estructurada para dar respuestas rápidas basadas en variables geográficas y operativas. Se divide en dos componentes críticos:

### A. Panel de Filtros Multidimensionales
Agrupa los criterios de búsqueda de manera descendente (de lo macro a lo micro):
*   **Programa:** El contrato o licitación macro (ej: "CONSORCIO ALIMENTANDO CALI 2026").
*   **Departamento:** Filtro geográfico principal.
*   **Municipio:** Filtro geográfico secundario, dependiente del departamento.
*   **Modalidad:** Filtro operativo crítico (ej: "Complemento Alimentario", "Almuerzo Jornada Única", "Complemento AM/PM Industrializado").

*Acción:* Al aplicar estos filtros mediante el botón "Consultar", la vista inferior se actualiza para mostrar únicamente las operaciones que coinciden.

### B. Vista de Calendario Visual (El Tablero Operativo)
La innovación visual reside en no usar una simple tabla de datos, sino un **calendario mensual interactivo**.
*   Muestra el mes en curso (ej: Marzo 2026) en una cuadrícula de días (lunes a domingo).
*   Permite navegar entre meses y retornar rápidamente al día actual ("Hoy").
*   **Hipótesis de uso funcional:** En cada celda/día del calendario, el sistema debe indicar de forma gráfica (con colores, iconos o barras) el volumen de entregas programadas, si una escuela fue atendida, o si hay despachos pendientes. Es una herramienta de *tracking* logístico en tiempo real.

## 3. Conclusiones y Propuesta de Valor Extraída

La genialidad de este módulo reside en su simplicidad en la superficie para el operador que visualiza la información. No abruma con listados de miles de filas, sino que concentra la operación de toda una ciudad en un mapa temporal (el calendario).

**Para ERP_CHVS (App Planeación):** 
Nuestra meta no es solo replicar esta interfaz, sino **potenciarla**. Dado que ya contamos con un módulo de `logistica` (rutas) y un diseño de integración con SIESA (`PROPUESTA_INTEGRACION_SIESA.md`), nuestro módulo de despachos en `planeacion` puede convertirse en el **orquestador central**:
*   Desde el calendario determinaremos automáticamente las necesidades en gramos mediante el módulo de `nutricion`.
*   El botón de "Generar Despacho" no solo creará un registro web, sino que será el disparador para enviar las Requisiciones de Compra/Ordenes (SC/RQI) al ERP Financiero a través de la capa `Api/`.
